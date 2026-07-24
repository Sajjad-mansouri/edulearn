import datetime

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from assessments.models import QuizAttempt
from assessments.tests.factories import (
    QuizAttemptFactory,
    QuizContentFactory,
)
from courses.tests.factories import CourseFactory
from enrollments.tests.factories import EnrollmentFactory


@pytest.mark.django_db
class TestQuizAttemptModel:
    """Tests for the QuizAttempt model."""

    @pytest.fixture
    def enrollment(self):
        return EnrollmentFactory()

    @pytest.fixture
    def quiz(self, enrollment):
        return QuizContentFactory(
            content__lesson__section__course=enrollment.course,
        )

    def test_create_attempt(
        self,
        enrollment,
        quiz,
    ):
        """A quiz attempt can be created."""
        attempt = QuizAttempt.objects.create(
            enrollment=enrollment,
            quiz=quiz,
            attempt_number=1,
            score=85,
        )

        assert attempt.enrollment == enrollment
        assert attempt.quiz == quiz
        assert attempt.attempt_number == 1
        assert attempt.score == 85

    def test_string_representation(self):
        """String representation returns user, quiz and attempt number."""
        attempt = QuizAttemptFactory()

        assert str(attempt) == (
            f"{attempt.enrollment.user} - "
            f"{attempt.quiz} "
            f"(Attempt {attempt.attempt_number})"
        )

    def test_score_defaults_to_zero(
        self,
        enrollment,
        quiz,
    ):
        """Score defaults to zero."""
        attempt = QuizAttempt.objects.create(
            enrollment=enrollment,
            quiz=quiz,
            attempt_number=1,
        )

        assert attempt.score == 0

    def test_started_at_is_set(
        self,
        enrollment,
        quiz,
    ):
        """Started time is automatically assigned."""
        attempt = QuizAttempt.objects.create(
            enrollment=enrollment,
            quiz=quiz,
            attempt_number=1,
        )

        assert attempt.started_at is not None

    def test_submitted_at_defaults_to_none(
        self,
        enrollment,
        quiz,
    ):
        """Submitted time defaults to None."""
        attempt = QuizAttempt.objects.create(
            enrollment=enrollment,
            quiz=quiz,
            attempt_number=1,
        )

        assert attempt.submitted_at is None

    def test_score_cannot_exceed_100(
        self,
        enrollment,
        quiz,
    ):
        """Score cannot exceed 100."""
        attempt = QuizAttempt(
            enrollment=enrollment,
            quiz=quiz,
            attempt_number=1,
            score=101,
        )

        with pytest.raises(ValidationError):
            attempt.full_clean()

    def test_score_cannot_be_negative(
        self,
        enrollment,
        quiz,
    ):
        """Score cannot be negative."""
        attempt = QuizAttempt(
            enrollment=enrollment,
            quiz=quiz,
            attempt_number=1,
            score=-1,
        )

        with pytest.raises(ValidationError):
            attempt.full_clean()

    def test_submission_time_cannot_be_before_started_time(
        self,
        enrollment,
        quiz,
    ):
        """Submission time cannot be before started time."""
        started = timezone.now()
        submitted = started - datetime.timedelta(minutes=1)

        attempt = QuizAttempt(
            enrollment=enrollment,
            quiz=quiz,
            attempt_number=1,
            started_at=started,
            submitted_at=submitted,
        )

        with pytest.raises(ValidationError):
            attempt.full_clean()

    def test_quiz_course_must_match_enrollment_course(
        self,
        enrollment,
    ):
        """Quiz must belong to the enrollment course."""
        another_course = CourseFactory()

        quiz = QuizContentFactory(
            content__lesson__section__course=another_course,
        )

        attempt = QuizAttempt(
            enrollment=enrollment,
            quiz=quiz,
            attempt_number=1,
        )

        with pytest.raises(ValidationError):
            attempt.full_clean()

    def test_attempt_number_must_be_unique_per_quiz_and_enrollment(
        self,
        enrollment,
        quiz,
    ):
        """Attempt number must be unique within a quiz."""
        QuizAttemptFactory(
            enrollment=enrollment,
            quiz=quiz,
            attempt_number=1,
        )

        with pytest.raises(IntegrityError):
            QuizAttemptFactory(
                enrollment=enrollment,
                quiz=quiz,
                attempt_number=1,
            )

    def test_same_attempt_number_can_be_used_for_different_enrollments(
        self,
        quiz,
    ):
        """Different enrollments may reuse the same attempt number."""
        attempt1 = QuizAttemptFactory(
            quiz=quiz,
            attempt_number=1,
        )

        attempt2 = QuizAttemptFactory(
            quiz=quiz,
            attempt_number=1,
        )

        assert attempt1.attempt_number == attempt2.attempt_number == 1

    def test_same_enrollment_can_have_multiple_attempts(
        self,
        enrollment,
        quiz,
    ):
        """An enrollment may have multiple attempts."""
        attempt1 = QuizAttemptFactory(
            enrollment=enrollment,
            quiz=quiz,
            attempt_number=1,
        )

        attempt2 = QuizAttemptFactory(
            enrollment=enrollment,
            quiz=quiz,
            attempt_number=2,
        )

        assert set(quiz.attempts.all()) == {
            attempt1,
            attempt2,
        }

    def test_deleting_quiz_deletes_attempts(self):
        """Deleting a quiz cascades to its attempts."""
        attempt = QuizAttemptFactory()

        quiz = attempt.quiz

        quiz.delete()

        assert not QuizAttempt.objects.filter(
            pk=attempt.pk,
        ).exists()

    def test_deleting_enrollment_deletes_attempts(self):
        """Deleting an enrollment cascades to its attempts."""
        attempt = QuizAttemptFactory()

        enrollment = attempt.enrollment

        enrollment.delete()

        assert not QuizAttempt.objects.filter(
            pk=attempt.pk,
        ).exists()
