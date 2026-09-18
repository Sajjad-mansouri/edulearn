import pytest
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from courses.models.course import Course
from enrollments.api.views import CurrentUserEnrollmentStatus
from enrollments.models import Enrollment


class TestCurrentUserEnrollmentStatus:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.factory = APIRequestFactory()
        self.view = CurrentUserEnrollmentStatus.as_view()

    def test_returns_not_enrolled_when_course_id_is_missing(
        self,
        test_user,
    ):
        # Arrange
        request = self.factory.get("/enrollments/status/")
        force_authenticate(request, user=test_user)

        # Act
        response = self.view(request)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            "is_enrolled": False,
        }

    def test_returns_enrolled_for_active_enrollment(
        self,
        test_user,
        course,
        enrollment,
    ):
        # Arrange
        enrollment.status = Enrollment.Status.ACTIVE
        enrollment.save(update_fields=["status"])

        request = self.factory.get(
            f"/enrollments/status/{course.id}/",
        )
        force_authenticate(request, user=test_user)

        # Act
        response = self.view(
            request,
            course_id=course.id,
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            "is_enrolled": True,
            "enrollment_id": enrollment.id,
        }

    def test_returns_enrolled_for_completed_enrollment(
        self,
        test_user,
        course,
        enrollment,
    ):
        # Arrange
        enrollment.status = Enrollment.Status.COMPLETED
        enrollment.save(update_fields=["status"])

        request = self.factory.get(
            f"/enrollments/status/{course.id}/",
        )
        force_authenticate(request, user=test_user)

        # Act
        response = self.view(
            request,
            course_id=course.id,
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            "is_enrolled": True,
            "enrollment_id": enrollment.id,
        }

    @pytest.mark.parametrize(
        "enrollment_status",
        [
            Enrollment.Status.CANCELLED,
            Enrollment.Status.SUSPENDED,
            Enrollment.Status.PENDING,
        ],
    )
    def test_returns_not_enrolled_for_inactive_enrollment_status(
        self,
        test_user,
        course,
        enrollment,
        enrollment_status,
    ):
        # Arrange
        enrollment.status = enrollment_status
        enrollment.save(update_fields=["status"])

        request = self.factory.get(
            f"/enrollments/status/{course.id}/",
        )
        force_authenticate(request, user=test_user)

        # Act
        response = self.view(
            request,
            course_id=course.id,
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            "is_enrolled": False,
            "enrollment_id": None,
        }

    def test_returns_not_enrolled_when_user_has_no_enrollment(
        self,
        test_user,
        course,
    ):
        # Arrange
        request = self.factory.get(
            f"/enrollments/status/{course.id}/",
        )
        force_authenticate(request, user=test_user)

        # Act
        response = self.view(
            request,
            course_id=course.id,
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            "is_enrolled": False,
            "enrollment_id": None,
        }

    def test_does_not_return_another_users_enrollment(
        self,
        test_user,
        course,
        another_user_enrollment,
    ):
        # Arrange
        another_user_enrollment.status = Enrollment.Status.ACTIVE
        another_user_enrollment.save(update_fields=["status"])

        request = self.factory.get(
            f"/enrollments/status/{course.id}/",
        )
        force_authenticate(request, user=test_user)

        # Act
        response = self.view(
            request,
            course_id=course.id,
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            "is_enrolled": False,
            "enrollment_id": None,
        }

    def test_returns_current_users_enrollment_when_other_user_is_also_enrolled(
        self,
        test_user,
        course,
        enrollment,
        another_user_enrollment,
    ):
        # Arrange
        enrollment.status = Enrollment.Status.ACTIVE
        enrollment.save(update_fields=["status"])

        another_user_enrollment.status = Enrollment.Status.COMPLETED
        another_user_enrollment.save(update_fields=["status"])

        request = self.factory.get(
            f"/enrollments/status/{course.id}/",
        )
        force_authenticate(request, user=test_user)

        # Act
        response = self.view(
            request,
            course_id=course.id,
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            "is_enrolled": True,
            "enrollment_id": enrollment.id,
        }

    def test_returns_404_for_nonexistent_course(
        self,
        test_user,
    ):
        # Arrange
        nonexistent_course_id = 999999

        request = self.factory.get(
            f"/enrollments/status/{nonexistent_course_id}/",
        )
        force_authenticate(request, user=test_user)

        # Act
        response = self.view(
            request,
            course_id=nonexistent_course_id,
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_does_not_return_enrollment_from_different_course(
        self,
        test_user,
        course,
        category,
    ):
        # Arrange
        another_course = Course.objects.create(
            title="Another Course",
            owner=test_user,
            category=category,
        )

        Enrollment.objects.create(
            user=test_user,
            course=another_course,
            status=Enrollment.Status.ACTIVE,
        )

        request = self.factory.get(
            f"/enrollments/status/{course.id}/",
        )
        force_authenticate(request, user=test_user)

        # Act
        response = self.view(
            request,
            course_id=course.id,
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            "is_enrolled": False,
            "enrollment_id": None,
        }

    def test_returns_active_enrollment_id_not_another_users_id(
        self,
        test_user,
        course,
        enrollment,
        another_user_enrollment,
    ):
        # Arrange
        enrollment.status = Enrollment.Status.ACTIVE
        enrollment.save(update_fields=["status"])

        another_user_enrollment.status = Enrollment.Status.ACTIVE
        another_user_enrollment.save(update_fields=["status"])

        request = self.factory.get(
            f"/enrollments/status/{course.id}/",
        )
        force_authenticate(request, user=test_user)

        # Act
        response = self.view(
            request,
            course_id=course.id,
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_enrolled"] is True
        assert response.data["enrollment_id"] == enrollment.id
        assert response.data["enrollment_id"] != another_user_enrollment.id
