from django.urls import resolve, reverse
from rest_framework import status
from rest_framework.test import APIRequestFactory

from instructors.api.serializers import InstructorDashboardSerializer
from instructors.api.views import InstructorStudentsApiView


class TestInstructorStudentsApiView:
    def test_unauthenticated_user_cannot_access_students_dashboard(
        self,
        api_client,
    ):
        # Arrange
        url = reverse("instructor_api:students")

        # Act
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_student_cannot_access_students_dashboard(
        self,
        api_client,
        student_user,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)
        url = reverse("instructor_api:students")

        # Act
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_instructor_can_access_students_dashboard(
        self,
        api_client,
        instructor_user,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)
        url = reverse("instructor_api:students")

        # Act
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

    def test_authenticated_instructor_gets_successful_response(
        self,
        api_client,
        instructor_user,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)
        url = reverse("instructor_api:students")

        # Act
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data is not None

    def test_get_object_returns_authenticated_user(
        self,
        instructor_user,
    ):
        # Arrange
        factory = APIRequestFactory()
        request = factory.get(
            reverse("instructor_api:students"),
        )
        request.user = instructor_user

        view = InstructorStudentsApiView()
        view.request = request

        # Act
        result = view.get_object()

        # Assert
        assert result == instructor_user

    def test_get_object_returns_authenticated_user_not_student(
        self,
        instructor_user,
        student_user,
    ):
        # Arrange
        factory = APIRequestFactory()
        request = factory.get(
            reverse("instructor_api:students"),
        )
        request.user = instructor_user

        view = InstructorStudentsApiView()
        view.request = request

        # Act
        result = view.get_object()

        # Assert
        assert result == instructor_user
        assert result != student_user

    def test_get_object_does_not_query_for_another_user(
        self,
        instructor_user,
        student_user,
    ):
        # Arrange
        factory = APIRequestFactory()
        request = factory.get(
            reverse("instructor_api:students"),
        )
        request.user = instructor_user

        view = InstructorStudentsApiView()
        view.request = request

        # Act
        result = view.get_object()

        # Assert
        assert result.pk == instructor_user.pk
        assert result.pk != student_user.pk

    def test_serializer_class_is_instructor_dashboard_serializer(self):
        # Arrange
        view = InstructorStudentsApiView()

        # Act
        serializer_class = view.serializer_class

        # Assert
        assert serializer_class is InstructorDashboardSerializer

    def test_permission_classes_are_configured(self):
        # Arrange
        view = InstructorStudentsApiView()

        # Act
        permission_classes = view.permission_classes

        # Assert
        assert permission_classes

        permission_class_names = {
            permission_class.__name__ for permission_class in permission_classes
        }

        assert "IsInstructor" in permission_class_names

    def test_students_url_resolves_to_correct_view(self):
        # Arrange
        url = reverse("instructor_api:students")

        # Act
        match = resolve(url)

        # Assert
        assert match.func.view_class is InstructorStudentsApiView

    def test_students_url_has_no_url_parameters(self):
        # Arrange
        url = reverse("instructor_api:students")

        # Act
        match = resolve(url)

        # Assert
        assert match.kwargs == {}

    def test_students_url_does_not_require_primary_key(self):
        # Arrange
        url = reverse("instructor_api:students")

        # Act
        match = resolve(url)

        # Assert
        assert "pk" not in match.kwargs

    def test_students_url_uses_expected_path(self):
        # Arrange
        url = reverse("instructor_api:students")

        # Act
        normalized_url = url.rstrip("/")

        # Assert
        assert normalized_url.endswith("/students")

    def test_get_object_ignores_url_kwargs(
        self,
        instructor_user,
    ):
        # Arrange
        factory = APIRequestFactory()
        request = factory.get(
            reverse("instructor_api:students"),
        )
        request.user = instructor_user

        view = InstructorStudentsApiView()
        view.request = request
        view.kwargs = {"pk": 999999}

        # Act
        result = view.get_object()

        # Assert
        assert result == instructor_user

    def test_get_object_returns_same_user_on_repeated_calls(
        self,
        instructor_user,
    ):
        # Arrange
        factory = APIRequestFactory()
        request = factory.get(
            reverse("instructor_api:students"),
        )
        request.user = instructor_user

        view = InstructorStudentsApiView()
        view.request = request

        # Act
        first_result = view.get_object()
        second_result = view.get_object()

        # Assert
        assert first_result == instructor_user
        assert second_result == instructor_user
        assert first_result == second_result

    def test_student_cannot_access_dashboard_even_when_authenticated(
        self,
        api_client,
        student_user,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)
        url = reverse("instructor_api:students")

        # Act
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_instructor_dashboard_endpoint_uses_get_method(
        self,
        api_client,
        instructor_user,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)
        url = reverse("instructor_api:students")

        # Act
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

    def test_post_method_is_not_supported(
        self,
        api_client,
        instructor_user,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)
        url = reverse("instructor_api:students")

        # Act
        response = api_client.post(url, {})

        # Assert
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_put_method_is_not_supported(
        self,
        api_client,
        instructor_user,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)
        url = reverse("instructor_api:students")

        # Act
        response = api_client.put(url, {})

        # Assert
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_delete_method_is_not_supported(
        self,
        api_client,
        instructor_user,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)
        url = reverse("instructor_api:students")

        # Act
        response = api_client.delete(url)

        # Assert
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_patch_method_is_not_supported(
        self,
        api_client,
        instructor_user,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)
        url = reverse("instructor_api:students")

        # Act
        response = api_client.patch(url, {})

        # Assert
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
