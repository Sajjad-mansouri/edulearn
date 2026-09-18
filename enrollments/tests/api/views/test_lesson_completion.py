from datetime import timedelta

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from curriculums.models import Lesson, LessonContent, Section
from enrollments.api.views import LessonCompletion
from enrollments.models import Enrollment, LessonContentProgress, LessonProgress


@pytest.mark.django_db
class TestLessonCompletion:
    @pytest.fixture
    def factory(self):
        return APIRequestFactory()

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
    def lesson(self, section):
        return Lesson.objects.create(
            section=section,
            title="Introduction to Django",
            description="Learn Django fundamentals.",
            order=1,
            duration=timedelta(minutes=30),
            is_published=True,
            is_preview=False,
        )

    @pytest.fixture
    def lesson_content(self, lesson):
        return LessonContent.objects.create(
            lesson=lesson,
            content_type=LessonContent.Type.ARTICLE,
            order=1,
            is_main_content=True,
        )

    @pytest.fixture
    def second_lesson(self, section):
        return Lesson.objects.create(
            section=section,
            title="Django Models",
            description="Learn Django models.",
            order=2,
            duration=timedelta(minutes=30),
            is_published=True,
            is_preview=False,
        )

    @pytest.fixture
    def second_lesson_content(self, second_lesson):
        return LessonContent.objects.create(
            lesson=second_lesson,
            content_type=LessonContent.Type.ARTICLE,
            order=1,
            is_main_content=True,
        )

    def _url(self, enrollment, lesson):
        return reverse(
            "enrollment_api:complete_lesson",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lesson.id,
            },
        )

    def _get_response(
        self,
        factory,
        user,
        enrollment,
        lesson,
    ):
        request = factory.post(self._url(enrollment, lesson))
        force_authenticate(request, user=user)

        return LessonCompletion.as_view()(
            request,
            enrollment_id=enrollment.id,
            lesson_id=lesson.id,
        )

    def test_complete_lesson_returns_success_response(
        self,
        factory,
        test_user,
        enrollment,
        lesson,
        lesson_content,
    ):
        response = self._get_response(
            factory,
            test_user,
            enrollment,
            lesson,
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_complete_lesson_creates_content_progress(
        self,
        factory,
        test_user,
        enrollment,
        lesson,
        lesson_content,
    ):
        assert not LessonContentProgress.objects.filter(
            enrollment=enrollment,
            content=lesson_content,
        ).exists()

        response = self._get_response(
            factory,
            test_user,
            enrollment,
            lesson,
        )

        assert response.status_code == status.HTTP_200_OK

        progress = LessonContentProgress.objects.get(
            enrollment=enrollment,
            content=lesson_content,
        )

        assert progress.status == LessonContentProgress.Status.COMPLETED
        assert progress.started_at is not None
        assert progress.completed_at is not None

    def test_complete_lesson_marks_existing_content_progress_completed(
        self,
        factory,
        test_user,
        enrollment,
        lesson,
        lesson_content,
    ):
        content_progress = LessonContentProgress.objects.create(
            enrollment=enrollment,
            content=lesson_content,
            status=LessonContentProgress.Status.IN_PROGRESS,
        )

        response = self._get_response(
            factory,
            test_user,
            enrollment,
            lesson,
        )

        assert response.status_code == status.HTTP_200_OK

        content_progress.refresh_from_db()

        assert content_progress.status == LessonContentProgress.Status.COMPLETED
        assert content_progress.started_at is not None
        assert content_progress.completed_at is not None

        assert (
            LessonContentProgress.objects.filter(
                enrollment=enrollment,
                content=lesson_content,
            ).count()
            == 1
        )

    def test_complete_lesson_marks_lesson_progress_completed(
        self,
        factory,
        test_user,
        enrollment,
        lesson,
        lesson_content,
    ):
        response = self._get_response(
            factory,
            test_user,
            enrollment,
            lesson,
        )

        assert response.status_code == status.HTTP_200_OK

        lesson_progress = LessonProgress.objects.get(
            enrollment=enrollment,
            lesson=lesson,
        )

        assert lesson_progress.status == LessonProgress.Status.COMPLETED
        assert lesson_progress.completed_at is not None

    def test_complete_lesson_returns_completed_lesson(
        self,
        factory,
        test_user,
        enrollment,
        lesson,
        lesson_content,
    ):
        response = self._get_response(
            factory,
            test_user,
            enrollment,
            lesson,
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["completedLessons"] == [lesson.id]

    def test_complete_lesson_returns_correct_completed_count(
        self,
        factory,
        test_user,
        enrollment,
        lesson,
        lesson_content,
        second_lesson,
        second_lesson_content,
    ):
        response = self._get_response(
            factory,
            test_user,
            enrollment,
            lesson,
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["completedCount"] == 1

    def test_complete_lesson_returns_total_lesson_count(
        self,
        factory,
        test_user,
        enrollment,
        lesson,
        lesson_content,
        second_lesson,
        second_lesson_content,
    ):
        response = self._get_response(
            factory,
            test_user,
            enrollment,
            lesson,
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["totalLessons"] == 2

    def test_complete_lesson_does_not_count_incomplete_lessons(
        self,
        factory,
        test_user,
        enrollment,
        lesson,
        lesson_content,
        second_lesson,
        second_lesson_content,
    ):
        response = self._get_response(
            factory,
            test_user,
            enrollment,
            lesson,
        )

        assert response.status_code == status.HTTP_200_OK

        assert response.data["completedLessons"] == [lesson.id]
        assert response.data["completedCount"] == 1
        assert response.data["totalLessons"] == 2

    def test_complete_lesson_can_be_called_again_without_duplicate_progress(
        self,
        factory,
        test_user,
        enrollment,
        lesson,
        lesson_content,
    ):
        first_response = self._get_response(
            factory,
            test_user,
            enrollment,
            lesson,
        )

        second_response = self._get_response(
            factory,
            test_user,
            enrollment,
            lesson,
        )

        assert first_response.status_code == status.HTTP_200_OK
        assert second_response.status_code == status.HTTP_200_OK

        assert (
            LessonContentProgress.objects.filter(
                enrollment=enrollment,
                content=lesson_content,
            ).count()
            == 1
        )

        assert (
            LessonProgress.objects.filter(
                enrollment=enrollment,
                lesson=lesson,
            ).count()
            == 1
        )

        assert second_response.data["completedLessons"] == [lesson.id]
        assert second_response.data["completedCount"] == 1

    def test_complete_lesson_does_not_access_lesson_from_another_course(
        self,
        factory,
        test_user,
        enrollment,
        lesson,
        lesson_content,
        another_user,
        category,
    ):
        another_course = self._create_course(
            owner=another_user,
            category=category,
            title="Another Course",
        )

        another_section = Section.objects.create(
            course=another_course,
            title="Another Section",
            description="Another section",
            order=1,
            duration=timedelta(hours=1),
        )

        another_lesson = Lesson.objects.create(
            section=another_section,
            title="Another Lesson",
            description="Another lesson",
            order=1,
            duration=timedelta(minutes=30),
            is_published=True,
            is_preview=False,
        )

        another_content = LessonContent.objects.create(
            lesson=another_lesson,
            content_type=LessonContent.Type.ARTICLE,
            order=1,
            is_main_content=True,
        )

        response = self._get_response(
            factory,
            test_user,
            enrollment,
            another_lesson,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

        assert not LessonContentProgress.objects.filter(
            enrollment=enrollment,
            content=another_content,
        ).exists()

    def test_complete_lesson_rejects_user_without_enrollment(
        self,
        factory,
        another_user,
        course,
        lesson,
        lesson_content,
    ):
        enrollment = Enrollment.objects.create(
            user=another_user,
            course=course,
            status=Enrollment.Status.ACTIVE,
        )

        response = self._get_response(
            factory,
            another_user,
            enrollment,
            lesson,
        )

        assert response.status_code == status.HTTP_200_OK

    def test_complete_lesson_rejects_different_users_enrollment(
        self,
        factory,
        test_user,
        another_user,
        another_user_enrollment,
        lesson,
        lesson_content,
    ):
        response = self._get_response(
            factory,
            test_user,
            another_user_enrollment,
            lesson,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

        assert not LessonContentProgress.objects.filter(
            enrollment=another_user_enrollment,
            content=lesson_content,
        ).exists()

    @pytest.mark.parametrize(
        "enrollment_status",
        [
            Enrollment.Status.PENDING,
            Enrollment.Status.CANCELLED,
            Enrollment.Status.SUSPENDED,
        ],
    )
    def test_complete_lesson_rejects_non_active_enrollment(
        self,
        factory,
        test_user,
        course,
        lesson,
        lesson_content,
        enrollment_status,
    ):
        enrollment = Enrollment.objects.create(
            user=test_user,
            course=course,
            status=enrollment_status,
        )

        response = self._get_response(
            factory,
            test_user,
            enrollment,
            lesson,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

        assert not LessonContentProgress.objects.filter(
            enrollment=enrollment,
            content=lesson_content,
        ).exists()

    def test_complete_lesson_allows_completed_enrollment(
        self,
        factory,
        test_user,
        course,
        lesson,
        lesson_content,
    ):
        enrollment = Enrollment.objects.create(
            user=test_user,
            course=course,
            status=Enrollment.Status.COMPLETED,
        )

        response = self._get_response(
            factory,
            test_user,
            enrollment,
            lesson,
        )

        assert response.status_code == status.HTTP_200_OK

        progress = LessonContentProgress.objects.get(
            enrollment=enrollment,
            content=lesson_content,
        )

        assert progress.status == LessonContentProgress.Status.COMPLETED

    def test_complete_lesson_rejects_unauthenticated_user(
        self,
        factory,
        enrollment,
        lesson,
    ):
        request = factory.post(self._url(enrollment, lesson))

        response = LessonCompletion.as_view()(
            request,
            enrollment_id=enrollment.id,
            lesson_id=lesson.id,
        )

        assert response.status_code in {
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        }

    def _create_course(self, owner, category, title):
        from courses.models.course import Course

        return Course.objects.create(
            title=title,
            owner=owner,
            category=category,
        )
