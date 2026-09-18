from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from courses.models import Course, CourseFeedback
from enrollments.models import Enrollment


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def student_courses_url():
    return reverse("enrollment_api:student_courses")


@pytest.fixture
def authenticated_student_client(api_client, student_user):
    api_client.force_authenticate(user=student_user)
    return api_client


class TestStudentCoursesApiViewAuthentication:
    def test_unauthenticated_user_cannot_access_student_courses(
        self,
        api_client,
        student_courses_url,
    ):
        # Arrange
        # No authentication.

        # Act
        response = api_client.get(student_courses_url)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestStudentCoursesApiViewPermissions:
    def test_authenticated_non_student_cannot_access_student_courses(
        self,
        api_client,
        test_user,
        student_courses_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        # Act
        response = api_client.get(student_courses_url)

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_student_can_access_student_courses(
        self,
        authenticated_student_client,
        student_courses_url,
    ):
        # Arrange
        # Authenticated student fixture.

        # Act
        response = authenticated_student_client.get(student_courses_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK


class TestStudentCoursesApiViewQueryset:
    def test_returns_active_enrollment(
        self,
        authenticated_student_client,
        student_user,
        course,
        enrollment,
        student_courses_url,
    ):
        # Arrange
        enrollment.status = Enrollment.Status.ACTIVE
        enrollment.progress = Decimal("35.50")
        enrollment.save(update_fields=["status", "progress"])

        # Act
        response = authenticated_student_client.get(student_courses_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        results = response.data["results"]

        returned_course_ids = {item["id"] for item in results}

        assert course.id in returned_course_ids

        course_data = next(item for item in results if item["id"] == course.id)

        assert course_data["enrollment_id"] == enrollment.id
        assert course_data["progress"] == 35.50

    def test_returns_completed_enrollment(
        self,
        authenticated_student_client,
        course,
        enrollment,
        student_courses_url,
    ):
        # Arrange
        enrollment.status = Enrollment.Status.COMPLETED
        enrollment.progress = Decimal("100.00")
        enrollment.save(update_fields=["status", "progress"])

        # Act
        response = authenticated_student_client.get(student_courses_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        results = response.data["results"]

        course_data = next(item for item in results if item["id"] == course.id)

        assert course_data["enrollment_id"] == enrollment.id
        assert course_data["progress"] == 100.00

    @pytest.mark.parametrize(
        "enrollment_status",
        [
            Enrollment.Status.PENDING,
            Enrollment.Status.CANCELLED,
            Enrollment.Status.SUSPENDED,
        ],
    )
    def test_excludes_ineligible_enrollment_statuses(
        self,
        authenticated_student_client,
        course,
        enrollment,
        student_courses_url,
        enrollment_status,
    ):
        # Arrange
        enrollment.status = enrollment_status
        enrollment.save(update_fields=["status"])

        # Act
        response = authenticated_student_client.get(student_courses_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        results = response.data["results"]

        returned_course_ids = {item["id"] for item in results}

        assert course.id not in returned_course_ids

    def test_does_not_return_courses_without_enrollment(
        self,
        authenticated_student_client,
        course,
        student_courses_url,
    ):
        # Arrange
        # No enrollment for the student.

        # Act
        response = authenticated_student_client.get(student_courses_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == []

    def test_does_not_return_another_users_enrollment(
        self,
        authenticated_student_client,
        student_user,
        course,
        another_user_enrollment,
        student_courses_url,
    ):
        # Arrange
        assert another_user_enrollment.user != student_user
        assert another_user_enrollment.course == course

        # Act
        response = authenticated_student_client.get(student_courses_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        returned_course_ids = {item["id"] for item in response.data["results"]}

        assert course.id not in returned_course_ids

    def test_returns_only_current_students_courses(
        self,
        authenticated_student_client,
        student_user,
        course,
        category,
        another_user,
        student_courses_url,
    ):
        # Arrange
        student_enrollment = Enrollment.objects.create(
            user=student_user,
            course=course,
            status=Enrollment.Status.ACTIVE,
        )

        another_course = Course.objects.create(
            title="Another Course",
            owner=another_user,
            category=category,
        )

        Enrollment.objects.create(
            user=another_user,
            course=another_course,
            status=Enrollment.Status.ACTIVE,
        )

        # Act
        response = authenticated_student_client.get(student_courses_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        returned_course_ids = {item["id"] for item in response.data["results"]}

        assert course.id in returned_course_ids
        assert another_course.id not in returned_course_ids

        course_data = next(
            item for item in response.data["results"] if item["id"] == course.id
        )

        assert course_data["enrollment_id"] == student_enrollment.id


class TestStudentCoursesApiViewAnnotations:
    def test_returns_current_students_enrollment_id(
        self,
        authenticated_student_client,
        course,
        enrollment,
        student_courses_url,
    ):
        # Arrange
        enrollment.status = Enrollment.Status.ACTIVE
        enrollment.save(update_fields=["status"])

        # Act
        response = authenticated_student_client.get(student_courses_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        course_data = next(
            item for item in response.data["results"] if item["id"] == course.id
        )

        assert course_data["enrollment_id"] == enrollment.id

    def test_returns_current_students_progress(
        self,
        authenticated_student_client,
        course,
        enrollment,
        student_courses_url,
    ):
        # Arrange
        enrollment.status = Enrollment.Status.ACTIVE
        enrollment.progress = Decimal("67.25")
        enrollment.save(update_fields=["status", "progress"])

        # Act
        response = authenticated_student_client.get(student_courses_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        course_data = next(
            item for item in response.data["results"] if item["id"] == course.id
        )

        assert course_data["progress"] == 67.25

    def test_returns_last_accessed_from_enrollment(
        self,
        authenticated_student_client,
        course,
        enrollment,
        student_courses_url,
    ):
        # Arrange
        last_activity = timezone.now()

        enrollment.status = Enrollment.Status.ACTIVE
        enrollment.last_activity_at = last_activity
        enrollment.save(
            update_fields=["status", "last_activity_at"],
        )

        # Act
        response = authenticated_student_client.get(student_courses_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        course_data = next(
            item for item in response.data["results"] if item["id"] == course.id
        )

        assert course_data["last_accessed"] is not None

    def test_returns_enrolled_at_from_enrollment(
        self,
        authenticated_student_client,
        course,
        enrollment,
        student_courses_url,
    ):
        # Arrange
        enrollment.status = Enrollment.Status.ACTIVE
        enrollment.save(update_fields=["status"])

        enrollment.refresh_from_db()

        # Act
        response = authenticated_student_client.get(student_courses_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        course_data = next(
            item for item in response.data["results"] if item["id"] == course.id
        )

        assert course_data["enrolled_at"] is not None

    def test_rating_is_aggregated_from_course_feedback(
        self,
        authenticated_student_client,
        course,
        enrollment,
        student_courses_url,
    ):
        # Arrange
        enrollment.status = Enrollment.Status.ACTIVE
        enrollment.save(update_fields=["status"])

        CourseFeedback.objects.create(
            enrollment=enrollment,
            rating=4,
            comment="Good course",
        )

        # Act
        response = authenticated_student_client.get(student_courses_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        course_data = next(
            item for item in response.data["results"] if item["id"] == course.id
        )

        assert course_data["rating"] == 4.0


class TestStudentCoursesApiViewMultipleCourses:
    def test_returns_multiple_enrolled_courses(
        self,
        authenticated_student_client,
        student_user,
        course,
        category,
        another_user,
        student_courses_url,
    ):
        # Arrange
        Enrollment.objects.create(
            user=student_user,
            course=course,
            status=Enrollment.Status.ACTIVE,
        )

        second_course = Course.objects.create(
            title="Second Course",
            owner=another_user,
            category=category,
        )

        second_enrollment = Enrollment.objects.create(
            user=student_user,
            course=second_course,
            status=Enrollment.Status.ACTIVE,
        )

        # Act
        response = authenticated_student_client.get(student_courses_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        returned_course_ids = {item["id"] for item in response.data["results"]}

        assert course.id in returned_course_ids
        assert second_course.id in returned_course_ids

        assert response.data["count"] >= 2

        second_course_data = next(
            item for item in response.data["results"] if item["id"] == second_course.id
        )

        assert second_course_data["enrollment_id"] == second_enrollment.id

    def test_does_not_duplicate_course_from_feedback_join(
        self,
        authenticated_student_client,
        course,
        enrollment,
        student_courses_url,
    ):
        # Arrange
        enrollment.status = Enrollment.Status.ACTIVE
        enrollment.save(update_fields=["status"])

        CourseFeedback.objects.create(
            enrollment=enrollment,
            rating=5,
            comment="Excellent",
        )

        # Act
        response = authenticated_student_client.get(student_courses_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        matching_courses = [
            item for item in response.data["results"] if item["id"] == course.id
        ]

        assert len(matching_courses) == 1


class TestStudentCoursesApiViewOrdering:
    def test_courses_are_ordered_by_enrolled_at_descending(
        self,
        authenticated_student_client,
        student_user,
        course,
        category,
        another_user,
        student_courses_url,
    ):
        # Arrange
        first_enrollment = Enrollment.objects.create(
            user=student_user,
            course=course,
            status=Enrollment.Status.ACTIVE,
        )

        second_course = Course.objects.create(
            title="Recently Enrolled Course",
            owner=another_user,
            category=category,
        )

        second_enrollment = Enrollment.objects.create(
            user=student_user,
            course=second_course,
            status=Enrollment.Status.ACTIVE,
        )

        # Ensure deterministic ordering.
        second_enrollment.enrolled_at = (
            first_enrollment.enrolled_at + timezone.timedelta(seconds=10)
        )
        second_enrollment.save(update_fields=["enrolled_at"])

        # Act
        response = authenticated_student_client.get(student_courses_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        results = response.data["results"]

        first_index = next(
            index for index, item in enumerate(results) if item["id"] == course.id
        )

        second_index = next(
            index
            for index, item in enumerate(results)
            if item["id"] == second_course.id
        )

        assert second_index < first_index


class TestStudentCoursesApiViewPagination:
    def test_response_is_paginated(
        self,
        authenticated_student_client,
        student_courses_url,
    ):
        # Arrange
        # The configured ListAPIView pagination should be active.

        # Act
        response = authenticated_student_client.get(student_courses_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        assert "count" in response.data
        assert "results" in response.data

    def test_empty_result_contains_empty_results_list(
        self,
        authenticated_student_client,
        student_courses_url,
    ):
        # Arrange
        # Student has no enrollments.

        # Act
        response = authenticated_student_client.get(student_courses_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0
        assert response.data["results"] == []
