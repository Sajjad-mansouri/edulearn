# instructors/tests/api/views/test_courses.py

import pytest
from django.urls import resolve, reverse
from rest_framework import serializers, status
from rest_framework.test import APIRequestFactory

from instructors.api.serializers import InstructorFilterCoursesSerializer
from instructors.api.views import InstructorFilterCoursesApiView


@pytest.mark.django_db
class TestInstructorFilterCoursesApiView:
    def test_unauthenticated_user_cannot_access_courses(
        self,
        api_client,
    ):
        url = reverse("instructor_api:instructor_filter_courses")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_student_cannot_access_courses(
        self,
        api_client,
        student_user,
    ):
        api_client.force_authenticate(user=student_user)

        url = reverse("instructor_api:instructor_filter_courses")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_instructor_can_access_courses(
        self,
        api_client,
        instructor_user,
    ):
        api_client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:instructor_filter_courses")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_get_object_returns_authenticated_user(
        self,
        instructor_user,
    ):
        factory = APIRequestFactory()
        request = factory.get(reverse("instructor_api:instructor_filter_courses"))
        request.user = instructor_user

        view = InstructorFilterCoursesApiView()
        view.request = request

        result = view.get_object()

        assert result == instructor_user

    def test_get_object_does_not_return_another_user(
        self,
        instructor_user,
        student_user,
    ):
        factory = APIRequestFactory()
        request = factory.get(reverse("instructor_api:instructor_filter_courses"))
        request.user = instructor_user

        view = InstructorFilterCoursesApiView()
        view.request = request

        result = view.get_object()

        assert result != student_user

    def test_uses_expected_serializer(
        self,
        instructor_user,
    ):
        factory = APIRequestFactory()
        request = factory.get(reverse("instructor_api:instructor_filter_courses"))
        request.user = instructor_user

        view = InstructorFilterCoursesApiView()
        view.request = request

        assert view.get_serializer_class() is InstructorFilterCoursesSerializer

    def test_returns_only_authenticated_instructors_courses(
        self,
        api_client,
        instructor_user,
        instructor_course,
    ):
        api_client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:instructor_filter_courses")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["courses"] == {
            instructor_course.slug: instructor_course.title,
        }

    def test_response_contains_courses_key(
        self,
        api_client,
        instructor_user,
    ):
        api_client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:instructor_filter_courses")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "courses" in response.data

    def test_courses_is_returned_as_slug_to_title_mapping(
        self,
        api_client,
        instructor_user,
        instructor_course,
    ):
        api_client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:instructor_filter_courses")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        courses = response.data["courses"]

        assert courses[instructor_course.slug] == instructor_course.title
        assert all(
            isinstance(slug, str) and isinstance(title, str)
            for slug, title in courses.items()
        )

    def test_instructor_with_no_courses_gets_empty_mapping(
        self,
        api_client,
        instructor_user,
    ):
        api_client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:instructor_filter_courses")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"courses": {}}

    def test_serializer_returns_owned_courses_as_slug_to_title_mapping(
        self,
        instructor_user,
        instructor_course,
    ):
        serializer = InstructorFilterCoursesSerializer(
            instance=instructor_user,
        )

        data = serializer.data

        assert data["courses"] == {
            instructor_course.slug: instructor_course.title,
        }

    def test_serializer_returns_empty_mapping_without_courses(
        self,
        instructor_user,
    ):
        serializer = InstructorFilterCoursesSerializer(
            instance=instructor_user,
        )

        data = serializer.data

        assert data == {"courses": {}}

    def test_serializer_contains_only_courses_field(self):
        serializer = InstructorFilterCoursesSerializer()

        assert list(serializer.fields) == ["courses"]

    def test_courses_field_is_serializer_method_field(self):
        serializer = InstructorFilterCoursesSerializer()

        field = serializer.fields["courses"]

        assert isinstance(
            field,
            serializers.SerializerMethodField,
        )

    def test_url_resolves_to_expected_view(self):
        url = reverse("instructor_api:instructor_filter_courses")

        match = resolve(url)

        assert match.func.view_class is InstructorFilterCoursesApiView

    def test_url_has_expected_path(self):
        url = reverse("instructor_api:instructor_filter_courses")

        assert url.endswith("/courses/compact/")

    def test_post_method_is_not_allowed(
        self,
        api_client,
        instructor_user,
    ):
        api_client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:instructor_filter_courses")

        response = api_client.post(url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_put_method_is_not_allowed(
        self,
        api_client,
        instructor_user,
    ):
        api_client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:instructor_filter_courses")

        response = api_client.put(url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_patch_method_is_not_allowed(
        self,
        api_client,
        instructor_user,
    ):
        api_client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:instructor_filter_courses")

        response = api_client.patch(url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_delete_method_is_not_allowed(
        self,
        api_client,
        instructor_user,
    ):
        api_client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:instructor_filter_courses")

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
