import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from courses.models.wishlist import CourseWishlist

pytestmark = pytest.mark.django_db


class TestCourseWishlistRemoveApiView:
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
    def wishlist(self, student_user, course):
        return CourseWishlist.objects.create(
            user=student_user,
            course=course,
        )

    @pytest.fixture
    def url(self, wishlist):
        return reverse(
            "courses_api:course_wishlist_remove",
            kwargs={"pk": wishlist.pk},
        )

    def test_student_can_remove_own_wishlist(
        self,
        api_client,
        student_user,
        wishlist,
        url,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        # Act
        response = api_client.delete(url)

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT

        assert not CourseWishlist.objects.filter(
            pk=wishlist.pk,
        ).exists()

    def test_remove_returns_204_with_empty_response_body(
        self,
        api_client,
        student_user,
        wishlist,
        url,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        # Act
        response = api_client.delete(url)

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.data is None

    def test_student_cannot_remove_another_students_wishlist(
        self,
        api_client,
        student_user,
        another_student,
        course,
    ):
        # Arrange
        wishlist = CourseWishlist.objects.create(
            user=another_student,
            course=course,
        )

        url = reverse(
            "courses_api:course_wishlist_remove",
            kwargs={"pk": wishlist.pk},
        )

        api_client.force_authenticate(user=student_user)

        # Act
        response = api_client.delete(url)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

        assert CourseWishlist.objects.filter(
            pk=wishlist.pk,
        ).exists()

        assert CourseWishlist.objects.filter(
            pk=wishlist.pk,
            user=another_student,
        ).exists()

    def test_student_cannot_remove_nonexistent_wishlist(
        self,
        api_client,
        student_user,
    ):
        # Arrange
        nonexistent_wishlist_id = 999999

        url = reverse(
            "courses_api:course_wishlist_remove",
            kwargs={"pk": nonexistent_wishlist_id},
        )

        api_client.force_authenticate(user=student_user)

        # Act
        response = api_client.delete(url)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_non_student_cannot_remove_wishlist(
        self,
        api_client,
        another_user,
        student_user,
        course,
    ):
        # Arrange
        wishlist = CourseWishlist.objects.create(
            user=student_user,
            course=course,
        )

        url = reverse(
            "courses_api:course_wishlist_remove",
            kwargs={"pk": wishlist.pk},
        )

        api_client.force_authenticate(user=another_user)

        # Act
        response = api_client.delete(url)

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

        assert CourseWishlist.objects.filter(
            pk=wishlist.pk,
        ).exists()

    def test_unauthenticated_user_cannot_remove_wishlist(
        self,
        api_client,
        wishlist,
        url,
    ):
        # Arrange
        # No authentication is configured.

        # Act
        response = api_client.delete(url)

        # Assert
        assert response.status_code in {
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        }

        assert CourseWishlist.objects.filter(
            pk=wishlist.pk,
        ).exists()

    @pytest.mark.parametrize(
        "method",
        [
            "get",
            "post",
            "put",
            "patch",
        ],
    )
    def test_non_delete_methods_are_not_allowed(
        self,
        api_client,
        student_user,
        wishlist,
        url,
        method,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        # Act
        response = getattr(api_client, method)(url)

        # Assert
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        assert CourseWishlist.objects.filter(
            pk=wishlist.pk,
        ).exists()

    def test_removing_one_wishlist_does_not_remove_other_wishlists(
        self,
        api_client,
        student_user,
        another_student,
        course,
    ):
        # Arrange
        first_wishlist = CourseWishlist.objects.create(
            user=student_user,
            course=course,
        )
        second_wishlist = CourseWishlist.objects.create(
            user=another_student,
            course=course,
        )

        url = reverse(
            "courses_api:course_wishlist_remove",
            kwargs={"pk": first_wishlist.pk},
        )

        api_client.force_authenticate(user=student_user)

        # Act
        response = api_client.delete(url)

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT

        assert not CourseWishlist.objects.filter(
            pk=first_wishlist.pk,
        ).exists()

        assert CourseWishlist.objects.filter(
            pk=second_wishlist.pk,
        ).exists()

    def test_removing_wishlist_only_affects_target_wishlist(
        self,
        api_client,
        student_user,
        course,
        another_user,
    ):
        # Arrange
        another_course = course.__class__.objects.create(
            title="Another Course",
            owner=another_user,
            category=course.category,
        )

        first_wishlist = CourseWishlist.objects.create(
            user=student_user,
            course=course,
        )
        second_wishlist = CourseWishlist.objects.create(
            user=student_user,
            course=another_course,
        )

        url = reverse(
            "courses_api:course_wishlist_remove",
            kwargs={"pk": first_wishlist.pk},
        )

        api_client.force_authenticate(user=student_user)

        # Act
        response = api_client.delete(url)

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT

        assert not CourseWishlist.objects.filter(
            pk=first_wishlist.pk,
        ).exists()

        assert CourseWishlist.objects.filter(
            pk=second_wishlist.pk,
        ).exists()
