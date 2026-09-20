import pytest
from django.contrib.auth import get_user_model
from django.urls import resolve, reverse
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import Role
from courses.models import Course

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestCourseSubmitApiView:
    @pytest.fixture
    def url(self, instructor_course):
        return reverse(
            "instructor_api:submit_course",
            kwargs={"course_id": instructor_course.pk},
        )

    def test_unauthenticated_user_cannot_submit_course(
        self,
        api_client: APIClient,
        url: str,
        instructor_course,
    ):
        # Arrange
        course_id = instructor_course.pk

        # Act
        response = api_client.post(url)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        instructor_course.refresh_from_db()
        assert instructor_course.pk == course_id

    def test_non_instructor_user_cannot_submit_course(
        self,
        api_client: APIClient,
        student_user,
        instructor_course,
        url,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        # Act
        response = api_client.post(url)

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

        instructor_course.refresh_from_db()
        assert instructor_course.review_status != Course.ReviewStatus.PENDING

    def test_instructor_can_submit_owned_course(
        self,
        api_client: APIClient,
        instructor_user,
        instructor_course,
        url,
    ):
        # Arrange
        instructor_course.review_status = Course.ReviewStatus.NOT_SUBMITTED
        instructor_course.status = Course.Status.DRAFT
        instructor_course.save(
            update_fields=["review_status", "status"],
        )

        api_client.force_authenticate(user=instructor_user)

        # Act
        response = api_client.post(url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        instructor_course.refresh_from_db()

        assert instructor_course.review_status == Course.ReviewStatus.PENDING
        assert instructor_course.status == Course.Status.SUBMITTED

    def test_course_with_changes_requested_can_be_submitted(
        self,
        api_client: APIClient,
        instructor_user,
        instructor_course,
        url,
    ):
        # Arrange
        instructor_course.review_status = Course.ReviewStatus.CHANGES_REQUESTED
        instructor_course.status = Course.Status.DRAFT
        instructor_course.save(
            update_fields=["review_status", "status"],
        )

        api_client.force_authenticate(user=instructor_user)

        # Act
        response = api_client.post(url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        instructor_course.refresh_from_db()

        assert instructor_course.review_status == Course.ReviewStatus.PENDING
        assert instructor_course.status == Course.Status.SUBMITTED

    @pytest.mark.parametrize(
        "review_status",
        [
            Course.ReviewStatus.NOT_SUBMITTED,
            Course.ReviewStatus.CHANGES_REQUESTED,
        ],
    )
    def test_allowed_review_statuses_are_transitioned_to_pending(
        self,
        api_client: APIClient,
        instructor_user,
        instructor_course,
        review_status,
        url,
    ):
        # Arrange
        instructor_course.review_status = review_status
        instructor_course.status = Course.Status.DRAFT
        instructor_course.save(
            update_fields=["review_status", "status"],
        )

        api_client.force_authenticate(user=instructor_user)

        # Act
        response = api_client.post(url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        instructor_course.refresh_from_db()

        assert instructor_course.review_status == Course.ReviewStatus.PENDING
        assert instructor_course.status == Course.Status.SUBMITTED

    @pytest.mark.parametrize(
        "review_status",
        [
            Course.ReviewStatus.PENDING,
            Course.ReviewStatus.UNDER_REVIEW,
            Course.ReviewStatus.APPROVED,
            Course.ReviewStatus.REJECTED,
        ],
    )
    def test_course_with_ineligible_review_status_cannot_be_submitted(
        self,
        api_client: APIClient,
        instructor_user,
        instructor_course,
        review_status,
        url,
    ):
        # Arrange
        instructor_course.review_status = review_status
        instructor_course.status = Course.Status.DRAFT
        instructor_course.save(
            update_fields=["review_status", "status"],
        )

        api_client.force_authenticate(user=instructor_user)

        # Act
        response = api_client.post(url)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

        instructor_course.refresh_from_db()

        assert instructor_course.review_status == review_status
        assert instructor_course.status == Course.Status.DRAFT

    def test_instructor_cannot_submit_course_owned_by_another_instructor(
        self,
        api_client: APIClient,
        instructor_user,
        instructor_course,
    ):
        # Arrange
        another_instructor = User.objects.create_user(
            username="another_instructor",
            email="another_instructor@example.com",
            password="test-password",
        )

        instructor_role, _ = Role.objects.get_or_create(
            name=Role.Roles.INSTRUCTOR,
        )
        another_instructor.roles.add(instructor_role)

        instructor_course.owner = another_instructor
        instructor_course.review_status = Course.ReviewStatus.NOT_SUBMITTED
        instructor_course.status = Course.Status.DRAFT
        instructor_course.save(
            update_fields=["owner", "review_status", "status"],
        )

        url = reverse(
            "instructor_api:submit_course",
            kwargs={"course_id": instructor_course.pk},
        )

        api_client.force_authenticate(user=instructor_user)

        # Act
        response = api_client.post(url)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

        instructor_course.refresh_from_db()

        assert instructor_course.owner_id == another_instructor.pk
        assert instructor_course.review_status == Course.ReviewStatus.NOT_SUBMITTED
        assert instructor_course.status == Course.Status.DRAFT

    def test_nonexistent_course_returns_404(
        self,
        api_client: APIClient,
        instructor_user,
    ):
        # Arrange
        nonexistent_course_id = 999999

        url = reverse(
            "instructor_api:submit_course",
            kwargs={"course_id": nonexistent_course_id},
        )

        api_client.force_authenticate(user=instructor_user)

        # Act
        response = api_client.post(url)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_submitting_course_changes_only_submission_fields(
        self,
        api_client: APIClient,
        instructor_user,
        instructor_course,
        url,
    ):
        # Arrange
        instructor_course.review_status = Course.ReviewStatus.CHANGES_REQUESTED
        instructor_course.status = Course.Status.DRAFT

        original_title = instructor_course.title
        original_owner_id = instructor_course.owner_id
        original_pk = instructor_course.pk

        instructor_course.save(
            update_fields=["review_status", "status"],
        )

        api_client.force_authenticate(user=instructor_user)

        # Act
        response = api_client.post(url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        instructor_course.refresh_from_db()

        assert instructor_course.pk == original_pk
        assert instructor_course.owner_id == original_owner_id
        assert instructor_course.title == original_title
        assert instructor_course.status == Course.Status.SUBMITTED
        assert instructor_course.review_status == Course.ReviewStatus.PENDING

    def test_response_contains_submitted_course_fields(
        self,
        api_client: APIClient,
        instructor_user,
        instructor_course,
        url,
    ):
        # Arrange
        instructor_course.review_status = Course.ReviewStatus.NOT_SUBMITTED
        instructor_course.status = Course.Status.DRAFT
        instructor_course.save(
            update_fields=["review_status", "status"],
        )

        api_client.force_authenticate(user=instructor_user)

        # Act
        response = api_client.post(url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        assert response.data["id"] == instructor_course.pk
        assert response.data["status"] == Course.Status.SUBMITTED
        assert response.data["review_status"] == Course.ReviewStatus.PENDING

    def test_response_does_not_contain_unexpected_submission_fields(
        self,
        api_client: APIClient,
        instructor_user,
        instructor_course,
        url,
    ):
        # Arrange
        instructor_course.review_status = Course.ReviewStatus.NOT_SUBMITTED
        instructor_course.status = Course.Status.DRAFT
        instructor_course.save(
            update_fields=["review_status", "status"],
        )

        api_client.force_authenticate(user=instructor_user)

        # Act
        response = api_client.post(url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert set(response.data.keys()) == {
            "id",
            "status",
            "review_status",
        }

    def test_submit_does_not_require_request_body(
        self,
        api_client: APIClient,
        instructor_user,
        instructor_course,
        url,
    ):
        # Arrange
        instructor_course.review_status = Course.ReviewStatus.NOT_SUBMITTED
        instructor_course.status = Course.Status.DRAFT
        instructor_course.save(
            update_fields=["review_status", "status"],
        )

        api_client.force_authenticate(user=instructor_user)

        # Act
        response = api_client.post(url, data={})

        # Assert
        assert response.status_code == status.HTTP_200_OK

        instructor_course.refresh_from_db()

        assert instructor_course.status == Course.Status.SUBMITTED
        assert instructor_course.review_status == Course.ReviewStatus.PENDING

    @pytest.mark.parametrize(
        "method",
        ["get", "put", "patch", "delete"],
    )
    def test_unsupported_http_methods_return_405(
        self,
        api_client: APIClient,
        instructor_user,
        instructor_course,
        url,
        method,
    ):
        # Arrange
        instructor_course.review_status = Course.ReviewStatus.NOT_SUBMITTED
        instructor_course.status = Course.Status.DRAFT
        instructor_course.save(
            update_fields=["review_status", "status"],
        )

        api_client.force_authenticate(user=instructor_user)

        # Act
        response = getattr(api_client, method)(url)

        # Assert
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        instructor_course.refresh_from_db()

        assert instructor_course.review_status == (Course.ReviewStatus.NOT_SUBMITTED)
        assert instructor_course.status == Course.Status.DRAFT

    def test_unsupported_method_does_not_change_course(
        self,
        api_client: APIClient,
        instructor_user,
        instructor_course,
        url,
    ):
        # Arrange
        instructor_course.review_status = Course.ReviewStatus.CHANGES_REQUESTED
        instructor_course.status = Course.Status.DRAFT
        instructor_course.save(
            update_fields=["review_status", "status"],
        )

        api_client.force_authenticate(user=instructor_user)

        # Act
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        instructor_course.refresh_from_db()

        assert instructor_course.review_status == Course.ReviewStatus.CHANGES_REQUESTED
        assert instructor_course.status == Course.Status.DRAFT

    def test_submit_url_resolves_to_course_submit_view(
        self,
        instructor_course,
    ):
        # Arrange
        url = reverse(
            "instructor_api:submit_course",
            kwargs={"course_id": instructor_course.pk},
        )

        # Act
        match = resolve(url)

        # Assert
        assert match.url_name == "submit_course"
        assert match.func.view_class.__name__ == "CourseSubmitApiView"

    def test_submit_url_contains_course_id(
        self,
        instructor_course,
    ):
        # Arrange
        url = reverse(
            "instructor_api:submit_course",
            kwargs={"course_id": instructor_course.pk},
        )

        # Assert
        assert url.endswith(
            f"/courses/{instructor_course.pk}/submit/",
        )
