from datetime import timedelta

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from curriculums.models import Lesson, LessonContent, Section
from enrollments.models import (
    LessonContentProgress,
    VideoProgress,
    VideoWatchEvent,
)


@pytest.mark.django_db
class TestLessonVideoProgressApiView:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def section(self, course):
        return Section.objects.create(
            course=course,
            title="Django Basics",
            description="Django fundamentals",
            order=1,
            duration=timedelta(hours=1),
        )

    @pytest.fixture
    def lessons(self, section):
        return [
            Lesson.objects.create(
                section=section,
                title="Introduction to Django",
                description="Learn Django fundamentals.",
                order=1,
                duration=timedelta(minutes=30),
                is_published=True,
                is_preview=False,
            ),
            Lesson.objects.create(
                section=section,
                title="Django Models",
                description="Learn Django models.",
                order=2,
                duration=timedelta(minutes=30),
                is_published=True,
                is_preview=False,
            ),
        ]

    @pytest.fixture
    def video_content(self, lessons):
        return LessonContent.objects.create(
            lesson=lessons[0],
            is_main_content=True,
            title="Introduction to Django Video",
            content_type=LessonContent.Type.VIDEO,
            order=1,
        )

    @pytest.fixture
    def article_content(self, lessons):
        return LessonContent.objects.create(
            lesson=lessons[1],
            is_main_content=True,
            title="Django Models Article",
            content_type=LessonContent.Type.ARTICLE,
            order=1,
        )

    @pytest.fixture
    def lesson_content_progress(
        self,
        enrollment,
        video_content,
    ):
        return LessonContentProgress.objects.create(
            enrollment=enrollment,
            content=video_content,
        )

    @pytest.fixture
    def video_progress(
        self,
        lesson_content_progress,
    ):
        return VideoProgress.objects.create(
            lesson_content_progress=lesson_content_progress,
            watched_seconds=30,
        )

    @pytest.fixture
    def video_progress_url(
        self,
        enrollment,
        video_content,
    ):
        return reverse(
            "enrollment_api:enrollment_video_progress",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": video_content.lesson_id,
            },
        )

    def test_updates_existing_video_progress(
        self,
        api_client,
        test_user,
        video_progress,
        video_progress_url,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            video_progress_url,
            {"timestamp": 60},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"success": True}

        video_progress.refresh_from_db()

        assert video_progress.watched_seconds == 60

        assert VideoWatchEvent.objects.filter(
            video_progress=video_progress,
            watched_seconds=60,
        ).exists()

    def test_does_not_move_progress_backward(
        self,
        api_client,
        test_user,
        video_progress,
        video_progress_url,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            video_progress_url,
            {"timestamp": 10},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        video_progress.refresh_from_db()

        assert video_progress.watched_seconds == 30

        assert VideoWatchEvent.objects.filter(
            video_progress=video_progress,
            watched_seconds=10,
        ).exists()

    def test_keeps_same_progress_when_timestamp_is_equal(
        self,
        api_client,
        test_user,
        video_progress,
        video_progress_url,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            video_progress_url,
            {"timestamp": 30},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        video_progress.refresh_from_db()

        assert video_progress.watched_seconds == 30

    def test_creates_video_progress_for_first_update(
        self,
        api_client,
        test_user,
        enrollment,
        video_content,
        video_progress_url,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            video_progress_url,
            {"timestamp": 45},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"success": True}

        content_progress = LessonContentProgress.objects.get(
            enrollment=enrollment,
            content=video_content,
        )

        video_progress = VideoProgress.objects.get(
            lesson_content_progress=content_progress,
        )

        assert video_progress.watched_seconds == 45

        assert VideoWatchEvent.objects.filter(
            video_progress=video_progress,
            watched_seconds=45,
        ).exists()

    @pytest.mark.parametrize(
        "payload",
        [
            {},
            {"timestamp": None},
            {"timestamp": -1},
            {"timestamp": -10},
            {"timestamp": "30"},
            {"timestamp": "30.5"},
            {"timestamp": ""},
            {"timestamp": []},
            {"timestamp": {}},
        ],
    )
    def test_rejects_invalid_timestamp(
        self,
        api_client,
        test_user,
        video_progress_url,
        payload,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            video_progress_url,
            payload,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            "error": "Valid timestamp required",
        }

    def test_accepts_zero_timestamp(
        self,
        api_client,
        test_user,
        video_progress,
        video_progress_url,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            video_progress_url,
            {"timestamp": 0},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        video_progress.refresh_from_db()

        assert video_progress.watched_seconds == 30

        assert VideoWatchEvent.objects.filter(
            video_progress=video_progress,
            watched_seconds=0,
        ).exists()

    def test_rejects_nonexistent_lesson(
        self,
        api_client,
        test_user,
        enrollment,
    ):
        api_client.force_authenticate(user=test_user)

        url = reverse(
            "enrollment_api:enrollment_video_progress",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": 999999,
            },
        )

        response = api_client.post(
            url,
            {"timestamp": 30},
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_rejects_non_video_content(
        self,
        api_client,
        test_user,
        enrollment,
        article_content,
    ):
        api_client.force_authenticate(user=test_user)

        url = reverse(
            "enrollment_api:enrollment_video_progress",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": article_content.lesson_id,
            },
        )

        response = api_client.post(
            url,
            {"timestamp": 30},
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_rejects_lesson_from_another_course(
        self,
        api_client,
        test_user,
        enrollment,
        category,
    ):
        api_client.force_authenticate(user=test_user)

        another_course = enrollment.course.__class__.objects.create(
            title="Another Course",
            owner=test_user,
            category=category,
        )

        another_section = Section.objects.create(
            course=another_course,
            title="Another Section",
            description="Another course section",
            order=1,
            duration=timedelta(hours=1),
        )

        another_lesson = Lesson.objects.create(
            section=another_section,
            title="Another Lesson",
            description="Lesson from another course.",
            order=1,
            duration=timedelta(minutes=30),
            is_published=True,
            is_preview=False,
        )

        LessonContent.objects.create(
            lesson=another_lesson,
            is_main_content=True,
            title="Another Video",
            content_type=LessonContent.Type.VIDEO,
            order=1,
        )

        url = reverse(
            "enrollment_api:enrollment_video_progress",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": another_lesson.id,
            },
        )

        response = api_client.post(
            url,
            {"timestamp": 30},
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_rejects_another_users_enrollment(
        self,
        api_client,
        test_user,
        another_user_enrollment,
        video_content,
    ):
        api_client.force_authenticate(user=test_user)

        url = reverse(
            "enrollment_api:enrollment_video_progress",
            kwargs={
                "enrollment_id": another_user_enrollment.id,
                "lesson_id": video_content.lesson_id,
            },
        )

        response = api_client.post(
            url,
            {"timestamp": 30},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize(
        "enrollment_status",
        [
            "cancelled",
            "suspended",
            "pending",
        ],
    )
    def test_rejects_inactive_enrollment(
        self,
        api_client,
        test_user,
        enrollment,
        video_content,
        enrollment_status,
    ):
        api_client.force_authenticate(user=test_user)

        enrollment.status = enrollment_status
        enrollment.save(update_fields=["status"])

        url = reverse(
            "enrollment_api:enrollment_video_progress",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": video_content.lesson_id,
            },
        )

        response = api_client.post(
            url,
            {"timestamp": 30},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_allows_completed_enrollment(
        self,
        api_client,
        test_user,
        enrollment,
        video_progress_url,
    ):
        api_client.force_authenticate(user=test_user)

        enrollment.status = enrollment.Status.COMPLETED
        enrollment.save(update_fields=["status"])

        response = api_client.post(
            video_progress_url,
            {"timestamp": 60},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

    def test_requires_authentication(
        self,
        api_client,
        video_progress_url,
    ):
        response = api_client.post(
            video_progress_url,
            {"timestamp": 30},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_creates_watch_event_for_every_valid_update(
        self,
        api_client,
        test_user,
        video_progress,
        video_progress_url,
    ):
        api_client.force_authenticate(user=test_user)

        initial_count = VideoWatchEvent.objects.filter(
            video_progress=video_progress,
        ).count()

        first_response = api_client.post(
            video_progress_url,
            {"timestamp": 40},
            format="json",
        )
        second_response = api_client.post(
            video_progress_url,
            {"timestamp": 60},
            format="json",
        )

        assert first_response.status_code == status.HTTP_200_OK
        assert second_response.status_code == status.HTTP_200_OK

        assert (
            VideoWatchEvent.objects.filter(
                video_progress=video_progress,
            ).count()
            == initial_count + 2
        )

        assert VideoWatchEvent.objects.filter(
            video_progress=video_progress,
            watched_seconds=40,
        ).exists()

        assert VideoWatchEvent.objects.filter(
            video_progress=video_progress,
            watched_seconds=60,
        ).exists()

    def test_does_not_create_progress_for_invalid_timestamp(
        self,
        api_client,
        test_user,
        enrollment,
        video_content,
        video_progress_url,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            video_progress_url,
            {"timestamp": -5},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        assert not LessonContentProgress.objects.filter(
            enrollment=enrollment,
            content=video_content,
        ).exists()

        assert not VideoWatchEvent.objects.exists()

    def test_progress_belongs_to_requested_enrollment(
        self,
        api_client,
        test_user,
        enrollment,
        another_user_enrollment,
        video_content,
    ):
        api_client.force_authenticate(user=test_user)

        other_content_progress = LessonContentProgress.objects.create(
            enrollment=another_user_enrollment,
            content=video_content,
        )

        other_video_progress = VideoProgress.objects.create(
            lesson_content_progress=other_content_progress,
            watched_seconds=90,
        )

        url = reverse(
            "enrollment_api:enrollment_video_progress",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": video_content.lesson_id,
            },
        )

        response = api_client.post(
            url,
            {"timestamp": 30},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        other_video_progress.refresh_from_db()

        assert other_video_progress.watched_seconds == 90

        own_content_progress = LessonContentProgress.objects.get(
            enrollment=enrollment,
            content=video_content,
        )

        own_video_progress = VideoProgress.objects.get(
            lesson_content_progress=own_content_progress,
        )

        assert own_video_progress.watched_seconds == 30
