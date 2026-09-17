import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from courses.models.wishlist import CourseWishlist

pytestmark = pytest.mark.django_db


class TestCourseWishlistToggleApiView:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def student_user(self, test_user):
        test_user.roles.create(name="student")
        return test_user

    @pytest.fixture
    def another_student(self, another_user):
        another_user.roles.create(name="student")
        return another_user

    @pytest.fixture
    def url(self, course):
        return reverse(
            "courses_api:course_wishlist_toggle",
            kwargs={"course_id": course.id},
        )

    def test_student_can_add_course_to_wishlist(
        self,
        api_client,
        student_user,
        course,
        url,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        # Act
        response = api_client.post(url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"is_wishlisted": True}

        assert CourseWishlist.objects.filter(
            user=student_user,
            course=course,
        ).exists()

    def test_student_can_remove_course_from_wishlist(
        self,
        api_client,
        student_user,
        course,
        url,
    ):
        # Arrange
        CourseWishlist.objects.create(
            user=student_user,
            course=course,
        )
        api_client.force_authenticate(user=student_user)

        # Act
        response = api_client.post(url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"is_wishlisted": False}

        assert not CourseWishlist.objects.filter(
            user=student_user,
            course=course,
        ).exists()

    def test_post_toggles_wishlist_state(
        self,
        api_client,
        student_user,
        course,
        url,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        # Act
        first_response = api_client.post(url)
        second_response = api_client.post(url)

        # Assert
        assert first_response.status_code == status.HTTP_200_OK
        assert first_response.data == {"is_wishlisted": True}

        assert second_response.status_code == status.HTTP_200_OK
        assert second_response.data == {"is_wishlisted": False}

        assert not CourseWishlist.objects.filter(
            user=student_user,
            course=course,
        ).exists()

    def test_wishlist_is_created_for_requesting_user(
        self,
        api_client,
        student_user,
        course,
        url,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        # Act
        response = api_client.post(url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        wishlist = CourseWishlist.objects.get(
            user=student_user,
            course=course,
        )

        assert wishlist.user == student_user
        assert wishlist.course == course

    def test_wishlist_state_is_independent_between_users(
        self,
        api_client,
        student_user,
        another_student,
        course,
        url,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        # Act
        first_response = api_client.post(url)

        api_client.force_authenticate(user=another_student)

        second_response = api_client.post(url)

        # Assert
        assert first_response.status_code == status.HTTP_200_OK
        assert first_response.data == {"is_wishlisted": True}

        assert second_response.status_code == status.HTTP_200_OK
        assert second_response.data == {"is_wishlisted": True}

        assert CourseWishlist.objects.filter(
            user=student_user,
            course=course,
        ).exists()

        assert CourseWishlist.objects.filter(
            user=another_student,
            course=course,
        ).exists()

        assert (
            CourseWishlist.objects.filter(
                course=course,
            ).count()
            == 2
        )

    def test_second_toggle_only_removes_requesting_users_wishlist(
        self,
        api_client,
        student_user,
        another_student,
        course,
        url,
    ):
        # Arrange
        CourseWishlist.objects.create(
            user=student_user,
            course=course,
        )
        CourseWishlist.objects.create(
            user=another_student,
            course=course,
        )

        api_client.force_authenticate(user=student_user)

        # Act
        response = api_client.post(url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"is_wishlisted": False}

        assert not CourseWishlist.objects.filter(
            user=student_user,
            course=course,
        ).exists()

        assert CourseWishlist.objects.filter(
            user=another_student,
            course=course,
        ).exists()

    def test_non_student_cannot_toggle_course_wishlist(
        self,
        api_client,
        another_user,
        course,
        url,
    ):
        # Arrange
        api_client.force_authenticate(user=another_user)

        # Act
        response = api_client.post(url)

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

        assert not CourseWishlist.objects.filter(
            user=another_user,
            course=course,
        ).exists()

    def test_nonexistent_course_returns_404(
        self,
        api_client,
        student_user,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        nonexistent_course_id = 999999

        url = reverse(
            "courses_api:course_wishlist_toggle",
            kwargs={"course_id": nonexistent_course_id},
        )

        # Act
        response = api_client.post(url)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_nonexistent_course_does_not_create_wishlist(
        self,
        api_client,
        student_user,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        nonexistent_course_id = 999999

        url = reverse(
            "courses_api:course_wishlist_toggle",
            kwargs={"course_id": nonexistent_course_id},
        )

        # Act
        response = api_client.post(url)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

        assert not CourseWishlist.objects.filter(
            user=student_user,
        ).exists()

    def test_unauthenticated_user_cannot_toggle_course_wishlist(
        self,
        api_client,
        course,
        url,
    ):
        # Arrange
        # No authentication is configured.

        # Act
        response = api_client.post(url)

        # Assert
        assert response.status_code in {
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        }

        assert not CourseWishlist.objects.filter(
            course=course,
        ).exists()

    @pytest.mark.parametrize(
        "method",
        [
            "get",
            "put",
            "patch",
            "delete",
        ],
    )
    def test_non_post_methods_are_not_allowed(
        self,
        api_client,
        student_user,
        url,
        method,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        # Act
        response = getattr(api_client, method)(url)

        # Assert
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
