from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from courses.models.course import Course
from curriculums.models.lesson import Lesson
from curriculums.models.lesson_content import LessonContent
from curriculums.models.section import Section
from enrollments.models.enrollment import Enrollment
from enrollments.models.lesson_content_progress import LessonContentProgress
from enrollments.models.lesson_progress import LessonProgress

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestLessonProgressFixtures:
    @pytest.fixture
    def test_user(self):
        return User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

    @pytest.fixture
    def course(self, test_user):
        return Course.objects.create(
            title="Django Development",
            owner=test_user,
        )

    @pytest.fixture
    def section(self, course):
        return Section.objects.create(
            course=course,
            title="Introduction",
            order=1,
        )

    @pytest.fixture
    def lesson(self, section):
        return Lesson.objects.create(
            section=section,
            title="Getting Started",
            slug="getting-started",
            order=1,
        )

    @pytest.fixture
    def enrollment(self, test_user, course):
        return Enrollment.objects.create(
            user=test_user,
            course=course,
        )

    @pytest.fixture
    def lesson_content(self, lesson):
        return LessonContent.objects.create(
            lesson=lesson,
            title="Introduction Video",
            content_type=LessonContent.Type.VIDEO,
            order=1,
        )

    @pytest.fixture
    def second_lesson_content(self, lesson):
        return LessonContent.objects.create(
            lesson=lesson,
            title="Introduction Article",
            content_type=LessonContent.Type.ARTICLE,
            order=2,
        )

    @pytest.fixture
    def lesson_progress(self, enrollment, lesson):
        return LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=lesson,
        )

    @pytest.fixture
    def content_progress(
        self,
        enrollment,
        lesson_content,
    ):
        return LessonContentProgress.objects.create(
            enrollment=enrollment,
            content=lesson_content,
        )


class TestLessonProgressCreation(TestLessonProgressFixtures):
    def test_lesson_progress_can_be_created(
        self,
        enrollment,
        lesson,
    ):
        progress = LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=lesson,
        )

        assert progress.pk is not None
        assert progress.enrollment == enrollment
        assert progress.lesson == lesson

    def test_default_status_is_not_started(
        self,
        lesson_progress,
    ):
        assert lesson_progress.status == LessonProgress.Status.NOT_STARTED

    def test_default_progress_is_zero(
        self,
        lesson_progress,
    ):
        assert lesson_progress.progress == Decimal("0")

    def test_started_at_is_empty_by_default(
        self,
        lesson_progress,
    ):
        assert lesson_progress.started_at is None

    def test_completed_at_is_empty_by_default(
        self,
        lesson_progress,
    ):
        assert lesson_progress.completed_at is None

    @pytest.mark.parametrize(
        "status",
        [
            LessonProgress.Status.NOT_STARTED,
            LessonProgress.Status.IN_PROGRESS,
            LessonProgress.Status.COMPLETED,
        ],
    )
    def test_all_status_values_are_valid(
        self,
        enrollment,
        lesson,
        status,
    ):
        progress = LessonProgress(
            enrollment=enrollment,
            lesson=lesson,
            status=status,
        )

        progress.full_clean()

        assert progress.status == status


