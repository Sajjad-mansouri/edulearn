from decimal import Decimal
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.utils import timezone

from assessments.models.assignment import Assignment
from assessments.models.assignment_submission import (
    AssignmentSubmission,
    AssignmentSubmissionFile,
)
from courses.models.course import Course
from curriculums.models.lesson import Lesson
from curriculums.models.lesson_content import LessonContent
from curriculums.models.section import Section
from enrollments.models.enrollment import Enrollment

User = get_user_model()


@pytest.fixture
def submission_user(db):
    return User.objects.create_user(
        username="submission_user",
        email="submission_user@example.com",
        password="test-password",
    )


@pytest.fixture
def submission_course(db, submission_user):
    return Course.objects.create(
        title="Submission Course",
        owner=submission_user,
    )


@pytest.fixture
def submission_section(db, submission_course):
    return Section.objects.create(
        course=submission_course,
        title="Submission Section",
    )


@pytest.fixture
def submission_lesson(db, submission_section):
    return Lesson.objects.create(
        section=submission_section,
        title="Submission Lesson",
        slug="submission-lesson",
    )


@pytest.fixture
def lesson_content(db, submission_lesson):
    return LessonContent.objects.create(
        lesson=submission_lesson,
        title="Assignment Content",
        content_type=LessonContent.Type.ASSIGNMENT,
        order=1,
    )


@pytest.fixture
def assignment(db, lesson_content):
    return Assignment.objects.create(
        content=lesson_content,
        passing_score=70,
        max_score=100,
        due_date=timezone.now() + timezone.timedelta(days=7),
    )


@pytest.fixture
def enrollment(db, submission_user, submission_course):
    return Enrollment.objects.create(
        user=submission_user,
        course=submission_course,
        status=Enrollment.Status.ACTIVE,
    )


@pytest.fixture
def submission(assignment, enrollment):
    """
    submitted_at is deliberately populated because the current save()
    implementation compares submitted_at with due_date without checking
    for None.
    """
    return AssignmentSubmission.objects.create(
        assignment=assignment,
        enrollment=enrollment,
        attempt_number=1,
        submitted_at=timezone.now(),
    )


@pytest.fixture
def second_assignment(db, submission_course):
    section = Section.objects.create(
        course=submission_course,
        title="Second Section",
    )

    lesson = Lesson.objects.create(
        section=section,
        title="Second Lesson",
        slug="second-lesson",
    )

    content = LessonContent.objects.create(
        lesson=lesson,
        title="Second Assignment Content",
        content_type=LessonContent.Type.ASSIGNMENT,
        order=1,
    )

    return Assignment.objects.create(
        content=content,
        max_score=100,
        due_date=timezone.now() + timezone.timedelta(days=7),
    )


class TestAssignmentSubmissionCreation:
    def test_creates_submission(
        self,
        submission,
        assignment,
        enrollment,
    ):
        assert submission.pk is not None
        assert submission.assignment == assignment
        assert submission.enrollment == enrollment

    def test_default_status_is_draft(self, assignment, enrollment):
        submission = AssignmentSubmission(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
        )

        assert submission.status == AssignmentSubmission.Status.DRAFT

    def test_default_submission_text_is_empty(self, assignment, enrollment):
        submission = AssignmentSubmission(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
        )

        assert submission.submission_text == ""

    def test_default_feedback_is_empty(self, assignment, enrollment):
        submission = AssignmentSubmission(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
        )

        assert submission.feedback == ""

    def test_default_score_is_none(self, assignment, enrollment):
        submission = AssignmentSubmission(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
        )

        assert submission.score is None

    def test_default_submitted_at_is_none(self, assignment, enrollment):
        submission = AssignmentSubmission(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
        )

        assert submission.submitted_at is None

    def test_default_graded_at_is_none(self, assignment, enrollment):
        submission = AssignmentSubmission(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
        )

        assert submission.graded_at is None

    def test_str_contains_user_assignment_and_attempt(
        self,
        submission,
        enrollment,
        assignment,
    ):
        expected = (
            f"{enrollment.user} - {assignment} (Attempt {submission.attempt_number})"
        )

        assert str(submission) == expected


