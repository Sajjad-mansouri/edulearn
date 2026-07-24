import datetime
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from assessments.models import AssignmentSubmission, AssignmentSubmissionFile
from assessments.tests.factories import (
    AssignmentFactory,
    AssignmentSubmissionFactory,
    AssignmentSubmissionFileFactory,
)
from enrollments.tests.factories import EnrollmentFactory
from utils.test.files import file_field


@pytest.mark.django_db
class TestAssignmentSubmissionModel:
    """Tests for the AssignmentSubmission model."""

    @pytest.fixture
    def enrollment(self):
        return EnrollmentFactory()

    @pytest.fixture
    def assignment(self, enrollment):
        return AssignmentFactory(
            content__lesson__section__course=enrollment.course,
        )

    def test_create_assignment_submission(
        self,
        assignment,
        enrollment,
    ):
        """An assignment submission can be created."""
        submission = AssignmentSubmission.objects.create(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
            status=AssignmentSubmission.Status.DRAFT,
            submission_text="My solution",
        )

        assert submission.assignment == assignment
        assert submission.enrollment == enrollment
        assert submission.attempt_number == 1
        assert submission.status == AssignmentSubmission.Status.DRAFT
        assert submission.submission_text == "My solution"
        assert submission.score is None
        assert submission.feedback == ""
        assert submission.started_at is not None
        assert submission.submitted_at is None
        assert submission.graded_at is None

    def test_string_representation(self):
        """String representation includes user, assignment and attempt."""
        submission = AssignmentSubmissionFactory()

        assert (
            str(submission) == f"{submission.enrollment.user} - "
            f"{submission.assignment} "
            f"(Attempt {submission.attempt_number})"
        )

    def test_status_defaults_to_draft(
        self,
        assignment,
        enrollment,
    ):
        """Status defaults to draft."""
        submission = AssignmentSubmission.objects.create(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
        )

        assert submission.status == AssignmentSubmission.Status.DRAFT

    def test_submission_text_defaults_to_empty(
        self,
        assignment,
        enrollment,
    ):
        """Submission text defaults to empty."""
        submission = AssignmentSubmission.objects.create(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
        )

        assert submission.submission_text == ""

    def test_feedback_defaults_to_empty(
        self,
        assignment,
        enrollment,
    ):
        """Feedback defaults to empty."""
        submission = AssignmentSubmission.objects.create(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
        )

        assert submission.feedback == ""

    def test_score_defaults_to_none(
        self,
        assignment,
        enrollment,
    ):
        """Score defaults to None."""
        submission = AssignmentSubmission.objects.create(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
        )

        assert submission.score is None

    def test_same_assignment_can_have_multiple_submissions(
        self,
        assignment,
        enrollment,
    ):
        """Multiple attempts are allowed."""
        submission1 = AssignmentSubmissionFactory(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
        )

        submission2 = AssignmentSubmissionFactory(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=2,
        )

        assert set(assignment.submissions.all()) == {
            submission1,
            submission2,
        }

    def test_attempt_number_must_be_unique_per_assignment_and_enrollment(
        self,
        assignment,
        enrollment,
    ):
        """Duplicate attempt numbers are not allowed."""
        AssignmentSubmissionFactory(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
        )

        with pytest.raises(IntegrityError):
            AssignmentSubmissionFactory(
                assignment=assignment,
                enrollment=enrollment,
                attempt_number=1,
            )

    def test_assignment_must_match_enrollment_course(
        self,
        enrollment,
    ):
        """Assignment must belong to the enrollment course."""
        assignment = AssignmentFactory()

        submission = AssignmentSubmission(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
        )

        with pytest.raises(ValidationError):
            submission.full_clean()

    def test_score_cannot_be_negative(
        self,
        assignment,
        enrollment,
    ):
        """Score cannot be negative."""
        submission = AssignmentSubmission(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
            score=Decimal("-1"),
        )

        with pytest.raises(ValidationError):
            submission.full_clean()

    def test_score_cannot_exceed_assignment_max_score(
        self,
        assignment,
        enrollment,
    ):
        """Score cannot exceed assignment maximum score."""
        assignment.max_score = 50
        assignment.save()

        submission = AssignmentSubmission(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
            score=Decimal("60"),
        )

        with pytest.raises(ValidationError):
            submission.full_clean()

    def test_submission_time_cannot_be_before_started_time(
        self,
        assignment,
        enrollment,
    ):
        """Submission time cannot be before start time."""
        submission = AssignmentSubmission(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
        )

        submission.started_at = timezone.now()
        submission.submitted_at = submission.started_at - datetime.timedelta(minutes=1)

        with pytest.raises(ValidationError):
            submission.full_clean()

    def test_graded_time_cannot_be_before_submission_time(
        self,
        assignment,
        enrollment,
    ):
        """Grading time cannot be before submission time."""
        submission = AssignmentSubmission(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
        )

        submission.started_at = timezone.now()
        submission.submitted_at = submission.started_at + datetime.timedelta(minutes=10)
        submission.graded_at = submission.submitted_at - datetime.timedelta(minutes=1)

        with pytest.raises(ValidationError):
            submission.full_clean()

    def test_submit_marks_submission_as_submitted(
        self,
        assignment,
        enrollment,
    ):
        """submit() updates status and submission time."""
        submission = AssignmentSubmission.objects.create(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
        )

        assert submission.submitted_at is None

        submission.submit()

        assert submission.status == AssignmentSubmission.Status.SUBMITTED
        assert submission.submitted_at is not None

    def test_submit_does_not_override_existing_submission_time(
        self,
        assignment,
        enrollment,
    ):
        """submit() preserves an existing submission timestamp."""
        submitted_at = timezone.now()

        submission = AssignmentSubmission.objects.create(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
            submitted_at=submitted_at,
        )

        submission.submit()

        assert submission.submitted_at == submitted_at

    def test_mark_graded_updates_submission(
        self,
        assignment,
        enrollment,
    ):
        """mark_graded() updates grading fields."""
        submission = AssignmentSubmission.objects.create(
            assignment=assignment,
            enrollment=enrollment,
            attempt_number=1,
        )

        submission.mark_graded(
            score=Decimal("87.50"),
            feedback="Well done.",
        )

        assert submission.status == AssignmentSubmission.Status.GRADED
        assert submission.score == Decimal("87.50")
        assert submission.feedback == "Well done."
        assert submission.graded_at is not None

    def test_deleting_assignment_deletes_submissions(self):
        """Deleting an assignment cascades to submissions."""
        submission = AssignmentSubmissionFactory()

        assignment = submission.assignment

        assignment.delete()

        assert not AssignmentSubmission.objects.filter(
            pk=submission.pk,
        ).exists()

    def test_deleting_enrollment_deletes_submissions(self):
        """Deleting an enrollment cascades to submissions."""
        submission = AssignmentSubmissionFactory()

        enrollment = submission.enrollment

        enrollment.delete()

        assert not AssignmentSubmission.objects.filter(
            pk=submission.pk,
        ).exists()


