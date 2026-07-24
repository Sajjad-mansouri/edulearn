import datetime

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from courses.tests.factories import CourseFactory
from enrollments.models import CourseProgress
from enrollments.tests.factories import (
    CourseProgressFactory,
    EnrollmentFactory,
)


@pytest.mark.django_db
class TestCourseProgressModel:
    """Tests for the CourseProgress model."""

    @pytest.fixture
    def enrollment(self):
        return EnrollmentFactory()

    def test_create_progress(self, enrollment):
        """A course progress record can be created."""
        progress = CourseProgress.objects.create(
            enrollment=enrollment,
            course=enrollment.course,
            status=CourseProgress.Status.IN_PROGRESS,
            progress_percentage=40,
            started_at=timezone.now(),
        )

        assert progress.enrollment == enrollment
        assert progress.course == enrollment.course
        assert progress.status == CourseProgress.Status.IN_PROGRESS
        assert progress.progress_percentage == 40

    def test_string_representation(self):
        """String representation returns user and course."""
        progress = CourseProgressFactory()

        assert str(progress) == f"{progress.enrollment.user} - {progress.course}"

    def test_status_defaults_to_not_started(self, enrollment):
        """Status defaults to NOT_STARTED."""
        progress = CourseProgress.objects.create(
            enrollment=enrollment,
            course=enrollment.course,
        )

        assert progress.status == CourseProgress.Status.NOT_STARTED

    def test_progress_percentage_defaults_to_zero(self, enrollment):
        """Progress percentage defaults to zero."""
        progress = CourseProgress.objects.create(
            enrollment=enrollment,
            course=enrollment.course,
        )

        assert progress.progress_percentage == 0

    def test_started_at_defaults_to_none(self, enrollment):
        """Started time defaults to None."""
        progress = CourseProgress.objects.create(
            enrollment=enrollment,
            course=enrollment.course,
        )

        assert progress.started_at is None

    def test_completed_at_defaults_to_none(self, enrollment):
        """Completed time defaults to None."""
        progress = CourseProgress.objects.create(
            enrollment=enrollment,
            course=enrollment.course,
        )

        assert progress.completed_at is None

    def test_progress_percentage_cannot_exceed_100(
        self,
        enrollment,
    ):
        """Progress percentage cannot exceed 100."""
        progress = CourseProgress(
            enrollment=enrollment,
            course=enrollment.course,
            progress_percentage=101,
        )

        with pytest.raises(ValidationError):
            progress.full_clean()

    def test_progress_percentage_cannot_be_negative(
        self,
        enrollment,
    ):
        """Progress percentage cannot be negative."""
        progress = CourseProgress(
            enrollment=enrollment,
            course=enrollment.course,
            progress_percentage=-1,
        )

        with pytest.raises(ValidationError):
            progress.full_clean()

    def test_completed_at_cannot_be_before_started_at(
        self,
        enrollment,
    ):
        """Completion time cannot be before start time."""
        started = timezone.now()
        completed = started - datetime.timedelta(minutes=1)

        progress = CourseProgress(
            enrollment=enrollment,
            course=enrollment.course,
            started_at=started,
            completed_at=completed,
        )

        with pytest.raises(ValidationError):
            progress.full_clean()

    def test_course_must_match_enrollment_course(
        self,
        enrollment,
    ):
        """Course must match the enrollment course."""
        another_course = CourseFactory()

        progress = CourseProgress(
            enrollment=enrollment,
            course=another_course,
        )

        with pytest.raises(ValidationError):
            progress.full_clean()

    def test_enrollment_can_have_only_one_course_progress(
        self,
        enrollment,
    ):
        """An enrollment can have only one course progress."""
        CourseProgressFactory(
            enrollment=enrollment,
        )

        with pytest.raises(IntegrityError):
            CourseProgressFactory(
                enrollment=enrollment,
            )

    def test_deleting_enrollment_deletes_progress(self):
        """Deleting an enrollment cascades to course progress."""
        progress = CourseProgressFactory()

        enrollment = progress.enrollment

        enrollment.delete()

        assert not CourseProgress.objects.filter(
            pk=progress.pk,
        ).exists()

    def test_deleting_course_deletes_progress(self):
        """Deleting a course cascades to course progress."""
        progress = CourseProgressFactory()

        course = progress.course

        course.delete()

        assert not CourseProgress.objects.filter(
            pk=progress.pk,
        ).exists()
