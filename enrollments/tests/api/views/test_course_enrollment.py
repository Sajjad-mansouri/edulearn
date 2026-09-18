import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from enrollments.models import Enrollment


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def enroll_course_url(course):
    return reverse(
        "enrollment_api:enroll_course",
        kwargs={"course_id": course.id},
    )


class TestCourseEnrollmentAuthentication:
    def test_unauthenticated_user_cannot_enroll(
        self,
        api_client,
        enroll_course_url,
    ):
        # Arrange
        assert Enrollment.objects.count() == 0

        # Act
        response = api_client.post(enroll_course_url)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert Enrollment.objects.count() == 0


class TestCourseEnrollmentSuccess:
    def test_authenticated_user_can_enroll_in_course(
        self,
        api_client,
        test_user,
        course,
        enroll_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        # Act
        response = api_client.post(enroll_course_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        enrollment = Enrollment.objects.get(
            user=test_user,
            course=course,
        )

        assert response.data == {
            "enrollment_id": enrollment.id,
        }

    def test_enrollment_is_created_for_authenticated_user(
        self,
        api_client,
        test_user,
        course,
        enroll_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        # Act
        response = api_client.post(enroll_course_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        enrollment = Enrollment.objects.get(
            id=response.data["enrollment_id"],
        )

        assert enrollment.user == test_user
        assert enrollment.course == course

    def test_enrollment_uses_default_status(
        self,
        api_client,
        test_user,
        course,
        enroll_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        # Act
        response = api_client.post(enroll_course_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        enrollment = Enrollment.objects.get(
            id=response.data["enrollment_id"],
        )

        assert enrollment.status == Enrollment.Status.PENDING

    def test_only_one_enrollment_is_created(
        self,
        api_client,
        test_user,
        course,
        enroll_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        # Act
        response = api_client.post(enroll_course_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        assert (
            Enrollment.objects.filter(
                user=test_user,
                course=course,
            ).count()
            == 1
        )


class TestCourseEnrollmentIdempotency:
    def test_repeated_enrollment_returns_existing_enrollment(
        self,
        api_client,
        test_user,
        course,
        enroll_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        first_response = api_client.post(enroll_course_url)

        first_enrollment_id = first_response.data["enrollment_id"]

        # Act
        second_response = api_client.post(enroll_course_url)

        # Assert
        assert first_response.status_code == status.HTTP_200_OK
        assert second_response.status_code == status.HTTP_200_OK

        assert second_response.data == {
            "enrollment_id": first_enrollment_id,
        }

        assert (
            Enrollment.objects.filter(
                user=test_user,
                course=course,
            ).count()
            == 1
        )

    def test_repeated_enrollment_does_not_create_new_record(
        self,
        api_client,
        test_user,
        course,
        enroll_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        first_response = api_client.post(enroll_course_url)

        assert (
            Enrollment.objects.filter(
                user=test_user,
                course=course,
            ).count()
            == 1
        )

        # Act
        second_response = api_client.post(enroll_course_url)

        # Assert
        assert second_response.status_code == status.HTTP_200_OK

        assert (
            Enrollment.objects.filter(
                user=test_user,
                course=course,
            ).count()
            == 1
        )

        assert (
            second_response.data["enrollment_id"]
            == first_response.data["enrollment_id"]
        )


class TestCourseEnrollmentExistingEnrollment:
    def test_existing_enrollment_is_returned(
        self,
        api_client,
        test_user,
        course,
        enrollment,
        enroll_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        # Act
        response = api_client.post(enroll_course_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        assert response.data == {
            "enrollment_id": enrollment.id,
        }

        assert (
            Enrollment.objects.filter(
                user=test_user,
                course=course,
            ).count()
            == 1
        )

    def test_existing_enrollment_status_is_not_changed(
        self,
        api_client,
        test_user,
        course,
        enrollment,
        enroll_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        enrollment.status = Enrollment.Status.COMPLETED
        enrollment.save(update_fields=["status"])

        # Act
        response = api_client.post(enroll_course_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["enrollment_id"] == enrollment.id

        enrollment.refresh_from_db()

        assert enrollment.status == Enrollment.Status.COMPLETED


class TestCourseEnrollmentIsolation:
    def test_enrollment_is_created_for_current_user_not_course_owner(
        self,
        api_client,
        test_user,
        another_user,
        course,
        enroll_course_url,
    ):
        # Arrange
        assert course.owner == test_user

        api_client.force_authenticate(user=another_user)

        # Act
        response = api_client.post(enroll_course_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        enrollment = Enrollment.objects.get(
            id=response.data["enrollment_id"],
        )

        assert enrollment.user == another_user
        assert enrollment.course == course

    def test_different_users_get_different_enrollments(
        self,
        api_client,
        test_user,
        another_user,
        course,
    ):
        # Arrange
        url = reverse(
            "enrollment_api:enroll_course",
            kwargs={"course_id": course.id},
        )

        # Act
        api_client.force_authenticate(user=test_user)
        first_response = api_client.post(url)

        api_client.force_authenticate(user=another_user)
        second_response = api_client.post(url)

        # Assert
        assert first_response.status_code == status.HTTP_200_OK
        assert second_response.status_code == status.HTTP_200_OK

        assert (
            first_response.data["enrollment_id"]
            != second_response.data["enrollment_id"]
        )

        assert Enrollment.objects.filter(course=course).count() == 2

        assert (
            Enrollment.objects.filter(
                user=test_user,
                course=course,
            ).count()
            == 1
        )

        assert (
            Enrollment.objects.filter(
                user=another_user,
                course=course,
            ).count()
            == 1
        )


class TestCourseEnrollmentNotFound:
    def test_nonexistent_course_returns_not_found(
        self,
        api_client,
        test_user,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        url = reverse(
            "enrollment_api:enroll_course",
            kwargs={"course_id": 999999},
        )

        # Act
        response = api_client.post(url)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Enrollment.objects.count() == 0

    def test_invalid_course_id_returns_not_found(
        self,
        api_client,
        test_user,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        url = reverse(
            "enrollment_api:enroll_course",
            kwargs={"course_id": "does-not-exist"},
        )

        # Act
        response = api_client.post(url)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Enrollment.objects.count() == 0
