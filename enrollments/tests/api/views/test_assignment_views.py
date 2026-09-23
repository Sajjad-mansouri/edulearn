from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from assessments.models import Assignment, AssignmentSubmission
from curriculums.models import Lesson, LessonContent, Section
from enrollments.api.serializers import (
    AssignmentSerializer,
    AssignmentSubmissionSerializer,
)


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
        max_score=100,
        max_attempts=3,
    )


@pytest.fixture
def assignment_url(enrollment, lesson):
    return reverse(
        "enrollment_api:assignment",
        kwargs={
            "enrollment_id": enrollment.id,
            "lesson_id": lesson.id,
        },
    )


@pytest.fixture
def submission(enrollment, assignment):
    return AssignmentSubmission.objects.create(
        assignment=assignment,
        enrollment=enrollment,
        attempt_number=1,
        status=AssignmentSubmission.Status.SUBMITTED,
        submission_text="My Django assignment.",
        score=Decimal("85.00"),
    )


@pytest.fixture
def second_submission(enrollment, assignment):
    return AssignmentSubmission.objects.create(
        assignment=assignment,
        enrollment=enrollment,
        attempt_number=2,
        status=AssignmentSubmission.Status.GRADED,
        submission_text="Updated Django assignment.",
        score=Decimal("95.00"),
    )