class TestLessonProgressValidation(TestLessonProgressFixtures):
    def test_enrollment_is_required(self, lesson):
        progress = LessonProgress(
            lesson=lesson,
        )

        with pytest.raises(ValidationError) as exc_info:
            progress.full_clean()

        assert "enrollment" in exc_info.value.message_dict

    def test_lesson_is_required(self, enrollment):
        progress = LessonProgress(
            enrollment=enrollment,
        )

        with pytest.raises(ValidationError) as exc_info:
            progress.full_clean()

        assert "lesson" in exc_info.value.message_dict

    @pytest.mark.parametrize(
        "progress_value",
        [
            Decimal("-0.01"),
            Decimal("-1"),
            Decimal("100.01"),
            Decimal("101"),
        ],
    )
    def test_progress_must_be_between_zero_and_one_hundred(
        self,
        enrollment,
        lesson,
        progress_value,
    ):
        progress = LessonProgress(
            enrollment=enrollment,
            lesson=lesson,
            progress=progress_value,
        )

        with pytest.raises(ValidationError) as exc_info:
            progress.full_clean()

        assert "progress" in exc_info.value.message_dict

    @pytest.mark.parametrize(
        "progress_value",
        [
            Decimal("0"),
            Decimal("0.01"),
            Decimal("25"),
            Decimal("50.50"),
            Decimal("99.99"),
            Decimal("100"),
        ],
    )
    def test_progress_accepts_values_between_zero_and_one_hundred(
        self,
        enrollment,
        lesson,
        progress_value,
    ):
        progress = LessonProgress(
            enrollment=enrollment,
            lesson=lesson,
            progress=progress_value,
        )

        progress.full_clean()

        assert progress.progress == progress_value

    def test_completed_at_cannot_be_before_started_at(
        self,
        enrollment,
        lesson,
    ):
        started_at = timezone.now()
        completed_at = started_at - timedelta(minutes=1)

        progress = LessonProgress(
            enrollment=enrollment,
            lesson=lesson,
            started_at=started_at,
            completed_at=completed_at,
        )

        with pytest.raises(ValidationError) as exc_info:
            progress.full_clean()

        assert "completed_at" in exc_info.value.message_dict

    def test_completed_at_can_equal_started_at(
        self,
        enrollment,
        lesson,
    ):
        timestamp = timezone.now()

        progress = LessonProgress(
            enrollment=enrollment,
            lesson=lesson,
            started_at=timestamp,
            completed_at=timestamp,
        )

        progress.full_clean()


class TestLessonProgressUniqueness(TestLessonProgressFixtures):
    def test_same_enrollment_and_lesson_cannot_have_two_progress_records(
        self,
        lesson_progress,
        enrollment,
        lesson,
    ):
        duplicate = LessonProgress(
            enrollment=enrollment,
            lesson=lesson,
        )

        with pytest.raises(ValidationError) as exc_info:
            duplicate.full_clean()

        assert "__all__" in exc_info.value.message_dict

    def test_uniqueness_is_enforced_at_database_level(
        self,
        lesson_progress,
        enrollment,
        lesson,
    ):
        with pytest.raises(IntegrityError):
            LessonProgress.objects.create(
                enrollment=enrollment,
                lesson=lesson,
            )


class TestLessonProgressRelationships(TestLessonProgressFixtures):
    def test_enrollment_has_reverse_lesson_progress_relation(
        self,
        enrollment,
        lesson_progress,
    ):
        assert lesson_progress in enrollment.lesson_progress.all()

    def test_lesson_has_reverse_progress_records_relation(
        self,
        lesson,
        lesson_progress,
    ):
        assert lesson_progress in lesson.progress_records.all()

    def test_deleting_enrollment_deletes_lesson_progress(
        self,
        enrollment,
        lesson_progress,
    ):
        progress_id = lesson_progress.pk

        enrollment.delete()

        assert not LessonProgress.objects.filter(pk=progress_id).exists()

    def test_deleting_lesson_deletes_lesson_progress(
        self,
        lesson,
        lesson_progress,
    ):
        progress_id = lesson_progress.pk

        lesson.delete()

        assert not LessonProgress.objects.filter(pk=progress_id).exists()


class TestLessonProgressStringRepresentation(TestLessonProgressFixtures):
    def test_str_contains_user_and_lesson(
        self,
        lesson_progress,
        test_user,
        lesson,
    ):
        result = str(lesson_progress)

        assert str(test_user) in result
        assert str(lesson) in result


