import pytest
from rest_framework.test import APIRequestFactory

from accounts.models import Role
from instructors.api.permissions import IsInstructor


@pytest.mark.django_db
class TestIsInstructor:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.permission = IsInstructor()
        self.factory = APIRequestFactory()

    def test_allows_authenticated_instructor(self, instructor_user):
        request = self.factory.get("/")
        request.user = instructor_user

        result = self.permission.has_permission(request, view=None)

        assert result is True

    def test_denies_unauthenticated_user(self):
        request = self.factory.get("/")
        request.user = None

        result = self.permission.has_permission(request, view=None)

        assert result is False

    def test_denies_authenticated_non_instructor(self, student_user):
        request = self.factory.get("/")
        request.user = student_user

        result = self.permission.has_permission(request, view=None)

        assert result is False

    def test_allows_user_with_multiple_roles(self, student_user):
        instructor_role, _ = Role.objects.get_or_create(
            name=Role.Roles.INSTRUCTOR,
        )
        student_user.roles.add(instructor_role)

        request = self.factory.get("/")
        request.user = student_user

        result = self.permission.has_permission(request, view=None)

        assert result is True

    def test_message(self):
        assert (
            self.permission.message
            == "You must be an instructor to access this resource."
        )
