import pytest
from django.contrib.auth import get_user_model
from rest_framework import serializers

from profiles.api.serializers.profile import UserUpdateSerializer

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="profile_update_user",
        email="profile-update@example.com",
        password="test-password",
    )


@pytest.fixture
def another_user(db):
    return User.objects.create_user(
        username="another_profile_user",
        email="another-profile@example.com",
        password="test-password",
    )


class TestUserUpdateSerializerConfiguration:
    def test_serializer_is_model_serializer(self):
        serializer = UserUpdateSerializer()

        assert isinstance(serializer, serializers.ModelSerializer)

    def test_serializer_model_is_user(self):
        serializer = UserUpdateSerializer()

        assert serializer.Meta.model is User

    def test_serializer_has_expected_fields(self):
        serializer = UserUpdateSerializer()

        assert list(serializer.fields) == [
            "username",
            "email",
        ]

    def test_username_field_is_writable(self):
        serializer = UserUpdateSerializer()

        field = serializer.fields["username"]

        assert field.read_only is False
        assert field.write_only is False

    def test_email_field_is_writable(self):
        serializer = UserUpdateSerializer()

        field = serializer.fields["email"]

        assert field.read_only is False
        assert field.write_only is False

    def test_username_is_required(self):
        serializer = UserUpdateSerializer()

        assert serializer.fields["username"].required is True

    def test_username_does_not_allow_null(self):
        serializer = UserUpdateSerializer()

        assert serializer.fields["username"].allow_null is False

    def test_email_does_not_allow_null(self):
        serializer = UserUpdateSerializer()

        assert serializer.fields["email"].allow_null is False

    def test_only_username_and_email_are_exposed(self):
        serializer = UserUpdateSerializer()

        assert set(serializer.fields) == {
            "username",
            "email",
        }


