from datetime import date
from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image
from rest_framework import serializers, status
from rest_framework.test import APIClient, APIRequestFactory

from accounts.models import User
from profiles.api.serializers import TopNavUserSerializer
from profiles.api.views import CurrentUserApiView
from profiles.models import InstructorProfile, Profile


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def api_request_factory():
    return APIRequestFactory()


@pytest.fixture
def user(db):
    user = User.objects.create_user(
        username="current_user",
        email="current_user@example.com",
        password="test-password",
        first_name="Current",
        last_name="User",
    )

    Profile.objects.create(
        user=user,
        website="https://example.com",
        country="Azerbaijan",
        timezone="Asia/Baku",
        language="en",
        date_of_birth=date(1995, 5, 15),
        company="Example Company",
        job_title="Software Engineer",
    )

    return user


@pytest.fixture
def another_user(db):
    user = User.objects.create_user(
        username="another_user",
        email="another_user@example.com",
        password="test-password",
        first_name="Another",
        last_name="User",
    )

    Profile.objects.create(
        user=user,
        website="https://another.example.com",
        country="Germany",
        timezone="Europe/Berlin",
        language="de",
        date_of_birth=date(1998, 8, 20),
        company="Another Company",
        job_title="Developer",
    )

    return user


@pytest.fixture
def user_profile(user):
    return user.profile


@pytest.fixture
def another_user_profile(another_user):
    return another_user.profile


@pytest.fixture
def instructor_profile(user_profile):
    return InstructorProfile.objects.create(
        profile=user_profile,
        professional_title="Software Engineering Instructor",
        organization="Example Academy",
    )


@pytest.fixture
def valid_avatar():
    image = Image.new("RGB", (100, 100), "white")

    image_file = BytesIO()
    image.save(image_file, format="JPEG")
    image_file.seek(0)

    return SimpleUploadedFile(
        "avatar.jpg",
        image_file.read(),
        content_type="image/jpeg",
    )


@pytest.fixture
def user_profile_with_avatar(user_profile, valid_avatar):
    user_profile.avatar = valid_avatar
    user_profile.save(update_fields=["avatar"])

    return user_profile


@pytest.fixture
def current_user_url():
    return reverse("profile-api:current_user")


