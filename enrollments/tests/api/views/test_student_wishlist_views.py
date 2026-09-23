from datetime import timedelta

import pytest
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from courses.models import CourseWishlist
from courses.models.feedback import CourseFeedback


@pytest.fixture
def authenticated_student_client(student_user):
    client = APIClient()
    client.force_authenticate(user=student_user)
    return client


@pytest.fixture
def student_wishlist_url():
    return reverse("enrollment_api:student_wishlist")


class TestStudentWishlistApiViewAuthentication:
    def test_unauthenticated_user_cannot_access_wishlist(
        self,
        api_client,
        student_wishlist_url,
    ):
        # Arrange
        url = student_wishlist_url

        # Act
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_non_student_user_cannot_access_wishlist(
        self,
        test_user,
        student_wishlist_url,
    ):
        # Arrange
        client = APIClient()
        client.force_authenticate(user=test_user)

        # Act
        response = client.get(student_wishlist_url)

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_student_user_can_access_wishlist(
        self,
        authenticated_student_client,
        student_wishlist_url,
    ):
        # Arrange
        url = student_wishlist_url

        # Act
        response = authenticated_student_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_200_OK


class TestStudentWishlistApiViewQueryset:
    def test_returns_only_current_students_wishlist(
        self,
        authenticated_student_client,
        student_user,
        another_user,
        course,
        student_wishlist_url,
    ):
        # Arrange
        other_course = course.__class__.objects.create(
            title="Another Course",
            owner=another_user,
            category=course.category,
        )

        CourseWishlist.objects.create(
            user=student_user,
            course=course,
        )
        CourseWishlist.objects.create(
            user=another_user,
            course=other_course,
        )

        # Act
        response = authenticated_student_client.get(student_wishlist_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        results = response.data["results"]

        assert len(results) == 1
        assert results[0]["course_id"] == str(course.id)

    def test_returns_empty_results_when_wishlist_is_empty(
        self,
        authenticated_student_client,
        student_wishlist_url,
    ):
        # Arrange
        # No wishlist entries exist for the student.

        # Act
        response = authenticated_student_client.get(student_wishlist_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == []

    def test_returns_multiple_wishlist_courses(
        self,
        authenticated_student_client,
        student_user,
        course,
        student_wishlist_url,
    ):
        # Arrange
        second_course = course.__class__.objects.create(
            title="Second Course",
            owner=student_user,
            category=course.category,
        )
        third_course = course.__class__.objects.create(
            title="Third Course",
            owner=student_user,
            category=course.category,
        )

        CourseWishlist.objects.create(
            user=student_user,
            course=course,
        )
        CourseWishlist.objects.create(
            user=student_user,
            course=second_course,
        )
        CourseWishlist.objects.create(
            user=student_user,
            course=third_course,
        )

        # Act
        response = authenticated_student_client.get(student_wishlist_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3
        assert len(response.data["results"]) == 3

        returned_course_ids = {item["course_id"] for item in response.data["results"]}

        assert returned_course_ids == {
            str(course.id),
            str(second_course.id),
            str(third_course.id),
        }


class TestStudentWishlistApiViewOrdering:
    def test_returns_wishlist_ordered_by_newest_first(
        self,
        authenticated_student_client,
        student_user,
        course,
        student_wishlist_url,
    ):
        # Arrange
        second_course = course.__class__.objects.create(
            title="Second Course",
            owner=student_user,
            category=course.category,
        )
        third_course = course.__class__.objects.create(
            title="Third Course",
            owner=student_user,
            category=course.category,
        )

        first_wishlist = CourseWishlist.objects.create(
            user=student_user,
            course=course,
        )
        second_wishlist = CourseWishlist.objects.create(
            user=student_user,
            course=second_course,
        )
        third_wishlist = CourseWishlist.objects.create(
            user=student_user,
            course=third_course,
        )

        base_time = timezone.now()

        CourseWishlist.objects.filter(pk=first_wishlist.pk).update(
            created_at=base_time - timedelta(days=2)
        )
        CourseWishlist.objects.filter(pk=second_wishlist.pk).update(
            created_at=base_time - timedelta(days=1)
        )
        CourseWishlist.objects.filter(pk=third_wishlist.pk).update(created_at=base_time)

        # Act
        response = authenticated_student_client.get(student_wishlist_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        results = response.data["results"]

        returned_course_ids = [item["course_id"] for item in results]

        assert returned_course_ids == [
            str(third_course.id),
            str(second_course.id),
            str(course.id),
        ]


class TestStudentWishlistApiViewAnnotations:
    def test_returns_rating_and_rating_count_for_course_with_feedback(
        self,
        authenticated_student_client,
        student_user,
        course,
        enrollment,
        student_wishlist_url,
    ):
        # Arrange
        CourseWishlist.objects.create(
            user=student_user,
            course=course,
        )

        CourseFeedback.objects.create(
            enrollment=enrollment,
            rating=4,
        )

        # Act
        response = authenticated_student_client.get(student_wishlist_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        result = response.data["results"][0]

        assert result["course_id"] == str(course.id)
        assert result["rating"] == 4.0
        assert result["rating_count"] == 1

    def test_averages_feedback_ratings_for_course(
        self,
        authenticated_student_client,
        student_user,
        course,
        enrollment,
        another_user_enrollment,
        student_wishlist_url,
    ):
        # Arrange
        CourseWishlist.objects.create(
            user=student_user,
            course=course,
        )

        CourseFeedback.objects.create(
            enrollment=enrollment,
            rating=4,
        )
        CourseFeedback.objects.create(
            enrollment=another_user_enrollment,
            rating=2,
        )

        # Act
        response = authenticated_student_client.get(student_wishlist_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        result = response.data["results"][0]

        assert result["rating"] == 3.0
        assert result["rating_count"] == 2

    def test_course_without_feedback_has_null_rating_and_zero_count(
        self,
        authenticated_student_client,
        student_user,
        course,
        student_wishlist_url,
    ):
        # Arrange
        CourseWishlist.objects.create(
            user=student_user,
            course=course,
        )

        # Act
        response = authenticated_student_client.get(student_wishlist_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        result = response.data["results"][0]

        assert result["rating"] is None
        assert result["rating_count"] == 0

    def test_feedback_from_another_course_does_not_affect_rating(
        self,
        authenticated_student_client,
        student_user,
        another_user,
        course,
        enrollment,
        student_wishlist_url,
    ):
        # Arrange
        other_course = course.__class__.objects.create(
            title="Another Course",
            owner=another_user,
            category=course.category,
        )

        other_enrollment = enrollment.__class__.objects.create(
            user=another_user,
            course=other_course,
            status=enrollment.Status.ACTIVE,
        )

        CourseWishlist.objects.create(
            user=student_user,
            course=course,
        )

        CourseFeedback.objects.create(
            enrollment=enrollment,
            rating=5,
        )
        CourseFeedback.objects.create(
            enrollment=other_enrollment,
            rating=1,
        )

        # Act
        response = authenticated_student_client.get(student_wishlist_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        result = response.data["results"][0]

        assert result["course_id"] == str(course.id)
        assert result["rating"] == 5.0
        assert result["rating_count"] == 1


class TestStudentWishlistApiViewSerializer:
    def test_returns_expected_wishlist_fields(
        self,
        authenticated_student_client,
        student_user,
        course,
        student_wishlist_url,
    ):
        # Arrange
        CourseWishlist.objects.create(
            user=student_user,
            course=course,
        )

        # Act
        response = authenticated_student_client.get(student_wishlist_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        result = response.data["results"][0]

        expected_fields = {
            "id",
            "title",
            "instructor",
            "thumbnail",
            "rating",
            "rating_count",
            "difficulty",
            "duration",
            "price",
            "original_price",
            "category",
            "date_saved",
            "course_id",
            "course_slug",
        }

        assert set(result) == expected_fields

    def test_returns_course_information(
        self,
        authenticated_student_client,
        student_user,
        course,
        student_wishlist_url,
    ):
        # Arrange
        CourseWishlist.objects.create(
            user=student_user,
            course=course,
        )

        # Act
        response = authenticated_student_client.get(student_wishlist_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        result = response.data["results"][0]

        assert (
            result["id"]
            == CourseWishlist.objects.get(
                user=student_user,
                course=course,
            ).id
        )
        assert result["title"] == course.title
        assert result["course_id"] == str(course.id)
        assert result["course_slug"] == course.slug
        assert result["difficulty"] == course.level
        assert result["category"] == course.category.name

    def test_returns_discounted_price(
        self,
        authenticated_student_client,
        student_user,
        course,
        student_wishlist_url,
    ):
        # Arrange
        CourseWishlist.objects.create(
            user=student_user,
            course=course,
        )

        # Act
        response = authenticated_student_client.get(student_wishlist_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        result = response.data["results"][0]

        assert result["price"] == course.get_discounted_price


class TestStudentWishlistApiViewModelConstraints:
    def test_same_user_cannot_wishlist_same_course_twice(
        self,
        student_user,
        course,
    ):
        # Arrange
        CourseWishlist.objects.create(
            user=student_user,
            course=course,
        )

        # Act / Assert
        with pytest.raises(IntegrityError):
            CourseWishlist.objects.create(
                user=student_user,
                course=course,
            )

    def test_different_users_can_wishlist_same_course(
        self,
        student_user,
        another_user,
        course,
    ):
        # Arrange
        first_wishlist = CourseWishlist.objects.create(
            user=student_user,
            course=course,
        )

        # Act
        second_wishlist = CourseWishlist.objects.create(
            user=another_user,
            course=course,
        )

        # Assert
        assert first_wishlist.pk != second_wishlist.pk
        assert CourseWishlist.objects.filter(course=course).count() == 2


class TestStudentWishlistApiViewPagination:
    def test_response_is_paginated(
        self,
        authenticated_student_client,
        student_user,
        course,
        student_wishlist_url,
    ):
        # Arrange
        CourseWishlist.objects.create(
            user=student_user,
            course=course,
        )

        # Act
        response = authenticated_student_client.get(student_wishlist_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "count" in response.data
        assert "next" in response.data
        assert "previous" in response.data
        assert "results" in response.data
        assert response.data["count"] == 1
        assert len(response.data["results"]) == 1
