from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from courses.models.course import Course
from curriculums.models.lesson import Lesson
from curriculums.models.lesson_content import LessonContent
from curriculums.models.section import Section
from curriculums.models.video_content import VideoContent
from enrollments.models.enrollment import Enrollment
from enrollments.models.lesson_content_progress import LessonContentProgress
from enrollments.models.video_progress import VideoProgress, VideoWatchEvent


class TestVideoProgressFixtures:
    @pytest.fixture
    def test_user(self, db):
        from django.contrib.auth import get_user_model

        User = get_user_model()

        return User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

    @pytest.fixture
    def course(self, db, test_user):
        return Course.objects.create(
            title="Django Development",
            owner=test_user,
        )

    @pytest.fixture
    def section(self, db, course):
        return Section.objects.create(
            course=course,
            title="Introduction",
        )

    @pytest.fixture
    def lesson(self, db, section):
        return Lesson.objects.create(
            section=section,
            title="Video Lesson",
            slug="video-lesson",
        )

    @pytest.fixture
    def lesson_content(self, db, lesson):
        return LessonContent.objects.create(
            lesson=lesson,
            title="Introduction Video",
            content_type=LessonContent.Type.VIDEO,
            order=1,
        )

    @pytest.fixture
    def video_content(self, db, lesson_content):
        return VideoContent.objects.create(
            content=lesson_content,
            source=VideoContent.Source.URL,
            external_url="https://example.com/video.mp4",
            duration=timedelta(seconds=600),
        )

    @pytest.fixture
    def enrollment(self, db, test_user, course):
        return Enrollment.objects.create(
            user=test_user,
            course=course,
        )

    @pytest.fixture
    def lesson_content_progress(
        self,
        db,
        enrollment,
        lesson_content,
    ):
        return LessonContentProgress.objects.create(
            enrollment=enrollment,
            content=lesson_content,
        )

    @pytest.fixture
    def video_progress(
        self,
        db,
        lesson_content_progress,
        video_content,
    ):
        return VideoProgress.objects.create(
            lesson_content_progress=lesson_content_progress,
        )


class TestVideoProgressCreation(TestVideoProgressFixtures):
    def test_video_progress_is_created(
        self,
        video_progress,
        lesson_content_progress,
    ):
        assert video_progress.pk is not None
        assert video_progress.lesson_content_progress_id == lesson_content_progress.pk

    def test_watched_seconds_defaults_to_zero(
        self,
        video_progress,
    ):
        assert video_progress.watched_seconds == 0

    def test_string_representation_uses_user_and_content(
        self,
        video_progress,
        test_user,
        lesson_content,
    ):
        assert str(video_progress) == (f"{test_user} - {lesson_content.title}")

    def test_lesson_content_progress_has_reverse_video_progress_relation(
        self,
        lesson_content_progress,
        video_progress,
    ):
        assert lesson_content_progress.video_progress == video_progress

    def test_lesson_content_progress_is_required(self):
        video_progress = VideoProgress()

        with pytest.raises(ValidationError) as exc_info:
            video_progress.full_clean()

        assert "lesson_content_progress" in exc_info.value.message_dict

    def test_one_video_progress_per_content_progress(
        self,
        video_progress,
    ):
        with pytest.raises(IntegrityError):
            VideoProgress.objects.create(
                lesson_content_progress=(video_progress.lesson_content_progress),
            )


class TestVideoProgressRelationships(TestVideoProgressFixtures):
    def test_deleting_content_progress_deletes_video_progress(
        self,
        lesson_content_progress,
        video_progress,
    ):
        video_progress_id = video_progress.pk

        lesson_content_progress.delete()

        assert not VideoProgress.objects.filter(pk=video_progress_id).exists()

    def test_deleting_video_progress_keeps_content_progress(
        self,
        video_progress,
        lesson_content_progress,
    ):
        video_progress.delete()

        assert LessonContentProgress.objects.filter(
            pk=lesson_content_progress.pk
        ).exists()