@pytest.mark.django_db
class TestAssignmentSubmissionFileModel:
    """Tests for the AssignmentSubmissionFile model."""

    @pytest.fixture
    def submission(self):
        return AssignmentSubmissionFactory()

    def test_create_submission_file(self, submission):
        """A submission file can be created."""
        uploaded_file = file_field(
            name="solution.pdf",
            content=b"PDF content",
        )

        submission_file = AssignmentSubmissionFile.objects.create(
            submission=submission,
            file=uploaded_file,
            original_filename="solution.pdf",
        )

        assert submission_file.submission == submission
        assert submission_file.original_filename == "solution.pdf"
        assert submission_file.file.name.endswith("solution.pdf")
        assert submission_file.uploaded_at is not None

    def test_string_representation(self):
        """String representation returns the original filename."""
        submission_file = AssignmentSubmissionFileFactory(
            original_filename="project.zip",
        )

        assert str(submission_file) == "project.zip"

    def test_submission_can_have_multiple_files(self, submission):
        """A submission can contain multiple uploaded files."""
        file1 = AssignmentSubmissionFileFactory(
            submission=submission,
            original_filename="report.pdf",
        )

        file2 = AssignmentSubmissionFileFactory(
            submission=submission,
            original_filename="source.zip",
        )

        assert set(submission.files.all()) == {
            file1,
            file2,
        }

    def test_original_filename_is_required(self, submission):
        """Original filename is required."""
        submission_file = AssignmentSubmissionFile(
            submission=submission,
            file=file_field(),
            original_filename="",
        )

        with pytest.raises(ValidationError):
            submission_file.full_clean()

    def test_deleting_submission_deletes_files(self):
        """Deleting a submission cascades to its uploaded files."""
        submission_file = AssignmentSubmissionFileFactory()

        submission = submission_file.submission

        submission.delete()

        assert not AssignmentSubmissionFile.objects.filter(
            pk=submission_file.pk,
        ).exists()

    def test_files_are_ordered_by_upload_time(self, submission):
        """Files are returned in upload order."""
        file1 = AssignmentSubmissionFileFactory(
            submission=submission,
            original_filename="a.pdf",
        )
        file2 = AssignmentSubmissionFileFactory(
            submission=submission,
            original_filename="b.pdf",
        )

        files = list(submission.files.all())

        assert files == [
            file1,
            file2,
        ]