class TestAssignmentSubmissionFields:
    @pytest.mark.parametrize(
        "status",
        [
            AssignmentSubmission.Status.DRAFT,
            AssignmentSubmission.Status.SUBMITTED,
            AssignmentSubmission.Status.GRADED,
            AssignmentSubmission.Status.RETURNED,
            AssignmentSubmission.Status.LATE,
        ],
    )
    def test_status_accepts_defined_choices(
        self,
        assignment,
        enrollment,
        status,
    ):
        submission = AssignmentSubmission.objects.create(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
            status=status,
            submitted_at=timezone.now(),
        )

        submission.refresh_from_db()

        assert submission.status == status

    @pytest.mark.parametrize(
        "submission_text",
        [
            "",
            "My solution is attached.",
            "This is my detailed written submission.",
        ],
    )
    def test_submission_text_accepts_values(
        self,
        assignment,
        enrollment,
        submission_text,
    ):
        submission = AssignmentSubmission.objects.create(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
            submission_text=submission_text,
            submitted_at=timezone.now(),
        )

        submission.refresh_from_db()

        assert submission.submission_text == submission_text

    @pytest.mark.parametrize(
        "score",
        [
            Decimal("0"),
            Decimal("50"),
            Decimal("99.50"),
            Decimal("100"),
            None,
        ],
    )
    def test_score_accepts_supported_values(
        self,
        assignment,
        enrollment,
        score,
    ):
        submission = AssignmentSubmission(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
            score=score,
        )

        assert submission.score == score

    def test_feedback_accepts_text(
        self,
        assignment,
        enrollment,
    ):
        submission = AssignmentSubmission.objects.create(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
            feedback="Good work.",
            submitted_at=timezone.now(),
        )

        submission.refresh_from_db()

        assert submission.feedback == "Good work."

    def test_submitted_at_accepts_datetime(
        self,
        assignment,
        enrollment,
    ):
        submitted_at = timezone.now()

        submission = AssignmentSubmission.objects.create(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
            submitted_at=submitted_at,
        )

        submission.refresh_from_db()

        assert submission.submitted_at == submitted_at

    def test_graded_at_accepts_datetime(
        self,
        assignment,
        enrollment,
    ):
        submitted_at = timezone.now()
        graded_at = submitted_at + timezone.timedelta(hours=1)

        submission = AssignmentSubmission.objects.create(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
            submitted_at=submitted_at,
            graded_at=graded_at,
        )

        submission.refresh_from_db()

        assert submission.graded_at == graded_at


class TestAssignmentSubmissionRequiredFields:
    def test_assignment_is_required(self, enrollment):
        submission = AssignmentSubmission(
            enrollment=enrollment,
            attempt_number=1,
        )

        with pytest.raises(ValidationError) as exc_info:
            AssignmentSubmission._meta.get_field("assignment").validate(
                submission.assignment_id,
                submission,
            )

        assert exc_info.value.messages

    def test_enrollment_is_required(self, assignment):
        submission = AssignmentSubmission(
            assignment=assignment,
            attempt_number=1,
        )

        with pytest.raises(ValidationError) as exc_info:
            AssignmentSubmission._meta.get_field("enrollment").validate(
                submission.enrollment_id,
                submission,
            )

        assert exc_info.value.messages

    def test_attempt_number_is_required(self, assignment, enrollment):
        submission = AssignmentSubmission(
            assignment=assignment,
            enrollment=enrollment,
        )

        with pytest.raises(ValidationError) as exc_info:
            AssignmentSubmission._meta.get_field("attempt_number").validate(
                submission.attempt_number,
                submission,
            )

        assert exc_info.value.messages


