from unittest.mock import ANY, patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

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