class TestVideoProgressDuration(TestVideoProgressFixtures):
    def test_duration_seconds_returns_duration_as_decimal_seconds(
        self,
        video_progress,
    ):
        assert video_progress.duration_seconds == Decimal("600")

    def test_duration_seconds_is_decimal(
        self,
        video_progress,
    ):
        assert isinstance(
            video_progress.duration_seconds,
            Decimal,
        )

    def test_duration_seconds_supports_fractional_seconds(
        self,
        video_progress,
        video_content,
    ):
        video_content.duration = timedelta(
            seconds=600,
            microseconds=500_000,
        )
        video_content.save(update_fields=["duration"])

        assert video_progress.duration_seconds == Decimal("600.5")

    def test_duration_seconds_returns_zero_when_duration_is_none(
        self,
        video_progress,
        video_content,
    ):
        video_content.duration = None
        video_content.save(update_fields=["duration"])

        assert video_progress.duration_seconds == Decimal("0")

    def test_duration_seconds_returns_zero_for_zero_duration(
        self,
        video_progress,
        video_content,
    ):
        video_content.duration = timedelta(0)
        video_content.save(update_fields=["duration"])

        assert video_progress.duration_seconds == Decimal("0")


class TestVideoProgressWatchedPercentage(TestVideoProgressFixtures):
    def test_watched_percentage_is_zero_when_nothing_watched(
        self,
        video_progress,
    ):
        assert video_progress.watched_percentage == Decimal("0")

    def test_watched_percentage_is_calculated_correctly(
        self,
        video_progress,
    ):
        video_progress.watched_seconds = 300

        assert video_progress.watched_percentage == Decimal("50")

    def test_watched_percentage_is_ninety_at_ninety_percent(
        self,
        video_progress,
    ):
        video_progress.watched_seconds = 540

        assert video_progress.watched_percentage == Decimal("90")

    def test_watched_percentage_is_one_hundred_at_full_duration(
        self,
        video_progress,
    ):
        video_progress.watched_seconds = 600

        assert video_progress.watched_percentage == Decimal("100")

    def test_watched_percentage_can_exceed_one_hundred_when_manually_set(
        self,
        video_progress,
    ):
        video_progress.watched_seconds = 900

        assert video_progress.watched_percentage == Decimal("150")

    def test_watched_percentage_is_zero_without_video_duration(
        self,
        video_progress,
        video_content,
    ):
        video_content.duration = None
        video_content.save(update_fields=["duration"])

        video_progress.watched_seconds = 100

        assert video_progress.watched_percentage == Decimal("0")

    def test_watched_percentage_is_decimal(
        self,
        video_progress,
    ):
        video_progress.watched_seconds = 100

        assert isinstance(
            video_progress.watched_percentage,
            Decimal,
        )