class TestUserUpdateSerializerValidation:
    def test_valid_username(self, user):
        serializer = UserUpdateSerializer(
            user,
            data={"username": "updated_username"},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["username"] == "updated_username"

    def test_valid_email(self, user):
        serializer = UserUpdateSerializer(
            user,
            data={"email": "updated@example.com"},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["email"] == "updated@example.com"

    def test_valid_username_and_email(self, user):
        serializer = UserUpdateSerializer(
            user,
            data={
                "username": "updated_username",
                "email": "updated@example.com",
            },
            partial=True,
        )

        assert serializer.is_valid() is True

        assert serializer.validated_data == {
            "username": "updated_username",
            "email": "updated@example.com",
        }

    def test_username_is_trimmed(self, user):
        serializer = UserUpdateSerializer(
            user,
            data={"username": "  updated_username  "},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["username"] == "updated_username"

    def test_email_is_trimmed(self, user):
        serializer = UserUpdateSerializer(
            user,
            data={"email": "  updated@example.com  "},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["email"] == "updated@example.com"

    def test_email_case_is_preserved_by_serializer(self, user):
        serializer = UserUpdateSerializer(
            user,
            data={"email": "Updated@Example.COM"},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["email"] == "Updated@Example.COM"

    def test_invalid_email_is_rejected(self, user):
        serializer = UserUpdateSerializer(
            user,
            data={"email": "not-an-email"},
            partial=True,
        )

        assert serializer.is_valid() is False
        assert "email" in serializer.errors

    def test_email_without_domain_is_rejected(self, user):
        serializer = UserUpdateSerializer(
            user,
            data={"email": "user@"},
            partial=True,
        )

        assert serializer.is_valid() is False
        assert "email" in serializer.errors

    def test_email_without_local_part_is_rejected(self, user):
        serializer = UserUpdateSerializer(
            user,
            data={"email": "@example.com"},
            partial=True,
        )

        assert serializer.is_valid() is False
        assert "email" in serializer.errors

    def test_null_email_is_rejected(self, user):
        serializer = UserUpdateSerializer(
            user,
            data={"email": None},
            partial=True,
        )

        assert serializer.is_valid() is False
        assert "email" in serializer.errors

    def test_empty_username_is_rejected(self, user):
        serializer = UserUpdateSerializer(
            user,
            data={"username": ""},
            partial=True,
        )

        assert serializer.is_valid() is False
        assert "username" in serializer.errors

    def test_whitespace_only_username_is_rejected(self, user):
        serializer = UserUpdateSerializer(
            user,
            data={"username": "   "},
            partial=True,
        )

        assert serializer.is_valid() is False
        assert "username" in serializer.errors

    def test_null_username_is_rejected(self, user):
        serializer = UserUpdateSerializer(
            user,
            data={"username": None},
            partial=True,
        )

        assert serializer.is_valid() is False
        assert "username" in serializer.errors

    def test_username_at_model_maximum_length_is_valid(self, user):
        max_length = User._meta.get_field("username").max_length
        username = "u" * max_length

        serializer = UserUpdateSerializer(
            user,
            data={"username": username},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["username"] == username

    def test_username_over_model_maximum_length_is_rejected(self, user):
        max_length = User._meta.get_field("username").max_length
        username = "u" * (max_length + 1)

        serializer = UserUpdateSerializer(
            user,
            data={"username": username},
            partial=True,
        )

        assert serializer.is_valid() is False
        assert "username" in serializer.errors

    def test_non_string_username_is_coerced_to_string(self, user):
        serializer = UserUpdateSerializer(
            user,
            data={"username": 12345},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["username"] == "12345"

    def test_non_string_email_is_rejected(self, user):
        serializer = UserUpdateSerializer(
            user,
            data={"email": 12345},
            partial=True,
        )

        assert serializer.is_valid() is False
        assert "email" in serializer.errors

    def test_empty_partial_data_is_valid(self, user):
        serializer = UserUpdateSerializer(
            user,
            data={},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data == {}


class TestUserUpdateSerializerUniqueness:
    def test_duplicate_username_is_rejected(
        self,
        user,
        another_user,
    ):
        serializer = UserUpdateSerializer(
            user,
            data={"username": another_user.username},
            partial=True,
        )

        assert serializer.is_valid() is False
        assert "username" in serializer.errors

    def test_duplicate_email_is_rejected(
        self,
        user,
        another_user,
    ):
        serializer = UserUpdateSerializer(
            user,
            data={"email": another_user.email},
            partial=True,
        )

        assert serializer.is_valid() is False
        assert "email" in serializer.errors

    def test_user_can_keep_own_username(self, user):
        serializer = UserUpdateSerializer(
            user,
            data={"username": user.username},
            partial=True,
        )

        assert serializer.is_valid() is True

    def test_user_can_keep_own_email(self, user):
        serializer = UserUpdateSerializer(
            user,
            data={"email": user.email},
            partial=True,
        )

        assert serializer.is_valid() is True


class TestUserUpdateSerializerPartialUpdates:
    def test_username_update_preserves_email(self, user):
        original_email = user.email

        serializer = UserUpdateSerializer(
            user,
            data={"username": "updated_username"},
            partial=True,
        )

        assert serializer.is_valid() is True

        serializer.save()
        user.refresh_from_db()

        assert user.username == "updated_username"
        assert user.email == original_email

    def test_email_update_preserves_username(self, user):
        original_username = user.username

        serializer = UserUpdateSerializer(
            user,
            data={"email": "updated@example.com"},
            partial=True,
        )

        assert serializer.is_valid() is True

        serializer.save()
        user.refresh_from_db()

        assert user.username == original_username
        assert user.email == "updated@example.com"

    def test_both_fields_can_be_updated(self, user):
        serializer = UserUpdateSerializer(
            user,
            data={
                "username": "updated_username",
                "email": "updated@example.com",
            },
            partial=True,
        )

        assert serializer.is_valid() is True

        serializer.save()
        user.refresh_from_db()

        assert user.username == "updated_username"
        assert user.email == "updated@example.com"

    def test_empty_partial_update_does_not_change_user(self, user):
        original_username = user.username
        original_email = user.email

        serializer = UserUpdateSerializer(
            user,
            data={},
            partial=True,
        )

        assert serializer.is_valid() is True

        serializer.save()
        user.refresh_from_db()

        assert user.username == original_username
        assert user.email == original_email


class TestUserUpdateSerializerFullUpdates:
    def test_full_update_requires_username(self, user):
        serializer = UserUpdateSerializer(
            user,
            data={"email": "updated@example.com"},
        )

        assert serializer.is_valid() is False
        assert "username" in serializer.errors

    def test_partial_update_accepts_username_without_email(self, user):
        serializer = UserUpdateSerializer(
            user,
            data={"username": "updated_username"},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data == {
            "username": "updated_username",
        }

    def test_full_update_accepts_username_and_email(self, user):
        serializer = UserUpdateSerializer(
            user,
            data={
                "username": "updated_username",
                "email": "updated@example.com",
            },
        )

        assert serializer.is_valid() is True

        assert serializer.validated_data == {
            "username": "updated_username",
            "email": "updated@example.com",
        }

    def test_full_update_requires_email(self, user):
        data = {
            "username": "updated_username",
        }

        serializer = UserUpdateSerializer(
            instance=user,
            data=data,
        )

        assert serializer.is_valid() is False
        assert "email" in serializer.errors

    def test_full_update_rejects_empty_email(self, user):
        data = {
            "username": "updated_username",
            "email": "",
        }

        serializer = UserUpdateSerializer(
            instance=user,
            data=data,
        )

        assert serializer.is_valid() is False
        assert "email" in serializer.errors


class TestUserUpdateSerializerIgnoredFields:
    def test_id_is_ignored(self, user):
        serializer = UserUpdateSerializer(
            user,
            data={
                "username": "updated_username",
                "id": user.pk + 1000,
            },
            partial=True,
        )

        assert serializer.is_valid() is True
        assert "id" not in serializer.validated_data

    def test_first_name_is_ignored(self, user):
        original_first_name = user.first_name

        serializer = UserUpdateSerializer(
            user,
            data={
                "username": "updated_username",
                "first_name": "Should not change",
            },
            partial=True,
        )

        assert serializer.is_valid() is True
        assert "first_name" not in serializer.validated_data

        serializer.save()
        user.refresh_from_db()

        assert user.first_name == original_first_name

    def test_last_name_is_ignored(self, user):
        original_last_name = user.last_name

        serializer = UserUpdateSerializer(
            user,
            data={
                "username": "updated_username",
                "last_name": "Should not change",
            },
            partial=True,
        )

        assert serializer.is_valid() is True
        assert "last_name" not in serializer.validated_data

        serializer.save()
        user.refresh_from_db()

        assert user.last_name == original_last_name

    def test_password_is_ignored(self, user):
        original_password = user.password

        serializer = UserUpdateSerializer(
            user,
            data={
                "username": "updated_username",
                "password": "new-password",
            },
            partial=True,
        )

        assert serializer.is_valid() is True
        assert "password" not in serializer.validated_data

        serializer.save()
        user.refresh_from_db()

        assert user.password == original_password

    def test_is_staff_is_ignored(self, user):
        original_is_staff = user.is_staff

        serializer = UserUpdateSerializer(
            user,
            data={
                "username": "updated_username",
                "is_staff": not original_is_staff,
            },
            partial=True,
        )

        assert serializer.is_valid() is True
        assert "is_staff" not in serializer.validated_data

        serializer.save()
        user.refresh_from_db()

        assert user.is_staff == original_is_staff

    def test_is_superuser_is_ignored(self, user):
        original_is_superuser = user.is_superuser

        serializer = UserUpdateSerializer(
            user,
            data={
                "username": "updated_username",
                "is_superuser": not original_is_superuser,
            },
            partial=True,
        )

        assert serializer.is_valid() is True
        assert "is_superuser" not in serializer.validated_data

        serializer.save()
        user.refresh_from_db()

        assert user.is_superuser == original_is_superuser

    def test_is_active_is_ignored(self, user):
        original_is_active = user.is_active

        serializer = UserUpdateSerializer(
            user,
            data={
                "username": "updated_username",
                "is_active": not original_is_active,
            },
            partial=True,
        )

        assert serializer.is_valid() is True
        assert "is_active" not in serializer.validated_data

        serializer.save()
        user.refresh_from_db()

        assert user.is_active == original_is_active

    def test_unknown_field_is_ignored(self, user):
        serializer = UserUpdateSerializer(
            user,
            data={
                "username": "updated_username",
                "unknown_field": "ignored",
            },
            partial=True,
        )

        assert serializer.is_valid() is True
        assert "unknown_field" not in serializer.validated_data


class TestUserUpdateSerializerRepresentation:
    def test_representation_contains_only_serializer_fields(self, user):
        serializer = UserUpdateSerializer(user)

        assert set(serializer.data.keys()) == {
            "username",
            "email",
        }

    def test_representation_contains_username(self, user):
        serializer = UserUpdateSerializer(user)

        assert serializer.data["username"] == user.username

    def test_representation_contains_email(self, user):
        serializer = UserUpdateSerializer(user)

        assert serializer.data["email"] == user.email

    def test_password_is_not_in_representation(self, user):
        serializer = UserUpdateSerializer(user)

        assert "password" not in serializer.data

    def test_is_staff_is_not_in_representation(self, user):
        serializer = UserUpdateSerializer(user)

        assert "is_staff" not in serializer.data

    def test_is_superuser_is_not_in_representation(self, user):
        serializer = UserUpdateSerializer(user)

        assert "is_superuser" not in serializer.data

    def test_is_active_is_not_in_representation(self, user):
        serializer = UserUpdateSerializer(user)

        assert "is_active" not in serializer.data


class TestUserUpdateSerializerPersistence:
    def test_username_is_persisted(self, user):
        serializer = UserUpdateSerializer(
            user,
            data={"username": "persisted_username"},
            partial=True,
        )

        assert serializer.is_valid() is True

        result = serializer.save()

        user.refresh_from_db()

        assert result is user
        assert user.username == "persisted_username"

    def test_email_is_persisted(self, user):
        serializer = UserUpdateSerializer(
            user,
            data={"email": "persisted@example.com"},
            partial=True,
        )

        assert serializer.is_valid() is True

        result = serializer.save()

        user.refresh_from_db()

        assert result is user
        assert user.email == "persisted@example.com"

    def test_both_fields_are_persisted(self, user):
        serializer = UserUpdateSerializer(
            user,
            data={
                "username": "persisted_username",
                "email": "persisted@example.com",
            },
            partial=True,
        )

        assert serializer.is_valid() is True

        result = serializer.save()

        user.refresh_from_db()

        assert result is user
        assert user.username == "persisted_username"
        assert user.email == "persisted@example.com"


class TestUserUpdateSerializerNonMutation:
    def test_validation_does_not_modify_user(self, user):
        original_username = user.username
        original_email = user.email

        serializer = UserUpdateSerializer(
            user,
            data={
                "username": "temporary_username",
                "email": "temporary@example.com",
            },
            partial=True,
        )

        assert serializer.is_valid() is True

        user.refresh_from_db()

        assert user.username == original_username
        assert user.email == original_email

    def test_invalid_validation_does_not_modify_user(self, user):
        original_username = user.username
        original_email = user.email

        serializer = UserUpdateSerializer(
            user,
            data={
                "username": "",
                "email": "invalid-email",
            },
            partial=True,
        )

        assert serializer.is_valid() is False

        user.refresh_from_db()

        assert user.username == original_username
        assert user.email == original_email

    def test_save_returns_same_user_instance(self, user):
        serializer = UserUpdateSerializer(
            user,
            data={"username": "updated_username"},
            partial=True,
        )

        assert serializer.is_valid() is True

        result = serializer.save()

        assert result is user
        assert result.pk == user.pk
