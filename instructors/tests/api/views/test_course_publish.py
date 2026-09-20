import pytest
from django.urls import resolve, reverse
from rest_framework import status
from rest_framework.test import APIClient

from courses.models import Course

pytestmark = pytest.mark.django_db


class TestCoursePublishApiView:
    @pytest.fixture
    def url(self, instructor_course):
        return reverse(
            "instructor_api:publish_course",
            kwargs={"course_id": instructor_course.pk},
        )

    def test_unauthenticated_user_cannot_publish_course(
        self,
        api_client: APIClient,
        instructor_course,
        url,
    ):
        # Arrange
        instructor_course.review_status = Course.ReviewStatus.APPROVED
        instructor_course.status = Course.Status.SUBMITTED
        instructor_course.save(
            update_fields=["review_status", "status"],
        )

        # Act
        response = api_client.post(url)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        instructor_course.refresh_from_db()

        assert instructor_course.status == Course.Status.SUBMITTED
        assert instructor_course.review_status == Course.ReviewStatus.APPROVED

    def test_non_instructor_user_cannot_publish_course(
        self,
        api_client: APIClient,
        student_user,
        instructor_course,
        url,
    ):
        # Arrange
        instructor_course.review_status = Course.ReviewStatus.APPROVED
        instructor_course.status = Course.Status.SUBMITTED
        instructor_course.save(
            update_fields=["review_status", "status"],
        )

        api_client.force_authenticate(user=student_user)

        # Act
        response = api_client.post(url)

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

        instructor_course.refresh_from_db()

        assert instructor_course.status == Course.Status.SUBMITTED
        assert instructor_course.review_status == Course.ReviewStatus.APPROVED

    def test_instructor_can_publish_approved_submitted_course(
        self,
        api_client: APIClient,
        instructor_user,
        instructor_course,
        url,
    ):
        # Arrange
        instructor_course.review_status = Course.ReviewStatus.APPROVED
        instructor_course.status = Course.Status.SUBMITTED
        instructor_course.save(
            update_fields=["review_status", "status"],
        )

        api_client.force_authenticate(user=instructor_user)

        # Act
        response = api_client.post(url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        instructor_course.refresh_from_db()

        assert instructor_course.status == Course.Status.PUBLISHED
        assert instructor_course.review_status == Course.ReviewStatus.APPROVED

    @pytest.mark.parametrize(
        "review_status",
        [
            Course.ReviewStatus.NOT_SUBMITTED,
            Course.ReviewStatus.PENDING,
            Course.ReviewStatus.UNDER_REVIEW,
            Course.ReviewStatus.CHANGES_REQUESTED,
            Course.ReviewStatus.REJECTED,
        ],
    )
    def test_course_with_non_approved_review_status_cannot_be_published(
        self,
        api_client: APIClient,
        instructor_user,
        instructor_course,
        review_status,
        url,
    ):
        # Arrange
        instructor_course.review_status = review_status
        instructor_course.status = Course.Status.SUBMITTED
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
        assert instructor_course.status == Course.Status.SUBMITTED

    @pytest.mark.parametrize(
        "course_status",
        [
            Course.Status.DRAFT,
            Course.Status.UPDATED,
            Course.Status.ARCHIVED,
        ],
    )
    def test_approved_course_with_non_submitted_status_cannot_be_published(
        self,
        api_client: APIClient,
        instructor_user,
        instructor_course,
        course_status,
        url,
    ):
        # Arrange
        instructor_course.review_status = Course.ReviewStatus.APPROVED
        instructor_course.status = course_status
        instructor_course.save(
            update_fields=["review_status", "status"],
        )

        api_client.force_authenticate(user=instructor_user)

        # Act
        response = api_client.post(url)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

        instructor_course.refresh_from_db()

        assert instructor_course.review_status == Course.ReviewStatus.APPROVED
        assert instructor_course.status == course_status

    def test_instructor_cannot_publish_course_owned_by_another_instructor(
        self,
        api_client: APIClient,
        instructor_user,
        instructor_course,
    ):
        # Arrange
        another_instructor = type(instructor_user).objects.create_user(
            username="another_instructor",
            email="another_instructor@example.com",
            password="test-password",
        )

        instructor_course.owner = another_instructor
        instructor_course.review_status = Course.ReviewStatus.APPROVED
        instructor_course.status = Course.Status.SUBMITTED
        instructor_course.save(
            update_fields=["owner", "review_status", "status"],
        )

        url = reverse(
            "instructor_api:publish_course",
            kwargs={"course_id": instructor_course.pk},
        )

        api_client.force_authenticate(user=instructor_user)

        # Act
        response = api_client.post(url)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

        instructor_course.refresh_from_db()

        assert instructor_course.owner_id == another_instructor.pk
        assert instructor_course.review_status == Course.ReviewStatus.APPROVED
        assert instructor_course.status == Course.Status.SUBMITTED

    def test_nonexistent_course_returns_404(
        self,
        api_client: APIClient,
        instructor_user,
    ):
        # Arrange
        nonexistent_course_id = 999999

        url = reverse(
            "instructor_api:publish_course",
            kwargs={"course_id": nonexistent_course_id},
        )

        api_client.force_authenticate(user=instructor_user)

        # Act
        response = api_client.post(url)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_publishing_changes_only_course_status(
        self,
        api_client: APIClient,
        instructor_user,
        instructor_course,
        url,
    ):
        # Arrange
        instructor_course.review_status = Course.ReviewStatus.APPROVED
        instructor_course.status = Course.Status.SUBMITTED

        original_id = instructor_course.pk
        original_owner_id = instructor_course.owner_id
        original_title = instructor_course.title

        instructor_course.save(
            update_fields=["review_status", "status"],
        )

        api_client.force_authenticate(user=instructor_user)

        # Act
        response = api_client.post(url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        instructor_course.refresh_from_db()

        assert instructor_course.pk == original_id
        assert instructor_course.owner_id == original_owner_id
        assert instructor_course.title == original_title

        assert instructor_course.status == Course.Status.PUBLISHED
        assert instructor_course.review_status == Course.ReviewStatus.APPROVED

    def test_response_contains_expected_fields(
        self,
        api_client: APIClient,
        instructor_user,
        instructor_course,
        url,
    ):
        # Arrange
        instructor_course.review_status = Course.ReviewStatus.APPROVED
        instructor_course.status = Course.Status.SUBMITTED
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

    def test_response_contains_published_status(
        self,
        api_client: APIClient,
        instructor_user,
        instructor_course,
        url,
    ):
        # Arrange
        instructor_course.review_status = Course.ReviewStatus.APPROVED
        instructor_course.status = Course.Status.SUBMITTED
        instructor_course.save(
            update_fields=["review_status", "status"],
        )

        api_client.force_authenticate(user=instructor_user)

        # Act
        response = api_client.post(url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == instructor_course.pk
        assert response.data["status"] == Course.Status.PUBLISHED
        assert response.data["review_status"] == Course.ReviewStatus.APPROVED

    def test_request_body_is_not_required(
        self,
        api_client: APIClient,
        instructor_user,
        instructor_course,
        url,
    ):
        # Arrange
        instructor_course.review_status = Course.ReviewStatus.APPROVED
        instructor_course.status = Course.Status.SUBMITTED
        instructor_course.save(
            update_fields=["review_status", "status"],
        )

        api_client.force_authenticate(user=instructor_user)

        # Act
        response = api_client.post(url, data={})

        # Assert
        assert response.status_code == status.HTTP_200_OK

        instructor_course.refresh_from_db()

        assert instructor_course.status == Course.Status.PUBLISHED
        assert instructor_course.review_status == Course.ReviewStatus.APPROVED

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
        instructor_course.review_status = Course.ReviewStatus.APPROVED
        instructor_course.status = Course.Status.SUBMITTED
        instructor_course.save(
            update_fields=["review_status", "status"],
        )

        api_client.force_authenticate(user=instructor_user)

        # Act
        response = getattr(api_client, method)(url)

        # Assert
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        instructor_course.refresh_from_db()

        assert instructor_course.status == Course.Status.SUBMITTED
        assert instructor_course.review_status == Course.ReviewStatus.APPROVED

    def test_unsupported_method_does_not_modify_course(
        self,
        api_client: APIClient,
        instructor_user,
        instructor_course,
        url,
    ):
        # Arrange
        instructor_course.review_status = Course.ReviewStatus.APPROVED
        instructor_course.status = Course.Status.SUBMITTED
        instructor_course.save(
            update_fields=["review_status", "status"],
        )

        api_client.force_authenticate(user=instructor_user)

        # Act
        response = api_client.patch(url)

        # Assert
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        instructor_course.refresh_from_db()

        assert instructor_course.status == Course.Status.SUBMITTED
        assert instructor_course.review_status == Course.ReviewStatus.APPROVED

    def test_publish_url_resolves_to_course_publish_view(
        self,
        instructor_course,
    ):
        # Arrange
        url = reverse(
            "instructor_api:publish_course",
            kwargs={"course_id": instructor_course.pk},
        )

        # Act
        match = resolve(url)

        # Assert
        assert match.url_name == "publish_course"
        assert match.func.view_class.__name__ == "CoursePublishApiView"

    def test_publish_url_contains_course_id(
        self,
        instructor_course,
    ):
        # Arrange
        url = reverse(
            "instructor_api:publish_course",
            kwargs={"course_id": instructor_course.pk},
        )

        # Assert
        assert url.endswith(
            f"/courses/{instructor_course.pk}/publish/",
        )