class TestAssignmentSubmissionValidation:
    def test_assignment_and_enrollment_from_same_course_are_valid(
        self,
        assignment,
        enrollment,
    ):
        submission = AssignmentSubmission(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
        )

        submission.full_clean()

    def test_assignment_from_different_course_is_rejected(
        self,
        assignment,
        enrollment,
        submission_user,
    ):
        other_course = Course.objects.create(
            title="Other Course",
            owner=submission_user,
        )

        section = Section.objects.create(
            course=other_course,
            title="Other Section",
        )

        lesson = Lesson.objects.create(
            section=section,
            title="Other Lesson",
            slug="other-assignment-lesson",
        )

        content = LessonContent.objects.create(
            lesson=lesson,
            title="Other Assignment",
            content_type=LessonContent.Type.ASSIGNMENT,
            order=1,
        )

        other_assignment = Assignment.objects.create(
            content=content,
            max_score=100,
        )

        submission = AssignmentSubmission(
            assignment=other_assignment,
            enrollment=enrollment,
            attempt_number=1,
        )

        with pytest.raises(ValidationError) as exc_info:
            submission.full_clean()

        assert "assignment" in exc_info.value.message_dict
        assert (
            "Assignment must belong to the enrollment course."
            in exc_info.value.message_dict["assignment"]
        )

    @pytest.mark.parametrize(
        "score",
        [
            Decimal("0"),
            Decimal("50"),
            Decimal("100"),
        ],
    )
    def test_score_within_assignment_maximum_is_valid(
        self,
        assignment,
        enrollment,
        score,
    ):
        submission = AssignmentSubmission(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
            score=score,
        )

        submission.full_clean()

    def test_negative_score_is_rejected(
        self,
        assignment,
        enrollment,
    ):
        submission = AssignmentSubmission(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
            score=Decimal("-1"),
        )

        with pytest.raises(ValidationError) as exc_info:
            submission.full_clean()

        assert "score" in exc_info.value.message_dict
        assert (
            "Score must be between 0 and the assignment maximum score."
            in exc_info.value.message_dict["score"]
        )

    def test_score_above_assignment_maximum_is_rejected(
        self,
        assignment,
        enrollment,
    ):
        submission = AssignmentSubmission(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
            score=Decimal("100.01"),
        )

        with pytest.raises(ValidationError) as exc_info:
            submission.full_clean()

        assert "score" in exc_info.value.message_dict

    def test_graded_at_before_submitted_at_is_rejected(
        self,
        assignment,
        enrollment,
    ):
        submitted_at = timezone.now()
        graded_at = submitted_at - timezone.timedelta(minutes=1)

        submission = AssignmentSubmission(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
            submitted_at=submitted_at,
            graded_at=graded_at,
        )

        with pytest.raises(ValidationError) as exc_info:
            submission.full_clean()

        assert "graded_at" in exc_info.value.message_dict
        assert (
            "Grading time cannot be before submission time."
            in exc_info.value.message_dict["graded_at"]
        )

    def test_graded_at_equal_to_submitted_at_is_valid(
        self,
        assignment,
        enrollment,
    ):
        submitted_at = timezone.now()

        submission = AssignmentSubmission(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
            submitted_at=submitted_at,
            graded_at=submitted_at,
        )

        submission.full_clean()


class TestAssignmentSubmissionUniqueness:
    def test_same_assignment_attempt_cannot_be_duplicated(
        self,
        submission,
        assignment,
        enrollment,
    ):
        duplicate = AssignmentSubmission(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=submission.attempt_number,
            submitted_at=timezone.now(),
        )

        with pytest.raises(IntegrityError):
            duplicate.save()

    def test_different_attempt_numbers_are_allowed(
        self,
        submission,
        assignment,
        enrollment,
    ):
        second_submission = AssignmentSubmission.objects.create(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=2,
            submitted_at=timezone.now(),
        )

        assert second_submission.pk is not None

    def test_different_assignments_can_use_same_attempt_number(
        self,
        submission,
        second_assignment,
        enrollment,
    ):
        second_submission = AssignmentSubmission.objects.create(
            assignment=second_assignment,
            enrollment=enrollment,
            attempt_number=1,
            submitted_at=timezone.now(),
        )

        assert second_submission.pk is not None


class TestAssignmentSubmissionRelationships:
    def test_assignment_reverse_relation(
        self,
        submission,
        assignment,
    ):
        assert submission in assignment.submissions.all()

    def test_enrollment_reverse_relation(
        self,
        submission,
        enrollment,
    ):
        assert submission in enrollment.assignment_submissions.all()

    def test_deleting_assignment_cascades_to_submission(
        self,
        submission,
        assignment,
    ):
        submission_id = submission.pk

        assignment.delete()

        assert not AssignmentSubmission.objects.filter(pk=submission_id).exists()

    def test_deleting_enrollment_cascades_to_submission(
        self,
        submission,
        enrollment,
    ):
        submission_id = submission.pk

        enrollment.delete()

        assert not AssignmentSubmission.objects.filter(pk=submission_id).exists()


