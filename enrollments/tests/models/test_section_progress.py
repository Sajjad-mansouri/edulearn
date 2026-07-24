import datetime

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from curriculums.tests.factories import SectionFactory
from enrollments.models import SectionProgress
from enrollments.tests.factories import (
    EnrollmentFactory,
    SectionProgressFactory,
)


@pytest.mark.django_db
class TestSectionProgressModel:
    """Tests for the SectionProgress model."""

    @pytest.fixture
    def enrollment(self):
        return EnrollmentFactory()

    @pytest.fixture
    def section(self):
        return SectionFactory()

    def test_create_progress(
        self,
        enrollment,
        section,
    ):
        """A section progress record can be created."""
        progress = SectionProgress.objects.create(
            enrollment=enrollment,
            section=section,
            status=SectionProgress.Status.IN_PROGRESS,
            progress_percentage=40,
            started_at=timezone.now(),
        )

        assert progress.enrollment == enrollment
        assert progress.section == section
        assert progress.status == SectionProgress.Status.IN_PROGRESS
        assert progress.progress_percentage == 40

    def test_string_representation(self):
        """String representation returns user and section."""
        progress = SectionProgressFactory()

        assert str(progress) == f"{progress.enrollment.user} - {progress.section}"

    def test_status_defaults_to_not_started(
        self,
        enrollment,
        section,
    ):
        """Status defaults to NOT_STARTED."""
        progress = SectionProgress.objects.create(
            enrollment=enrollment,
            section=section,
        )

        assert progress.status == SectionProgress.Status.NOT_STARTED

    def test_progress_percentage_defaults_to_zero(
        self,
        enrollment,
        section,
    ):
        """Progress percentage defaults to zero."""
        progress = SectionProgress.objects.create(
            enrollment=enrollment,
            section=section,
        )

        assert progress.progress_percentage == 0

    def test_started_at_defaults_to_none(
        self,
        enrollment,
        section,
    ):
        """Started time defaults to None."""
        progress = SectionProgress.objects.create(
            enrollment=enrollment,
            section=section,
        )

        assert progress.started_at is None

    def test_completed_at_defaults_to_none(
        self,
        enrollment,
        section,
    ):
        """Completed time defaults to None."""
        progress = SectionProgress.objects.create(
            enrollment=enrollment,
            section=section,
        )

        assert progress.completed_at is None

    def test_progress_percentage_cannot_exceed_100(
        self,
        enrollment,
        section,
    ):
        """Progress percentage cannot exceed 100."""
        progress = SectionProgress(
            enrollment=enrollment,
            section=section,
            progress_percentage=101,
        )

        with pytest.raises(ValidationError):
            progress.full_clean()

    def test_progress_percentage_cannot_be_negative(
        self,
        enrollment,
        section,
    ):
        """Progress percentage cannot be negative."""
        progress = SectionProgress(
            enrollment=enrollment,
            section=section,
            progress_percentage=-1,
        )

        with pytest.raises(ValidationError):
            progress.full_clean()

    def test_completed_at_cannot_be_before_started_at(
        self,
        enrollment,
        section,
    ):
        """Completion time cannot be before start time."""
        started = timezone.now()
        completed = started - datetime.timedelta(minutes=1)

        progress = SectionProgress(
            enrollment=enrollment,
            section=section,
            started_at=started,
            completed_at=completed,
        )

        with pytest.raises(ValidationError):
            progress.full_clean()

    def test_progress_must_be_unique_per_enrollment_and_section(
        self,
        enrollment,
        section,
    ):
        """An enrollment cannot have duplicate progress for the same section."""
        SectionProgressFactory(
            enrollment=enrollment,
            section=section,
        )

        with pytest.raises(IntegrityError):
            SectionProgressFactory(
                enrollment=enrollment,
                section=section,
            )

    def test_same_section_can_have_progress_for_multiple_enrollments(
        self,
        section,
    ):
        """Different enrollments may track the same section."""
        progress1 = SectionProgressFactory(
            section=section,
        )

        progress2 = SectionProgressFactory(
            section=section,
        )

        assert progress1.section == progress2.section

    def test_same_enrollment_can_track_multiple_sections(
        self,
        enrollment,
    ):
        """One enrollment can track multiple sections."""
        progress1 = SectionProgressFactory(
            enrollment=enrollment,
        )

        progress2 = SectionProgressFactory(
            enrollment=enrollment,
        )

        assert set(enrollment.section_progress.all()) == {
            progress1,
            progress2,
        }

    def test_deleting_enrollment_deletes_progress(self):
        """Deleting an enrollment cascades to section progress."""
        progress = SectionProgressFactory()

        enrollment = progress.enrollment

        enrollment.delete()

        assert not SectionProgress.objects.filter(
            pk=progress.pk,
        ).exists()

    def test_deleting_section_deletes_progress(self):
        """Deleting a section cascades to section progress."""
        progress = SectionProgressFactory()

        section = progress.section

        section.delete()

        assert not SectionProgress.objects.filter(
            pk=progress.pk,
        ).exists()