class TestLessonProgressMarkCompleted(TestLessonProgressFixtures):
    def test_mark_completed_sets_status_to_completed(
        self,
        lesson_progress,
    ):
        lesson_progress.mark_completed()

        lesson_progress.refresh_from_db()

        assert lesson_progress.status == LessonProgress.Status.COMPLETED

    def test_mark_completed_sets_progress_to_one_hundred(
        self,
        lesson_progress,
    ):
        lesson_progress.mark_completed()

        lesson_progress.refresh_from_db()

        assert lesson_progress.progress == Decimal("100.00")

    def test_mark_completed_sets_started_at_when_missing(
        self,
        lesson_progress,
    ):
        before = timezone.now()

        lesson_progress.mark_completed()

        after = timezone.now()
        lesson_progress.refresh_from_db()

        assert lesson_progress.started_at is not None
        assert before <= lesson_progress.started_at <= after

    def test_mark_completed_sets_completed_at_when_missing(
        self,
        lesson_progress,
    ):
        before = timezone.now()

        lesson_progress.mark_completed()

        after = timezone.now()
        lesson_progress.refresh_from_db()

        assert lesson_progress.completed_at is not None
        assert before <= lesson_progress.completed_at <= after

    def test_mark_completed_preserves_existing_started_at(
        self,
        lesson_progress,
    ):
        started_at = timezone.now() - timedelta(hours=2)

        lesson_progress.started_at = started_at
        lesson_progress.save(update_fields=["started_at"])

        lesson_progress.mark_completed()

        lesson_progress.refresh_from_db()

        assert lesson_progress.started_at == started_at

    def test_mark_completed_preserves_existing_completed_at(
        self,
        lesson_progress,
    ):
        completed_at = timezone.now() - timedelta(hours=1)

        lesson_progress.completed_at = completed_at
        lesson_progress.status = LessonProgress.Status.IN_PROGRESS
        lesson_progress.progress = Decimal("50")
        lesson_progress.save(
            update_fields=[
                "completed_at",
                "status",
                "progress",
            ]
        )

        lesson_progress.mark_completed()

        lesson_progress.refresh_from_db()

        assert lesson_progress.completed_at == completed_at

    def test_mark_completed_updates_enrollment_progress(
        self,
        enrollment,
        lesson,
    ):
        lesson_progress = LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=lesson,
        )

        lesson_progress.mark_completed()

        enrollment.refresh_from_db()

        assert enrollment.progress == Decimal("100.00")
        assert enrollment.completed_at is not None


