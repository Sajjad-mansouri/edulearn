import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from courses.models.course import Course
from courses.models.feedback import (
    CourseFeedback,
    CourseFeedbackInteraction,
)
from enrollments.models import Enrollment


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def student_enrollment(course, student_user):
    return Enrollment.objects.create(
        user=student_user,
        course=course,
    )


@pytest.fixture
def another_student_enrollment(course, another_user):
    return Enrollment.objects.create(
        user=another_user,
        course=course,
    )


@pytest.fixture
def course_review(student_enrollment):
    return CourseFeedback.objects.create(
        enrollment=student_enrollment,
        rating=5,
        comment="Excellent course.",
    )


@pytest.fixture
def review_helpful_url(course, course_review):
    return reverse(
        "courses_api:review_helpful",
        kwargs={
            "course_id": course.id,
            "review_id": course_review.id,
        },
    )


class TestCourseReviewHelpfulApiView:
    def test_student_can_mark_review_as_helpful(
        self,
        api_client,
        student_user,
        course_review,
        review_helpful_url,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        # Act
        response = api_client.post(review_helpful_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            "helpful_count": 1,
            "user_has_liked": True,
        }

        assert CourseFeedbackInteraction.objects.filter(
            feedback=course_review,
            enrollment__user=student_user,
        ).exists()

    def test_student_can_remove_helpful_vote(
        self,
        api_client,
        student_user,
        student_enrollment,
        course_review,
        review_helpful_url,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        interaction = CourseFeedbackInteraction.objects.create(
            enrollment=student_enrollment,
            feedback=course_review,
        )

        # Act
        response = api_client.post(review_helpful_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            "helpful_count": 0,
            "user_has_liked": False,
        }

        assert not CourseFeedbackInteraction.objects.filter(
            pk=interaction.pk,
        ).exists()

    def test_student_can_toggle_helpful_vote(
        self,
        api_client,
        student_user,
        course_review,
        review_helpful_url,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        # Act
        first_response = api_client.post(review_helpful_url)
        second_response = api_client.post(review_helpful_url)
        third_response = api_client.post(review_helpful_url)

        # Assert
        assert first_response.status_code == status.HTTP_200_OK
        assert first_response.data == {
            "helpful_count": 1,
            "user_has_liked": True,
        }

        assert second_response.status_code == status.HTTP_200_OK
        assert second_response.data == {
            "helpful_count": 0,
            "user_has_liked": False,
        }

        assert third_response.status_code == status.HTTP_200_OK
        assert third_response.data == {
            "helpful_count": 1,
            "user_has_liked": True,
        }

        assert (
            CourseFeedbackInteraction.objects.filter(
                feedback=course_review,
                enrollment__user=student_user,
            ).count()
            == 1
        )

    def test_helpful_count_includes_other_users(
        self,
        api_client,
        student_user,
        another_student_enrollment,
        course_review,
        review_helpful_url,
    ):
        # Arrange
        CourseFeedbackInteraction.objects.create(
            enrollment=another_student_enrollment,
            feedback=course_review,
        )

        api_client.force_authenticate(user=student_user)

        # Act
        response = api_client.post(review_helpful_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            "helpful_count": 2,
            "user_has_liked": True,
        }

        assert (
            CourseFeedbackInteraction.objects.filter(
                feedback=course_review,
            ).count()
            == 2
        )

    def test_unliking_review_decreases_helpful_count(
        self,
        api_client,
        student_user,
        student_enrollment,
        another_student_enrollment,
        course_review,
        review_helpful_url,
    ):
        # Arrange
        CourseFeedbackInteraction.objects.create(
            enrollment=student_enrollment,
            feedback=course_review,
        )
        CourseFeedbackInteraction.objects.create(
            enrollment=another_student_enrollment,
            feedback=course_review,
        )

        api_client.force_authenticate(user=student_user)

        # Act
        response = api_client.post(review_helpful_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            "helpful_count": 1,
            "user_has_liked": False,
        }

        assert (
            CourseFeedbackInteraction.objects.filter(
                feedback=course_review,
            ).count()
            == 1
        )

    def test_response_reports_true_when_current_user_has_liked(
        self,
        api_client,
        student_user,
        student_enrollment,
        course_review,
        review_helpful_url,
    ):
        # Arrange
        CourseFeedbackInteraction.objects.create(
            enrollment=student_enrollment,
            feedback=course_review,
        )

        api_client.force_authenticate(user=student_user)

        # Act
        response = api_client.post(review_helpful_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["user_has_liked"] is False

    def test_response_reports_false_when_current_user_has_not_liked(
        self,
        api_client,
        student_user,
        course_review,
        review_helpful_url,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        # Act
        response = api_client.post(review_helpful_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["user_has_liked"] is True

    def test_student_must_be_enrolled_in_course(
        self,
        api_client,
        student_user,
        course_review,
        category,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        other_course = Course.objects.create(
            title="Another Course",
            owner=student_user,
            category=category,
        )

        url = reverse(
            "courses_api:review_helpful",
            kwargs={
                "course_id": other_course.id,
                "review_id": course_review.id,
            },
        )

        # Act
        response = api_client.post(url)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

        assert not CourseFeedbackInteraction.objects.filter(
            feedback=course_review,
        ).exists()

    def test_non_student_cannot_mark_review_as_helpful(
        self,
        api_client,
        another_user,
        review_helpful_url,
    ):
        # Arrange
        api_client.force_authenticate(user=another_user)

        # Act
        response = api_client.post(review_helpful_url)

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_user_cannot_mark_review_as_helpful(
        self,
        api_client,
        review_helpful_url,
    ):
        # Arrange
        # No authentication.

        # Act
        response = api_client.post(review_helpful_url)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_nonexistent_course_returns_404(
        self,
        api_client,
        student_user,
        course_review,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        url = reverse(
            "courses_api:review_helpful",
            kwargs={
                "course_id": 999999,
                "review_id": course_review.id,
            },
        )

        # Act
        response = api_client.post(url)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_nonexistent_review_returns_404(
        self,
        api_client,
        student_user,
        course,
        student_enrollment,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        url = reverse(
            "courses_api:review_helpful",
            kwargs={
                "course_id": course.id,
                "review_id": 999999,
            },
        )

        # Act
        response = api_client.post(url)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize(
        "http_method",
        [
            "get",
            "put",
            "patch",
            "delete",
        ],
    )
    def test_unsupported_http_methods_return_405(
        self,
        api_client,
        student_user,
        review_helpful_url,
        http_method,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        method = getattr(api_client, http_method)

        # Act
        response = method(review_helpful_url)

        # Assert
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