class TestAssignmentSubmissionSubmit:
    def test_submit_changes_status_to_submitted(
        self,
        submission,
    ):
        submission.status = AssignmentSubmission.Status.DRAFT

        submission.submit()

        assert submission.status == AssignmentSubmission.Status.SUBMITTED

    def test_submit_sets_submitted_at_when_missing(
        self,
        assignment,
        enrollment,
    ):
        submission = AssignmentSubmission(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
        )

        before = timezone.now()

        submission.submit()

        after = timezone.now()

        assert submission.status == AssignmentSubmission.Status.SUBMITTED
        assert submission.submitted_at is not None
        assert before <= submission.submitted_at <= after

    def test_submit_does_not_replace_existing_submitted_at(
        self,
        assignment,
        enrollment,
    ):
        original_time = timezone.now() - timezone.timedelta(hours=1)

        submission = AssignmentSubmission(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
            submitted_at=original_time,
        )

        submission.submit()

        assert submission.submitted_at == original_time


class TestAssignmentSubmissionMarkGraded:
    def test_mark_graded_sets_score(
        self,
        submission,
    ):
        submission.mark_graded(Decimal("85"))

        assert submission.score == Decimal("85")

    def test_mark_graded_sets_feedback(
        self,
        submission,
    ):
        submission.mark_graded(
            Decimal("85"),
            feedback="Good work.",
        )

        assert submission.feedback == "Good work."

    def test_mark_graded_sets_graded_status(
        self,
        submission,
    ):
        submission.mark_graded(Decimal("85"))

        assert submission.status == AssignmentSubmission.Status.GRADED

    def test_mark_graded_sets_graded_at(
        self,
        submission,
    ):
        before = timezone.now()

        submission.mark_graded(Decimal("85"))

        after = timezone.now()

        assert submission.graded_at is not None
        assert before <= submission.graded_at <= after

    def test_mark_graded_accepts_zero_score(
        self,
        submission,
    ):
        submission.mark_graded(Decimal("0"))

        assert submission.score == Decimal("0")
        assert submission.status == AssignmentSubmission.Status.GRADED


class TestAssignmentSubmissionLetterGrade:
    @pytest.mark.parametrize(
        ("score", "expected_grade"),
        [
            (Decimal("100"), "A"),
            (Decimal("95"), "A"),
            (Decimal("90"), "A"),
            (Decimal("89.99"), "B"),
            (Decimal("80"), "B"),
            (Decimal("79.99"), "C"),
            (Decimal("70"), "C"),
            (Decimal("69.99"), "D"),
            (Decimal("50"), "D"),
            (Decimal("0"), "D"),
        ],
    )
    def test_returns_expected_letter_grade(
        self,
        submission,
        score,
        expected_grade,
    ):
        submission.score = score

        assert submission.get_letter_grade() == expected_grade

    def test_returns_empty_string_when_score_is_none(
        self,
        submission,
    ):
        submission.score = None

        assert submission.get_letter_grade() == ""


class TestAssignmentSubmissionSave:
    def test_submission_before_due_date_does_not_become_late(
        self,
        assignment,
        enrollment,
    ):
        submitted_at = assignment.due_date - timezone.timedelta(days=1)

        submission = AssignmentSubmission.objects.create(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
            submitted_at=submitted_at,
        )

        assert submission.status == AssignmentSubmission.Status.DRAFT

    def test_submission_after_due_date_becomes_late(
        self,
        assignment,
        enrollment,
    ):
        submitted_at = assignment.due_date + timezone.timedelta(minutes=1)

        submission = AssignmentSubmission.objects.create(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
            submitted_at=submitted_at,
        )

        assert submission.status == AssignmentSubmission.Status.LATE

    def test_score_sets_status_to_graded(
        self,
        assignment,
        enrollment,
    ):
        submission = AssignmentSubmission.objects.create(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
            submitted_at=timezone.now(),
            score=Decimal("80"),
        )

        assert submission.status == AssignmentSubmission.Status.GRADED
        assert submission.graded_at is not None

    def test_zero_score_should_set_status_to_graded(
        self,
        assignment,
        enrollment,
    ):
        submission = AssignmentSubmission.objects.create(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
            submitted_at=timezone.now(),
            score=Decimal("0"),
        )

        assert submission.status == AssignmentSubmission.Status.GRADED
        assert submission.graded_at is not None