class TestLessonProgressRecalculateProgress(TestLessonProgressFixtures):
    def test_no_content_sets_progress_to_zero(
        self,
        lesson_progress,
    ):
        lesson_progress.recalculate_progress()

        lesson_progress.refresh_from_db()

        assert lesson_progress.progress == Decimal("0.00")
        assert lesson_progress.status == LessonProgress.Status.IN_PROGRESS
        assert lesson_progress.started_at is not None
        assert lesson_progress.completed_at is None

    def test_incomplete_content_sets_progress_to_zero(
        self,
        lesson_progress,
        lesson_content,
    ):
        LessonContentProgress.objects.create(
            enrollment=lesson_progress.enrollment,
            content=lesson_content,
            status=LessonContentProgress.Status.IN_PROGRESS,
        )

        lesson_progress.recalculate_progress()

        lesson_progress.refresh_from_db()

        assert lesson_progress.progress == Decimal("0.00")
        assert lesson_progress.status == LessonProgress.Status.IN_PROGRESS
        assert lesson_progress.completed_at is None

    def test_completed_content_sets_progress_to_one_hundred(
        self,
        lesson_progress,
        lesson_content,
    ):
        now = timezone.now()

        LessonContentProgress.objects.create(
            enrollment=lesson_progress.enrollment,
            content=lesson_content,
            status=LessonContentProgress.Status.COMPLETED,
            started_at=now,
            completed_at=now,
        )

        lesson_progress.recalculate_progress()

        lesson_progress.refresh_from_db()

        assert lesson_progress.progress == Decimal("100.00")
        assert lesson_progress.status == LessonProgress.Status.COMPLETED
        assert lesson_progress.started_at is not None
        assert lesson_progress.completed_at is not None

    def test_only_completed_content_counts(
        self,
        lesson_progress,
        lesson_content,
    ):
        LessonContentProgress.objects.create(
            enrollment=lesson_progress.enrollment,
            content=lesson_content,
            status=LessonContentProgress.Status.IN_PROGRESS,
        )

        lesson_progress.recalculate_progress()

        lesson_progress.refresh_from_db()

        assert lesson_progress.progress == Decimal("0.00")
        assert lesson_progress.status == LessonProgress.Status.IN_PROGRESS

    def test_incomplete_progress_clears_completed_at(
        self,
        lesson_progress,
        lesson_content,
    ):
        completed_at = timezone.now() - timedelta(hours=1)

        lesson_progress.status = LessonProgress.Status.COMPLETED
        lesson_progress.progress = Decimal("100")
        lesson_progress.started_at = completed_at - timedelta(hours=1)
        lesson_progress.completed_at = completed_at
        lesson_progress.save()

        LessonContentProgress.objects.create(
            enrollment=lesson_progress.enrollment,
            content=lesson_content,
            status=LessonContentProgress.Status.IN_PROGRESS,
        )

        lesson_progress.recalculate_progress()

        lesson_progress.refresh_from_db()

        assert lesson_progress.progress == Decimal("0.00")
        assert lesson_progress.status == LessonProgress.Status.IN_PROGRESS
        assert lesson_progress.completed_at is None

    def test_existing_completed_at_is_preserved_at_one_hundred_percent(
        self,
        lesson_progress,
        lesson_content,
    ):
        completed_at = timezone.now() - timedelta(hours=2)

        lesson_progress.started_at = completed_at - timedelta(hours=1)
        lesson_progress.completed_at = completed_at
        lesson_progress.status = LessonProgress.Status.COMPLETED
        lesson_progress.progress = Decimal("100")
        lesson_progress.save()

        now = timezone.now()

        LessonContentProgress.objects.create(
            enrollment=lesson_progress.enrollment,
            content=lesson_content,
            status=LessonContentProgress.Status.COMPLETED,
            started_at=now,
            completed_at=now,
        )

        lesson_progress.recalculate_progress()

        lesson_progress.refresh_from_db()

        assert lesson_progress.progress == Decimal("100.00")
        assert lesson_progress.completed_at == completed_at

    def test_recalculate_progress_sets_started_at_when_missing(
        self,
        lesson_progress,
        lesson_content,
    ):
        before = timezone.now()

        LessonContentProgress.objects.create(
            enrollment=lesson_progress.enrollment,
            content=lesson_content,
            status=LessonContentProgress.Status.IN_PROGRESS,
        )

        lesson_progress.recalculate_progress()

        after = timezone.now()
        lesson_progress.refresh_from_db()

        assert before <= lesson_progress.started_at <= after

    def test_recalculate_progress_updates_enrollment_after_lesson_is_saved(
        self,
        enrollment,
        lesson,
        lesson_content,
    ):
        lesson_progress = LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=lesson,
        )

        LessonContentProgress.objects.create(
            enrollment=enrollment,
            content=lesson_content,
            status=LessonContentProgress.Status.COMPLETED,
            started_at=timezone.now(),
            completed_at=timezone.now(),
        )

        lesson_progress.recalculate_progress()

        lesson_progress.refresh_from_db()
        enrollment.refresh_from_db()

        assert lesson_progress.progress == Decimal("100.00")
        assert lesson_progress.status == LessonProgress.Status.COMPLETED
        assert enrollment.progress == Decimal("100.00")
        assert enrollment.completed_at is not None