class TestVideoProgressUpdateProgress(TestVideoProgressFixtures):
    def test_update_progress_saves_watched_seconds(
        self,
        video_progress,
    ):
        video_progress.update_progress(120)

        video_progress.refresh_from_db()

        assert video_progress.watched_seconds == 120

    def test_update_progress_clamps_negative_value_to_zero(
        self,
        video_progress,
    ):
        video_progress.update_progress(-100)

        video_progress.refresh_from_db()

        assert video_progress.watched_seconds == 0

    def test_update_progress_clamps_value_to_video_duration(
        self,
        video_progress,
    ):
        video_progress.update_progress(1000)

        video_progress.refresh_from_db()

        assert video_progress.watched_seconds == 600

    def test_update_progress_accepts_exact_video_duration(
        self,
        video_progress,
    ):
        video_progress.update_progress(600)

        video_progress.refresh_from_db()

        assert video_progress.watched_seconds == 600

    def test_update_progress_keeps_highest_watched_position(
        self,
        video_progress,
    ):
        video_progress.update_progress(400)
        video_progress.update_progress(200)

        video_progress.refresh_from_db()

        assert video_progress.watched_seconds == 400

    def test_update_progress_updates_to_higher_position(
        self,
        video_progress,
    ):
        video_progress.update_progress(200)
        video_progress.update_progress(500)

        video_progress.refresh_from_db()

        assert video_progress.watched_seconds == 500

    def test_update_progress_does_not_move_position_backward(
        self,
        video_progress,
    ):
        video_progress.update_progress(500)
        video_progress.update_progress(100)

        video_progress.refresh_from_db()

        assert video_progress.watched_seconds == 500

    def test_update_progress_at_ninety_percent_completes_content(
        self,
        video_progress,
        lesson_content_progress,
    ):
        video_progress.update_progress(540)

        lesson_content_progress.refresh_from_db()

        assert lesson_content_progress.status == LessonContentProgress.Status.COMPLETED
        assert lesson_content_progress.completed_at is not None

    def test_update_progress_above_ninety_percent_completes_content(
        self,
        video_progress,
        lesson_content_progress,
    ):
        video_progress.update_progress(550)

        lesson_content_progress.refresh_from_db()

        assert lesson_content_progress.status == LessonContentProgress.Status.COMPLETED
        assert lesson_content_progress.completed_at is not None

    def test_update_progress_below_ninety_percent_starts_content(
        self,
        video_progress,
        lesson_content_progress,
    ):
        video_progress.update_progress(100)

        lesson_content_progress.refresh_from_db()

        assert (
            lesson_content_progress.status == LessonContentProgress.Status.IN_PROGRESS
        )
        assert lesson_content_progress.started_at is not None
        assert lesson_content_progress.completed_at is None

    def test_update_progress_at_zero_starts_not_started_content(
        self,
        video_progress,
        lesson_content_progress,
    ):
        before = timezone.now()

        video_progress.update_progress(0)

        after = timezone.now()
        lesson_content_progress.refresh_from_db()

        assert (
            lesson_content_progress.status == LessonContentProgress.Status.IN_PROGRESS
        )
        assert lesson_content_progress.started_at is not None
        assert before <= lesson_content_progress.started_at <= after

    def test_update_progress_does_not_restart_in_progress_content(
        self,
        video_progress,
        lesson_content_progress,
    ):
        original_started_at = timezone.now() - timedelta(hours=2)

        lesson_content_progress.status = LessonContentProgress.Status.IN_PROGRESS
        lesson_content_progress.started_at = original_started_at
        lesson_content_progress.save(
            update_fields=[
                "status",
                "started_at",
            ]
        )

        video_progress.update_progress(100)

        lesson_content_progress.refresh_from_db()

        assert (
            lesson_content_progress.status == LessonContentProgress.Status.IN_PROGRESS
        )
        assert lesson_content_progress.started_at == original_started_at

    def test_update_progress_keeps_completed_content_completed(
        self,
        video_progress,
        lesson_content_progress,
    ):
        completed_at = timezone.now() - timedelta(hours=1)

        lesson_content_progress.status = LessonContentProgress.Status.COMPLETED
        lesson_content_progress.started_at = completed_at - timedelta(hours=1)
        lesson_content_progress.completed_at = completed_at
        lesson_content_progress.save(
            update_fields=[
                "status",
                "started_at",
                "completed_at",
            ]
        )

        video_progress.update_progress(100)

        lesson_content_progress.refresh_from_db()

        assert lesson_content_progress.status == LessonContentProgress.Status.COMPLETED
        assert lesson_content_progress.completed_at == completed_at


class TestVideoProgressUpdateWithoutDuration(
    TestVideoProgressFixtures,
):
    def test_update_progress_does_not_clamp_without_duration(
        self,
        video_progress,
        video_content,
    ):
        video_content.duration = None
        video_content.save(update_fields=["duration"])

        video_progress.update_progress(1000)

        video_progress.refresh_from_db()

        assert video_progress.watched_seconds == 1000

    def test_negative_progress_is_clamped_without_duration(
        self,
        video_progress,
        video_content,
    ):
        video_content.duration = None
        video_content.save(update_fields=["duration"])

        video_progress.update_progress(-100)

        video_progress.refresh_from_db()

        assert video_progress.watched_seconds == 0

    def test_update_progress_starts_content_without_duration(
        self,
        video_progress,
        video_content,
        lesson_content_progress,
    ):
        video_content.duration = None
        video_content.save(update_fields=["duration"])

        video_progress.update_progress(100)

        lesson_content_progress.refresh_from_db()

        assert (
            lesson_content_progress.status == LessonContentProgress.Status.IN_PROGRESS
        )
        assert lesson_content_progress.started_at is not None


