from datetime import timedelta

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from curriculums.models import Lesson, Section
from enrollments.models import Enrollment, LessonProgress


@pytest.mark.django_db
class TestEnrollmentProgress:
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
    def progress_url(self, enrollment):
        return reverse(
            "enrollment_api:enrollment_progress",
            kwargs={"enrollment_id": enrollment.id},
        )

    def test_get_enrollment_progress_returns_expected_response(
        self,
        api_client,
        test_user,
        enrollment,
        lessons,
        progress_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        # Act
        response = api_client.get(progress_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["enrollmentId"] == enrollment.id
        assert response.data["overallProgress"] == float(enrollment.progress)
        assert response.data["completedLessons"] == []
        assert response.data["completedCount"] == 0
        assert response.data["totalLessons"] == len(lessons)
        assert response.data["bookmarkedLessons"] == []

    def test_get_enrollment_progress_returns_completed_lessons(
        self,
        api_client,
        test_user,
        enrollment,
        lessons,
        progress_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=lessons[0],
            status=LessonProgress.Status.COMPLETED,
        )

        # Act
        response = api_client.get(progress_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["completedLessons"] == [lessons[0].id]
        assert response.data["completedCount"] == 1

    def test_get_enrollment_progress_does_not_count_incomplete_lessons(
        self,
        api_client,
        test_user,
        enrollment,
        lessons,
        progress_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=lessons[0],
            status=LessonProgress.Status.IN_PROGRESS,
        )

        # Act
        response = api_client.get(progress_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["completedLessons"] == []
        assert response.data["completedCount"] == 0

    def test_get_enrollment_progress_does_not_count_not_started_lessons(
        self,
        api_client,
        test_user,
        enrollment,
        lessons,
        progress_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=lessons[0],
            status=LessonProgress.Status.NOT_STARTED,
        )

        # Act
        response = api_client.get(progress_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["completedLessons"] == []
        assert response.data["completedCount"] == 0

    def test_get_enrollment_progress_returns_multiple_completed_lessons(
        self,
        api_client,
        test_user,
        enrollment,
        lessons,
        progress_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=lessons[0],
            status=LessonProgress.Status.COMPLETED,
        )
        LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=lessons[2],
            status=LessonProgress.Status.COMPLETED,
        )

        # Act
        response = api_client.get(progress_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert set(response.data["completedLessons"]) == {
            lessons[0].id,
            lessons[2].id,
        }
        assert response.data["completedCount"] == 2

    def test_get_enrollment_progress_returns_zero_progress_for_new_enrollment(
        self,
        api_client,
        test_user,
        enrollment,
        lessons,
        progress_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        # Act
        response = api_client.get(progress_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["overallProgress"] == float(enrollment.progress)
        assert response.data["completedLessons"] == []
        assert response.data["completedCount"] == 0
        assert response.data["totalLessons"] == len(lessons)
        assert response.data["bookmarkedLessons"] == []

    def test_get_enrollment_progress_returns_bookmarked_lessons(
        self,
        api_client,
        test_user,
        enrollment,
        lessons,
        progress_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        lessons[0].bookmarks.create(enrollment=enrollment)
        lessons[2].bookmarks.create(enrollment=enrollment)

        # Act
        response = api_client.get(progress_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert set(response.data["bookmarkedLessons"]) == {
            lessons[0].id,
            lessons[2].id,
        }

    def test_get_enrollment_progress_does_not_return_bookmarks_from_another_enrollment(
        self,
        api_client,
        test_user,
        enrollment,
        another_user_enrollment,
        lessons,
        progress_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        lessons[0].bookmarks.create(
            enrollment=another_user_enrollment,
        )

        # Act
        response = api_client.get(progress_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["bookmarkedLessons"] == []

    def test_get_enrollment_progress_does_not_return_completed_lessons_from_another_enrollment(
        self,
        api_client,
        test_user,
        enrollment,
        another_user_enrollment,
        lessons,
        progress_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        LessonProgress.objects.create(
            enrollment=another_user_enrollment,
            lesson=lessons[0],
            status=LessonProgress.Status.COMPLETED,
        )

        # Act
        response = api_client.get(progress_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["completedLessons"] == []
        assert response.data["completedCount"] == 0

    def test_get_enrollment_progress_does_not_include_lessons_from_another_course(
        self,
        api_client,
        test_user,
        enrollment,
        lessons,
        category,
        progress_url,
    ):
        # Arrange
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

        LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=another_lesson,
            status=LessonProgress.Status.COMPLETED,
        )

        # Act
        response = api_client.get(progress_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert another_lesson.id not in response.data["completedLessons"]
        assert response.data["completedCount"] == 0
        assert response.data["totalLessons"] == len(lessons)

    def test_get_enrollment_progress_rejects_another_users_enrollment(
        self,
        api_client,
        test_user,
        another_user_enrollment,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        url = reverse(
            "enrollment_api:enrollment_progress",
            kwargs={"enrollment_id": another_user_enrollment.id},
        )

        # Act
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize(
        "enrollment_status",
        [
            Enrollment.Status.CANCELLED,
            Enrollment.Status.SUSPENDED,
            Enrollment.Status.PENDING,
        ],
    )
    def test_get_enrollment_progress_rejects_inactive_enrollment_statuses(
        self,
        api_client,
        test_user,
        enrollment,
        enrollment_status,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        enrollment.status = enrollment_status
        enrollment.save(update_fields=["status"])

        url = reverse(
            "enrollment_api:enrollment_progress",
            kwargs={"enrollment_id": enrollment.id},
        )

        # Act
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_enrollment_progress_allows_completed_enrollment(
        self,
        api_client,
        test_user,
        enrollment,
        lessons,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        enrollment.status = Enrollment.Status.COMPLETED
        enrollment.save(update_fields=["status"])

        url = reverse(
            "enrollment_api:enrollment_progress",
            kwargs={"enrollment_id": enrollment.id},
        )

        # Act
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["enrollmentId"] == enrollment.id
        assert response.data["totalLessons"] == len(lessons)

    def test_get_enrollment_progress_requires_authentication(
        self,
        api_client,
        enrollment,
    ):
        # Arrange
        url = reverse(
            "enrollment_api:enrollment_progress",
            kwargs={"enrollment_id": enrollment.id},
        )

        # Act
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_enrollment_progress_rejects_nonexistent_enrollment(
        self,
        api_client,
        test_user,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        url = reverse(
            "enrollment_api:enrollment_progress",
            kwargs={"enrollment_id": 999999},
        )

        # Act
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_enrollment_progress_counts_lessons_across_all_sections(
        self,
        api_client,
        test_user,
        enrollment,
        lessons,
        progress_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        second_section = Section.objects.create(
            course=enrollment.course,
            title="Advanced Django",
            description="Advanced Django topics.",
            order=2,
            duration=timedelta(hours=1),
        )

        additional_lessons = [
            Lesson.objects.create(
                section=second_section,
                title="Django Signals",
                description="Learn Django signals.",
                order=1,
                duration=timedelta(minutes=30),
                is_published=True,
                is_preview=False,
            ),
            Lesson.objects.create(
                section=second_section,
                title="Django Caching",
                description="Learn Django caching.",
                order=2,
                duration=timedelta(minutes=30),
                is_published=True,
                is_preview=False,
            ),
        ]

        # Act
        response = api_client.get(progress_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["totalLessons"] == (len(lessons) + len(additional_lessons))

    def test_get_enrollment_progress_completed_lessons_are_scoped_to_enrollment(
        self,
        api_client,
        test_user,
        enrollment,
        another_user_enrollment,
        lessons,
        progress_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=lessons[0],
            status=LessonProgress.Status.COMPLETED,
        )

        LessonProgress.objects.create(
            enrollment=another_user_enrollment,
            lesson=lessons[1],
            status=LessonProgress.Status.COMPLETED,
        )

        # Act
        response = api_client.get(progress_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["completedLessons"] == [lessons[0].id]
        assert response.data["completedCount"] == 1

    def test_get_enrollment_progress_returns_only_completed_lessons(
        self,
        api_client,
        test_user,
        enrollment,
        lessons,
        progress_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=lessons[0],
            status=LessonProgress.Status.COMPLETED,
        )

        LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=lessons[1],
            status=LessonProgress.Status.IN_PROGRESS,
        )

        LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=lessons[2],
            status=LessonProgress.Status.NOT_STARTED,
        )

        # Act
        response = api_client.get(progress_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["completedLessons"] == [lessons[0].id]
        assert response.data["completedCount"] == 1

    def test_get_enrollment_progress_bookmarked_lessons_are_scoped_to_enrollment(
        self,
        api_client,
        test_user,
        enrollment,
        another_user_enrollment,
        lessons,
        progress_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        lessons[0].bookmarks.create(
            enrollment=enrollment,
        )

        lessons[1].bookmarks.create(
            enrollment=another_user_enrollment,
        )

        # Act
        response = api_client.get(progress_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["bookmarkedLessons"] == [lessons[0].id]
