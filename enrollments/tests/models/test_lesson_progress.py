import datetime

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from curriculums.tests.factories import LessonFactory
from enrollments.models import LessonProgress
from enrollments.tests.factories import (
    EnrollmentFactory,
    LessonProgressFactory,
)


@pytest.mark.django_db
class TestLessonProgressModel:
    """Tests for the LessonProgress model."""

    @pytest.fixture
    def enrollment(self):
        return EnrollmentFactory()

    @pytest.fixture
    def lesson(self):
        return LessonFactory()

    def test_create_progress(
        self,
        enrollment,
        lesson,
    ):
        """A lesson progress record can be created."""
        progress = LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=lesson,
            status=LessonProgress.Status.IN_PROGRESS,
            progress_percentage=40,
            started_at=timezone.now(),
        )

        assert progress.enrollment == enrollment
        assert progress.lesson == lesson
        assert progress.status == LessonProgress.Status.IN_PROGRESS
        assert progress.progress_percentage == 40

    def test_string_representation(self):
        """String representation returns user and lesson."""
        progress = LessonProgressFactory()

        assert str(progress) == f"{progress.enrollment.user} - {progress.lesson}"

    def test_status_defaults_to_not_started(
        self,
        enrollment,
        lesson,
    ):
        """Status defaults to NOT_STARTED."""
        progress = LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=lesson,
        )

        assert progress.status == LessonProgress.Status.NOT_STARTED

    def test_progress_percentage_defaults_to_zero(
        self,
        enrollment,
        lesson,
    ):
        """Progress percentage defaults to zero."""
        progress = LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=lesson,
        )

        assert progress.progress_percentage == 0

    def test_started_at_defaults_to_none(
        self,
        enrollment,
        lesson,
    ):
        """Started time defaults to None."""
        progress = LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=lesson,
        )

        assert progress.started_at is None

    def test_completed_at_defaults_to_none(
        self,
        enrollment,
        lesson,
    ):
        """Completed time defaults to None."""
        progress = LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=lesson,
        )

        assert progress.completed_at is None

    def test_progress_percentage_cannot_exceed_100(
        self,
        enrollment,
        lesson,
    ):
        """Progress percentage cannot exceed 100."""
        progress = LessonProgress(
            enrollment=enrollment,
            lesson=lesson,
            progress_percentage=101,
        )

        with pytest.raises(ValidationError):
            progress.full_clean()

    def test_progress_percentage_cannot_be_negative(
        self,
        enrollment,
        lesson,
    ):
        """Progress percentage cannot be negative."""
        progress = LessonProgress(
            enrollment=enrollment,
            lesson=lesson,
            progress_percentage=-1,
        )

        with pytest.raises(ValidationError):
            progress.full_clean()

    def test_completed_at_cannot_be_before_started_at(
        self,
        enrollment,
        lesson,
    ):
        """Completion time cannot be before start time."""
        started = timezone.now()
        completed = started - datetime.timedelta(minutes=1)

        progress = LessonProgress(
            enrollment=enrollment,
            lesson=lesson,
            started_at=started,
            completed_at=completed,
        )

        with pytest.raises(ValidationError):
            progress.full_clean()

    def test_progress_must_be_unique_per_enrollment_and_lesson(
        self,
        enrollment,
        lesson,
    ):
        """An enrollment cannot have duplicate progress for the same lesson."""
        LessonProgressFactory(
            enrollment=enrollment,
            lesson=lesson,
        )

        with pytest.raises(IntegrityError):
            LessonProgressFactory(
                enrollment=enrollment,
                lesson=lesson,
            )

    def test_same_lesson_can_have_progress_for_multiple_enrollments(
        self,
        lesson,
    ):
        """Different enrollments may track the same lesson."""
        progress1 = LessonProgressFactory(
            lesson=lesson,
        )

        progress2 = LessonProgressFactory(
            lesson=lesson,
        )

        assert progress1.lesson == progress2.lesson

    def test_same_enrollment_can_track_multiple_lessons(
        self,
        enrollment,
    ):
        """One enrollment can track multiple lessons."""
        progress1 = LessonProgressFactory(
            enrollment=enrollment,
        )

        progress2 = LessonProgressFactory(
            enrollment=enrollment,
        )

        assert set(enrollment.lesson_progress.all()) == {
            progress1,
            progress2,
        }

    def test_deleting_enrollment_deletes_progress(self):
        """Deleting an enrollment cascades to lesson progress."""
        progress = LessonProgressFactory()

        enrollment = progress.enrollment

        enrollment.delete()

        assert not LessonProgress.objects.filter(
            pk=progress.pk,
        ).exists()

    def test_deleting_lesson_deletes_progress(self):
        """Deleting a lesson cascades to lesson progress."""
        progress = LessonProgressFactory()

        lesson = progress.lesson

        lesson.delete()

        assert not LessonProgress.objects.filter(
            pk=progress.pk,
        ).exists()