class TestVideoProgressSyncContentProgress(
    TestVideoProgressFixtures,
):
    def test_sync_completes_content_at_exactly_ninety_percent(
        self,
        video_progress,
        lesson_content_progress,
    ):
        video_progress.watched_seconds = 540
        video_progress.save(update_fields=["watched_seconds"])

        video_progress.sync_content_progress()

        lesson_content_progress.refresh_from_db()

        assert lesson_content_progress.status == LessonContentProgress.Status.COMPLETED
        assert lesson_content_progress.completed_at is not None

    def test_sync_completes_content_above_ninety_percent(
        self,
        video_progress,
        lesson_content_progress,
    ):
        video_progress.watched_seconds = 550
        video_progress.save(update_fields=["watched_seconds"])

        video_progress.sync_content_progress()

        lesson_content_progress.refresh_from_db()

        assert lesson_content_progress.status == LessonContentProgress.Status.COMPLETED

    def test_sync_starts_not_started_content_below_ninety_percent(
        self,
        video_progress,
        lesson_content_progress,
    ):
        video_progress.watched_seconds = 100
        video_progress.save(update_fields=["watched_seconds"])

        before = timezone.now()

        video_progress.sync_content_progress()

        after = timezone.now()
        lesson_content_progress.refresh_from_db()

        assert (
            lesson_content_progress.status == LessonContentProgress.Status.IN_PROGRESS
        )
        assert lesson_content_progress.started_at is not None
        assert before <= lesson_content_progress.started_at <= after

    def test_sync_does_not_restart_in_progress_content(
        self,
        video_progress,
        lesson_content_progress,
    ):
        original_started_at = timezone.now() - timedelta(hours=2)

        lesson_content_progress.status = LessonContentProgress.Status.IN_PROGRESS
        lesson_content_progress.started_at = original_started_at
        lesson_content_progress.save(
            update_fields=[
                "status",
                "started_at",
            ]
        )

        video_progress.watched_seconds = 100
        video_progress.save(update_fields=["watched_seconds"])

        video_progress.sync_content_progress()

        lesson_content_progress.refresh_from_db()

        assert lesson_content_progress.started_at == original_started_at
        assert (
            lesson_content_progress.status == LessonContentProgress.Status.IN_PROGRESS
        )

    def test_sync_does_not_change_completed_content_below_ninety_percent(
        self,
        video_progress,
        lesson_content_progress,
    ):
        completed_at = timezone.now() - timedelta(hours=1)

        lesson_content_progress.status = LessonContentProgress.Status.COMPLETED
        lesson_content_progress.started_at = completed_at - timedelta(hours=1)
        lesson_content_progress.completed_at = completed_at
        lesson_content_progress.save(
            update_fields=[
                "status",
                "started_at",
                "completed_at",
            ]
        )

        video_progress.watched_seconds = 100
        video_progress.save(update_fields=["watched_seconds"])

        video_progress.sync_content_progress()

        lesson_content_progress.refresh_from_db()

        assert lesson_content_progress.status == LessonContentProgress.Status.COMPLETED
        assert lesson_content_progress.completed_at == completed_at


class TestVideoWatchEventFixtures:
    @pytest.fixture
    def test_user(self, db):
        from django.contrib.auth import get_user_model

        User = get_user_model()

        return User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

    @pytest.fixture
    def course(self, db, test_user):
        return Course.objects.create(
            title="Django Development",
            owner=test_user,
        )

    @pytest.fixture
    def section(self, db, course):
        return Section.objects.create(
            course=course,
            title="Introduction",
        )

    @pytest.fixture
    def lesson(self, db, section):
        return Lesson.objects.create(
            section=section,
            title="Video Lesson",
            slug="video-lesson",
        )

    @pytest.fixture
    def lesson_content(self, db, lesson):
        return LessonContent.objects.create(
            lesson=lesson,
            title="Introduction Video",
            content_type=LessonContent.Type.VIDEO,
            order=1,
        )

    @pytest.fixture
    def video_content(self, db, lesson_content):
        return VideoContent.objects.create(
            content=lesson_content,
            source=VideoContent.Source.URL,
            external_url="https://example.com/video.mp4",
            duration=timedelta(seconds=600),
        )

    @pytest.fixture
    def enrollment(self, db, test_user, course):
        return Enrollment.objects.create(
            user=test_user,
            course=course,
        )

    @pytest.fixture
    def lesson_content_progress(
        self,
        db,
        enrollment,
        lesson_content,
    ):
        return LessonContentProgress.objects.create(
            enrollment=enrollment,
            content=lesson_content,
        )

    @pytest.fixture
    def video_progress(
        self,
        db,
        lesson_content_progress,
        video_content,
    ):
        return VideoProgress.objects.create(
            lesson_content_progress=lesson_content_progress,
        )

    @pytest.fixture
    def watch_event(
        self,
        db,
        video_progress,
    ):
        return VideoWatchEvent.objects.create(
            video_progress=video_progress,
            watched_seconds=120,
        )


