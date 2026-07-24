import datetime

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from curriculums.tests.factories import LessonContentFactory
from enrollments.models import LessonContentProgress
from enrollments.tests.factories import (
    EnrollmentFactory,
    LessonContentProgressFactory,
)


@pytest.mark.django_db
class TestLessonContentProgressModel:
    """Tests for the LessonContentProgress model."""

    @pytest.fixture
    def enrollment(self):
        return EnrollmentFactory()

    @pytest.fixture
    def content(self):
        return LessonContentFactory()

    def test_create_progress(
        self,
        enrollment,
        content,
    ):
        """A lesson content progress record can be created."""
        progress = LessonContentProgress.objects.create(
            enrollment=enrollment,
            content=content,
            status=LessonContentProgress.Status.IN_PROGRESS,
            watch_percentage=40,
            resume_position=datetime.timedelta(minutes=5),
        )

        assert progress.enrollment == enrollment
        assert progress.content == content
        assert progress.status == LessonContentProgress.Status.IN_PROGRESS
        assert progress.watch_percentage == 40
        assert progress.resume_position == datetime.timedelta(minutes=5)

    def test_string_representation(self):
        """String representation should contain user and content."""
        progress = LessonContentProgressFactory()

        assert str(progress) == (
            f"{progress.enrollment.user} - {progress.content.title}"
        )

    def test_status_defaults_to_not_started(
        self,
        enrollment,
        content,
    ):
        """Status defaults to NOT_STARTED."""
        progress = LessonContentProgress.objects.create(
            enrollment=enrollment,
            content=content,
        )

        assert progress.status == LessonContentProgress.Status.NOT_STARTED

    def test_watch_percentage_defaults_to_zero(
        self,
        enrollment,
        content,
    ):
        """Watch percentage defaults to zero."""
        progress = LessonContentProgress.objects.create(
            enrollment=enrollment,
            content=content,
        )

        assert progress.watch_percentage == 0

    def test_resume_position_is_optional(
        self,
        enrollment,
        content,
    ):
        """Resume position is optional."""
        progress = LessonContentProgress.objects.create(
            enrollment=enrollment,
            content=content,
        )

        assert progress.resume_position is None

    def test_started_at_defaults_to_none(
        self,
        enrollment,
        content,
    ):
        """Started time defaults to None."""
        progress = LessonContentProgress.objects.create(
            enrollment=enrollment,
            content=content,
        )

        assert progress.started_at is None

    def test_completed_at_defaults_to_none(
        self,
        enrollment,
        content,
    ):
        """Completed time defaults to None."""
        progress = LessonContentProgress.objects.create(
            enrollment=enrollment,
            content=content,
        )

        assert progress.completed_at is None

    def test_watch_percentage_cannot_be_greater_than_100(
        self,
        enrollment,
        content,
    ):
        """Watch percentage cannot exceed 100."""
        progress = LessonContentProgress(
            enrollment=enrollment,
            content=content,
            watch_percentage=101,
        )

        with pytest.raises(ValidationError):
            progress.full_clean()

    def test_watch_percentage_cannot_be_negative(
        self,
        enrollment,
        content,
    ):
        """Watch percentage cannot be negative."""
        progress = LessonContentProgress(
            enrollment=enrollment,
            content=content,
            watch_percentage=-1,
        )

        with pytest.raises(ValidationError):
            progress.full_clean()

    def test_completed_at_cannot_be_before_started_at(
        self,
        enrollment,
        content,
    ):
        """Completion time cannot be before start time."""
        started = timezone.now()
        completed = started - datetime.timedelta(minutes=1)

        progress = LessonContentProgress(
            enrollment=enrollment,
            content=content,
            started_at=started,
            completed_at=completed,
        )

        with pytest.raises(ValidationError):
            progress.full_clean()

    def test_progress_must_be_unique_per_enrollment_and_content(
        self,
        enrollment,
        content,
    ):
        """An enrollment cannot have duplicate progress for the same content."""
        LessonContentProgressFactory(
            enrollment=enrollment,
            content=content,
        )

        with pytest.raises(IntegrityError):
            LessonContentProgressFactory(
                enrollment=enrollment,
                content=content,
            )

    def test_same_content_can_have_progress_for_multiple_enrollments(
        self,
        content,
    ):
        """Different enrollments may track the same content."""
        progress1 = LessonContentProgressFactory(
            content=content,
        )

        progress2 = LessonContentProgressFactory(
            content=content,
        )

        assert progress1.content == progress2.content

    def test_same_enrollment_can_track_multiple_contents(
        self,
        enrollment,
    ):
        """One enrollment can track multiple lesson contents."""
        progress1 = LessonContentProgressFactory(
            enrollment=enrollment,
        )

        progress2 = LessonContentProgressFactory(
            enrollment=enrollment,
        )

        assert set(enrollment.content_progress.all()) == {
            progress1,
            progress2,
        }

    def test_mark_started_sets_started_at(self):
        """mark_started sets the started time."""
        progress = LessonContentProgressFactory()

        assert progress.started_at is None

        progress.mark_started()

        assert progress.started_at is not None

    def test_mark_started_changes_status_to_in_progress(self):
        """mark_started changes NOT_STARTED to IN_PROGRESS."""
        progress = LessonContentProgressFactory(
            status=LessonContentProgress.Status.NOT_STARTED,
        )

        progress.mark_started()

        assert progress.status == LessonContentProgress.Status.IN_PROGRESS

    def test_mark_started_does_not_change_completed_status(self):
        """mark_started does not overwrite COMPLETED status."""
        progress = LessonContentProgressFactory(
            status=LessonContentProgress.Status.COMPLETED,
        )

        progress.mark_started()

        assert progress.status == LessonContentProgress.Status.COMPLETED

    def test_mark_completed_sets_completed_state(self):
        """mark_completed updates all completion fields."""
        progress = LessonContentProgressFactory(
            status=LessonContentProgress.Status.IN_PROGRESS,
            watch_percentage=45,
            completed_at=None,
        )

        progress.mark_completed()

        assert progress.status == LessonContentProgress.Status.COMPLETED
        assert progress.watch_percentage == 100
        assert progress.started_at is not None
        assert progress.completed_at is not None

    def test_deleting_enrollment_deletes_progress(self):
        """Deleting an enrollment cascades to progress."""
        progress = LessonContentProgressFactory()

        enrollment = progress.enrollment

        enrollment.delete()

        assert not LessonContentProgress.objects.filter(
            pk=progress.pk,
        ).exists()

    def test_deleting_content_deletes_progress(self):
        """Deleting lesson content cascades to progress."""
        progress = LessonContentProgressFactory()

        content = progress.content

        content.delete()

        assert not LessonContentProgress.objects.filter(
            pk=progress.pk,
        ).exists()