class TestLessonContentProgressCreation(TestLessonProgressFixtures):
    def test_content_progress_can_be_created(
        self,
        enrollment,
        lesson_content,
    ):
        progress = LessonContentProgress.objects.create(
            enrollment=enrollment,
            content=lesson_content,
        )

        assert progress.pk is not None
        assert progress.enrollment == enrollment
        assert progress.content == lesson_content

    def test_default_status_is_not_started(
        self,
        content_progress,
    ):
        assert content_progress.status == LessonContentProgress.Status.NOT_STARTED

    def test_started_at_is_empty_by_default(
        self,
        content_progress,
    ):
        assert content_progress.started_at is None

    def test_completed_at_is_empty_by_default(
        self,
        content_progress,
    ):
        assert content_progress.completed_at is None

    @pytest.mark.parametrize(
        "status",
        [
            LessonContentProgress.Status.NOT_STARTED,
            LessonContentProgress.Status.IN_PROGRESS,
            LessonContentProgress.Status.COMPLETED,
        ],
    )
    def test_all_status_values_are_valid(
        self,
        enrollment,
        lesson_content,
        status,
    ):
        progress = LessonContentProgress(
            enrollment=enrollment,
            content=lesson_content,
            status=status,
        )

        if status == LessonContentProgress.Status.COMPLETED:
            progress.completed_at = timezone.now()

        progress.full_clean()

        assert progress.status == status


class TestLessonContentProgressValidation(TestLessonProgressFixtures):
    def test_enrollment_is_required(
        self,
        lesson_content,
    ):
        progress = LessonContentProgress(
            content=lesson_content,
        )

        with pytest.raises(ValidationError) as exc_info:
            progress.full_clean()

        assert "enrollment" in exc_info.value.message_dict

    def test_content_is_required(
        self,
        enrollment,
    ):
        progress = LessonContentProgress(
            enrollment=enrollment,
        )

        with pytest.raises(ValidationError) as exc_info:
            progress.full_clean()

        assert "content" in exc_info.value.message_dict

    def test_completed_at_cannot_be_before_started_at(
        self,
        enrollment,
        lesson_content,
    ):
        started_at = timezone.now()
        completed_at = started_at - timedelta(minutes=1)

        progress = LessonContentProgress(
            enrollment=enrollment,
            content=lesson_content,
            started_at=started_at,
            completed_at=completed_at,
        )

        with pytest.raises(ValidationError) as exc_info:
            progress.full_clean()

        assert "completed_at" in exc_info.value.message_dict

    def test_completed_status_requires_completed_at(
        self,
        enrollment,
        lesson_content,
    ):
        progress = LessonContentProgress(
            enrollment=enrollment,
            content=lesson_content,
            status=LessonContentProgress.Status.COMPLETED,
        )

        with pytest.raises(ValidationError) as exc_info:
            progress.full_clean()

        assert "completed_at" in exc_info.value.message_dict

    def test_completed_status_with_completed_at_is_valid(
        self,
        enrollment,
        lesson_content,
    ):
        completed_at = timezone.now()

        progress = LessonContentProgress(
            enrollment=enrollment,
            content=lesson_content,
            status=LessonContentProgress.Status.COMPLETED,
            started_at=completed_at,
            completed_at=completed_at,
        )

        progress.full_clean()


class TestLessonContentProgressUniqueness(TestLessonProgressFixtures):
    def test_same_enrollment_and_content_cannot_have_two_progress_records(
        self,
        content_progress,
        enrollment,
        lesson_content,
    ):
        duplicate = LessonContentProgress(
            enrollment=enrollment,
            content=lesson_content,
        )

        with pytest.raises(ValidationError) as exc_info:
            duplicate.full_clean()

        assert "__all__" in exc_info.value.message_dict

    def test_uniqueness_is_enforced_at_database_level(
        self,
        content_progress,
        enrollment,
        lesson_content,
    ):
        with pytest.raises(IntegrityError):
            LessonContentProgress.objects.create(
                enrollment=enrollment,
                content=lesson_content,
            )


