from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from django.contrib.auth import get_user_model
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from profiles.api.serializers.navigation import TopNavUserSerializer
from profiles.models import InstructorProfile, Profile

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="navigation_user",
        email="navigation@example.com",
        password="test-password",
        first_name="Navigation",
        last_name="User",
    )


@pytest.fixture
def profile(db, user):
    return Profile.objects.create(user=user)


@pytest.fixture
def instructor_profile(db, profile):
    return InstructorProfile.objects.create(profile=profile)


@pytest.fixture
def api_request():
    factory = APIRequestFactory()
    return Request(factory.get("/dashboard/"))


@pytest.fixture
def serializer():
    return TopNavUserSerializer()


class TestTopNavUserSerializer:
    def test_fields(self, serializer):
        assert set(serializer.fields) == {
            "id",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "avatar_url",
            "role",
        }

    def test_all_fields_are_read_only(self, serializer):
        for field_name, field in serializer.fields.items():
            assert field.read_only is True, field_name

    def test_id_is_read_only(self, serializer):
        assert serializer.fields["id"].read_only is True

    def test_first_name_is_read_only(self, serializer):
        assert serializer.fields["first_name"].read_only is True

    def test_last_name_is_read_only(self, serializer):
        assert serializer.fields["last_name"].read_only is True

    def test_full_name_is_read_only(self, serializer):
        assert serializer.fields["full_name"].read_only is True

    def test_email_is_read_only(self, serializer):
        assert serializer.fields["email"].read_only is True

    def test_avatar_url_is_read_only(self, serializer):
        assert serializer.fields["avatar_url"].read_only is True

    def test_role_is_read_only(self, serializer):
        assert serializer.fields["role"].read_only is True

    def test_full_name_uses_user_full_name(self, user, profile):
        serializer = TopNavUserSerializer(user)

        assert serializer.data["full_name"] == "Navigation User"

    def test_full_name_falls_back_to_username(
        self,
        user,
        profile,
    ):
        user.first_name = ""
        user.last_name = ""
        user.save(update_fields=["first_name", "last_name"])

        serializer = TopNavUserSerializer(user)

        assert serializer.data["full_name"] == user.username

    def test_full_name_with_only_first_name(self, user, profile):
        user.first_name = "Navigation"
        user.last_name = ""
        user.save(update_fields=["first_name", "last_name"])

        serializer = TopNavUserSerializer(user)

        assert serializer.data["full_name"] == user.get_full_name()

    def test_full_name_with_only_last_name(self, user, profile):
        user.first_name = ""
        user.last_name = "User"
        user.save(update_fields=["first_name", "last_name"])

        serializer = TopNavUserSerializer(user)

        assert serializer.data["full_name"] == user.get_full_name()

    def test_avatar_url_is_none_when_user_has_no_avatar(
        self,
        user,
        profile,
    ):
        assert not profile.avatar

        serializer = TopNavUserSerializer(user)

        assert serializer.data["avatar_url"] is None

    def test_avatar_url_returns_relative_url_without_request(
        self,
        user,
        profile,
    ):
        profile.avatar = SimpleNamespace(
            url="/media/avatars/navigation-user.jpg",
        )

        serializer = TopNavUserSerializer(user)

        assert serializer.data["avatar_url"] == ("/media/avatars/navigation-user.jpg")

    def test_avatar_url_returns_absolute_url_with_request(
        self,
        user,
        profile,
        api_request,
    ):
        profile.avatar = SimpleNamespace(
            url="/media/avatars/navigation-user.jpg",
        )

        serializer = TopNavUserSerializer(
            user,
            context={"request": api_request},
        )

        assert serializer.data["avatar_url"] == (
            "http://testserver/media/avatars/navigation-user.jpg"
        )

    def test_avatar_url_uses_request_build_absolute_uri(
        self,
        user,
        profile,
    ):
        profile.avatar = SimpleNamespace(
            url="/media/avatars/navigation-user.jpg",
        )

        request = Mock()
        request.build_absolute_uri.return_value = (
            "https://example.com/media/avatars/navigation-user.jpg"
        )

        serializer = TopNavUserSerializer(
            user,
            context={"request": request},
        )

        assert serializer.data["avatar_url"] == (
            "https://example.com/media/avatars/navigation-user.jpg"
        )

        request.build_absolute_uri.assert_called_once_with(
            "/media/avatars/navigation-user.jpg"
        )

    def test_student_role_without_instructor_profile(
        self,
        user,
        profile,
    ):
        assert not hasattr(profile, "instructor_profile")

        serializer = TopNavUserSerializer(user)

        assert serializer.data["role"] == "student"

    def test_instructor_role_with_instructor_profile(
        self,
        user,
        profile,
        instructor_profile,
    ):
        assert profile.instructor_profile == instructor_profile

        serializer = TopNavUserSerializer(user)

        assert serializer.data["role"] == "instructor"

    def test_representation_contains_expected_user_data(
        self,
        user,
        profile,
    ):
        serializer = TopNavUserSerializer(user)

        assert serializer.data == {
            "id": user.pk,
            "first_name": "Navigation",
            "last_name": "User",
            "full_name": "Navigation User",
            "email": "navigation@example.com",
            "avatar_url": None,
            "role": "student",
        }

    def test_representation_does_not_expose_unlisted_user_fields(
        self,
        user,
        profile,
    ):
        serializer = TopNavUserSerializer(user)

        assert set(serializer.data) == {
            "id",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "avatar_url",
            "role",
        }

    def test_read_only_fields_ignore_input(
        self,
        user,
        profile,
    ):
        serializer = TopNavUserSerializer(
            user,
            data={
                "id": user.pk + 100,
                "first_name": "Changed",
                "last_name": "Name",
                "full_name": "Changed Name",
                "email": "changed@example.com",
                "avatar_url": "/media/avatar.jpg",
                "role": "instructor",
            },
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data == {}

    def test_partial_input_is_ignored(
        self,
        user,
        profile,
    ):
        serializer = TopNavUserSerializer(
            user,
            data={"first_name": "Changed"},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data == {}

    def test_serialization_does_not_modify_user(
        self,
        user,
        profile,
    ):
        original_values = {
            "pk": user.pk,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
        }

        serializer = TopNavUserSerializer(user)

        _ = serializer.data

        assert user.pk == original_values["pk"]
        assert user.first_name == original_values["first_name"]
        assert user.last_name == original_values["last_name"]
        assert user.email == original_values["email"]

    def test_get_full_name_returns_full_name(
        self,
        user,
        profile,
    ):
        serializer = TopNavUserSerializer()

        assert serializer.get_full_name(user) == "Navigation User"

    def test_get_full_name_falls_back_to_username(
        self,
        user,
        profile,
    ):
        user.first_name = ""
        user.last_name = ""
        user.save(update_fields=["first_name", "last_name"])

        serializer = TopNavUserSerializer()

        assert serializer.get_full_name(user) == user.username

    def test_get_avatar_url_returns_none_without_avatar(
        self,
        user,
        profile,
    ):
        serializer = TopNavUserSerializer()

        assert serializer.get_avatar_url(user) is None

    def test_get_avatar_url_returns_relative_url_without_request(
        self,
        user,
        profile,
    ):
        profile.avatar = SimpleNamespace(
            url="/media/avatars/navigation-user.jpg",
        )

        serializer = TopNavUserSerializer()

        assert serializer.get_avatar_url(user) == ("/media/avatars/navigation-user.jpg")

    def test_get_avatar_url_builds_absolute_url(
        self,
        user,
        profile,
    ):
        profile.avatar = SimpleNamespace(
            url="/media/avatars/navigation-user.jpg",
        )

        request = Mock()
        request.build_absolute_uri.return_value = (
            "https://example.com/media/avatars/navigation-user.jpg"
        )

        serializer = TopNavUserSerializer(
            context={"request": request},
        )

        assert serializer.get_avatar_url(user) == (
            "https://example.com/media/avatars/navigation-user.jpg"
        )

        request.build_absolute_uri.assert_called_once_with(
            "/media/avatars/navigation-user.jpg"
        )

    def test_get_role_returns_student_without_instructor_profile(
        self,
        user,
        profile,
    ):
        serializer = TopNavUserSerializer()

        assert serializer.get_role(user) == "student"

    def test_get_role_returns_instructor_with_instructor_profile(
        self,
        user,
        profile,
        instructor_profile,
    ):
        serializer = TopNavUserSerializer()

        assert serializer.get_role(user) == "instructor"
