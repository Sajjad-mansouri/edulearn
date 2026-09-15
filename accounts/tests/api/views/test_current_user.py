import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from accounts.models import Role

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestCurrentUserApiView:
    url = reverse("accounts-api:current_user")

    @pytest.fixture
    def authenticated_client(self, api_client, test_user):
        api_client.force_authenticate(user=test_user)
        return api_client

    @pytest.fixture
    def instructor_role(self, db):
        return Role.objects.create(
            name=Role.Roles.INSTRUCTOR,
        )

    @pytest.fixture
    def student_role(self, db):
        return Role.objects.create(
            name=Role.Roles.STUDENT,
        )

    def test_current_user_requires_authentication(
        self,
        api_client,
    ):
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_current_user_returns_200_for_authenticated_user(
        self,
        authenticated_client,
    ):
        response = authenticated_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK

    def test_current_user_returns_expected_response_fields(
        self,
        authenticated_client,
    ):
        response = authenticated_client.get(self.url)

        assert set(response.data.keys()) == {
            "id",
            "username",
            "email",
            "is_authenticated",
            "is_instructor",
            "is_student",
            "avatar",
            "first_name",
            "last_name",
        }

    def test_current_user_returns_authenticated_user_id(
        self,
        authenticated_client,
        test_user,
    ):
        response = authenticated_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == test_user.id

    def test_current_user_returns_authenticated_username(
        self,
        authenticated_client,
        test_user,
    ):
        response = authenticated_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == test_user.username

    def test_current_user_returns_authenticated_email(
        self,
        authenticated_client,
        test_user,
    ):
        response = authenticated_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == test_user.email

    def test_current_user_returns_authenticated_first_name(
        self,
        authenticated_client,
        test_user,
    ):
        response = authenticated_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == test_user.first_name

    def test_current_user_returns_authenticated_last_name(
        self,
        authenticated_client,
        test_user,
    ):
        response = authenticated_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["last_name"] == test_user.last_name

    def test_current_user_is_authenticated_is_true(
        self,
        authenticated_client,
    ):
        response = authenticated_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_authenticated"] is True

    def test_current_user_is_student_is_false_without_student_role(
        self,
        authenticated_client,
    ):
        response = authenticated_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_student"] is False

    def test_current_user_is_instructor_is_false_without_instructor_role(
        self,
        authenticated_client,
    ):
        response = authenticated_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_instructor"] is False

    def test_current_user_reports_student_role(
        self,
        authenticated_client,
        test_user,
        student_role,
    ):
        student_role.users.add(test_user)

        response = authenticated_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_student"] is True
        assert response.data["is_instructor"] is False

    def test_current_user_reports_instructor_role(
        self,
        authenticated_client,
        test_user,
        instructor_role,
    ):
        instructor_role.users.add(test_user)

        response = authenticated_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_instructor"] is True
        assert response.data["is_student"] is False

    def test_current_user_reports_both_roles(
        self,
        authenticated_client,
        test_user,
        student_role,
        instructor_role,
    ):
        student_role.users.add(test_user)
        instructor_role.users.add(test_user)

        response = authenticated_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_student"] is True
        assert response.data["is_instructor"] is True

    def test_current_user_returns_false_for_roles_not_assigned_to_user(
        self,
        authenticated_client,
        student_role,
        instructor_role,
    ):
        response = authenticated_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_student"] is False
        assert response.data["is_instructor"] is False

    def test_current_user_returns_avatar_field(
        self,
        authenticated_client,
    ):
        response = authenticated_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert "avatar" in response.data

    def test_current_user_returns_null_avatar_when_user_has_no_avatar(
        self,
        authenticated_client,
    ):
        response = authenticated_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["avatar"] is None

    def test_current_user_returns_the_request_user_not_another_user(
        self,
        api_client,
        test_user,
        db,
    ):
        another_user = User.objects.create_user(
            username="another_user",
            email="another_user@example.com",
            password="test-password",
            first_name="Another",
            last_name="User",
        )

        api_client.force_authenticate(user=test_user)

        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == test_user.id
        assert response.data["id"] != another_user.id
        assert response.data["username"] == test_user.username
        assert response.data["username"] != another_user.username
        assert response.data["email"] == test_user.email
        assert response.data["email"] != another_user.email

    def test_current_user_returns_correct_data_after_switching_authenticated_user(
        self,
        api_client,
        test_user,
        db,
    ):
        another_user = User.objects.create_user(
            username="another_user",
            email="another_user@example.com",
            password="test-password",
            first_name="Another",
            last_name="User",
        )

        api_client.force_authenticate(user=test_user)

        first_response = api_client.get(self.url)

        assert first_response.status_code == status.HTTP_200_OK
        assert first_response.data["id"] == test_user.id

        api_client.force_authenticate(user=another_user)

        second_response = api_client.get(self.url)

        assert second_response.status_code == status.HTTP_200_OK
        assert second_response.data["id"] == another_user.id
        assert second_response.data["id"] != test_user.id
        assert second_response.data["username"] == another_user.username
        assert second_response.data["email"] == another_user.email

    def test_current_user_does_not_accept_user_id_from_query_parameters(
        self,
        api_client,
        test_user,
        db,
    ):
        another_user = User.objects.create_user(
            username="another_user",
            email="another_user@example.com",
            password="test-password",
        )

        api_client.force_authenticate(user=test_user)

        response = api_client.get(
            self.url,
            {"id": another_user.id},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == test_user.id
        assert response.data["id"] != another_user.id

    def test_current_user_ignores_unrelated_query_parameters(
        self,
        authenticated_client,
        test_user,
    ):
        response = authenticated_client.get(
            self.url,
            {
                "page": 2,
                "search": "another_user",
                "username": "another_user",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == test_user.id
        assert response.data["username"] == test_user.username

    def test_current_user_does_not_accept_post_request(
        self,
        authenticated_client,
    ):
        response = authenticated_client.post(
            self.url,
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_current_user_does_not_accept_put_request(
        self,
        authenticated_client,
    ):
        response = authenticated_client.put(
            self.url,
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_current_user_does_not_accept_patch_request(
        self,
        authenticated_client,
    ):
        response = authenticated_client.patch(
            self.url,
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_current_user_does_not_accept_delete_request(
        self,
        authenticated_client,
    ):
        response = authenticated_client.delete(self.url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_current_user_does_not_allow_post_for_anonymous_user(
        self,
        api_client,
    ):
        response = api_client.post(
            self.url,
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_current_user_does_not_allow_put_for_anonymous_user(
        self,
        api_client,
    ):
        response = api_client.put(
            self.url,
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_current_user_does_not_allow_patch_for_anonymous_user(
        self,
        api_client,
    ):
        response = api_client.patch(
            self.url,
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_current_user_does_not_allow_delete_for_anonymous_user(
        self,
        api_client,
    ):
        response = api_client.delete(self.url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