class TestLessonContentProgressRelationships(TestLessonProgressFixtures):
    def test_enrollment_has_reverse_content_progress_relation(
        self,
        enrollment,
        content_progress,
    ):
        assert content_progress in enrollment.content_progress.all()

    def test_content_has_reverse_progress_records_relation(
        self,
        lesson_content,
        content_progress,
    ):
        assert content_progress in lesson_content.progress_records.all()

    def test_deleting_enrollment_deletes_content_progress(
        self,
        enrollment,
        content_progress,
    ):
        progress_id = content_progress.pk

        enrollment.delete()

        assert not LessonContentProgress.objects.filter(pk=progress_id).exists()

    def test_deleting_content_deletes_content_progress(
        self,
        lesson_content,
        content_progress,
    ):
        progress_id = content_progress.pk

        lesson_content.delete()

        assert not LessonContentProgress.objects.filter(pk=progress_id).exists()


class TestLessonContentProgressStringRepresentation(TestLessonProgressFixtures):
    def test_str_contains_user_and_content_title(
        self,
        content_progress,
        test_user,
        lesson_content,
    ):
        result = str(content_progress)

        assert str(test_user) in result
        assert lesson_content.title in result


class TestLessonContentProgressMarkStarted(TestLessonProgressFixtures):
    def test_mark_started_sets_started_at(
        self,
        content_progress,
    ):
        before = timezone.now()

        content_progress.mark_started()

        after = timezone.now()
        content_progress.refresh_from_db()

        assert before <= content_progress.started_at <= after

    def test_mark_started_changes_not_started_to_in_progress(
        self,
        content_progress,
    ):
        assert content_progress.status == LessonContentProgress.Status.NOT_STARTED

        content_progress.mark_started()

        content_progress.refresh_from_db()

        assert content_progress.status == LessonContentProgress.Status.IN_PROGRESS

    def test_mark_started_does_not_change_in_progress_status(
        self,
        content_progress,
    ):
        content_progress.status = LessonContentProgress.Status.IN_PROGRESS
        content_progress.save(update_fields=["status"])

        content_progress.mark_started()

        content_progress.refresh_from_db()

        assert content_progress.status == LessonContentProgress.Status.IN_PROGRESS

    def test_mark_started_does_not_replace_existing_started_at(
        self,
        content_progress,
    ):
        started_at = timezone.now() - timedelta(hours=2)

        content_progress.started_at = started_at
        content_progress.save(update_fields=["started_at"])

        content_progress.mark_started()

        content_progress.refresh_from_db()

        assert content_progress.started_at == started_at

    def test_mark_started_does_not_change_completed_status(
        self,
        content_progress,
    ):
        now = timezone.now()

        content_progress.status = LessonContentProgress.Status.COMPLETED
        content_progress.started_at = now - timedelta(hours=1)
        content_progress.completed_at = now
        content_progress.save(
            update_fields=[
                "status",
                "started_at",
                "completed_at",
            ]
        )

        content_progress.mark_started()

        content_progress.refresh_from_db()

        assert content_progress.status == LessonContentProgress.Status.COMPLETED