class TestAssignmentSubmissionPersistence:
    def test_updates_status(
        self,
        submission,
    ):
        submission.status = AssignmentSubmission.Status.RETURNED
        submission.save()

        submission.refresh_from_db()

        assert submission.status == AssignmentSubmission.Status.RETURNED

    def test_updates_submission_text(
        self,
        submission,
    ):
        submission.submission_text = "Updated submission."
        submission.save()

        submission.refresh_from_db()

        assert submission.submission_text == "Updated submission."

    def test_updates_feedback(
        self,
        submission,
    ):
        submission.feedback = "Updated feedback."
        submission.save()

        submission.refresh_from_db()

        assert submission.feedback == "Updated feedback."

    def test_updates_score(
        self,
        submission,
    ):
        submission.score = Decimal("75")
        submission.save()

        submission.refresh_from_db()

        assert submission.score == Decimal("75")

    def test_updated_changes_when_saved(
        self,
        submission,
    ):
        original_updated = submission.updated

        submission.feedback = "Changed."
        submission.save()

        submission.refresh_from_db()

        assert submission.updated >= original_updated


class TestAssignmentSubmissionFileCreation:
    @pytest.fixture
    def uploaded_file(self):
        return SimpleUploadedFile(
            "solution.pdf",
            b"assignment file content",
            content_type="application/pdf",
        )

    def test_creates_submission_file(
        self,
        submission,
        uploaded_file,
    ):
        submission_file = AssignmentSubmissionFile.objects.create(
            submission=submission,
            file=uploaded_file,
            original_filename="solution.pdf",
        )

        assert submission_file.pk is not None
        assert submission_file.submission == submission

    def test_str_returns_original_filename(
        self,
        submission,
        uploaded_file,
    ):
        submission_file = AssignmentSubmissionFile.objects.create(
            submission=submission,
            file=uploaded_file,
            original_filename="solution.pdf",
        )

        assert str(submission_file) == "solution.pdf"

    def test_size_is_taken_from_uploaded_file(
        self,
        submission,
        uploaded_file,
    ):
        submission_file = AssignmentSubmissionFile.objects.create(
            submission=submission,
            file=uploaded_file,
            original_filename="solution.pdf",
        )

        assert submission_file.size == len(b"assignment file content")

    def test_file_name_returns_base_filename(
        self,
        submission,
        uploaded_file,
    ):
        submission_file = AssignmentSubmissionFile.objects.create(
            submission=submission,
            file=uploaded_file,
            original_filename="solution.pdf",
        )

        assert submission_file.file_name == Path(submission_file.file.name).name

    def test_uploaded_at_is_set(
        self,
        submission,
        uploaded_file,
    ):
        submission_file = AssignmentSubmissionFile.objects.create(
            submission=submission,
            file=uploaded_file,
            original_filename="solution.pdf",
        )

        assert submission_file.uploaded_at is not None


class TestAssignmentSubmissionFileFields:
    def test_original_filename_is_required(self, submission):
        submission_file = AssignmentSubmissionFile(
            submission=submission,
        )

        with pytest.raises(ValidationError) as exc_info:
            AssignmentSubmissionFile._meta.get_field("original_filename").validate(
                submission_file.original_filename,
                submission_file,
            )

        assert exc_info.value.messages

    def test_submission_is_required(self):
        submission_file = AssignmentSubmissionFile()

        with pytest.raises(ValidationError) as exc_info:
            AssignmentSubmissionFile._meta.get_field("submission").validate(
                submission_file.submission_id,
                submission_file,
            )

        assert exc_info.value.messages

    def test_size_can_be_null(self, submission, tmp_path):
        submission_file = AssignmentSubmissionFile(
            submission=submission,
            original_filename="solution.pdf",
        )

        submission_file.file = ""
        submission_file.size = None

        assert submission_file.size is None


