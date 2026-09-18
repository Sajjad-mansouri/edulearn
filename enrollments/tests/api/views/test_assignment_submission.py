from decimal import Decimal

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from assessments.models import (
    Assignment,
    AssignmentSubmission,
    AssignmentSubmissionFile,
)
from curriculums.models import Lesson, LessonContent, Section


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def section(course):
    return Section.objects.create(
        course=course,
        title="Django Fundamentals",
        description="Django fundamentals section.",
        order=1,
    )


@pytest.fixture
def lesson(section):
    return Lesson.objects.create(
        section=section,
        title="Django Assignment",
        description="Assignment lesson.",
        slug="django-assignment",
        order=1,
        is_published=True,
    )


@pytest.fixture
def assignment_content(lesson):
    return LessonContent.objects.create(
        lesson=lesson,
        is_main_content=True,
        title="Django Assignment",
        content_type=LessonContent.Type.ASSIGNMENT,
        order=1,
    )


@pytest.fixture
def assignment(assignment_content):
    return Assignment.objects.create(
        content=assignment_content,
        instructions="Build a Django application.",
        max_score=100,
        max_attempts=3,
        accepted_file_types="pdf,docx,zip",
        max_file_size_mb=5,
    )


@pytest.fixture
def assignment_submit_url(enrollment, lesson):
    return reverse(
        "enrollment_api:assignment_submit",
        kwargs={
            "enrollment_id": enrollment.id,
            "lesson_id": lesson.id,
        },
    )


@pytest.fixture
def authenticated_client(api_client, test_user):
    api_client.force_authenticate(user=test_user)
    return api_client


@pytest.fixture
def submission(enrollment, assignment):
    return AssignmentSubmission.objects.create(
        assignment=assignment,
        enrollment=enrollment,
        attempt_number=1,
        status=AssignmentSubmission.Status.SUBMITTED,
        submission_text="Initial submission",
    )


class TestAssignmentSubmissionApiViewAuthentication:
    def test_unauthenticated_user_cannot_submit(
        self,
        api_client,
        assignment_submit_url,
    ):
        # Arrange
        payload = {
            "submission_text": "My assignment",
        }

        # Act
        response = api_client.post(
            assignment_submit_url,
            data=payload,
        )

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert AssignmentSubmission.objects.count() == 0


