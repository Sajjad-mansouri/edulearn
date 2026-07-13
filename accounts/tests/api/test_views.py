from unittest.mock import ANY, patch

import pytest
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from accounts.api.views import LoginApiView
from accounts.tests.factories import UserFactory


@pytest.mark.django_db
class TestRegisterApiView:
    """Tests for RegisterApiView."""

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def url(self):
        return reverse("accounts:register")

    @pytest.fixture
    def valid_payload(self):
        return {
            "first_name": "Test",
            "last_name": "User",
            "username": "test_user",
            "email": "test@example.com",
            "password1": "StrongPassword123!",
            "password2": "StrongPassword123!",
        }

    def test_register_returns_201_for_valid_data(
        self,
        api_client,
        url,
        valid_payload,
    ):
        """A user can register with valid data."""
        response = api_client.post(url, valid_payload)

        assert response.status_code == status.HTTP_201_CREATED

    def test_register_returns_400_for_invalid_data(
        self,
        api_client,
        url,
        valid_payload,
    ):
        """Registration fails when submitted data is invalid."""
        valid_payload["password2"] = "different-password"

        response = api_client.post(url, valid_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password2" in response.data

    @patch("accounts.api.views.register_user")
    def test_register_calls_register_user_service(
        self,
        mock_register_user,
        api_client,
        url,
        valid_payload,
    ):
        """Registration delegates business logic to the service layer."""
        response = api_client.post(url, valid_payload)

        assert response.status_code == status.HTTP_201_CREATED

        mock_register_user.assert_called_once_with(
            data={
                "first_name": "Test",
                "last_name": "User",
                "username": "test_user",
                "email": "test@example.com",
                "password1": "StrongPassword123!",
                "password2": "StrongPassword123!",
            },
            role_name="student",
            request=ANY,
        )

    def test_register_endpoint_is_accessible_without_authentication(
        self,
        api_client,
        url,
        valid_payload,
    ):
        """Anonymous users can access the registration endpoint."""
        response = api_client.post(url, valid_payload)

        assert response.status_code != status.HTTP_401_UNAUTHORIZED
        assert response.status_code != status.HTTP_403_FORBIDDEN

    def test_register_returns_400_when_username_already_exists(
        self,
        api_client,
        url,
        valid_payload,
    ):
        UserFactory(username="test_user")

        response = api_client.post(url, valid_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "username" in response.data


@pytest.mark.django_db
class TestRegisterInstructorApiView:
    """Tests for RegisterInstructorApiView."""

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def url(self):
        return reverse("accounts:register_instructor")

    @pytest.fixture
    def valid_payload(self):
        return {
            "first_name": "Test",
            "last_name": "Instructor",
            "username": "test_instructor",
            "email": "instructor@example.com",
            "password1": "StrongPassword123!",
            "password2": "StrongPassword123!",
        }

    @patch("accounts.api.views.register_user")
    def test_register_calls_register_user_with_teacher_role(
        self,
        mock_register_user,
        api_client,
        url,
        valid_payload,
    ):
        """Registration delegates to the service using the teacher role."""
        response = api_client.post(url, valid_payload)

        assert response.status_code == status.HTTP_201_CREATED

        mock_register_user.assert_called_once_with(
            data={
                "first_name": "Test",
                "last_name": "Instructor",
                "username": "test_instructor",
                "email": "instructor@example.com",
                "password1": "StrongPassword123!",
                "password2": "StrongPassword123!",
            },
            role_name="teacher",
            request=ANY,
        )

    def test_register_returns_201_for_valid_data(
        self,
        api_client,
        url,
        valid_payload,
    ):
        """An instructor can register with valid data."""
        response = api_client.post(url, valid_payload)

        assert response.status_code == status.HTTP_201_CREATED

    def test_register_endpoint_is_accessible_without_authentication(
        self,
        api_client,
        url,
        valid_payload,
    ):
        """Anonymous users can access the instructor registration endpoint."""
        response = api_client.post(url, valid_payload)

        assert response.status_code not in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )


@pytest.mark.django_db
class TestRegisterConfirmApiView:
    """Tests for RegisterConfirmApiView."""

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def inactive_user(self):
        return UserFactory(is_active=False)

    @pytest.fixture
    def valid_uid(self, inactive_user):
        return urlsafe_base64_encode(force_bytes(inactive_user.pk))

    @pytest.fixture
    def valid_token(self, inactive_user):
        return default_token_generator.make_token(inactive_user)

    @pytest.fixture
    def url(self, valid_uid, valid_token):
        return reverse(
            "accounts:register_confirm",
            kwargs={
                "uidb64": valid_uid,
                "token": valid_token,
            },
        )

    @patch("accounts.api.views.confirm_registration")
    def test_confirm_registration_for_valid_link(
        self,
        mock_confirm_registration,
        api_client,
        url,
        inactive_user,
    ):
        """A valid confirmation link activates the registration flow."""
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"detail": "Email verified successfully."}

        mock_confirm_registration.assert_called_once_with(
            inactive_user,
        )

    def test_returns_bad_request_for_invalid_uid(
        self,
        api_client,
        valid_token,
    ):
        """An invalid uid returns HTTP 400."""
        url = reverse(
            "accounts:register_confirm",
            kwargs={
                "uidb64": "invalid-uid",
                "token": valid_token,
            },
        )

        response = api_client.get(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {"detail": "Invalid confirmation link."}

    @patch("accounts.api.views.confirm_registration")
    def test_returns_bad_request_for_invalid_token(
        self,
        mock_confirm_registration,
        api_client,
        valid_uid,
    ):
        """An invalid token returns HTTP 400."""
        url = reverse(
            "accounts:register_confirm",
            kwargs={
                "uidb64": valid_uid,
                "token": "invalid-token",
            },
        )

        response = api_client.get(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {"detail": "Invalid confirmation link."}

        mock_confirm_registration.assert_not_called()

    @patch("accounts.api.views.confirm_registration")
    def test_confirm_registration_is_called_once(
        self,
        mock_confirm_registration,
        api_client,
        url,
        inactive_user,
    ):
        """The confirmation service is invoked exactly once."""
        api_client.get(url)

        mock_confirm_registration.assert_called_once_with(
            inactive_user,
        )


@pytest.mark.django_db
class TestLoginApiView:
    """Tests for LoginApiView."""

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def url(self):
        return reverse("accounts:login")

    @pytest.fixture
    def payload(self):
        return {
            "username": "test_user",
            "password": "secure_pass_1234",
        }

    @patch("accounts.api.views.perform_login")
    def test_returns_tokens_for_valid_credentials(
        self,
        mock_perform_login,
        api_client,
        url,
        payload,
    ):
        """A successful login returns the generated JWT tokens."""
        tokens = {
            "access": "access-token",
            "refresh": "refresh-token",
        }
        mock_perform_login.return_value = tokens

        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == tokens

        mock_perform_login.assert_called_once()

    @patch("accounts.api.views.perform_login")
    def test_passes_validated_data_to_service(
        self,
        mock_perform_login,
        api_client,
        url,
        payload,
    ):
        """The validated credentials are passed to the login service."""
        mock_perform_login.return_value = {
            "access": "access-token",
            "refresh": "refresh-token",
        }

        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK

        args, kwargs = mock_perform_login.call_args

        assert args[0] == payload
        assert args[1].__class__.__name__ == "Request"

    @pytest.mark.parametrize(
        "payload,field",
        [
            (
                {
                    "password": "secure_pass_1234",
                },
                "username",
            ),
            (
                {
                    "username": "test_user",
                },
                "password",
            ),
            (
                {},
                "username",
            ),
            (
                {},
                "password",
            ),
        ],
    )
    @patch("accounts.api.views.perform_login")
    @patch.object(LoginApiView, "throttle_classes", [])
    def test_returns_bad_request_for_invalid_payload(
        self,
        mock_perform_login,
        api_client,
        url,
        payload,
        field,
    ):
        """Invalid request data returns HTTP 400."""
        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert field in response.json()

        mock_perform_login.assert_not_called()


@pytest.mark.django_db
class TestLogoutApiView:
    """Tests for LogoutApiView."""

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def user(self):
        return UserFactory()

    @pytest.fixture
    def authenticated_client(self, api_client, user):
        api_client.force_authenticate(user=user)
        return api_client

    @pytest.fixture
    def url(self):
        return reverse("accounts:logout")

    @pytest.fixture
    def valid_payload(self):
        return {
            "refresh": "refresh-token",
        }

    @patch("accounts.api.views.logout_user")
    def test_logout_returns_success_response(
        self,
        mock_logout_user,
        authenticated_client,
        url,
        valid_payload,
    ):
        response = authenticated_client.post(
            url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "detail": "Successfully logged out.",
        }

        mock_logout_user.assert_called_once_with("refresh-token")

    @pytest.mark.parametrize(
        "payload",
        [
            {},
            {"refresh": ""},
        ],
    )
    @patch("accounts.api.views.logout_user")
    def test_returns_bad_request_for_invalid_payload(
        self,
        mock_logout_user,
        authenticated_client,
        url,
        payload,
    ):
        response = authenticated_client.post(
            url,
            payload,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "refresh" in response.json()

        mock_logout_user.assert_not_called()

    @patch("accounts.api.views.logout_user")
    def test_returns_bad_request_when_service_raises_validation_error(
        self,
        mock_logout_user,
        authenticated_client,
        url,
    ):
        mock_logout_user.side_effect = ValidationError(
            {"refresh": "Invalid refresh token."}
        )

        response = authenticated_client.post(
            url,
            {"refresh": "invalid-token"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        assert response.json() == {
            "refresh": "Invalid refresh token.",
        }

        mock_logout_user.assert_called_once_with("invalid-token")

    def test_requires_authentication(
        self,
        api_client,
        url,
        valid_payload,
    ):
        response = api_client.post(
            url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
