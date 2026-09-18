import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from enrollments.models import Enrollment


class TestEnrollmentCourseApiView:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = APIClient()

    def get_url(self, enrollment_id):
        return reverse(
            "enrollment_api:enrollment_course",
            kwargs={"enrollment_id": enrollment_id},
        )

    def test_returns_enrolled_course(
        self,
        test_user,
        enrollment,
        course,
    ):
        # Arrange
        self.client.force_authenticate(user=test_user)

        # Act
        response = self.client.get(
            self.get_url(enrollment.id),
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["courseId"] == course.id
        assert response.data["courseTitle"] == course.title
        assert response.data["enrollmentId"] == enrollment.id

    def test_returns_total_lessons(
        self,
        test_user,
        enrollment,
        course,
    ):
        # Arrange
        self.client.force_authenticate(user=test_user)

        # Act
        response = self.client.get(
            self.get_url(enrollment.id),
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["totalLessons"] == 0

    def test_returns_empty_sections_when_course_has_no_sections(
        self,
        test_user,
        enrollment,
        course,
    ):
        # Arrange
        self.client.force_authenticate(user=test_user)

        # Act
        response = self.client.get(
            self.get_url(enrollment.id),
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["sections"] == []

    def test_returns_active_enrollment_course(
        self,
        test_user,
        enrollment,
        course,
    ):
        # Arrange
        enrollment.status = Enrollment.Status.ACTIVE
        enrollment.save(update_fields=["status"])

        self.client.force_authenticate(user=test_user)

        # Act
        response = self.client.get(
            self.get_url(enrollment.id),
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["courseId"] == course.id
        assert response.data["enrollmentId"] == enrollment.id

    def test_returns_completed_enrollment_course(
        self,
        test_user,
        enrollment,
        course,
    ):
        # Arrange
        enrollment.status = Enrollment.Status.COMPLETED
        enrollment.save(update_fields=["status"])

        self.client.force_authenticate(user=test_user)

        # Act
        response = self.client.get(
            self.get_url(enrollment.id),
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["courseId"] == course.id
        assert response.data["enrollmentId"] == enrollment.id

    @pytest.mark.parametrize(
        "enrollment_status",
        [
            Enrollment.Status.PENDING,
            Enrollment.Status.CANCELLED,
            Enrollment.Status.SUSPENDED,
        ],
    )
    def test_rejects_inactive_enrollment(
        self,
        test_user,
        enrollment,
        enrollment_status,
    ):
        # Arrange
        enrollment.status = enrollment_status
        enrollment.save(update_fields=["status"])

        self.client.force_authenticate(user=test_user)

        # Act
        response = self.client.get(
            self.get_url(enrollment.id),
        )

        # Assert
        assert response.status_code in {
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        }

    def test_does_not_allow_another_users_enrollment(
        self,
        test_user,
        another_user_enrollment,
    ):
        # Arrange
        another_user_enrollment.status = Enrollment.Status.ACTIVE
        another_user_enrollment.save(update_fields=["status"])

        self.client.force_authenticate(user=test_user)

        # Act
        response = self.client.get(
            self.get_url(another_user_enrollment.id),
        )

        # Assert
        assert response.status_code in {
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        }

    def test_does_not_return_another_users_course_data(
        self,
        test_user,
        another_user_enrollment,
    ):
        # Arrange
        another_user_enrollment.status = Enrollment.Status.COMPLETED
        another_user_enrollment.save(update_fields=["status"])

        self.client.force_authenticate(user=test_user)

        # Act
        response = self.client.get(
            self.get_url(another_user_enrollment.id),
        )

        # Assert
        assert response.status_code in {
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        }

    def test_returns_403_for_nonexistent_enrollment(self, test_user):
        self.client.force_authenticate(user=test_user)

        response = self.client.get(self.get_url(999999))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_requires_authentication(
        self,
        enrollment,
    ):
        # Arrange
        url = self.get_url(enrollment.id)

        # Act
        response = self.client.get(url)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_enrollment_id_is_returned_from_url_context(
        self,
        test_user,
        enrollment,
    ):
        # Arrange
        self.client.force_authenticate(user=test_user)

        # Act
        response = self.client.get(
            self.get_url(enrollment.id),
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["enrollmentId"] == enrollment.id

    def test_returns_correct_course_for_enrollment(
        self,
        test_user,
        enrollment,
        course,
    ):
        # Arrange
        self.client.force_authenticate(user=test_user)

        # Act
        response = self.client.get(
            self.get_url(enrollment.id),
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["courseId"] == enrollment.course_id
        assert response.data["courseId"] == course.id

    def test_does_not_expose_unrelated_course_fields(
        self,
        test_user,
        enrollment,
    ):
        # Arrange
        self.client.force_authenticate(user=test_user)

        # Act
        response = self.client.get(
            self.get_url(enrollment.id),
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        assert "owner" not in response.data
        assert "category" not in response.data
        assert "price" not in response.data
        assert "description" not in response.data
        assert "status" not in response.data

    def test_returns_course_with_multiple_enrollments_for_current_user(
        self,
        test_user,
        enrollment,
        course,
        another_user_enrollment,
    ):
        # Arrange
        enrollment.status = Enrollment.Status.ACTIVE
        enrollment.save(update_fields=["status"])

        another_user_enrollment.status = Enrollment.Status.ACTIVE
        another_user_enrollment.save(update_fields=["status"])

        self.client.force_authenticate(user=test_user)

        # Act
        response = self.client.get(
            self.get_url(enrollment.id),
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["courseId"] == course.id
        assert response.data["enrollmentId"] == enrollment.id
        assert response.data["enrollmentId"] != another_user_enrollment.id
