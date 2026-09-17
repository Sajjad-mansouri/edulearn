import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from courses.models.feedback import CourseFeedback
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
def another_course_review(another_student_enrollment):
    return CourseFeedback.objects.create(
        enrollment=another_student_enrollment,
        rating=4,
        comment="Useful course.",
    )


@pytest.fixture
def remove_review_url(course, course_review):
    return reverse(
        "courses_api:remove_review",
        kwargs={
            "course_id": course.id,
            "review_id": course_review.id,
        },
    )


class TestCourseReviewDestroyApiView:
    def test_student_can_delete_own_review(
        self,
        api_client,
        student_user,
        course_review,
        remove_review_url,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        review_id = course_review.id

        # Act
        response = api_client.delete(remove_review_url)

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT

        assert not CourseFeedback.objects.filter(
            pk=review_id,
        ).exists()

    def test_student_cannot_delete_another_users_review(
        self,
        api_client,
        student_user,
        another_course_review,
        course,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        url = reverse(
            "courses_api:remove_review",
            kwargs={
                "course_id": course.id,
                "review_id": another_course_review.id,
            },
        )

        review_id = another_course_review.id

        # Act
        response = api_client.delete(url)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

        assert CourseFeedback.objects.filter(
            pk=review_id,
        ).exists()

    def test_unauthenticated_user_cannot_delete_review(
        self,
        api_client,
        course,
        course_review,
    ):
        # Arrange
        url = reverse(
            "courses_api:remove_review",
            kwargs={
                "course_id": course.id,
                "review_id": course_review.id,
            },
        )

        # Act
        response = api_client.delete(url)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        assert CourseFeedback.objects.filter(
            pk=course_review.id,
        ).exists()

    def test_non_student_cannot_delete_review(
        self,
        api_client,
        another_user,
        course,
        course_review,
    ):
        # Arrange
        api_client.force_authenticate(user=another_user)

        url = reverse(
            "courses_api:remove_review",
            kwargs={
                "course_id": course.id,
                "review_id": course_review.id,
            },
        )

        # Act
        response = api_client.delete(url)

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

        assert CourseFeedback.objects.filter(
            pk=course_review.id,
        ).exists()

    def test_nonexistent_review_returns_404(
        self,
        api_client,
        student_user,
        course,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        url = reverse(
            "courses_api:remove_review",
            kwargs={
                "course_id": course.id,
                "review_id": 999999,
            },
        )

        # Act
        response = api_client.delete(url)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_review_cannot_be_deleted_twice(
        self,
        api_client,
        student_user,
        course_review,
        remove_review_url,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        # Act
        first_response = api_client.delete(remove_review_url)
        second_response = api_client.delete(remove_review_url)

        # Assert
        assert first_response.status_code == status.HTTP_204_NO_CONTENT
        assert second_response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize(
        "http_method",
        [
            "get",
            "post",
            "put",
            "patch",
        ],
    )
    def test_unsupported_http_methods_return_405(
        self,
        api_client,
        student_user,
        course,
        course_review,
        http_method,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        url = reverse(
            "courses_api:remove_review",
            kwargs={
                "course_id": course.id,
                "review_id": course_review.id,
            },
        )

        method = getattr(api_client, http_method)

        # Act
        response = method(url)

        # Assert
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
