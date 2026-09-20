import pytest
from django.urls import reverse
from rest_framework import status

from courses.models import Course

pytestmark = pytest.mark.django_db


class TestCourseDeleteApiView:
    @pytest.fixture
    def url(self, instructor_course):
        return reverse(
            "instructor_api:course_delete",
            kwargs={"pk": instructor_course.pk},
        )

    def test_unauthenticated_user_cannot_delete_course(
        self,
        api_client,
        url,
    ):
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_non_instructor_user_cannot_delete_course(
        self,
        api_client,
        student_user,
        url,
    ):
        api_client.force_authenticate(user=student_user)

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == (
            "You must be an instructor to access this resource."
        )

    def test_instructor_can_delete_owned_course(
        self,
        api_client,
        instructor_user,
        instructor_course,
        url,
    ):
        api_client.force_authenticate(user=instructor_user)

        course_id = instructor_course.pk

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.data is None

        assert not Course.objects.filter(pk=course_id).exists()

    def test_delete_removes_course_from_database(
        self,
        api_client,
        instructor_user,
        instructor_course,
        url,
    ):
        api_client.force_authenticate(user=instructor_user)

        assert Course.objects.filter(pk=instructor_course.pk).exists()

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Course.objects.filter(pk=instructor_course.pk).exists()

    def test_instructor_cannot_delete_course_owned_by_another_instructor(
        self,
        api_client,
        instructor_user,
        instructor_course,
    ):
        another_instructor = type(instructor_user).objects.create_user(
            username="another_instructor",
            email="another_instructor@example.com",
            password="test-password",
        )

        another_course = Course.objects.create(
            owner=another_instructor,
            title="Another Instructor Course",
            slug="another-instructor-course",
        )

        url = reverse(
            "instructor_api:course_delete",
            kwargs={"pk": another_course.pk},
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Course.objects.filter(pk=another_course.pk).exists()

    def test_instructor_cannot_delete_nonexistent_course(
        self,
        api_client,
        instructor_user,
    ):
        nonexistent_pk = 999999

        url = reverse(
            "instructor_api:course_delete",
            kwargs={"pk": nonexistent_pk},
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize(
        "review_status",
        [
            Course.ReviewStatus.PENDING,
            Course.ReviewStatus.UNDER_REVIEW,
        ],
    )
    def test_course_under_review_cannot_be_deleted(
        self,
        api_client,
        instructor_user,
        instructor_course,
        review_status,
    ):
        instructor_course.review_status = review_status
        instructor_course.save(update_fields=["review_status"])

        url = reverse(
            "instructor_api:course_delete",
            kwargs={"pk": instructor_course.pk},
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Course.objects.filter(pk=instructor_course.pk).exists()

    @pytest.mark.parametrize(
        "review_status",
        [
            Course.ReviewStatus.NOT_SUBMITTED,
            Course.ReviewStatus.APPROVED,
            Course.ReviewStatus.CHANGES_REQUESTED,
            Course.ReviewStatus.REJECTED,
        ],
    )
    def test_course_with_deletable_review_status_can_be_deleted(
        self,
        api_client,
        instructor_user,
        instructor_course,
        review_status,
    ):
        instructor_course.review_status = review_status
        instructor_course.save(update_fields=["review_status"])

        url = reverse(
            "instructor_api:course_delete",
            kwargs={"pk": instructor_course.pk},
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Course.objects.filter(pk=instructor_course.pk).exists()

    def test_pending_course_is_not_deleted(
        self,
        api_client,
        instructor_user,
        instructor_course,
    ):
        instructor_course.review_status = Course.ReviewStatus.PENDING
        instructor_course.save(update_fields=["review_status"])

        course_id = instructor_course.pk

        url = reverse(
            "instructor_api:course_delete",
            kwargs={"pk": course_id},
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

        assert Course.objects.filter(pk=course_id).exists()

    def test_under_review_course_is_not_deleted(
        self,
        api_client,
        instructor_user,
        instructor_course,
    ):
        instructor_course.review_status = Course.ReviewStatus.UNDER_REVIEW
        instructor_course.save(update_fields=["review_status"])

        course_id = instructor_course.pk

        url = reverse(
            "instructor_api:course_delete",
            kwargs={"pk": course_id},
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

        assert Course.objects.filter(pk=course_id).exists()

    @pytest.mark.parametrize(
        "method",
        [
            "get",
            "post",
            "put",
            "patch",
        ],
    )
    def test_unsupported_http_methods_return_405(
        self,
        api_client,
        instructor_user,
        instructor_course,
        method,
    ):
        url = reverse(
            "instructor_api:course_delete",
            kwargs={"pk": instructor_course.pk},
        )

        api_client.force_authenticate(user=instructor_user)

        response = getattr(api_client, method)(url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_unsupported_method_does_not_delete_course(
        self,
        api_client,
        instructor_user,
        instructor_course,
    ):
        url = reverse(
            "instructor_api:course_delete",
            kwargs={"pk": instructor_course.pk},
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.patch(
            url,
            {"title": "Changed title"},
            format="json",
        )

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert Course.objects.filter(pk=instructor_course.pk).exists()

    def test_delete_url_resolves_correctly(
        self,
        instructor_course,
    ):
        url = reverse(
            "instructor_api:course_delete",
            kwargs={"pk": instructor_course.pk},
        )

        assert url.endswith(f"/courses/{instructor_course.pk}/delete/")

    def test_delete_only_affects_requested_course(
        self,
        api_client,
        instructor_user,
        instructor_course,
    ):
        another_course = Course.objects.create(
            owner=instructor_user,
            title="Another Course",
            slug="another-course",
        )

        url = reverse(
            "instructor_api:course_delete",
            kwargs={"pk": instructor_course.pk},
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        assert not Course.objects.filter(
            pk=instructor_course.pk,
        ).exists()

        assert Course.objects.filter(
            pk=another_course.pk,
        ).exists()