class TestVideoWatchEventCreation(TestVideoWatchEventFixtures):
    def test_watch_event_is_created(
        self,
        watch_event,
        video_progress,
    ):
        assert watch_event.pk is not None
        assert watch_event.video_progress_id == video_progress.pk

    def test_watch_event_stores_watched_seconds(
        self,
        watch_event,
    ):
        assert watch_event.watched_seconds == 120

    def test_created_at_is_set_automatically(
        self,
        watch_event,
    ):
        assert watch_event.created_at is not None

    def test_created_at_is_close_to_creation_time(
        self,
        watch_event,
    ):
        now = timezone.now()

        assert now - watch_event.created_at < timedelta(seconds=5)

    def test_video_progress_reverse_relation(
        self,
        video_progress,
        watch_event,
    ):
        assert list(video_progress.watch_events.all()) == [watch_event]


class TestVideoWatchEventValidation(TestVideoWatchEventFixtures):
    def test_video_progress_is_required(self):
        watch_event = VideoWatchEvent(
            watched_seconds=100,
        )

        with pytest.raises(ValidationError) as exc_info:
            watch_event.full_clean()

        assert "video_progress" in exc_info.value.message_dict

    def test_watched_seconds_is_required(
        self,
        video_progress,
    ):
        watch_event = VideoWatchEvent(
            video_progress=video_progress,
        )

        with pytest.raises(ValidationError) as exc_info:
            watch_event.full_clean()

        assert "watched_seconds" in exc_info.value.message_dict

    def test_negative_watched_seconds_is_rejected(
        self,
        video_progress,
    ):
        watch_event = VideoWatchEvent(
            video_progress=video_progress,
            watched_seconds=-1,
        )

        with pytest.raises(ValidationError) as exc_info:
            watch_event.full_clean()

        assert "watched_seconds" in exc_info.value.message_dict

    def test_zero_watched_seconds_is_valid(
        self,
        video_progress,
    ):
        watch_event = VideoWatchEvent(
            video_progress=video_progress,
            watched_seconds=0,
        )

        watch_event.full_clean()

        assert watch_event.watched_seconds == 0


class TestVideoWatchEventRelationships(TestVideoWatchEventFixtures):
    def test_multiple_watch_events_can_belong_to_same_video_progress(
        self,
        video_progress,
    ):
        first = VideoWatchEvent.objects.create(
            video_progress=video_progress,
            watched_seconds=30,
        )
        second = VideoWatchEvent.objects.create(
            video_progress=video_progress,
            watched_seconds=90,
        )

        assert video_progress.watch_events.count() == 2
        assert set(
            video_progress.watch_events.values_list(
                "pk",
                flat=True,
            )
        ) == {first.pk, second.pk}

    def test_deleting_video_progress_deletes_watch_events(
        self,
        video_progress,
        watch_event,
    ):
        watch_event_id = watch_event.pk

        video_progress.delete()

        assert not VideoWatchEvent.objects.filter(pk=watch_event_id).exists()

    def test_deleting_watch_event_keeps_video_progress(
        self,
        watch_event,
        video_progress,
    ):
        watch_event.delete()

        assert VideoProgress.objects.filter(
            pk=video_progress.pk,
        ).exists()


class TestVideoWatchEventUpdates(TestVideoWatchEventFixtures):
    def test_watched_seconds_can_be_updated(
        self,
        watch_event,
    ):
        watch_event.watched_seconds = 300
        watch_event.save(update_fields=["watched_seconds"])

        watch_event.refresh_from_db()

        assert watch_event.watched_seconds == 300

    def test_created_at_is_not_changed_when_updated(
        self,
        watch_event,
    ):
        original_created_at = watch_event.created_at

        watch_event.watched_seconds = 300
        watch_event.save(update_fields=["watched_seconds"])

        watch_event.refresh_from_db()

        assert watch_event.created_at == original_created_at


class TestVideoWatchEventTimestamps(TestVideoWatchEventFixtures):
    def test_created_at_is_auto_now_add(
        self,
        video_progress,
    ):
        before = timezone.now()

        event = VideoWatchEvent.objects.create(
            video_progress=video_progress,
            watched_seconds=100,
        )

        after = timezone.now()

        assert before <= event.created_at <= after
