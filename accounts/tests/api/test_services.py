from unittest.mock import Mock, patch

import pytest
from django.contrib.auth import get_user_model

from accounts.api.services import register_user
from accounts.models import Role

User = get_user_model()


@pytest.mark.django_db
class TestRegisterUser:
    """Tests for register_user service."""

    @pytest.fixture
    def registration_data(self):
        return {
            "first_name": "Test",
            "last_name": "User",
            "username": "test_user",
            "email": "test@example.com",
            "password1": "StrongPassword123!",
            "password2": "StrongPassword123!",
        }

    @pytest.fixture
    def request_mock(self):
        return Mock()

    @patch("accounts.api.services.send_registration_email")
    def test_register_user_creates_inactive_user(
        self,
        mock_send_registration_email,
        registration_data,
        request_mock,
    ):
        """The service creates an inactive user."""
        register_user(
            data=registration_data.copy(),
            role_name="student",
            request=request_mock,
        )

        user = User.objects.get(username="test_user")

        assert user.is_active is False
        assert user.email == "test@example.com"
        assert user.check_password("StrongPassword123!")

    @patch("accounts.api.services.send_registration_email")
    def test_register_user_assigns_role(
        self,
        mock_send_registration_email,
        registration_data,
        request_mock,
    ):
        """The created user is assigned to the requested role."""
        register_user(
            data=registration_data.copy(),
            role_name="student",
            request=request_mock,
        )

        user = User.objects.get(username="test_user")

        assert user.roles.filter(name="student").exists()

    @patch("accounts.api.services.send_registration_email")
    def test_register_user_creates_role_when_missing(
        self,
        mock_send_registration_email,
        registration_data,
        request_mock,
    ):
        """The requested role is created if it does not already exist."""
        assert not Role.objects.filter(name="student").exists()

        register_user(
            data=registration_data.copy(),
            role_name="student",
            request=request_mock,
        )

        assert Role.objects.filter(name="student").exists()

    @patch("accounts.api.services.send_registration_email")
    def test_register_user_uses_existing_role(
        self,
        mock_send_registration_email,
        registration_data,
        request_mock,
    ):
        """An existing role is reused instead of creating a duplicate."""
        Role.objects.create(name="student")

        register_user(
            data=registration_data.copy(),
            role_name="student",
            request=request_mock,
        )

        assert Role.objects.filter(name="student").count() == 1

    @patch("accounts.api.services.send_registration_email")
    def test_register_user_sends_registration_email(
        self,
        mock_send_registration_email,
        registration_data,
        request_mock,
    ):
        """A registration email is sent after successful registration."""
        register_user(
            data=registration_data.copy(),
            role_name="student",
            request=request_mock,
        )

        user = User.objects.get(username="test_user")

        mock_send_registration_email.assert_called_once_with(
            user=user,
            request=request_mock,
            role_name="student",
        )
