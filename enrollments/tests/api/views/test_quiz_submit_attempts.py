from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from assessments.models import QuizAttempt, QuizContent
from curriculums.models import Lesson, LessonContent, Section
from enrollments.models import Enrollment


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def section(course):
    return Section.objects.create(
        course=course,
        title="Python Basics",
        order=1,
    )


@pytest.fixture
def lesson(section):
    return Lesson.objects.create(
        section=section,
        title="Introduction to Python",
        slug="introduction-to-python",
        order=1,
    )


@pytest.fixture
def quiz_lesson_content(lesson):
    return LessonContent.objects.create(
        lesson=lesson,
        title="Python Quiz",
        content_type=LessonContent.Type.QUIZ,
        order=1,
        is_main_content=True,
    )


@pytest.fixture
def quiz_content(quiz_lesson_content):
    return QuizContent.objects.create(
        content=quiz_lesson_content,
        passing_score=70,
        max_attempts=3,
        show_correct_answers=True,
    )


@pytest.fixture
def quiz_submit_attempts_url(enrollment, lesson):
    return reverse(
        "enrollment_api:quiz_submit_attempts",
        kwargs={
            "enrollment_id": enrollment.id,
            "lesson_id": lesson.id,
        },
    )


@pytest.mark.django_db
class TestQuizSubmitAttemptsApiView:
    def test_requires_authentication(
        self,
        api_client,
        quiz_submit_attempts_url,
        quiz_content,
    ):
        response = api_client.get(quiz_submit_attempts_url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_returns_zero_attempts_when_no_attempt_exists(
        self,
        api_client,
        test_user,
        enrollment,
        quiz_content,
        quiz_submit_attempts_url,
        lesson,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.get(quiz_submit_attempts_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            "success": True,
            "lessonId": lesson.id,
            "attempts_used": 0,
            "max_attempts": 3,
            "attempts_remaining": 3,
            "best_score": None,
            "last_score": None,
            "can_attempt": True,
        }

        assert not QuizAttempt.objects.filter(
            enrollment=enrollment,
            quiz=quiz_content,
        ).exists()

    def test_returns_attempt_statistics(
        self,
        api_client,
        test_user,
        enrollment,
        quiz_content,
        quiz_submit_attempts_url,
        lesson,
    ):
        api_client.force_authenticate(user=test_user)

        QuizAttempt.objects.create(
            enrollment=enrollment,
            quiz=quiz_content,
            attempt_number=1,
            score=Decimal("60.00"),
        )
        QuizAttempt.objects.create(
            enrollment=enrollment,
            quiz=quiz_content,
            attempt_number=2,
            score=Decimal("80.00"),
        )

        response = api_client.get(quiz_submit_attempts_url)

        assert response.status_code == status.HTTP_200_OK

        assert response.data["success"] is True
        assert response.data["lessonId"] == lesson.id
        assert response.data["attempts_used"] == 2
        assert response.data["max_attempts"] == 3
        assert response.data["attempts_remaining"] == 1
        assert response.data["best_score"] == Decimal("80.00")
        assert response.data["last_score"] == Decimal("80.00")
        assert response.data["can_attempt"] is True

    def test_best_score_is_highest_score_not_last_score(
        self,
        api_client,
        test_user,
        enrollment,
        quiz_content,
        quiz_submit_attempts_url,
    ):
        api_client.force_authenticate(user=test_user)

        QuizAttempt.objects.create(
            enrollment=enrollment,
            quiz=quiz_content,
            attempt_number=1,
            score=Decimal("90.00"),
        )
        QuizAttempt.objects.create(
            enrollment=enrollment,
            quiz=quiz_content,
            attempt_number=2,
            score=Decimal("70.00"),
        )

        response = api_client.get(quiz_submit_attempts_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["best_score"] == Decimal("90.00")
        assert response.data["last_score"] == Decimal("70.00")

    def test_last_score_comes_from_highest_attempt_number(
        self,
        api_client,
        test_user,
        enrollment,
        quiz_content,
        quiz_submit_attempts_url,
    ):
        api_client.force_authenticate(user=test_user)

        QuizAttempt.objects.create(
            enrollment=enrollment,
            quiz=quiz_content,
            attempt_number=1,
            score=Decimal("95.00"),
        )
        QuizAttempt.objects.create(
            enrollment=enrollment,
            quiz=quiz_content,
            attempt_number=2,
            score=Decimal("55.00"),
        )
        QuizAttempt.objects.create(
            enrollment=enrollment,
            quiz=quiz_content,
            attempt_number=3,
            score=Decimal("75.00"),
        )

        response = api_client.get(quiz_submit_attempts_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["attempts_used"] == 3
        assert response.data["last_score"] == Decimal("75.00")
        assert response.data["best_score"] == Decimal("95.00")

    def test_cannot_attempt_when_max_attempts_reached(
        self,
        api_client,
        test_user,
        enrollment,
        quiz_content,
        quiz_submit_attempts_url,
    ):
        api_client.force_authenticate(user=test_user)

        for attempt_number in range(1, 4):
            QuizAttempt.objects.create(
                enrollment=enrollment,
                quiz=quiz_content,
                attempt_number=attempt_number,
                score=Decimal("70.00"),
            )

        response = api_client.get(quiz_submit_attempts_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["attempts_used"] == 3
        assert response.data["max_attempts"] == 3
        assert response.data["attempts_remaining"] == 0
        assert response.data["can_attempt"] is False

    def test_attempts_remaining_never_becomes_negative(
        self,
        api_client,
        test_user,
        enrollment,
        quiz_content,
        quiz_submit_attempts_url,
    ):
        api_client.force_authenticate(user=test_user)

        # This can occur if attempts were created outside the normal
        # QuizSubmitApiView flow or data was imported.
        for attempt_number in range(1, 5):
            QuizAttempt.objects.create(
                enrollment=enrollment,
                quiz=quiz_content,
                attempt_number=attempt_number,
                score=Decimal("50.00"),
            )

        response = api_client.get(quiz_submit_attempts_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["attempts_used"] == 4
        assert response.data["attempts_remaining"] == 0
        assert response.data["can_attempt"] is False

    def test_unlimited_attempts_allow_new_attempts(
        self,
        api_client,
        test_user,
        enrollment,
        quiz_content,
        quiz_submit_attempts_url,
    ):
        api_client.force_authenticate(user=test_user)

        quiz_content.max_attempts = 0
        quiz_content.save(update_fields=["max_attempts"])

        QuizAttempt.objects.create(
            enrollment=enrollment,
            quiz=quiz_content,
            attempt_number=1,
            score=Decimal("80.00"),
        )
        QuizAttempt.objects.create(
            enrollment=enrollment,
            quiz=quiz_content,
            attempt_number=2,
            score=Decimal("90.00"),
        )

        response = api_client.get(quiz_submit_attempts_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["attempts_used"] == 2
        assert response.data["max_attempts"] == 0
        assert response.data["can_attempt"] is True

        # Intended API contract should not expose float("inf").
        assert response.data["attempts_remaining"] is None

    def test_does_not_include_attempts_from_another_quiz(
        self,
        api_client,
        test_user,
        enrollment,
        quiz_content,
        quiz_submit_attempts_url,
        lesson,
        section,
    ):
        api_client.force_authenticate(user=test_user)

        other_lesson = Lesson.objects.create(
            section=section,
            title="Other Lesson",
            slug="other-lesson",
            order=2,
        )

        other_content = LessonContent.objects.create(
            lesson=other_lesson,
            title="Other Quiz",
            content_type=LessonContent.Type.QUIZ,
            order=1,
            is_main_content=True,
        )

        other_quiz = QuizContent.objects.create(
            content=other_content,
            passing_score=70,
            max_attempts=5,
        )

        QuizAttempt.objects.create(
            enrollment=enrollment,
            quiz=quiz_content,
            attempt_number=1,
            score=Decimal("60.00"),
        )

        QuizAttempt.objects.create(
            enrollment=enrollment,
            quiz=other_quiz,
            attempt_number=1,
            score=Decimal("100.00"),
        )

        response = api_client.get(quiz_submit_attempts_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["attempts_used"] == 1
        assert response.data["best_score"] == Decimal("60.00")
        assert response.data["last_score"] == Decimal("60.00")

    def test_does_not_include_attempts_from_another_enrollment(
        self,
        api_client,
        test_user,
        another_user_enrollment,
        quiz_content,
        quiz_submit_attempts_url,
    ):
        api_client.force_authenticate(user=test_user)

        QuizAttempt.objects.create(
            enrollment=another_user_enrollment,
            quiz=quiz_content,
            attempt_number=1,
            score=Decimal("100.00"),
        )

        response = api_client.get(quiz_submit_attempts_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["attempts_used"] == 0
        assert response.data["best_score"] is None
        assert response.data["last_score"] is None
        assert response.data["can_attempt"] is True

    def test_rejects_another_users_enrollment(
        self,
        api_client,
        test_user,
        another_user_enrollment,
        quiz_content,
        lesson,
    ):
        api_client.force_authenticate(user=test_user)

        url = reverse(
            "enrollment_api:quiz_submit_attempts",
            kwargs={
                "enrollment_id": another_user_enrollment.id,
                "lesson_id": lesson.id,
            },
        )

        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize(
        "status_value",
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
        quiz_content,
        quiz_submit_attempts_url,
        status_value,
    ):
        api_client.force_authenticate(user=test_user)

        enrollment.status = status_value
        enrollment.save(update_fields=["status"])

        response = api_client.get(quiz_submit_attempts_url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_allows_completed_enrollment(
        self,
        api_client,
        test_user,
        enrollment,
        quiz_content,
        quiz_submit_attempts_url,
    ):
        api_client.force_authenticate(user=test_user)

        enrollment.status = Enrollment.Status.COMPLETED
        enrollment.save(update_fields=["status"])

        QuizAttempt.objects.create(
            enrollment=enrollment,
            quiz=quiz_content,
            attempt_number=1,
            score=Decimal("85.00"),
        )

        response = api_client.get(quiz_submit_attempts_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["attempts_used"] == 1
        assert response.data["best_score"] == Decimal("85.00")
        assert response.data["last_score"] == Decimal("85.00")
        assert response.data["can_attempt"] is True

    def test_returns_404_for_nonexistent_lesson(
        self,
        api_client,
        test_user,
        enrollment,
    ):
        api_client.force_authenticate(user=test_user)

        url = reverse(
            "enrollment_api:quiz_submit_attempts",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": 999999,
            },
        )

        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_returns_404_for_lesson_from_another_course(
        self,
        api_client,
        test_user,
        enrollment,
        category,
    ):
        from courses.models import Course

        other_course = Course.objects.create(
            title="Other Course",
            owner=test_user,
            category=category,
        )

        other_section = Section.objects.create(
            course=other_course,
            title="Other Section",
            order=1,
        )

        other_lesson = Lesson.objects.create(
            section=other_section,
            title="Other Lesson",
            slug="other-lesson",
            order=1,
        )

        api_client.force_authenticate(user=test_user)

        url = reverse(
            "enrollment_api:quiz_submit_attempts",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": other_lesson.id,
            },
        )

        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_returns_404_for_lesson_without_quiz(
        self,
        api_client,
        test_user,
        enrollment,
        section,
    ):
        lesson = Lesson.objects.create(
            section=section,
            title="Article Lesson",
            slug="article-lesson",
            order=2,
        )

        api_client.force_authenticate(user=test_user)

        url = reverse(
            "enrollment_api:quiz_submit_attempts",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lesson.id,
            },
        )

        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
