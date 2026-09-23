from django.urls import resolve, reverse
from rest_framework import status
from rest_framework.test import APIRequestFactory

from instructors.api.serializers import AssignmentSubmissionSerializer
from instructors.api.views import InstructorAssignmentsApiView


class TestInstructorAssignmentsApiView:
    def test_unauthenticated_user_cannot_access_assignments(
        self,
        api_client,
    ):
        # Arrange
        url = reverse("instructor_api:assignments")

        # Act
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_student_cannot_access_instructor_assignments(
        self,
        api_client,
        student_user,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)
        url = reverse("instructor_api:assignments")

        # Act
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_instructor_can_access_assignments(
        self,
        api_client,
        instructor_user,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)
        url = reverse("instructor_api:assignments")

        # Act
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

    def test_get_queryset_filters_by_authenticated_instructor(
        self,
        instructor_user,
    ):
        # Arrange
        factory = APIRequestFactory()
        request = factory.get(
            reverse("instructor_api:assignments"),
        )
        request.user = instructor_user

        view = InstructorAssignmentsApiView()
        view.request = request

        # Act
        queryset = view.get_queryset()

        # Assert
        assert queryset.model.__name__ == "AssignmentSubmission"
        assert queryset.query.where.children

    def test_get_queryset_is_restricted_to_request_users_courses(
        self,
        instructor_user,
    ):
        # Arrange
        factory = APIRequestFactory()
        request = factory.get(
            reverse("instructor_api:assignments"),
        )
        request.user = instructor_user

        view = InstructorAssignmentsApiView()
        view.request = request

        # Act
        queryset = view.get_queryset()

        # Assert
        sql = str(queryset.query)

        assert "owner_id" in sql

    def test_get_queryset_uses_request_user_as_course_owner(
        self,
        instructor_user,
    ):
        # Arrange
        factory = APIRequestFactory()
        request = factory.get(
            reverse("instructor_api:assignments"),
        )
        request.user = instructor_user

        view = InstructorAssignmentsApiView()
        view.request = request

        # Act
        queryset = view.get_queryset()

        # Assert
        query_string = str(queryset.query)

        assert str(instructor_user.pk) in query_string

    def test_get_queryset_returns_assignment_submissions_queryset(
        self,
        instructor_user,
    ):
        # Arrange
        factory = APIRequestFactory()
        request = factory.get(
            reverse("instructor_api:assignments"),
        )
        request.user = instructor_user

        view = InstructorAssignmentsApiView()
        view.request = request

        # Act
        queryset = view.get_queryset()

        # Assert
        assert queryset.model._meta.model_name == "assignmentsubmission"

    def test_serializer_class_is_assignment_submission_serializer(self):
        # Arrange
        view = InstructorAssignmentsApiView()

        # Act
        serializer_class = view.serializer_class

        # Assert
        assert serializer_class is AssignmentSubmissionSerializer

    def test_permission_classes_are_configured(self):
        # Arrange
        view = InstructorAssignmentsApiView()

        # Act
        permission_classes = view.permission_classes

        # Assert
        permission_class_names = {
            permission_class.__name__ for permission_class in permission_classes
        }

        assert "IsInstructor" in permission_class_names

    def test_assignments_url_resolves_to_correct_view(self):
        # Arrange
        url = reverse("instructor_api:assignments")

        # Act
        match = resolve(url)

        # Assert
        assert match.func.view_class is InstructorAssignmentsApiView

    def test_assignments_url_has_no_url_parameters(self):
        # Arrange
        url = reverse("instructor_api:assignments")

        # Act
        match = resolve(url)

        # Assert
        assert match.kwargs == {}

    def test_assignments_url_does_not_require_primary_key(self):
        # Arrange
        url = reverse("instructor_api:assignments")

        # Act
        match = resolve(url)

        # Assert
        assert "pk" not in match.kwargs

    def test_assignments_url_uses_expected_path(self):
        # Arrange
        url = reverse("instructor_api:assignments")

        # Act
        normalized_url = url.rstrip("/")

        # Assert
        assert normalized_url.endswith("/assignments")

    def test_get_request_is_supported(
        self,
        api_client,
        instructor_user,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)
        url = reverse("instructor_api:assignments")

        # Act
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

    def test_post_request_is_not_supported(
        self,
        api_client,
        instructor_user,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)
        url = reverse("instructor_api:assignments")

        # Act
        response = api_client.post(url, {})

        # Assert
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_put_request_is_not_supported(
        self,
        api_client,
        instructor_user,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)
        url = reverse("instructor_api:assignments")

        # Act
        response = api_client.put(url, {})

        # Assert
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_patch_request_is_not_supported(
        self,
        api_client,
        instructor_user,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)
        url = reverse("instructor_api:assignments")

        # Act
        response = api_client.patch(url, {})

        # Assert
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_delete_request_is_not_supported(
        self,
        api_client,
        instructor_user,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)
        url = reverse("instructor_api:assignments")

        # Act
        response = api_client.delete(url)

        # Assert
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