class TestLessonContentProgressMarkCompleted(TestLessonProgressFixtures):
    def test_mark_completed_sets_completed_status(
        self,
        content_progress,
    ):
        content_progress.mark_completed()

        content_progress.refresh_from_db()

        assert content_progress.status == LessonContentProgress.Status.COMPLETED

    def test_mark_completed_sets_started_at_when_missing(
        self,
        content_progress,
    ):
        before = timezone.now()

        content_progress.mark_completed()

        after = timezone.now()
        content_progress.refresh_from_db()

        assert before <= content_progress.started_at <= after

    def test_mark_completed_sets_completed_at_when_missing(
        self,
        content_progress,
    ):
        before = timezone.now()

        content_progress.mark_completed()

        after = timezone.now()
        content_progress.refresh_from_db()

        assert before <= content_progress.completed_at <= after

    def test_mark_completed_preserves_existing_started_at(
        self,
        content_progress,
    ):
        started_at = timezone.now() - timedelta(hours=2)

        content_progress.started_at = started_at
        content_progress.save(update_fields=["started_at"])

        content_progress.mark_completed()

        content_progress.refresh_from_db()

        assert content_progress.started_at == started_at

    def test_mark_completed_preserves_existing_completed_at(
        self,
        content_progress,
    ):
        completed_at = timezone.now() - timedelta(hours=1)

        content_progress.status = LessonContentProgress.Status.IN_PROGRESS
        content_progress.started_at = completed_at - timedelta(hours=1)
        content_progress.completed_at = completed_at
        content_progress.save(
            update_fields=[
                "status",
                "started_at",
                "completed_at",
            ]
        )

        content_progress.mark_completed()

        content_progress.refresh_from_db()

        assert content_progress.completed_at == completed_at

    def test_mark_completed_creates_lesson_progress(
        self,
        enrollment,
        lesson,
        lesson_content,
    ):
        content_progress = LessonContentProgress.objects.create(
            enrollment=enrollment,
            content=lesson_content,
        )

        assert not LessonProgress.objects.filter(
            enrollment=enrollment,
            lesson=lesson,
        ).exists()

        content_progress.mark_completed()

        lesson_progress = LessonProgress.objects.get(
            enrollment=enrollment,
            lesson=lesson,
        )

        assert lesson_progress.pk is not None

    def test_mark_completed_updates_lesson_progress(
        self,
        enrollment,
        lesson,
        lesson_content,
    ):
        lesson_progress = LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=lesson,
        )

        content_progress = LessonContentProgress.objects.create(
            enrollment=enrollment,
            content=lesson_content,
        )

        content_progress.mark_completed()

        lesson_progress.refresh_from_db()

        assert lesson_progress.progress == Decimal("100")
        assert lesson_progress.status == LessonProgress.Status.COMPLETED

    def test_mark_completed_updates_enrollment_progress(
        self,
        enrollment,
        lesson_content,
    ):
        content_progress = LessonContentProgress.objects.create(
            enrollment=enrollment,
            content=lesson_content,
        )

        content_progress.mark_completed()

        enrollment.refresh_from_db()

        assert enrollment.progress == Decimal("100.00")
        assert enrollment.completed_at is not None


class TestLessonContentProgressUpdateLessonProgress(TestLessonProgressFixtures):
    def test_update_lesson_progress_creates_missing_lesson_progress(
        self,
        enrollment,
        lesson,
        lesson_content,
    ):
        content_progress = LessonContentProgress.objects.create(
            enrollment=enrollment,
            content=lesson_content,
        )

        content_progress.update_lesson_progress()

        lesson_progress = LessonProgress.objects.get(
            enrollment=enrollment,
            lesson=lesson,
        )

        assert lesson_progress.pk is not None

    def test_update_lesson_progress_reuses_existing_lesson_progress(
        self,
        enrollment,
        lesson,
        lesson_content,
    ):
        existing = LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=lesson,
        )

        content_progress = LessonContentProgress.objects.create(
            enrollment=enrollment,
            content=lesson_content,
        )

        content_progress.update_lesson_progress()

        assert (
            LessonProgress.objects.filter(
                enrollment=enrollment,
                lesson=lesson,
            ).count()
            == 1
        )

        existing.refresh_from_db()

        assert existing.pk is not None

    def test_update_lesson_progress_recalculates_parent_progress(
        self,
        enrollment,
        lesson,
        lesson_content,
    ):
        content_progress = LessonContentProgress.objects.create(
            enrollment=enrollment,
            content=lesson_content,
            status=LessonContentProgress.Status.COMPLETED,
            started_at=timezone.now(),
            completed_at=timezone.now(),
        )

        content_progress.update_lesson_progress()

        lesson_progress = LessonProgress.objects.get(
            enrollment=enrollment,
            lesson=lesson,
        )

        assert lesson_progress.progress == Decimal("100.00")
        assert lesson_progress.status == LessonProgress.Status.COMPLETED
        assert lesson_progress.started_at is not None
        assert lesson_progress.completed_at is not None
