import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestRegisterApiView:
    url = reverse("accounts-api:register")

    def test_register_requires_username(self, api_client):
        response = api_client.post(
            self.url,
            {
                "email": "test_user@example.com",
                "first_name": "Test",
                "last_name": "User",
                "password1": "Strong-password-123!",
                "password2": "Strong-password-123!",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "username" in response.data

    def test_register_accepts_valid_data(
        self,
        api_client,
        mocker,
    ):
        register_user = mocker.patch(
            "accounts.api.views.register_user",
        )

        payload = {
            "username": "test_user",
            "email": "test_user@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password1": "Strong-password-123!",
            "password2": "Strong-password-123!",
        }

        response = api_client.post(
            self.url,
            payload,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        register_user.assert_called_once()

    def test_register_calls_register_user_with_expected_arguments(
        self,
        api_client,
        mocker,
    ):
        register_user = mocker.patch(
            "accounts.api.views.register_user",
        )

        payload = {
            "username": "test_user",
            "email": "test_user@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password1": "Strong-password-123!",
            "password2": "Strong-password-123!",
        }

        api_client.post(
            self.url,
            payload,
            format="json",
        )

        register_user.assert_called_once()

        call_kwargs = register_user.call_args.kwargs

        assert call_kwargs["role_name"] == "student"
        assert call_kwargs["request"].method == "POST"

        assert call_kwargs["data"] == {
            "username": "test_user",
            "email": "test_user@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password1": "Strong-password-123!",
            "password2": "Strong-password-123!",
        }

    def test_register_passes_authenticated_request_to_service(
        self,
        api_client,
        mocker,
        test_user,
    ):
        register_user = mocker.patch(
            "accounts.api.views.register_user",
        )

        api_client.force_authenticate(user=test_user)

        payload = {
            "username": "new_user",
            "email": "new_user@example.com",
            "first_name": "New",
            "last_name": "User",
            "password1": "Strong-password-123!",
            "password2": "Strong-password-123!",
        }

        response = api_client.post(
            self.url,
            payload,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        request = register_user.call_args.kwargs["request"]

        assert request.user == test_user

    def test_register_allows_anonymous_users(
        self,
        api_client,
        mocker,
    ):
        register_user = mocker.patch(
            "accounts.api.views.register_user",
        )

        payload = {
            "username": "test_user",
            "email": "test_user@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password1": "Strong-password-123!",
            "password2": "Strong-password-123!",
        }

        response = api_client.post(
            self.url,
            payload,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert register_user.call_count == 1

        request = register_user.call_args.kwargs["request"]

        assert request.user.is_anonymous

    def test_register_rejects_mismatched_passwords(
        self,
        api_client,
        mocker,
    ):
        register_user = mocker.patch(
            "accounts.api.views.register_user",
        )

        payload = {
            "username": "test_user",
            "email": "test_user@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password1": "Strong-password-123!",
            "password2": "Different-password-123!",
        }

        response = api_client.post(
            self.url,
            payload,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["password2"] == ["Passwords do not match."]

        register_user.assert_not_called()

    def test_register_rejects_invalid_email(
        self,
        api_client,
        mocker,
    ):
        register_user = mocker.patch(
            "accounts.api.views.register_user",
        )

        payload = {
            "username": "test_user",
            "email": "not-an-email",
            "first_name": "Test",
            "last_name": "User",
            "password1": "Strong-password-123!",
            "password2": "Strong-password-123!",
        }

        response = api_client.post(
            self.url,
            payload,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

        register_user.assert_not_called()

    def test_register_rejects_missing_password1(
        self,
        api_client,
        mocker,
    ):
        register_user = mocker.patch(
            "accounts.api.views.register_user",
        )

        payload = {
            "username": "test_user",
            "email": "test_user@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password2": "Strong-password-123!",
        }

        response = api_client.post(
            self.url,
            payload,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password1" in response.data

        register_user.assert_not_called()

    def test_register_rejects_missing_password2(
        self,
        api_client,
        mocker,
    ):
        register_user = mocker.patch(
            "accounts.api.views.register_user",
        )

        payload = {
            "username": "test_user",
            "email": "test_user@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password1": "Strong-password-123!",
        }

        response = api_client.post(
            self.url,
            payload,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password2" in response.data

        register_user.assert_not_called()

    def test_register_rejects_empty_request(
        self,
        api_client,
        mocker,
    ):
        register_user = mocker.patch(
            "accounts.api.views.register_user",
        )

        response = api_client.post(
            self.url,
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "username" in response.data
        assert "password1" in response.data
        assert "password2" in response.data

        register_user.assert_not_called()

    def test_register_rejects_unsupported_http_method(
        self,
        api_client,
    ):
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_register_does_not_require_authentication(
        self,
        api_client,
        mocker,
    ):
        register_user = mocker.patch(
            "accounts.api.views.register_user",
        )

        payload = {
            "username": "test_user",
            "email": "test_user@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password1": "Strong-password-123!",
            "password2": "Strong-password-123!",
        }

        response = api_client.post(
            self.url,
            payload,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        register_user.assert_called_once()

    def test_register_does_not_create_user_when_serializer_is_invalid(
        self,
        api_client,
        mocker,
    ):
        register_user = mocker.patch(
            "accounts.api.views.register_user",
        )

        response = api_client.post(
            self.url,
            {
                "username": "test_user",
                "email": "invalid-email",
                "password1": "Strong-password-123!",
                "password2": "Strong-password-123!",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not User.objects.filter(
            username="test_user",
        ).exists()
        register_user.assert_not_called()

    def test_register_service_validation_error_returns_400(
        self,
        api_client,
        mocker,
    ):
        register_user = mocker.patch(
            "accounts.api.views.register_user",
        )
        register_user.side_effect = ValidationError("Registration failed.")

        payload = {
            "username": "test_user",
            "email": "test_user@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password1": "Strong-password-123!",
            "password2": "Strong-password-123!",
        }

        response = api_client.post(
            self.url,
            payload,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