class TestCurrentUserApiView:
    """Tests for CurrentUserApiView."""

    def test_view_uses_top_nav_user_serializer(self):
        assert CurrentUserApiView.serializer_class is TopNavUserSerializer

    def test_get_object_returns_request_user(
        self,
        api_request_factory,
        user,
    ):
        request = api_request_factory.get("/")

        view = CurrentUserApiView()
        view.request = request
        view.request.user = user

        result = view.get_object()

        assert result is user

    def test_get_object_does_not_return_another_user(
        self,
        api_request_factory,
        user,
        another_user,
    ):
        request = api_request_factory.get("/")

        view = CurrentUserApiView()
        view.request = request
        view.request.user = user

        result = view.get_object()

        assert result is user
        assert result is not another_user
        assert result.pk == user.pk
        assert result.pk != another_user.pk

    def test_get_returns_authenticated_user(
        self,
        api_client,
        current_user_url,
        user,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.get(current_user_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == user.pk
        assert response.data["first_name"] == user.first_name
        assert response.data["last_name"] == user.last_name
        assert response.data["email"] == user.email

    def test_get_returns_only_current_user_data(
        self,
        api_client,
        current_user_url,
        user,
        another_user,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.get(current_user_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == user.pk
        assert response.data["id"] != another_user.pk
        assert response.data["email"] == user.email
        assert response.data["email"] != another_user.email

    def test_query_parameters_cannot_select_another_user(
        self,
        api_client,
        current_user_url,
        user,
        another_user,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.get(
            current_user_url,
            {
                "id": another_user.pk,
                "user_id": another_user.pk,
                "username": another_user.username,
                "email": another_user.email,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == user.pk
        assert response.data["id"] != another_user.pk
        assert response.data["email"] == user.email

    def test_get_returns_expected_fields(
        self,
        api_client,
        current_user_url,
        user,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.get(current_user_url)

        assert response.status_code == status.HTTP_200_OK

        assert set(response.data.keys()) == {
            "id",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "avatar_url",
            "role",
        }

    def test_get_returns_full_name(
        self,
        api_client,
        current_user_url,
        user,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.get(current_user_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["full_name"] == "Current User"

    def test_full_name_returns_last_name_when_first_name_is_empty(
        self,
        api_client,
        current_user_url,
        user,
    ):
        user.first_name = ""
        user.last_name = "User"
        user.save(update_fields=["first_name", "last_name"])

        api_client.force_authenticate(user=user)

        response = api_client.get(current_user_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["full_name"] == "User"

    def test_full_name_returns_first_name_when_last_name_is_empty(
        self,
        api_client,
        current_user_url,
        user,
    ):
        user.first_name = "Current"
        user.last_name = ""
        user.save(update_fields=["first_name", "last_name"])

        api_client.force_authenticate(user=user)

        response = api_client.get(current_user_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["full_name"] == "Current"

    def test_full_name_falls_back_to_username_when_names_are_empty(
        self,
        api_client,
        current_user_url,
        user,
    ):
        user.first_name = ""
        user.last_name = ""
        user.save(update_fields=["first_name", "last_name"])

        api_client.force_authenticate(user=user)

        response = api_client.get(current_user_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["full_name"] == user.username

    def test_avatar_url_is_none_when_profile_has_no_avatar(
        self,
        api_client,
        current_user_url,
        user,
        user_profile,
    ):
        assert not user_profile.avatar

        api_client.force_authenticate(user=user)

        response = api_client.get(current_user_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["avatar_url"] is None

    def test_avatar_url_is_absolute_when_avatar_exists(
        self,
        api_client,
        current_user_url,
        user,
        user_profile_with_avatar,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.get(current_user_url)

        assert response.status_code == status.HTTP_200_OK

        avatar_url = response.data["avatar_url"]

        assert avatar_url is not None
        assert avatar_url.startswith("http://testserver/")
        assert avatar_url.endswith(user_profile_with_avatar.avatar.name)

    def test_avatar_url_contains_uploaded_avatar_path(
        self,
        api_client,
        current_user_url,
        user,
        user_profile_with_avatar,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.get(current_user_url)

        assert response.status_code == status.HTTP_200_OK

        avatar_url = response.data["avatar_url"]

        assert user_profile_with_avatar.avatar.url.lstrip("/") in avatar_url

    def test_student_role_is_returned_without_instructor_profile(
        self,
        api_client,
        current_user_url,
        user,
        user_profile,
    ):
        assert not hasattr(user_profile, "instructor_profile")

        api_client.force_authenticate(user=user)

        response = api_client.get(current_user_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["role"] == "student"

    def test_instructor_role_is_returned_with_instructor_profile(
        self,
        api_client,
        current_user_url,
        user,
        instructor_profile,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.get(current_user_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["role"] == "instructor"

    def test_get_does_not_modify_user(
        self,
        api_client,
        current_user_url,
        user,
    ):
        user.refresh_from_db()

        original_values = {
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }

        api_client.force_authenticate(user=user)

        response = api_client.get(current_user_url)

        assert response.status_code == status.HTTP_200_OK

        user.refresh_from_db()

        assert user.username == original_values["username"]
        assert user.email == original_values["email"]
        assert user.first_name == original_values["first_name"]
        assert user.last_name == original_values["last_name"]

    def test_get_does_not_modify_profile(
        self,
        api_client,
        current_user_url,
        user,
        user_profile,
    ):
        user_profile.refresh_from_db()

        original_values = {
            "website": user_profile.website,
            "country": user_profile.country,
            "timezone": user_profile.timezone,
            "language": user_profile.language,
            "date_of_birth": user_profile.date_of_birth,
            "company": user_profile.company,
            "job_title": user_profile.job_title,
        }

        api_client.force_authenticate(user=user)

        response = api_client.get(current_user_url)

        assert response.status_code == status.HTTP_200_OK

        user_profile.refresh_from_db()

        assert user_profile.website == original_values["website"]
        assert user_profile.country == original_values["country"]
        assert user_profile.timezone == original_values["timezone"]
        assert user_profile.language == original_values["language"]
        assert user_profile.date_of_birth == original_values["date_of_birth"]
        assert user_profile.company == original_values["company"]
        assert user_profile.job_title == original_values["job_title"]

    def test_post_is_not_allowed(
        self,
        api_client,
        current_user_url,
        user,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.post(
            current_user_url,
            {
                "first_name": "Updated",
                "last_name": "Name",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_put_is_not_allowed(
        self,
        api_client,
        current_user_url,
        user,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.put(
            current_user_url,
            {
                "first_name": "Updated",
                "last_name": "Name",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_patch_is_not_allowed(
        self,
        api_client,
        current_user_url,
        user,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.patch(
            current_user_url,
            {"first_name": "Updated"},
            format="json",
        )

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_delete_is_not_allowed(
        self,
        api_client,
        current_user_url,
        user,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.delete(current_user_url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_head_is_allowed(
        self,
        api_client,
        current_user_url,
        user,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.head(current_user_url)

        assert response.status_code == status.HTTP_200_OK

    def test_options_is_allowed(
        self,
        api_client,
        current_user_url,
        user,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.options(current_user_url)

        assert response.status_code == status.HTTP_200_OK


class TestTopNavUserSerializerThroughCurrentUserApiView:
    """Tests for TopNavUserSerializer."""

    def test_serializer_model(self):
        assert TopNavUserSerializer.Meta.model is User

    def test_serializer_fields(self):
        assert TopNavUserSerializer.Meta.fields == [
            "id",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "avatar_url",
            "role",
        ]

    def test_all_serializer_fields_are_read_only(self):
        serializer = TopNavUserSerializer()

        for field_name in TopNavUserSerializer.Meta.fields:
            assert serializer.fields[field_name].read_only is True

    def test_meta_read_only_fields_contains_all_fields(self):
        assert TopNavUserSerializer.Meta.read_only_fields == (
            TopNavUserSerializer.Meta.fields
        )

    def test_full_name_is_serializer_method_field(self):
        serializer = TopNavUserSerializer()

        assert isinstance(
            serializer.fields["full_name"],
            serializers.SerializerMethodField,
        )

    def test_avatar_url_is_serializer_method_field(self):
        serializer = TopNavUserSerializer()

        assert isinstance(
            serializer.fields["avatar_url"],
            serializers.SerializerMethodField,
        )

    def test_role_is_serializer_method_field(self):
        serializer = TopNavUserSerializer()

        assert isinstance(
            serializer.fields["role"],
            serializers.SerializerMethodField,
        )

    def test_unexposed_user_fields_are_not_serializer_fields(self):
        serializer = TopNavUserSerializer()

        assert "username" not in serializer.fields
        assert "password" not in serializer.fields
        assert "is_staff" not in serializer.fields
        assert "is_superuser" not in serializer.fields
        assert "is_active" not in serializer.fields
        assert "groups" not in serializer.fields
        assert "user_permissions" not in serializer.fields

    def test_serializer_returns_user_data(
        self,
        user,
    ):
        serializer = TopNavUserSerializer(user)

        data = serializer.data

        assert data["id"] == user.pk
        assert data["first_name"] == user.first_name
        assert data["last_name"] == user.last_name
        assert data["email"] == user.email
        assert data["full_name"] == "Current User"
        assert data["avatar_url"] is None
        assert data["role"] == "student"

    def test_serializer_returns_last_name_when_first_name_is_empty(
        self,
        user,
    ):
        user.first_name = ""
        user.last_name = "User"
        user.save(update_fields=["first_name", "last_name"])

        serializer = TopNavUserSerializer(user)

        assert serializer.data["full_name"] == "User"

    def test_serializer_returns_first_name_when_last_name_is_empty(
        self,
        user,
    ):
        user.first_name = "Current"
        user.last_name = ""
        user.save(update_fields=["first_name", "last_name"])

        serializer = TopNavUserSerializer(user)

        assert serializer.data["full_name"] == "Current"

    def test_serializer_uses_username_when_both_names_are_empty(
        self,
        user,
    ):
        user.first_name = ""
        user.last_name = ""
        user.save(update_fields=["first_name", "last_name"])

        serializer = TopNavUserSerializer(user)

        assert serializer.data["full_name"] == user.username

    def test_serializer_returns_student_role_without_instructor_profile(
        self,
        user,
        user_profile,
    ):
        serializer = TopNavUserSerializer(user)

        assert serializer.data["role"] == "student"

    def test_serializer_returns_instructor_role_with_instructor_profile(
        self,
        user,
        instructor_profile,
    ):
        serializer = TopNavUserSerializer(user)

        assert serializer.data["role"] == "instructor"

    def test_avatar_url_is_none_without_avatar(
        self,
        user,
        user_profile,
    ):
        serializer = TopNavUserSerializer(user)

        assert serializer.data["avatar_url"] is None

    def test_avatar_url_is_relative_without_request(
        self,
        user,
        user_profile_with_avatar,
    ):
        serializer = TopNavUserSerializer(user)

        avatar_url = serializer.data["avatar_url"]

        assert avatar_url == user_profile_with_avatar.avatar.url

    def test_avatar_url_is_absolute_with_request(
        self,
        api_request_factory,
        user,
        user_profile_with_avatar,
    ):
        request = api_request_factory.get("/")

        serializer = TopNavUserSerializer(
            user,
            context={"request": request},
        )

        avatar_url = serializer.data["avatar_url"]

        assert avatar_url.startswith("http://testserver/")
        assert avatar_url.endswith(user_profile_with_avatar.avatar.name)