class TestAssignmentApiView:
    def test_requires_authentication(
        self,
        api_client,
        assignment_url,
    ):
        # Arrange
        # No authentication.

        # Act
        response = api_client.get(assignment_url)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authenticated_enrolled_user_can_access_assignment(
        self,
        api_client,
        test_user,
        assignment,
        assignment_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        # Act
        response = api_client.get(assignment_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["lessonId"] == assignment.content.lesson.id

    def test_returns_assignment_data(
        self,
        api_client,
        test_user,
        assignment,
        assignment_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        expected_assignment = AssignmentSerializer(assignment).data

        # Act
        response = api_client.get(assignment_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["assignment"] == expected_assignment

    def test_returns_empty_submissions_when_no_submission_exists(
        self,
        api_client,
        test_user,
        assignment,
        assignment_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        # Act
        response = api_client.get(assignment_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["submissions"] == []
        assert response.data["attempts_used"] == 0

    def test_returns_current_enrollment_submissions_only(
        self,
        api_client,
        test_user,
        enrollment,
        another_user_enrollment,
        assignment,
        submission,
        assignment_url,
    ):
        # Arrange
        other_submission = AssignmentSubmission.objects.create(
            assignment=assignment,
            enrollment=another_user_enrollment,
            attempt_number=1,
            status=AssignmentSubmission.Status.SUBMITTED,
            submission_text="Another user's submission.",
            score=Decimal("70.00"),
        )

        api_client.force_authenticate(user=test_user)

        expected_submission = AssignmentSubmissionSerializer(submission).data
        unexpected_submission = AssignmentSubmissionSerializer(other_submission).data

        # Act
        response = api_client.get(assignment_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["submissions"] == [expected_submission]
        assert unexpected_submission not in response.data["submissions"]

    def test_returns_serialized_submissions(
        self,
        api_client,
        test_user,
        submission,
        assignment_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        expected_submission = AssignmentSubmissionSerializer(submission).data

        # Act
        response = api_client.get(assignment_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["submissions"] == [expected_submission]

    def test_returns_multiple_submissions(
        self,
        api_client,
        test_user,
        submission,
        second_submission,
        assignment_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        expected_submissions = AssignmentSubmissionSerializer(
            AssignmentSubmission.objects.filter(
                enrollment=submission.enrollment,
                assignment=submission.assignment,
            ).order_by("-submitted_at"),
            many=True,
        ).data

        # Act
        response = api_client.get(assignment_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["submissions"] == expected_submissions
        assert len(response.data["submissions"]) == 2

    def test_submissions_are_returned_in_submitted_at_descending_order(
        self,
        api_client,
        test_user,
        submission,
        second_submission,
        assignment_url,
    ):
        # Arrange
        from datetime import timedelta

        from django.utils import timezone

        now = timezone.now()

        submission.submitted_at = now - timedelta(days=2)
        submission.save(update_fields=["submitted_at"])

        second_submission.submitted_at = now - timedelta(days=1)
        second_submission.save(update_fields=["submitted_at"])

        api_client.force_authenticate(user=test_user)

        expected_submissions = AssignmentSubmissionSerializer(
            AssignmentSubmission.objects.filter(
                assignment=submission.assignment,
                enrollment=submission.enrollment,
            ).order_by("-submitted_at"),
            many=True,
        ).data

        # Act
        response = api_client.get(assignment_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["submissions"] == expected_submissions

    def test_attempts_used_equals_number_of_submissions(
        self,
        api_client,
        test_user,
        submission,
        second_submission,
        assignment_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        # Act
        response = api_client.get(assignment_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["attempts_used"] == 2

    def test_max_attempts_is_returned(
        self,
        api_client,
        test_user,
        assignment,
        assignment_url,
    ):
        # Arrange
        assignment.max_attempts = 3
        assignment.save(update_fields=["max_attempts"])

        api_client.force_authenticate(user=test_user)

        # Act
        response = api_client.get(assignment_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["max_attempts"] == 3

    def test_attempts_remaining_is_calculated_correctly(
        self,
        api_client,
        test_user,
        submission,
        second_submission,
        assignment_url,
    ):
        # Arrange
        submission.assignment.max_attempts = 3
        submission.assignment.save(update_fields=["max_attempts"])

        api_client.force_authenticate(user=test_user)

        # Act
        response = api_client.get(assignment_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["attempts_used"] == 2
        assert response.data["max_attempts"] == 3
        assert response.data["attempts_remaining"] == 1
        assert response.data["can_submit"] is True

    def test_can_submit_is_false_when_max_attempts_reached(
        self,
        api_client,
        test_user,
        assignment,
        enrollment,
        assignment_url,
    ):
        # Arrange
        assignment.max_attempts = 2
        assignment.save(update_fields=["max_attempts"])

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
            status=AssignmentSubmission.Status.GRADED,
        )

        api_client.force_authenticate(user=test_user)

        # Act
        response = api_client.get(assignment_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["attempts_used"] == 2
        assert response.data["max_attempts"] == 2
        assert response.data["attempts_remaining"] == 0
        assert response.data["can_submit"] is False

    def test_attempts_remaining_never_becomes_negative(
        self,
        api_client,
        test_user,
        assignment,
        enrollment,
        assignment_url,
    ):
        # Arrange
        assignment.max_attempts = 1
        assignment.save(update_fields=["max_attempts"])

        AssignmentSubmission.objects.create(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
            status=AssignmentSubmission.Status.SUBMITTED,
        )

        api_client.force_authenticate(user=test_user)

        # Act
        response = api_client.get(assignment_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["attempts_remaining"] == 0
        assert response.data["attempts_remaining"] >= 0
        assert response.data["can_submit"] is False

    def test_unlimited_attempts_are_supported(
        self,
        api_client,
        test_user,
        assignment,
        enrollment,
        assignment_url,
    ):
        # Arrange
        assignment.max_attempts = 0
        assignment.save(update_fields=["max_attempts"])

        for attempt_number in range(1, 5):
            AssignmentSubmission.objects.create(
                assignment=assignment,
                enrollment=enrollment,
                attempt_number=attempt_number,
                status=AssignmentSubmission.Status.SUBMITTED,
            )

        api_client.force_authenticate(user=test_user)

        # Act
        response = api_client.get(assignment_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["attempts_used"] == 4
        assert response.data["max_attempts"] == 0
        assert response.data["attempts_remaining"] == "Unlimited"
        assert response.data["can_submit"] is True

    def test_completed_enrollment_can_access_assignment(
        self,
        api_client,
        test_user,
        enrollment,
        assignment,
        assignment_url,
    ):
        # Arrange
        enrollment.status = enrollment.Status.COMPLETED
        enrollment.save(update_fields=["status"])

        api_client.force_authenticate(user=test_user)

        # Act
        response = api_client.get(assignment_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    @pytest.mark.parametrize(
        "enrollment_status",
        [
            "cancelled",
            "suspended",
            "pending",
        ],
    )
    def test_ineligible_enrollment_cannot_access_assignment(
        self,
        api_client,
        test_user,
        enrollment,
        assignment_url,
        enrollment_status,
    ):
        # Arrange
        enrollment.status = enrollment_status
        enrollment.save(update_fields=["status"])

        api_client.force_authenticate(user=test_user)

        # Act
        response = api_client.get(assignment_url)

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_another_user_cannot_access_enrollment_assignment(
        self,
        api_client,
        another_user,
        assignment_url,
    ):
        # Arrange
        api_client.force_authenticate(user=another_user)

        # Act
        response = api_client.get(assignment_url)

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_nonexistent_enrollment_is_rejected(
        self,
        api_client,
        test_user,
        assignment,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        url = reverse(
            "enrollment_api:assignment",
            kwargs={
                "enrollment_id": 999999,
                "lesson_id": assignment.content.lesson.id,
            },
        )

        # Act
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_nonexistent_lesson_returns_not_found(
        self,
        api_client,
        test_user,
        enrollment,
        assignment,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        url = reverse(
            "enrollment_api:assignment",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": 999999,
            },
        )

        # Act
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_lesson_from_another_course_returns_not_found(
        self,
        api_client,
        test_user,
        enrollment,
        category,
    ):
        # Arrange
        from courses.models import Course

        another_course = Course.objects.create(
            title="Another Course",
            owner=test_user,
            category=category,
        )

        another_section = Section.objects.create(
            course=another_course,
            title="Another Section",
            order=1,
        )

        another_lesson = Lesson.objects.create(
            section=another_section,
            title="Another Lesson",
            slug="another-lesson",
            order=1,
            is_published=True,
        )

        api_client.force_authenticate(user=test_user)

        url = reverse(
            "enrollment_api:assignment",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": another_lesson.id,
            },
        )

        # Act
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_lesson_without_assignment_returns_not_found(
        self,
        api_client,
        test_user,
        section,
    ):
        # Arrange
        lesson_without_assignment = Lesson.objects.create(
            section=section,
            title="Article Lesson",
            slug="article-lesson",
            order=2,
            is_published=True,
        )

        enrollment = pytest.importorskip(
            "enrollments.models"
        ).Enrollment.objects.create(
            user=test_user,
            course=section.course,
            status="active",
        )

        api_client.force_authenticate(user=test_user)

        url = reverse(
            "enrollment_api:assignment",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lesson_without_assignment.id,
            },
        )

        # Act
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_non_main_assignment_content_is_not_returned(
        self,
        api_client,
        test_user,
        enrollment,
        section,
    ):
        # Arrange
        lesson = Lesson.objects.create(
            section=section,
            title="Non Main Assignment",
            slug="non-main-assignment",
            order=2,
            is_published=True,
        )

        content = LessonContent.objects.create(
            lesson=lesson,
            is_main_content=False,
            title="Assignment",
            content_type=LessonContent.Type.ASSIGNMENT,
            order=1,
        )

        Assignment.objects.create(
            content=content,
            max_score=100,
            max_attempts=3,
        )

        api_client.force_authenticate(user=test_user)

        url = reverse(
            "enrollment_api:assignment",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lesson.id,
            },
        )

        # Act
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_non_assignment_content_is_not_returned(
        self,
        api_client,
        test_user,
        enrollment,
        section,
    ):
        # Arrange
        lesson = Lesson.objects.create(
            section=section,
            title="Video Lesson",
            slug="video-lesson",
            order=2,
            is_published=True,
        )

        LessonContent.objects.create(
            lesson=lesson,
            is_main_content=True,
            title="Video",
            content_type=LessonContent.Type.VIDEO,
            order=1,
        )

        api_client.force_authenticate(user=test_user)

        url = reverse(
            "enrollment_api:assignment",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lesson.id,
            },
        )

        # Act
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_submission_from_another_assignment_is_excluded(
        self,
        api_client,
        test_user,
        enrollment,
        assignment,
        submission,
        section,
        assignment_url,
    ):
        # Arrange
        other_lesson = Lesson.objects.create(
            section=section,
            title="Other Assignment",
            description="Another assignment lesson.",
            slug="other-assignment",
            order=2,
            is_published=True,
        )

        other_content = LessonContent.objects.create(
            lesson=other_lesson,
            is_main_content=True,
            title="Other Assignment",
            content_type=LessonContent.Type.ASSIGNMENT,
            order=1,
        )

        other_assignment = Assignment.objects.create(
            content=other_content,
            max_score=100,
            max_attempts=3,
        )

        other_submission = AssignmentSubmission.objects.create(
            assignment=other_assignment,
            enrollment=enrollment,
            attempt_number=1,
            status=AssignmentSubmission.Status.SUBMITTED,
            submission_text="Other assignment submission.",
        )

        api_client.force_authenticate(user=test_user)

        expected_submission = AssignmentSubmissionSerializer(submission).data
        unexpected_submission = AssignmentSubmissionSerializer(other_submission).data

        # Act
        response = api_client.get(assignment_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["submissions"] == [expected_submission]
        assert unexpected_submission not in response.data["submissions"]

    def test_submission_count_excludes_other_users_submissions(
        self,
        api_client,
        test_user,
        another_user_enrollment,
        assignment,
        submission,
        assignment_url,
    ):
        # Arrange
        AssignmentSubmission.objects.create(
            assignment=assignment,
            enrollment=another_user_enrollment,
            attempt_number=1,
            status=AssignmentSubmission.Status.SUBMITTED,
        )

        api_client.force_authenticate(user=test_user)

        # Act
        response = api_client.get(assignment_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["attempts_used"] == 1

    def test_response_contains_expected_top_level_fields(
        self,
        api_client,
        test_user,
        assignment,
        assignment_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        # Act
        response = api_client.get(assignment_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        assert set(response.data) == {
            "success",
            "lessonId",
            "assignment",
            "submissions",
            "attempts_used",
            "max_attempts",
            "attempts_remaining",
            "can_submit",
        }

    def test_response_reports_correct_lesson_id(
        self,
        api_client,
        test_user,
        assignment,
        assignment_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        # Act
        response = api_client.get(assignment_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["lessonId"] == assignment.content.lesson.id

    def test_draft_submission_is_included_in_submission_list(
        self,
        api_client,
        test_user,
        enrollment,
        assignment,
        assignment_url,
    ):
        # Arrange
        draft = AssignmentSubmission.objects.create(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
            status=AssignmentSubmission.Status.DRAFT,
            submission_text="Draft assignment.",
        )

        api_client.force_authenticate(user=test_user)

        expected_submission = AssignmentSubmissionSerializer(draft).data

        # Act
        response = api_client.get(assignment_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["submissions"] == [expected_submission]
        assert response.data["attempts_used"] == 1

    def test_graded_submission_is_included_in_submission_list(
        self,
        api_client,
        test_user,
        second_submission,
        assignment_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        expected_submission = AssignmentSubmissionSerializer(second_submission).data

        # Act
        response = api_client.get(assignment_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["submissions"] == [expected_submission]

    def test_late_submission_is_included_in_submission_list(
        self,
        api_client,
        test_user,
        enrollment,
        assignment,
        assignment_url,
    ):
        # Arrange
        late_submission = AssignmentSubmission.objects.create(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
            status=AssignmentSubmission.Status.LATE,
            submission_text="Late assignment.",
        )

        api_client.force_authenticate(user=test_user)

        expected_submission = AssignmentSubmissionSerializer(late_submission).data

        # Act
        response = api_client.get(assignment_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["submissions"] == [expected_submission]

    def test_assignment_serializer_matches_endpoint_contract(
        self,
        api_client,
        test_user,
        assignment,
        assignment_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        expected = AssignmentSerializer(assignment).data

        # Act
        response = api_client.get(assignment_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["assignment"] == expected

    def test_submission_serializer_matches_endpoint_contract(
        self,
        api_client,
        test_user,
        submission,
        assignment_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        expected = AssignmentSubmissionSerializer(submission).data

        # Act
        response = api_client.get(assignment_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["submissions"] == [expected]
