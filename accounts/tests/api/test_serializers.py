from unittest.mock import patch

import pytest
from django.contrib.auth.password_validation import ValidationError

from accounts.api.serializers import LoginSerializer, UserRegistrationSerializer


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


class TestLoginSerializer:
    """Tests for LoginSerializer."""

    @pytest.fixture
    def valid_data(self):
        return {
            "username": "test_user",
            "password": "secure_pass_1234",
        }

    def test_serializer_is_valid_with_valid_data(self, valid_data):
        serializer = LoginSerializer(data=valid_data)

        assert serializer.is_valid()
        assert serializer.validated_data == valid_data

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
    def test_required_fields(self, payload, field):
        serializer = LoginSerializer(data=payload)

        assert not serializer.is_valid()
        assert field in serializer.errors

    def test_password_field_is_write_only(self):
        serializer = LoginSerializer()

        assert serializer.fields["password"].write_only is True

    def test_username_field_is_not_write_only(self):
        serializer = LoginSerializer()

        assert serializer.fields["username"].write_only is False

    def test_rejects_unknown_fields(self, valid_data):
        serializer = LoginSerializer(
            data={
                **valid_data,
                "unexpected_field": "value",
            }
        )

        assert serializer.is_valid()
        assert "unexpected_field" not in serializer.errors
