from datetime import date

import pytest
from django.urls import reverse
from rest_framework import serializers, status
from rest_framework.test import APIClient

from accounts.models import User
from profiles.api.serializers import ProfileSerializer, StudentProfileSerializer
from profiles.api.views import StudentProfileApiView
from profiles.models import Profile, StudentProfile


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="student_profile_owner",
        email="student_profile_owner@example.com",
        password="test-password",
        first_name="Student",
        last_name="Profile",
    )


@pytest.fixture
def another_user(db):
    return User.objects.create_user(
        username="another_student",
        email="another_student@example.com",
        password="test-password",
        first_name="Another",
        last_name="Student",
    )


@pytest.fixture
def profile(user):
    return Profile.objects.create(
        user=user,
        website="https://example.com",
        country="Azerbaijan",
        timezone="Asia/Baku",
        language="en",
        date_of_birth=date(1995, 5, 15),
        company="Example Company",
        job_title="Student",
    )


@pytest.fixture
def another_profile(another_user):
    return Profile.objects.create(
        user=another_user,
        website="https://another.example.com",
        country="Germany",
        timezone="Europe/Berlin",
        language="de",
        date_of_birth=date(1998, 8, 20),
        company="Another Company",
        job_title="Student",
    )


@pytest.fixture
def student_profile(profile):
    return StudentProfile.objects.create(
        profile=profile,
        cover="",
        biography="Student biography",
        headline="Software engineering student",
    )


@pytest.fixture
def another_student_profile(another_profile):
    return StudentProfile.objects.create(
        profile=another_profile,
        cover="",
        biography="Another student biography",
        headline="Another student",
    )


@pytest.fixture
def student_profile_url():
    return reverse("profile-api:student_profile")


