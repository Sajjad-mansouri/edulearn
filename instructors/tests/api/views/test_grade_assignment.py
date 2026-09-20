from django.urls import resolve, reverse
from rest_framework import status
from rest_framework.test import APIRequestFactory

from instructors.api.serializers import GradeSerializer
from instructors.api.views import GradeAssignmentApiView


class TestGradeAssignmentApiView:
    def test_unauthenticated_user_cannot_grade_assignment(
        self,
        api_client,
    ):
        # Arrange
        url = reverse(
            "instructor_api:grade_assignment",
            kwargs={"pk": 1},
        )

        # Act
        response = api_client.patch(
            url,
            {
                "score": "80.00",
                "feedback": "Good work.",
            },
            format="json",
        )

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_student_cannot_grade_assignment(
        self,
        api_client,
        student_user,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        url = reverse(
            "instructor_api:grade_assignment",
            kwargs={"pk": 1},
        )

        # Act
        response = api_client.patch(
            url,
            {
                "score": "80.00",
                "feedback": "Good work.",
            },
            format="json",
        )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_view_uses_grade_serializer(self):
        # Arrange
        view = GradeAssignmentApiView()

        # Act
        serializer_class = view.serializer_class

        # Assert
        assert serializer_class is GradeSerializer

    def test_view_uses_instructor_permission(self):
        # Arrange
        view = GradeAssignmentApiView()

        # Act
        permission_classes = view.permission_classes

        # Assert
        permission_class_names = {
            permission_class.__name__ for permission_class in permission_classes
        }

        # Assert
        assert "IsInstructor" in permission_class_names

    def test_get_queryset_returns_assignment_submission_queryset(
        self,
        instructor_user,
    ):
        # Arrange
        factory = APIRequestFactory()
        request = factory.get(
            reverse(
                "instructor_api:grade_assignment",
                kwargs={"pk": 1},
            )
        )
        request.user = instructor_user

        view = GradeAssignmentApiView()
        view.request = request

        # Act
        queryset = view.get_queryset()

        # Assert
        assert queryset.model._meta.model_name == "assignmentsubmission"

    def test_get_queryset_filters_by_authenticated_user(
        self,
        instructor_user,
    ):
        # Arrange
        factory = APIRequestFactory()
        request = factory.get(
            reverse(
                "instructor_api:grade_assignment",
                kwargs={"pk": 1},
            )
        )
        request.user = instructor_user

        view = GradeAssignmentApiView()
        view.request = request

        # Act
        queryset = view.get_queryset()

        # Assert
        sql = str(queryset.query)

        assert "owner_id" in sql
        assert str(instructor_user.pk) in sql

    def test_get_queryset_is_filtered_through_course_owner(
        self,
        instructor_user,
    ):
        # Arrange
        factory = APIRequestFactory()
        request = factory.get(
            reverse(
                "instructor_api:grade_assignment",
                kwargs={"pk": 1},
            )
        )
        request.user = instructor_user

        view = GradeAssignmentApiView()
        view.request = request

        # Act
        queryset = view.get_queryset()

        # Assert
        query_string = str(queryset.query)

        assert "owner_id" in query_string

    def test_get_queryset_is_not_unrestricted(
        self,
        instructor_user,
    ):
        # Arrange
        factory = APIRequestFactory()
        request = factory.get(
            reverse(
                "instructor_api:grade_assignment",
                kwargs={"pk": 1},
            )
        )
        request.user = instructor_user

        view = GradeAssignmentApiView()
        view.request = request

        # Act
        queryset = view.get_queryset()

        # Assert
        assert queryset.query.where.children

    def test_nonexistent_submission_returns_not_found(
        self,
        api_client,
        instructor_user,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)

        url = reverse(
            "instructor_api:grade_assignment",
            kwargs={"pk": 999999999},
        )

        # Act
        response = api_client.patch(
            url,
            {
                "score": "80.00",
                "feedback": "Good work.",
            },
            format="json",
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_method_is_not_supported(
        self,
        api_client,
        instructor_user,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)

        url = reverse(
            "instructor_api:grade_assignment",
            kwargs={"pk": 1},
        )

        # Act
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_post_method_is_not_supported(
        self,
        api_client,
        instructor_user,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)

        url = reverse(
            "instructor_api:grade_assignment",
            kwargs={"pk": 1},
        )

        # Act
        response = api_client.post(
            url,
            {
                "score": "80.00",
                "feedback": "Good work.",
            },
            format="json",
        )

        # Assert
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_delete_method_is_not_supported(
        self,
        api_client,
        instructor_user,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)

        url = reverse(
            "instructor_api:grade_assignment",
            kwargs={"pk": 1},
        )

        # Act
        response = api_client.delete(url)

        # Assert
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_grade_assignment_url_resolves_to_correct_view(self):
        # Arrange
        url = reverse(
            "instructor_api:grade_assignment",
            kwargs={"pk": 1},
        )

        # Act
        match = resolve(url)

        # Assert
        assert match.func.view_class is GradeAssignmentApiView

    def test_grade_assignment_url_contains_submission_pk(self):
        # Arrange
        url = reverse(
            "instructor_api:grade_assignment",
            kwargs={"pk": 123},
        )

        # Act
        match = resolve(url)

        # Assert
        assert match.kwargs == {"pk": 123}

    def test_grade_assignment_url_uses_expected_path(self):
        # Arrange
        url = reverse(
            "instructor_api:grade_assignment",
            kwargs={"pk": 123},
        )

        # Act
        normalized_url = url.rstrip("/")

        # Assert
        assert normalized_url.endswith("/assignments/grade/123")
