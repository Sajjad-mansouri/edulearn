import pytest

from accounts.api.serializers import (
    LoginSerializer,
    LogoutSerializer,
    PasswordResetSerializer,
)


@pytest.mark.django_db
class TestLoginSerializer:
    def test_fields_are_defined_correctly(self):
        serializer = LoginSerializer()

        assert set(serializer.fields) == {
            "username",
            "password",
        }

    def test_username_is_required(self):
        serializer = LoginSerializer(
            data={
                "password": "test-password",
            }
        )

        assert serializer.is_valid() is False
        assert "username" in serializer.errors

    def test_password_is_required(self):
        serializer = LoginSerializer(
            data={
                "username": "test_user",
            }
        )

        assert serializer.is_valid() is False
        assert "password" in serializer.errors

    def test_valid_credentials_are_accepted(self):
        data = {
            "username": "test_user",
            "password": "test-password",
        }

        serializer = LoginSerializer(data=data)

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data == data

    def test_password_is_write_only(self):
        serializer = LoginSerializer()

        assert serializer.fields["password"].write_only is True

    def test_password_is_not_exposed_in_representation(self):
        serializer = LoginSerializer(
            data={
                "username": "test_user",
                "password": "test-password",
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.data == {
            "username": "test_user",
        }

    def test_empty_username_is_rejected(self):
        serializer = LoginSerializer(
            data={
                "username": "",
                "password": "test-password",
            }
        )

        assert serializer.is_valid() is False
        assert "username" in serializer.errors

    def test_empty_password_is_rejected(self):
        serializer = LoginSerializer(
            data={
                "username": "test_user",
                "password": "",
            }
        )

        assert serializer.is_valid() is False
        assert "password" in serializer.errors


@pytest.mark.django_db
class TestLogoutSerializer:
    def test_fields_are_defined_correctly(self):
        serializer = LogoutSerializer()

        assert set(serializer.fields) == {"refresh"}

    def test_refresh_is_required(self):
        serializer = LogoutSerializer(data={})

        assert serializer.is_valid() is False
        assert "refresh" in serializer.errors

    def test_valid_refresh_token_is_accepted(self):
        refresh_token = "test-refresh-token"

        serializer = LogoutSerializer(
            data={
                "refresh": refresh_token,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["refresh"] == refresh_token

    def test_empty_refresh_token_is_rejected(self):
        serializer = LogoutSerializer(
            data={
                "refresh": "",
            }
        )

        assert serializer.is_valid() is False
        assert "refresh" in serializer.errors

    def test_refresh_is_not_write_only(self):
        serializer = LogoutSerializer()

        assert serializer.fields["refresh"].write_only is False

    def test_refresh_is_present_in_representation(self):
        refresh_token = "test-refresh-token"

        serializer = LogoutSerializer(
            data={
                "refresh": refresh_token,
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.data == {
            "refresh": refresh_token,
        }


@pytest.mark.django_db
class TestPasswordResetSerializer:
    def test_fields_are_defined_correctly(self):
        serializer = PasswordResetSerializer()

        assert set(serializer.fields) == {"email"}

    def test_email_is_required(self):
        serializer = PasswordResetSerializer(data={})

        assert serializer.is_valid() is False
        assert "email" in serializer.errors

    def test_valid_email_is_accepted(self):
        email = "test_user@example.com"

        serializer = PasswordResetSerializer(
            data={
                "email": email,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["email"] == email

    @pytest.mark.parametrize(
        "email",
        [
            "invalid-email",
            "missing-at.example.com",
            "@example.com",
            "test_user@",
            "test_user.example.com",
        ],
    )
    def test_invalid_email_is_rejected(self, email):
        serializer = PasswordResetSerializer(
            data={
                "email": email,
            }
        )

        assert serializer.is_valid() is False
        assert "email" in serializer.errors

    def test_empty_email_is_rejected(self):
        serializer = PasswordResetSerializer(
            data={
                "email": "",
            }
        )

        assert serializer.is_valid() is False
        assert "email" in serializer.errors

    def test_email_is_present_in_representation(self):
        email = "test_user@example.com"

        serializer = PasswordResetSerializer(
            data={
                "email": email,
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.data == {
            "email": email,
        }

    def test_email_is_normalized_by_email_field(self):
        serializer = PasswordResetSerializer(
            data={
                "email": "test_user@EXAMPLE.COM",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["email"] == "test_user@EXAMPLE.COM"