class TestStudentProfileApiView:
    """Tests for StudentProfileApiView."""

    def test_view_uses_student_profile_serializer(self):
        assert StudentProfileApiView.serializer_class is StudentProfileSerializer

    def test_get_object_returns_authenticated_users_student_profile(
        self,
        api_client,
        user,
        student_profile,
    ):
        api_client.force_authenticate(user=user)

        view = StudentProfileApiView()
        view.request = api_client.get("/").wsgi_request
        view.request.user = user

        result = view.get_object()

        assert result == student_profile

    def test_get_object_does_not_return_another_users_student_profile(
        self,
        api_client,
        user,
        student_profile,
        another_student_profile,
    ):
        api_client.force_authenticate(user=user)

        view = StudentProfileApiView()
        view.request = api_client.get("/").wsgi_request
        view.request.user = user
        result = view.get_object()

        assert result == student_profile
        assert result != another_student_profile

    def test_get_returns_authenticated_users_student_profile(
        self,
        api_client,
        student_profile_url,
        user,
        student_profile,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.get(student_profile_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["biography"] == student_profile.biography
        assert response.data["headline"] == student_profile.headline

    def test_get_does_not_return_another_users_student_profile(
        self,
        api_client,
        student_profile_url,
        user,
        student_profile,
        another_student_profile,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.get(student_profile_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["biography"] == student_profile.biography
        assert response.data["headline"] == student_profile.headline
        assert response.data["biography"] != another_student_profile.biography
        assert response.data["headline"] != another_student_profile.headline

    def test_query_parameters_do_not_change_selected_student_profile(
        self,
        api_client,
        student_profile_url,
        user,
        student_profile,
        another_student_profile,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.get(
            student_profile_url,
            {
                "user": another_student_profile.profile.user_id,
                "profile": another_student_profile.profile_id,
                "id": another_student_profile.pk,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["biography"] == student_profile.biography
        assert response.data["headline"] == student_profile.headline

    def test_get_returns_nested_profile(
        self,
        api_client,
        student_profile_url,
        user,
        profile,
        student_profile,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.get(student_profile_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["profile"]["id"] == profile.pk
        assert response.data["profile"]["first_name"] == user.first_name
        assert response.data["profile"]["last_name"] == user.last_name
        assert response.data["profile"]["email"] == user.email

    def test_get_returns_nested_profile_values(
        self,
        api_client,
        student_profile_url,
        user,
        profile,
        student_profile,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.get(student_profile_url)

        nested_profile = response.data["profile"]

        assert nested_profile["website"] == profile.website
        assert nested_profile["country"] == profile.country
        assert nested_profile["timezone"] == profile.timezone
        assert nested_profile["date_of_birth"] == "1995-05-15"
        assert nested_profile["company"] == profile.company
        assert nested_profile["job_title"] == profile.job_title

    def test_get_returns_student_profile_fields(
        self,
        api_client,
        student_profile_url,
        user,
        student_profile,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.get(student_profile_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["biography"] == student_profile.biography
        assert response.data["headline"] == student_profile.headline

    def test_get_returns_expected_top_level_fields(
        self,
        api_client,
        student_profile_url,
        user,
        student_profile,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.get(student_profile_url)

        assert response.status_code == status.HTTP_200_OK

        assert set(response.data.keys()) == {
            "profile",
            "cover",
            "biography",
            "headline",
        }

    def test_get_returns_expected_nested_profile_fields(
        self,
        api_client,
        student_profile_url,
        user,
        student_profile,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.get(student_profile_url)

        assert response.status_code == status.HTTP_200_OK

        assert set(response.data["profile"].keys()) == {
            "id",
            "first_name",
            "last_name",
            "email",
            "avatar",
            "website",
            "country",
            "timezone",
            "date_of_birth",
            "company",
            "job_title",
            "skills",
            "educations",
            "experiences",
            "languages",
            "social_links",
        }

    def test_get_returns_empty_nested_profile_collections(
        self,
        api_client,
        student_profile_url,
        user,
        student_profile,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.get(student_profile_url)

        assert response.status_code == status.HTTP_200_OK

        nested_profile = response.data["profile"]

        assert nested_profile["skills"] == []
        assert nested_profile["educations"] == []
        assert nested_profile["experiences"] == []
        assert nested_profile["languages"] == []
        assert nested_profile["social_links"] == []

    def test_get_returns_empty_cover_when_not_set(
        self,
        api_client,
        student_profile_url,
        user,
        student_profile,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.get(student_profile_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["cover"] is None

    def test_get_does_not_modify_profile(
        self,
        api_client,
        student_profile_url,
        user,
        profile,
        student_profile,
    ):
        api_client.force_authenticate(user=user)

        profile.refresh_from_db()

        original_values = {
            "website": profile.website,
            "country": profile.country,
            "timezone": profile.timezone,
            "language": profile.language,
            "date_of_birth": profile.date_of_birth,
            "company": profile.company,
            "job_title": profile.job_title,
        }

        response = api_client.get(student_profile_url)

        assert response.status_code == status.HTTP_200_OK

        profile.refresh_from_db()

        assert profile.website == original_values["website"]
        assert profile.country == original_values["country"]
        assert profile.timezone == original_values["timezone"]
        assert profile.language == original_values["language"]
        assert profile.date_of_birth == original_values["date_of_birth"]
        assert profile.company == original_values["company"]
        assert profile.job_title == original_values["job_title"]

    def test_get_does_not_modify_student_profile(
        self,
        api_client,
        student_profile_url,
        user,
        student_profile,
    ):
        api_client.force_authenticate(user=user)

        student_profile.refresh_from_db()

        original_values = {
            "cover": student_profile.cover.name,
            "biography": student_profile.biography,
            "headline": student_profile.headline,
        }

        response = api_client.get(student_profile_url)

        assert response.status_code == status.HTTP_200_OK

        student_profile.refresh_from_db()

        assert student_profile.cover.name == original_values["cover"]
        assert student_profile.biography == original_values["biography"]
        assert student_profile.headline == original_values["headline"]

    def test_post_is_not_allowed(
        self,
        api_client,
        student_profile_url,
        user,
        student_profile,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.post(
            student_profile_url,
            {
                "biography": "Updated biography",
                "headline": "Updated headline",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_put_is_not_allowed(
        self,
        api_client,
        student_profile_url,
        user,
        student_profile,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.put(
            student_profile_url,
            {
                "biography": "Updated biography",
                "headline": "Updated headline",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_patch_is_not_allowed(
        self,
        api_client,
        student_profile_url,
        user,
        student_profile,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.patch(
            student_profile_url,
            {"headline": "Updated headline"},
            format="json",
        )

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_delete_is_not_allowed(
        self,
        api_client,
        student_profile_url,
        user,
        student_profile,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.delete(student_profile_url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_head_is_allowed(
        self,
        api_client,
        student_profile_url,
        user,
        student_profile,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.head(student_profile_url)

        assert response.status_code == status.HTTP_200_OK

    def test_options_is_allowed(
        self,
        api_client,
        student_profile_url,
        user,
        student_profile,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.options(student_profile_url)

        assert response.status_code == status.HTTP_200_OK


class TestStudentProfileSerializerThroughApiView:
    """Tests StudentProfileSerializer configuration."""

    def test_serializer_model(self):
        assert StudentProfileSerializer.Meta.model is StudentProfile

    def test_serializer_fields(self):
        assert StudentProfileSerializer.Meta.fields == [
            "profile",
            "cover",
            "biography",
            "headline",
        ]

    def test_profile_field_uses_profile_serializer(self):
        serializer = StudentProfileSerializer()

        profile_field = serializer.fields["profile"]

        assert isinstance(profile_field, ProfileSerializer)
        assert not isinstance(profile_field, serializers.ListSerializer)
        assert profile_field.read_only is True

    def test_student_profile_fields_are_present(self):
        serializer = StudentProfileSerializer()

        assert "cover" in serializer.fields
        assert "biography" in serializer.fields
        assert "headline" in serializer.fields

    def test_profile_field_is_read_only(self):
        serializer = StudentProfileSerializer()

        assert serializer.fields["profile"].read_only is True

    def test_cover_is_not_read_only(self):
        serializer = StudentProfileSerializer()

        assert serializer.fields["cover"].read_only is False

    def test_biography_is_not_read_only(self):
        serializer = StudentProfileSerializer()

        assert serializer.fields["biography"].read_only is False

    def test_headline_is_not_read_only(self):
        serializer = StudentProfileSerializer()

        assert serializer.fields["headline"].read_only is False

    def test_unexpected_fields_are_not_serializer_fields(self):
        serializer = StudentProfileSerializer()

        assert "application_status" not in serializer.fields
        assert "is_verified" not in serializer.fields
        assert "profile_id" not in serializer.fields
        assert "user" not in serializer.fields


class TestStudentProfileApiViewIsolation:
    """Tests that the endpoint is scoped to the authenticated user."""

    def test_authenticated_users_receive_their_own_profiles(
        self,
        api_client,
        student_profile_url,
        user,
        another_user,
        student_profile,
        another_student_profile,
    ):
        api_client.force_authenticate(user=user)

        first_response = api_client.get(student_profile_url)

        assert first_response.status_code == status.HTTP_200_OK
        assert first_response.data["profile"]["id"] == student_profile.profile_id

        api_client.force_authenticate(user=another_user)

        second_response = api_client.get(student_profile_url)

        assert second_response.status_code == status.HTTP_200_OK
        assert (
            second_response.data["profile"]["id"] == another_student_profile.profile_id
        )

        assert (
            first_response.data["profile"]["id"]
            != second_response.data["profile"]["id"]
        )

    def test_user_cannot_select_another_student_profile_by_query_parameter(
        self,
        api_client,
        student_profile_url,
        user,
        student_profile,
        another_student_profile,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.get(
            student_profile_url,
            {"student_profile_id": another_student_profile.pk},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["profile"]["id"] == student_profile.profile_id
        assert response.data["profile"]["id"] != another_student_profile.profile_id


class TestStudentProfileApiViewMethods:
    """Tests HTTP method behavior inherited from RetrieveAPIView."""

    @pytest.mark.parametrize(
        "method",
        ["post", "put", "patch", "delete"],
    )
    def test_unsupported_methods_return_405(
        self,
        api_client,
        student_profile_url,
        user,
        student_profile,
        method,
    ):
        api_client.force_authenticate(user=user)

        response = getattr(api_client, method)(student_profile_url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
