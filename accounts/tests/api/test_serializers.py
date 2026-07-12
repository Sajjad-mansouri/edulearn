from unittest.mock import patch

import pytest
from django.contrib.auth.password_validation import ValidationError

from accounts.api.serializers import UserRegistrationSerializer


@pytest.mark.django_db
class TestUserRegistrationSerializer:
    @pytest.fixture
    def registration_data(self):
        return {
            "first_name": "test_user",
            "last_name": "test_family",
            "email": "test_user@example.com",
            "username": "test_user",
            "password1": "StrongPassword123!",
            "password2": "StrongPassword123!",
        }

    def test_is_valid_returns_true_when_data_is_valid(self, registration_data):
        serializer = UserRegistrationSerializer(data=registration_data)

        assert serializer.is_valid() is True
        assert serializer.validated_data["password1"] == registration_data["password1"]
        assert serializer.validated_data["password2"] == registration_data["password2"]

    def test_is_valid_returns_error_when_passwords_do_not_match(
        self,
        registration_data,
    ):
        registration_data["password2"] = "AnotherPassword123!"

        serializer = UserRegistrationSerializer(data=registration_data)

        assert serializer.is_valid() is False
        assert serializer.errors == {"password2": ["Passwords do not match."]}

    @patch("accounts.api.serializers.validate_password")
    def test_validate_calls_django_password_validator(
        self,
        mock_validate_password,
        registration_data,
    ):
        serializer = UserRegistrationSerializer(data=registration_data)

        assert serializer.is_valid() is True

        mock_validate_password.assert_called_once_with(registration_data["password1"])

    @patch("accounts.api.serializers.validate_password")
    def test_returns_validation_error_when_password_validator_rejects_password(
        self,
        mock_validate_password,
        registration_data,
    ):
        mock_validate_password.side_effect = ValidationError(["Password is too weak."])

        serializer = UserRegistrationSerializer(data=registration_data)

        assert serializer.is_valid() is False
        assert serializer.errors == {"non_field_errors": ["Password is too weak."]}
