from datetime import timedelta

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from curriculums.models import Lesson, Section
from enrollments.models import CourseLessonBookmark, Enrollment


@pytest.mark.django_db
class TestLessonBookmarkApiView:
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
            Lesson.objects.create(
                section=section,
                title="Django Views",
                description="Learn Django views.",
                order=3,
                duration=timedelta(minutes=30),
                is_published=True,
                is_preview=False,
            ),
        ]

    @pytest.fixture
    def bookmark_url(self, enrollment, lessons):
        return reverse(
            "enrollment_api:toggle_lesson_bookmark",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lessons[0].id,
            },
        )

    def test_bookmarks_lesson(
        self,
        api_client,
        test_user,
        enrollment,
        lessons,
        bookmark_url,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.post(bookmark_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            "success": True,
            "bookmarked": True,
            "bookmarkedLessons": [lessons[0].id],
            "message": "Lesson bookmarked",
        }

        assert CourseLessonBookmark.objects.filter(
            enrollment=enrollment,
            lesson=lessons[0],
        ).exists()

    def test_removes_existing_bookmark(
        self,
        api_client,
        test_user,
        enrollment,
        lessons,
        bookmark_url,
    ):
        api_client.force_authenticate(user=test_user)

        bookmark = CourseLessonBookmark.objects.create(
            enrollment=enrollment,
            lesson=lessons[0],
        )

        response = api_client.post(bookmark_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            "success": True,
            "bookmarked": False,
            "bookmarkedLessons": [],
            "message": "Bookmark removed",
        }

        assert not CourseLessonBookmark.objects.filter(
            pk=bookmark.pk,
        ).exists()

    def test_toggling_twice_bookmarks_then_removes(
        self,
        api_client,
        test_user,
        enrollment,
        lessons,
        bookmark_url,
    ):
        api_client.force_authenticate(user=test_user)

        first_response = api_client.post(bookmark_url)
        second_response = api_client.post(bookmark_url)

        assert first_response.status_code == status.HTTP_200_OK
        assert second_response.status_code == status.HTTP_200_OK

        assert first_response.data["success"] is True
        assert first_response.data["bookmarked"] is True
        assert first_response.data["message"] == "Lesson bookmarked"

        assert second_response.data["success"] is True
        assert second_response.data["bookmarked"] is False
        assert second_response.data["message"] == "Bookmark removed"

        assert not CourseLessonBookmark.objects.filter(
            enrollment=enrollment,
            lesson=lessons[0],
        ).exists()

    def test_returns_all_bookmarked_lessons_for_enrollment(
        self,
        api_client,
        test_user,
        enrollment,
        lessons,
    ):
        api_client.force_authenticate(user=test_user)

        CourseLessonBookmark.objects.create(
            enrollment=enrollment,
            lesson=lessons[1],
        )
        CourseLessonBookmark.objects.create(
            enrollment=enrollment,
            lesson=lessons[2],
        )

        url = reverse(
            "enrollment_api:toggle_lesson_bookmark",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lessons[0].id,
            },
        )

        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["bookmarked"] is True
        assert set(response.data["bookmarkedLessons"]) == {
            lessons[0].id,
            lessons[1].id,
            lessons[2].id,
        }

    def test_does_not_return_bookmarks_from_another_enrollment(
        self,
        api_client,
        test_user,
        enrollment,
        another_user_enrollment,
        lessons,
        bookmark_url,
    ):
        api_client.force_authenticate(user=test_user)

        CourseLessonBookmark.objects.create(
            enrollment=another_user_enrollment,
            lesson=lessons[0],
        )

        response = api_client.post(bookmark_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["bookmarked"] is True
        assert response.data["bookmarkedLessons"] == [lessons[0].id]

        assert CourseLessonBookmark.objects.filter(
            enrollment=another_user_enrollment,
            lesson=lessons[0],
        ).exists()

    def test_does_not_remove_another_enrollments_bookmark(
        self,
        api_client,
        test_user,
        enrollment,
        another_user_enrollment,
        lessons,
        bookmark_url,
    ):
        api_client.force_authenticate(user=test_user)

        other_bookmark = CourseLessonBookmark.objects.create(
            enrollment=another_user_enrollment,
            lesson=lessons[0],
        )

        response = api_client.post(bookmark_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["bookmarked"] is True

        assert CourseLessonBookmark.objects.filter(
            pk=other_bookmark.pk,
        ).exists()

        assert CourseLessonBookmark.objects.filter(
            enrollment=enrollment,
            lesson=lessons[0],
        ).exists()

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

        url = reverse(
            "enrollment_api:toggle_lesson_bookmark",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": another_lesson.id,
            },
        )

        response = api_client.post(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

        assert not CourseLessonBookmark.objects.filter(
            enrollment=enrollment,
            lesson=another_lesson,
        ).exists()

    def test_rejects_nonexistent_lesson(
        self,
        api_client,
        test_user,
        enrollment,
    ):
        api_client.force_authenticate(user=test_user)

        url = reverse(
            "enrollment_api:toggle_lesson_bookmark",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": 999999,
            },
        )

        response = api_client.post(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_rejects_another_users_enrollment(
        self,
        api_client,
        test_user,
        another_user_enrollment,
        lessons,
    ):
        api_client.force_authenticate(user=test_user)

        url = reverse(
            "enrollment_api:toggle_lesson_bookmark",
            kwargs={
                "enrollment_id": another_user_enrollment.id,
                "lesson_id": lessons[0].id,
            },
        )

        response = api_client.post(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize(
        "enrollment_status",
        [
            Enrollment.Status.CANCELLED,
            Enrollment.Status.SUSPENDED,
            Enrollment.Status.PENDING,
        ],
    )
    def test_rejects_inactive_enrollment(
        self,
        api_client,
        test_user,
        enrollment,
        lessons,
        enrollment_status,
    ):
        api_client.force_authenticate(user=test_user)

        enrollment.status = enrollment_status
        enrollment.save(update_fields=["status"])

        url = reverse(
            "enrollment_api:toggle_lesson_bookmark",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lessons[0].id,
            },
        )

        response = api_client.post(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

        assert not CourseLessonBookmark.objects.filter(
            enrollment=enrollment,
            lesson=lessons[0],
        ).exists()

    def test_allows_completed_enrollment(
        self,
        api_client,
        test_user,
        enrollment,
        lessons,
    ):
        api_client.force_authenticate(user=test_user)

        enrollment.status = Enrollment.Status.COMPLETED
        enrollment.save(update_fields=["status"])

        url = reverse(
            "enrollment_api:toggle_lesson_bookmark",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lessons[0].id,
            },
        )

        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["bookmarked"] is True

        assert CourseLessonBookmark.objects.filter(
            enrollment=enrollment,
            lesson=lessons[0],
        ).exists()

    def test_requires_authentication(
        self,
        api_client,
        bookmark_url,
    ):
        response = api_client.post(bookmark_url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_returns_only_remaining_bookmarks_after_removing_one(
        self,
        api_client,
        test_user,
        enrollment,
        lessons,
    ):
        api_client.force_authenticate(user=test_user)

        CourseLessonBookmark.objects.create(
            enrollment=enrollment,
            lesson=lessons[0],
        )
        CourseLessonBookmark.objects.create(
            enrollment=enrollment,
            lesson=lessons[1],
        )
        CourseLessonBookmark.objects.create(
            enrollment=enrollment,
            lesson=lessons[2],
        )

        url = reverse(
            "enrollment_api:toggle_lesson_bookmark",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lessons[1].id,
            },
        )

        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["bookmarked"] is False
        assert set(response.data["bookmarkedLessons"]) == {
            lessons[0].id,
            lessons[2].id,
        }

        assert not CourseLessonBookmark.objects.filter(
            enrollment=enrollment,
            lesson=lessons[1],
        ).exists()

    def test_bookmark_is_created_for_correct_enrollment(
        self,
        api_client,
        test_user,
        enrollment,
        another_user_enrollment,
        lessons,
    ):
        api_client.force_authenticate(user=test_user)

        url = reverse(
            "enrollment_api:toggle_lesson_bookmark",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lessons[0].id,
            },
        )

        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK

        assert CourseLessonBookmark.objects.filter(
            enrollment=enrollment,
            lesson=lessons[0],
        ).exists()

        assert not CourseLessonBookmark.objects.filter(
            enrollment=another_user_enrollment,
            lesson=lessons[0],
        ).exists()