class TestAssignmentSubmissionApiViewAuthorization:
    def test_user_cannot_submit_to_another_users_enrollment(
        self,
        api_client,
        another_user_enrollment,
        assignment,
        lesson,
    ):
        # Arrange
        api_client.force_authenticate(
            user=assignment.content.lesson.section.course.owner
        )

        url = reverse(
            "enrollment_api:assignment_submit",
            kwargs={
                "enrollment_id": another_user_enrollment.id,
                "lesson_id": lesson.id,
            },
        )

        # Act
        response = api_client.post(
            url,
            data={"submission_text": "Unauthorized submission"},
        )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert AssignmentSubmission.objects.count() == 0

    def test_user_cannot_submit_to_nonexistent_enrollment(
        self,
        authenticated_client,
        assignment,
        lesson,
    ):
        # Arrange
        url = reverse(
            "enrollment_api:assignment_submit",
            kwargs={
                "enrollment_id": 999999,
                "lesson_id": lesson.id,
            },
        )

        # Act
        response = authenticated_client.post(
            url,
            data={"submission_text": "Invalid enrollment"},
        )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert AssignmentSubmission.objects.count() == 0

    def test_user_cannot_submit_assignment_from_another_course(
        self,
        authenticated_client,
        enrollment,
        another_user,
        category,
    ):
        # Arrange
        other_course = enrollment.course.__class__.objects.create(
            title="Another Course",
            owner=another_user,
            category=category,
        )

        other_section = Section.objects.create(
            course=other_course,
            title="Other Section",
            order=1,
        )

        other_lesson = Lesson.objects.create(
            section=other_section,
            title="Other Assignment",
            slug="other-assignment",
            order=1,
            is_published=True,
        )

        other_content = LessonContent.objects.create(
            lesson=other_lesson,
            is_main_content=True,
            title="Other Assignment",
            content_type=LessonContent.Type.ASSIGNMENT,
            order=1,
        )

        Assignment.objects.create(
            content=other_content,
            instructions="Assignment from another course.",
            max_attempts=3,
        )

        url = reverse(
            "enrollment_api:assignment_submit",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": other_lesson.id,
            },
        )

        # Act
        response = authenticated_client.post(
            url,
            data={"submission_text": "Cross-course submission"},
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert AssignmentSubmission.objects.count() == 0


class TestAssignmentSubmissionApiViewSuccessfulSubmission:
    def test_successful_submission(
        self,
        authenticated_client,
        assignment,
        assignment_submit_url,
    ):
        # Arrange
        payload = {
            "submission_text": "This is my completed assignment.",
        }

        # Act
        response = authenticated_client.post(
            assignment_submit_url,
            data=payload,
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        data = response.data

        assert data["success"] is True
        assert data["attempts_used"] == 1
        assert data["max_attempts"] == 3
        assert data["attempts_remaining"] == 2
        assert data["can_submit"] is True
        assert data["message"] == "Assignment submitted successfully!"

        submission = AssignmentSubmission.objects.get(
            assignment=assignment,
        )

        assert submission.attempt_number == 1
        assert submission.status == AssignmentSubmission.Status.SUBMITTED
        assert submission.submission_text == "This is my completed assignment."
        assert submission.score is None
        assert submission.feedback == ""
        assert submission.submitted_at is not None
        assert submission.graded_at is None

    def test_submission_text_is_returned(
        self,
        authenticated_client,
        assignment,
        assignment_submit_url,
    ):
        # Arrange
        submission_text = "Detailed assignment solution."

        # Act
        response = authenticated_client.post(
            assignment_submit_url,
            data={"submission_text": submission_text},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["submission"]["submissionText"] == submission_text

    def test_empty_submission_text_is_allowed(
        self,
        authenticated_client,
        assignment,
        assignment_submit_url,
    ):
        # Arrange
        payload = {}

        # Act
        response = authenticated_client.post(
            assignment_submit_url,
            data=payload,
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        submission = AssignmentSubmission.objects.get(
            assignment=assignment,
        )

        assert submission.submission_text == ""
        assert response.data["submission"]["submissionText"] == ""

    def test_new_submission_has_no_score_or_feedback(
        self,
        authenticated_client,
        assignment,
        assignment_submit_url,
    ):
        # Arrange
        payload = {
            "submission_text": "Assignment answer",
        }

        # Act
        response = authenticated_client.post(
            assignment_submit_url,
            data=payload,
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        submission = AssignmentSubmission.objects.get(
            assignment=assignment,
        )

        assert submission.score is None
        assert submission.feedback == ""

        assert response.data["submission"]["score"] is None
        assert response.data["submission"]["feedback"] == ""

    def test_new_submission_is_marked_submitted(
        self,
        authenticated_client,
        assignment,
        assignment_submit_url,
    ):
        # Arrange
        payload = {
            "submission_text": "Assignment answer",
        }

        # Act
        response = authenticated_client.post(
            assignment_submit_url,
            data=payload,
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        submission = AssignmentSubmission.objects.get(
            assignment=assignment,
        )

        assert submission.status == AssignmentSubmission.Status.SUBMITTED
        assert response.data["submission"]["status"] == (
            AssignmentSubmission.Status.SUBMITTED
        )

    def test_submission_attempt_number_starts_at_one(
        self,
        authenticated_client,
        assignment,
        assignment_submit_url,
    ):
        # Arrange
        payload = {
            "submission_text": "First attempt",
        }

        # Act
        response = authenticated_client.post(
            assignment_submit_url,
            data=payload,
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        submission = AssignmentSubmission.objects.get(
            assignment=assignment,
        )

        assert submission.attempt_number == 1
        assert response.data["submission"]["attemptNumber"] == 1

    def test_submitted_at_is_set(
        self,
        authenticated_client,
        assignment,
        assignment_submit_url,
    ):
        # Arrange
        payload = {
            "submission_text": "Assignment answer",
        }

        # Act
        response = authenticated_client.post(
            assignment_submit_url,
            data=payload,
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        submission = AssignmentSubmission.objects.get(
            assignment=assignment,
        )

        assert submission.submitted_at is not None
        assert response.data["submission"]["submittedAt"] is not None

    def test_graded_at_is_none_for_new_submission(
        self,
        authenticated_client,
        assignment,
        assignment_submit_url,
    ):
        # Arrange
        payload = {
            "submission_text": "Assignment answer",
        }

        # Act
        response = authenticated_client.post(
            assignment_submit_url,
            data=payload,
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        submission = AssignmentSubmission.objects.get(
            assignment=assignment,
        )

        assert submission.graded_at is None
        assert response.data["submission"]["gradedAt"] is None


class TestAssignmentSubmissionApiViewAttempts:
    def test_attempt_number_increments_for_existing_submissions(
        self,
        authenticated_client,
        assignment,
        enrollment,
        assignment_submit_url,
    ):
        # Arrange
        AssignmentSubmission.objects.create(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
            status=AssignmentSubmission.Status.SUBMITTED,
            submission_text="First attempt",
        )

        # Act
        response = authenticated_client.post(
            assignment_submit_url,
            data={"submission_text": "Second attempt"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["attempts_used"] == 2
        assert response.data["attempts_remaining"] == 1
        assert response.data["can_submit"] is True
        assert response.data["submission"]["attemptNumber"] == 2

        submissions = AssignmentSubmission.objects.filter(
            assignment=assignment,
            enrollment=enrollment,
        ).order_by("attempt_number")

        assert submissions.count() == 2
        assert submissions[0].attempt_number == 1
        assert submissions[1].attempt_number == 2

    def test_attempts_used_is_incremented(
        self,
        authenticated_client,
        assignment,
        enrollment,
        assignment_submit_url,
    ):
        # Arrange
        AssignmentSubmission.objects.create(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
            status=AssignmentSubmission.Status.SUBMITTED,
        )
        AssignmentSubmission.objects.create(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=2,
            status=AssignmentSubmission.Status.SUBMITTED,
        )

        # Act
        response = authenticated_client.post(
            assignment_submit_url,
            data={"submission_text": "Third attempt"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["attempts_used"] == 3
        assert response.data["attempts_remaining"] == 0
        assert response.data["can_submit"] is False
        assert response.data["submission"]["attemptNumber"] == 3

    def test_max_attempts_is_enforced(
        self,
        authenticated_client,
        assignment,
        enrollment,
        assignment_submit_url,
    ):
        # Arrange
        assignment.max_attempts = 2
        assignment.save(update_fields=["max_attempts"])

        for attempt_number in (1, 2):
            AssignmentSubmission.objects.create(
                assignment=assignment,
                enrollment=enrollment,
                attempt_number=attempt_number,
                status=AssignmentSubmission.Status.SUBMITTED,
            )

        # Act
        response = authenticated_client.post(
            assignment_submit_url,
            data={"submission_text": "Third attempt"},
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False
        assert response.data["error"] == "Maximum attempts reached"
        assert response.data["max_attempts"] == 2
        assert response.data["attempts_used"] == 2

        assert (
            AssignmentSubmission.objects.filter(
                assignment=assignment,
                enrollment=enrollment,
            ).count()
            == 2
        )

    def test_max_attempts_one_allows_only_one_submission(
        self,
        authenticated_client,
        assignment,
        enrollment,
        assignment_submit_url,
    ):
        # Arrange
        assignment.max_attempts = 1
        assignment.save(update_fields=["max_attempts"])

        # Act
        first_response = authenticated_client.post(
            assignment_submit_url,
            data={"submission_text": "First attempt"},
        )

        second_response = authenticated_client.post(
            assignment_submit_url,
            data={"submission_text": "Second attempt"},
        )

        # Assert
        assert first_response.status_code == status.HTTP_200_OK
        assert first_response.data["attempts_used"] == 1
        assert first_response.data["attempts_remaining"] == 0
        assert first_response.data["can_submit"] is False

        assert second_response.status_code == status.HTTP_400_BAD_REQUEST
        assert second_response.data["success"] is False
        assert second_response.data["attempts_used"] == 1

        assert (
            AssignmentSubmission.objects.filter(
                assignment=assignment,
                enrollment=enrollment,
            ).count()
            == 1
        )

    def test_unlimited_attempts_are_allowed(
        self,
        authenticated_client,
        assignment,
        enrollment,
        assignment_submit_url,
    ):
        # Arrange
        assignment.max_attempts = 0
        assignment.save(update_fields=["max_attempts"])

        # Act
        responses = [
            authenticated_client.post(
                assignment_submit_url,
                data={"submission_text": f"Attempt {attempt}"},
            )
            for attempt in range(1, 5)
        ]

        # Assert
        assert all(response.status_code == status.HTTP_200_OK for response in responses)

        last_response = responses[-1]

        assert last_response.data["attempts_used"] == 4
        assert last_response.data["max_attempts"] == 0
        assert last_response.data["attempts_remaining"] == "Unlimited"
        assert last_response.data["can_submit"] is True

        assert (
            AssignmentSubmission.objects.filter(
                assignment=assignment,
                enrollment=enrollment,
            ).count()
            == 4
        )

    def test_completed_enrollment_can_submit(
        self,
        authenticated_client,
        assignment,
        enrollment,
        assignment_submit_url,
    ):
        # Arrange
        enrollment.status = enrollment.Status.COMPLETED
        enrollment.save(update_fields=["status"])

        # Act
        response = authenticated_client.post(
            assignment_submit_url,
            data={"submission_text": "Completed enrollment submission"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

        assert (
            AssignmentSubmission.objects.filter(
                assignment=assignment,
                enrollment=enrollment,
            ).count()
            == 1
        )


class TestAssignmentSubmissionApiViewFileValidation:
    def test_accepts_valid_file_type(
        self,
        authenticated_client,
        assignment,
        assignment_submit_url,
    ):
        # Arrange
        uploaded_file = SimpleUploadedFile(
            "assignment.pdf",
            b"assignment content",
            content_type="application/pdf",
        )

        # Act
        response = authenticated_client.post(
            assignment_submit_url,
            data={
                "submission_text": "Assignment with PDF",
                "files": uploaded_file,
            },
            format="multipart",
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_accepts_multiple_configured_file_types(
        self,
        authenticated_client,
        assignment,
        assignment_submit_url,
    ):
        # Arrange
        pdf_file = SimpleUploadedFile(
            "assignment.pdf",
            b"pdf content",
            content_type="application/pdf",
        )
        docx_file = SimpleUploadedFile(
            "assignment.docx",
            b"docx content",
            content_type=(
                "application/vnd.openxmlformats-officedocument"
                ".wordprocessingml.document"
            ),
        )

        # Act
        response = authenticated_client.post(
            assignment_submit_url,
            data={
                "files": [pdf_file, docx_file],
            },
            format="multipart",
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

        submission = AssignmentSubmission.objects.get(
            assignment=assignment,
        )

        assert submission.files.count() == 2

    def test_file_extension_matching_is_case_insensitive(
        self,
        authenticated_client,
        assignment,
        assignment_submit_url,
    ):
        # Arrange
        uploaded_file = SimpleUploadedFile(
            "assignment.PDF",
            b"assignment content",
            content_type="application/pdf",
        )

        # Act
        response = authenticated_client.post(
            assignment_submit_url,
            data={"files": uploaded_file},
            format="multipart",
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_file_type_configuration_ignores_whitespace(
        self,
        authenticated_client,
        assignment,
        assignment_submit_url,
    ):
        # Arrange
        assignment.accepted_file_types = "pdf, docx, zip"
        assignment.save(update_fields=["accepted_file_types"])

        uploaded_file = SimpleUploadedFile(
            "assignment.docx",
            b"assignment content",
            content_type=(
                "application/vnd.openxmlformats-officedocument"
                ".wordprocessingml.document"
            ),
        )

        # Act
        response = authenticated_client.post(
            assignment_submit_url,
            data={"files": uploaded_file},
            format="multipart",
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_rejects_invalid_file_type(
        self,
        authenticated_client,
        assignment,
        assignment_submit_url,
    ):
        # Arrange
        uploaded_file = SimpleUploadedFile(
            "assignment.exe",
            b"executable content",
            content_type="application/octet-stream",
        )

        # Act
        response = authenticated_client.post(
            assignment_submit_url,
            data={"files": uploaded_file},
            format="multipart",
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False
        assert response.data["error"] == (
            "Invalid file(s). Check file types and sizes."
        )

        assert AssignmentSubmission.objects.count() == 0
        assert AssignmentSubmissionFile.objects.count() == 0

    def test_rejects_file_larger_than_maximum_size(
        self,
        authenticated_client,
        assignment,
        assignment_submit_url,
    ):
        # Arrange
        assignment.max_file_size_mb = 1
        assignment.save(update_fields=["max_file_size_mb"])

        oversized_content = b"x" * (1024 * 1024 + 1)

        uploaded_file = SimpleUploadedFile(
            "large.pdf",
            oversized_content,
            content_type="application/pdf",
        )

        # Act
        response = authenticated_client.post(
            assignment_submit_url,
            data={"files": uploaded_file},
            format="multipart",
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False
        assert response.data["error"] == (
            "Invalid file(s). Check file types and sizes."
        )

        assert AssignmentSubmission.objects.count() == 0
        assert AssignmentSubmissionFile.objects.count() == 0

    def test_accepts_file_exactly_at_maximum_size(
        self,
        authenticated_client,
        assignment,
        assignment_submit_url,
    ):
        # Arrange
        assignment.max_file_size_mb = 1
        assignment.save(update_fields=["max_file_size_mb"])

        exact_size_content = b"x" * (1024 * 1024)

        uploaded_file = SimpleUploadedFile(
            "maximum.pdf",
            exact_size_content,
            content_type="application/pdf",
        )

        # Act
        response = authenticated_client.post(
            assignment_submit_url,
            data={"files": uploaded_file},
            format="multipart",
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_accepts_any_file_when_no_file_types_are_configured(
        self,
        authenticated_client,
        assignment,
        assignment_submit_url,
    ):
        # Arrange
        assignment.accepted_file_types = ""
        assignment.save(update_fields=["accepted_file_types"])

        uploaded_file = SimpleUploadedFile(
            "assignment.xyz",
            b"arbitrary file content",
            content_type="application/octet-stream",
        )

        # Act
        response = authenticated_client.post(
            assignment_submit_url,
            data={"files": uploaded_file},
            format="multipart",
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

        assert AssignmentSubmissionFile.objects.count() == 1

    def test_accepts_file_with_no_extension_when_no_types_are_configured(
        self,
        authenticated_client,
        assignment,
        assignment_submit_url,
    ):
        # Arrange
        assignment.accepted_file_types = ""
        assignment.save(update_fields=["accepted_file_types"])

        uploaded_file = SimpleUploadedFile(
            "assignment",
            b"file without extension",
            content_type="application/octet-stream",
        )

        # Act
        response = authenticated_client.post(
            assignment_submit_url,
            data={"files": uploaded_file},
            format="multipart",
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True


class TestAssignmentSubmissionApiViewFilePersistence:
    def test_file_submission_creates_file_record(
        self,
        authenticated_client,
        assignment,
        assignment_submit_url,
    ):
        # Arrange
        uploaded_file = SimpleUploadedFile(
            "assignment.pdf",
            b"assignment content",
            content_type="application/pdf",
        )

        # Act
        response = authenticated_client.post(
            assignment_submit_url,
            data={"files": uploaded_file},
            format="multipart",
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        submission = AssignmentSubmission.objects.get(
            assignment=assignment,
        )

        submission_file = AssignmentSubmissionFile.objects.get(
            submission=submission,
        )

        assert submission_file.original_filename == "assignment.pdf"
        assert submission_file.size == len(b"assignment content")
        assert submission_file.file
        assert submission_file.file_name == "assignment.pdf"

    def test_original_filename_is_preserved(
        self,
        authenticated_client,
        assignment,
        assignment_submit_url,
    ):
        # Arrange
        uploaded_file = SimpleUploadedFile(
            "my-final-assignment.pdf",
            b"final assignment",
            content_type="application/pdf",
        )

        # Act
        response = authenticated_client.post(
            assignment_submit_url,
            data={"files": uploaded_file},
            format="multipart",
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        submission_file = AssignmentSubmissionFile.objects.get()

        assert submission_file.original_filename == ("my-final-assignment.pdf")

    def test_multiple_files_create_multiple_file_records(
        self,
        authenticated_client,
        assignment,
        assignment_submit_url,
    ):
        # Arrange
        first_file = SimpleUploadedFile(
            "assignment.pdf",
            b"pdf content",
            content_type="application/pdf",
        )
        second_file = SimpleUploadedFile(
            "source.zip",
            b"zip content",
            content_type="application/zip",
        )

        # Act
        response = authenticated_client.post(
            assignment_submit_url,
            data={
                "files": [first_file, second_file],
            },
            format="multipart",
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        submission = AssignmentSubmission.objects.get(
            assignment=assignment,
        )

        files = AssignmentSubmissionFile.objects.filter(
            submission=submission,
        ).order_by("id")

        assert files.count() == 2
        assert files[0].original_filename == "assignment.pdf"
        assert files[1].original_filename == "source.zip"

    def test_file_size_is_saved_from_uploaded_file(
        self,
        authenticated_client,
        assignment,
        assignment_submit_url,
    ):
        # Arrange
        content = b"some assignment content"

        uploaded_file = SimpleUploadedFile(
            "assignment.pdf",
            content,
            content_type="application/pdf",
        )

        # Act
        response = authenticated_client.post(
            assignment_submit_url,
            data={"files": uploaded_file},
            format="multipart",
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        submission_file = AssignmentSubmissionFile.objects.get()

        assert submission_file.size == len(content)


class TestAssignmentSubmissionApiViewResponse:
    def test_response_contains_expected_top_level_fields(
        self,
        authenticated_client,
        assignment,
        assignment_submit_url,
    ):
        # Arrange
        payload = {
            "submission_text": "Assignment answer",
        }

        # Act
        response = authenticated_client.post(
            assignment_submit_url,
            data=payload,
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        assert set(response.data.keys()) == {
            "success",
            "submission",
            "attempts_used",
            "max_attempts",
            "attempts_remaining",
            "can_submit",
            "message",
        }

    def test_response_contains_expected_submission_fields(
        self,
        authenticated_client,
        assignment,
        assignment_submit_url,
    ):
        # Arrange
        payload = {
            "submission_text": "Assignment answer",
        }

        # Act
        response = authenticated_client.post(
            assignment_submit_url,
            data=payload,
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        submission_data = response.data["submission"]

        assert set(submission_data.keys()) == {
            "attemptNumber",
            "status",
            "submissionText",
            "files",
            "score",
            "feedback",
            "submittedAt",
            "gradedAt",
        }

    def test_response_contains_empty_files_without_upload(
        self,
        authenticated_client,
        assignment,
        assignment_submit_url,
    ):
        # Arrange
        payload = {
            "submission_text": "No file attached",
        }

        # Act
        response = authenticated_client.post(
            assignment_submit_url,
            data=payload,
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["submission"]["files"] == []

    def test_response_contains_uploaded_files(
        self,
        authenticated_client,
        assignment,
        assignment_submit_url,
    ):
        # Arrange
        uploaded_file = SimpleUploadedFile(
            "assignment.pdf",
            b"assignment content",
            content_type="application/pdf",
        )

        # Act
        response = authenticated_client.post(
            assignment_submit_url,
            data={"files": uploaded_file},
            format="multipart",
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        files = response.data["submission"]["files"]

        assert len(files) == 1
        assert files[0]

    def test_successful_submission_returns_success_message(
        self,
        authenticated_client,
        assignment,
        assignment_submit_url,
    ):
        # Arrange
        payload = {
            "submission_text": "Successful submission",
        }

        # Act
        response = authenticated_client.post(
            assignment_submit_url,
            data=payload,
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["message"] == "Assignment submitted successfully!"


class TestAssignmentSubmissionApiViewIsolation:
    def test_submissions_are_scoped_to_current_enrollment(
        self,
        authenticated_client,
        assignment,
        enrollment,
        another_user_enrollment,
        assignment_submit_url,
    ):
        # Arrange
        AssignmentSubmission.objects.create(
            assignment=assignment,
            enrollment=another_user_enrollment,
            attempt_number=1,
            status=AssignmentSubmission.Status.SUBMITTED,
            submission_text="Another user's submission",
        )

        # Act
        response = authenticated_client.post(
            assignment_submit_url,
            data={"submission_text": "My submission"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["attempts_used"] == 1
        assert response.data["submission"]["attemptNumber"] == 1

        own_submissions = AssignmentSubmission.objects.filter(
            assignment=assignment,
            enrollment=enrollment,
        )

        other_submissions = AssignmentSubmission.objects.filter(
            assignment=assignment,
            enrollment=another_user_enrollment,
        )

        assert own_submissions.count() == 1
        assert other_submissions.count() == 1

        assert own_submissions.first().submission_text == "My submission"
        assert other_submissions.first().submission_text == "Another user's submission"

    def test_submissions_for_another_assignment_do_not_count_toward_attempts(
        self,
        authenticated_client,
        assignment,
        assignment_content,
        enrollment,
        course,
        assignment_submit_url,
    ):
        # Arrange
        second_lesson = Lesson.objects.create(
            section=assignment_content.lesson.section,
            title="Second Assignment",
            slug="second-assignment",
            order=2,
            is_published=True,
        )

        second_content = LessonContent.objects.create(
            lesson=second_lesson,
            is_main_content=True,
            title="Second Assignment",
            content_type=LessonContent.Type.ASSIGNMENT,
            order=1,
        )

        second_assignment = Assignment.objects.create(
            content=second_content,
            instructions="Second assignment.",
            max_attempts=1,
        )

        AssignmentSubmission.objects.create(
            assignment=second_assignment,
            enrollment=enrollment,
            attempt_number=1,
            status=AssignmentSubmission.Status.SUBMITTED,
        )

        # Act
        response = authenticated_client.post(
            assignment_submit_url,
            data={"submission_text": "First assignment submission"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["attempts_used"] == 1

        first_assignment_submissions = AssignmentSubmission.objects.filter(
            assignment=assignment,
            enrollment=enrollment,
        )

        second_assignment_submissions = AssignmentSubmission.objects.filter(
            assignment=second_assignment,
            enrollment=enrollment,
        )

        assert first_assignment_submissions.count() == 1
        assert second_assignment_submissions.count() == 1


class TestAssignmentSubmissionApiViewMissingResources:
    def test_nonexistent_lesson_returns_not_found(
        self,
        authenticated_client,
        assignment,
        enrollment,
    ):
        # Arrange
        url = reverse(
            "enrollment_api:assignment_submit",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": 999999,
            },
        )

        # Act
        response = authenticated_client.post(
            url,
            data={"submission_text": "Invalid lesson"},
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert AssignmentSubmission.objects.count() == 0

    def test_lesson_without_assignment_content_returns_not_found(
        self,
        authenticated_client,
        enrollment,
        section,
    ):
        # Arrange
        lesson = Lesson.objects.create(
            section=section,
            title="Lesson Without Assignment",
            slug="lesson-without-assignment",
            order=2,
            is_published=True,
        )

        url = reverse(
            "enrollment_api:assignment_submit",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lesson.id,
            },
        )

        # Act
        response = authenticated_client.post(
            url,
            data={"submission_text": "No assignment"},
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert AssignmentSubmission.objects.count() == 0

    def test_non_assignment_main_content_returns_not_found(
        self,
        authenticated_client,
        enrollment,
        lesson,
    ):
        # Arrange
        LessonContent.objects.create(
            lesson=lesson,
            is_main_content=True,
            title="Article Content",
            content_type=LessonContent.Type.ARTICLE,
            order=1,
        )

        url = reverse(
            "enrollment_api:assignment_submit",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lesson.id,
            },
        )

        # Act
        response = authenticated_client.post(
            url,
            data={"submission_text": "Invalid content type"},
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert AssignmentSubmission.objects.count() == 0

    def test_non_main_assignment_content_returns_not_found(
        self,
        authenticated_client,
        enrollment,
        lesson,
    ):
        # Arrange
        content = LessonContent.objects.create(
            lesson=lesson,
            is_main_content=False,
            title="Assignment Content",
            content_type=LessonContent.Type.ASSIGNMENT,
            order=1,
        )

        Assignment.objects.create(
            content=content,
            instructions="Assignment instructions.",
            max_attempts=3,
        )

        url = reverse(
            "enrollment_api:assignment_submit",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lesson.id,
            },
        )

        # Act
        response = authenticated_client.post(
            url,
            data={"submission_text": "Non-main assignment"},
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert AssignmentSubmission.objects.count() == 0


class TestAssignmentSubmissionApiViewTransaction:
    def test_invalid_file_does_not_create_submission(
        self,
        authenticated_client,
        assignment,
        assignment_submit_url,
    ):
        # Arrange
        invalid_file = SimpleUploadedFile(
            "malware.exe",
            b"invalid content",
            content_type="application/octet-stream",
        )

        # Act
        response = authenticated_client.post(
            assignment_submit_url,
            data={"files": invalid_file},
            format="multipart",
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert AssignmentSubmission.objects.count() == 0
        assert AssignmentSubmissionFile.objects.count() == 0

    def test_oversized_file_does_not_create_submission(
        self,
        authenticated_client,
        assignment,
        assignment_submit_url,
    ):
        # Arrange
        assignment.max_file_size_mb = 1
        assignment.save(update_fields=["max_file_size_mb"])

        oversized_file = SimpleUploadedFile(
            "large.pdf",
            b"x" * (1024 * 1024 + 1),
            content_type="application/pdf",
        )

        # Act
        response = authenticated_client.post(
            assignment_submit_url,
            data={"files": oversized_file},
            format="multipart",
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert AssignmentSubmission.objects.count() == 0
        assert AssignmentSubmissionFile.objects.count() == 0


class TestAssignmentSubmissionApiViewNumericValues:
    def test_new_submission_score_is_none(
        self,
        authenticated_client,
        assignment,
        assignment_submit_url,
    ):
        # Arrange
        payload = {
            "submission_text": "Assignment answer",
        }

        # Act
        response = authenticated_client.post(
            assignment_submit_url,
            data=payload,
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        submission = AssignmentSubmission.objects.get(
            assignment=assignment,
        )

        assert submission.score is None
        assert response.data["submission"]["score"] is None

    def test_existing_graded_submission_does_not_affect_new_submission_score(
        self,
        authenticated_client,
        assignment,
        enrollment,
        assignment_submit_url,
    ):
        # Arrange
        AssignmentSubmission.objects.create(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
            status=AssignmentSubmission.Status.GRADED,
            score=Decimal("85.00"),
            feedback="Good work.",
            submission_text="Previous submission",
        )

        # Act
        response = authenticated_client.post(
            assignment_submit_url,
            data={"submission_text": "New submission"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["attempts_used"] == 2
        assert response.data["submission"]["attemptNumber"] == 2
        assert response.data["submission"]["score"] is None
        assert response.data["submission"]["feedback"] == ""

        submissions = AssignmentSubmission.objects.filter(
            assignment=assignment,
            enrollment=enrollment,
        ).order_by("attempt_number")

        assert submissions.count() == 2
        assert submissions[0].score == Decimal("85.00")
        assert submissions[1].score is None