class TestAssignmentSubmissionFileRelationships:
    @pytest.fixture
    def uploaded_file(self):
        return SimpleUploadedFile(
            "solution.pdf",
            b"file content",
            content_type="application/pdf",
        )

    def test_submission_reverse_relation(
        self,
        submission,
        uploaded_file,
    ):
        submission_file = AssignmentSubmissionFile.objects.create(
            submission=submission,
            file=uploaded_file,
            original_filename="solution.pdf",
        )

        assert submission_file in submission.files.all()

    def test_multiple_files_can_belong_to_one_submission(
        self,
        submission,
        uploaded_file,
    ):
        first_file = AssignmentSubmissionFile.objects.create(
            submission=submission,
            file=uploaded_file,
            original_filename="solution.pdf",
        )

        second_uploaded_file = SimpleUploadedFile(
            "source.zip",
            b"zip content",
            content_type="application/zip",
        )

        second_file = AssignmentSubmissionFile.objects.create(
            submission=submission,
            file=second_uploaded_file,
            original_filename="source.zip",
        )

        assert set(submission.files.all()) == {
            first_file,
            second_file,
        }

    def test_deleting_submission_cascades_to_files(
        self,
        submission,
        uploaded_file,
    ):
        submission_file = AssignmentSubmissionFile.objects.create(
            submission=submission,
            file=uploaded_file,
            original_filename="solution.pdf",
        )

        file_id = submission_file.pk

        submission.delete()

        assert not AssignmentSubmissionFile.objects.filter(pk=file_id).exists()


class TestAssignmentSubmissionFilePersistence:
    @pytest.fixture
    def uploaded_file(self):
        return SimpleUploadedFile(
            "solution.pdf",
            b"initial content",
            content_type="application/pdf",
        )

    def test_updates_original_filename(
        self,
        submission,
        uploaded_file,
    ):
        submission_file = AssignmentSubmissionFile.objects.create(
            submission=submission,
            file=uploaded_file,
            original_filename="solution.pdf",
        )

        submission_file.original_filename = "updated-solution.pdf"
        submission_file.save()

        submission_file.refresh_from_db()

        assert submission_file.original_filename == "updated-solution.pdf"

    def test_size_is_recalculated_on_save(
        self,
        submission,
        uploaded_file,
    ):
        submission_file = AssignmentSubmissionFile.objects.create(
            submission=submission,
            file=uploaded_file,
            original_filename="solution.pdf",
        )

        new_file = SimpleUploadedFile(
            "updated.pdf",
            b"new larger file content",
            content_type="application/pdf",
        )

        submission_file.file = new_file
        submission_file.save()

        submission_file.refresh_from_db()

        assert submission_file.size == len(b"new larger file content")


class TestAssignmentSubmissionUploadPath:
    def test_upload_path_contains_expected_identifiers(
        self,
        submission,
    ):
        uploaded_file = SimpleUploadedFile(
            "solution.pdf",
            b"content",
            content_type="application/pdf",
        )

        submission_file = AssignmentSubmissionFile(
            submission=submission,
            file=uploaded_file,
            original_filename="solution.pdf",
        )

        path = submission_file.file.field.generate_filename(
            submission_file,
            "solution.pdf",
        )

        assert f"courses/{submission.enrollment.course.owner_id}/" in path
        assert f"{submission.enrollment.course_id}/" in path
        assert f"lesson_contents/{submission.assignment.content_id}/" in path
        assert "assignment_submission/" in path
        assert f"user_{submission.enrollment.user_id}" in path
        assert path.endswith("solution.pdf")


class TestAssignmentSubmissionFileOrdering:
    @pytest.fixture
    def uploaded_file(self):
        return SimpleUploadedFile(
            "solution.pdf",
            b"content",
            content_type="application/pdf",
        )

    def test_files_are_ordered_by_uploaded_at(
        self,
        submission,
        uploaded_file,
    ):
        first_file = AssignmentSubmissionFile.objects.create(
            submission=submission,
            file=uploaded_file,
            original_filename="first.pdf",
        )

        second_uploaded_file = SimpleUploadedFile(
            "second.pdf",
            b"second content",
            content_type="application/pdf",
        )

        second_file = AssignmentSubmissionFile.objects.create(
            submission=submission,
            file=second_uploaded_file,
            original_filename="second.pdf",
        )

        files = list(submission.files.all())

        assert files == [first_file, second_file]
