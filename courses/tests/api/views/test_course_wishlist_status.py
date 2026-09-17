import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from courses.models.wishlist import CourseWishlist

pytestmark = pytest.mark.django_db


class TestCourseWishlistStatusApiView:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def url(self, course):
        return reverse(
            "courses_api:course_wishlist_status",
            kwargs={"course_id": course.id},
        )

    def test_authenticated_user_gets_true_when_course_is_wishlisted(
        self,
        api_client,
        test_user,
        course,
        url,
    ):
        # Arrange
        CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )

        api_client.force_authenticate(user=test_user)

        # Act
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            "is_wishlisted": True,
        }

    def test_authenticated_user_gets_false_when_course_is_not_wishlisted(
        self,
        api_client,
        test_user,
        course,
        url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        # Act
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            "is_wishlisted": False,
        }

    def test_wishlist_status_belongs_to_requesting_user(
        self,
        api_client,
        test_user,
        another_user,
        course,
        url,
    ):
        # Arrange
        CourseWishlist.objects.create(
            user=another_user,
            course=course,
        )

        api_client.force_authenticate(user=test_user)

        # Act
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            "is_wishlisted": False,
        }

    def test_wishlist_status_is_true_only_for_matching_user_and_course(
        self,
        api_client,
        test_user,
        another_user,
        course,
        url,
    ):
        # Arrange
        CourseWishlist.objects.create(
            user=another_user,
            course=course,
        )

        another_course = course.__class__.objects.create(
            title="Another Course",
            owner=another_user,
            category=course.category,
        )

        CourseWishlist.objects.create(
            user=test_user,
            course=another_course,
        )

        api_client.force_authenticate(user=test_user)

        # Act
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            "is_wishlisted": False,
        }

    def test_nonexistent_course_returns_404(
        self,
        api_client,
        test_user,
    ):
        # Arrange
        nonexistent_course_id = 999999

        url = reverse(
            "courses_api:course_wishlist_status",
            kwargs={"course_id": nonexistent_course_id},
        )

        api_client.force_authenticate(user=test_user)

        # Act
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_nonexistent_course_does_not_create_wishlist(
        self,
        api_client,
        test_user,
    ):
        # Arrange
        nonexistent_course_id = 999999

        url = reverse(
            "courses_api:course_wishlist_status",
            kwargs={"course_id": nonexistent_course_id},
        )

        api_client.force_authenticate(user=test_user)

        # Act
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

        assert not CourseWishlist.objects.filter(
            user=test_user,
        ).exists()

    @pytest.mark.parametrize(
        "method",
        [
            "post",
            "put",
            "patch",
            "delete",
        ],
    )
    def test_non_get_methods_are_not_allowed(
        self,
        api_client,
        test_user,
        course,
        url,
        method,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        # Act
        response = getattr(api_client, method)(url)

        # Assert
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_get_does_not_modify_wishlist(
        self,
        api_client,
        test_user,
        course,
        url,
    ):
        # Arrange
        wishlist = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )

        initial_count = CourseWishlist.objects.count()

        api_client.force_authenticate(user=test_user)

        # Act
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            "is_wishlisted": True,
        }

        assert CourseWishlist.objects.count() == initial_count
        assert CourseWishlist.objects.filter(
            pk=wishlist.pk,
            user=test_user,
            course=course,
        ).exists()

    def test_user_with_multiple_wishlists_gets_status_for_requested_course_only(
        self,
        api_client,
        test_user,
        another_user,
        course,
    ):
        # Arrange
        another_course = course.__class__.objects.create(
            title="Another Course",
            owner=another_user,
            category=course.category,
        )

        CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )
        CourseWishlist.objects.create(
            user=test_user,
            course=another_course,
        )

        url = reverse(
            "courses_api:course_wishlist_status",
            kwargs={"course_id": course.id},
        )

        api_client.force_authenticate(user=test_user)

        # Act
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            "is_wishlisted": True,
        }
