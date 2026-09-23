import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory, force_authenticate

from profiles.api.serializers import ProfileSerializer
from profiles.api.views import ProfileApiView
from profiles.models import Profile

User = get_user_model()


@pytest.mark.django_db
class TestProfileApiView:
    """Tests for the authenticated user's profile API endpoint."""

    @pytest.fixture
    def user(self):
        """Create the account whose profile is returned by the endpoint."""
        return User.objects.create_user(
            username="profile_owner",
            email="profile-owner@example.com",
            password="test-password-123",
            first_name="Profile",
            last_name="Owner",
        )

    @pytest.fixture
    def another_user(self):
        """Create another account to verify profile ownership isolation."""
        return User.objects.create_user(
            username="another_user",
            email="another-user@example.com",
            password="test-password-123",
            first_name="Another",
            last_name="User",
        )

    @pytest.fixture
    def profile(self, user):
        """Create the authenticated user's profile."""
        return Profile.objects.create(
            user=user,
            website="https://example.com",
            country="Azerbaijan",
            timezone="Asia/Baku",
            language="en",
            date_of_birth="1995-05-15",
            company="Example Company",
            job_title="Software Engineer",
        )

    @pytest.fixture
    def another_profile(self, another_user):
        """Create a second user's profile."""
        return Profile.objects.create(
            user=another_user,
            website="https://another.example.com",
            country="Germany",
            timezone="Europe/Berlin",
            language="de",
            date_of_birth="1990-10-20",
            company="Another Company",
            job_title="Backend Developer",
        )

    @pytest.fixture
    def api_client(self):
        """Return a DRF API client."""
        from rest_framework.test import APIClient

        return APIClient()

    @pytest.fixture
    def profile_url(self):
        """Return the canonical profile endpoint URL."""
        return reverse("profile-api:profile")

    # ------------------------------------------------------------------
    # View configuration
    # ------------------------------------------------------------------

    def test_view_uses_profile_serializer(self):
        assert ProfileApiView.serializer_class is ProfileSerializer

    def test_view_is_retrieve_api_view(self):
        from rest_framework import generics

        assert issubclass(ProfileApiView, generics.RetrieveAPIView)

    # ------------------------------------------------------------------
    # get_object()
    # ------------------------------------------------------------------

    def test_get_object_returns_authenticated_users_profile(
        self,
        user,
        profile,
    ):
        factory = APIRequestFactory()
        request = factory.get("/profile/")
        force_authenticate(request, user=user)

        view = ProfileApiView()
        view.request = Request(request)

        result = view.get_object()

        assert result is profile
        assert result.user is user

    def test_get_object_never_returns_another_users_profile(
        self,
        user,
        profile,
        another_profile,
    ):
        factory = APIRequestFactory()
        request = factory.get("/profile/")
        force_authenticate(request, user=user)

        view = ProfileApiView()
        view.request = Request(request)

        result = view.get_object()

        assert result.pk == profile.pk
        assert result.pk != another_profile.pk
        assert result.user_id == user.pk
        assert result.user_id != another_profile.user_id

    def test_get_object_uses_request_user_profile_relation(
        self,
        user,
        profile,
    ):
        factory = APIRequestFactory()
        request = factory.get("/profile/")
        force_authenticate(request, user=user)

        view = ProfileApiView()
        view.request = Request(request)

        result = view.get_object()

        assert result == user.profile
        assert result == profile

    # ------------------------------------------------------------------
    # GET endpoint
    # ------------------------------------------------------------------

    def test_get_profile_returns_200(
        self,
        api_client,
        profile_url,
        user,
        profile,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.get(profile_url)

        assert response.status_code == status.HTTP_200_OK

    def test_get_profile_returns_authenticated_users_profile(
        self,
        api_client,
        profile_url,
        user,
        profile,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.get(profile_url)

        assert response.data["id"] == profile.pk

    def test_get_profile_returns_profile_data(
        self,
        api_client,
        profile_url,
        user,
        profile,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.get(profile_url)

        assert response.data["id"] == profile.pk
        assert response.data["first_name"] == user.first_name
        assert response.data["last_name"] == user.last_name
        assert response.data["email"] == user.email
        assert response.data["website"] == profile.website
        assert response.data["country"] == profile.country
        assert response.data["timezone"] == profile.timezone
        assert response.data["date_of_birth"] == "1995-05-15"
        assert response.data["company"] == profile.company
        assert response.data["job_title"] == profile.job_title

    def test_get_profile_does_not_return_another_users_profile(
        self,
        api_client,
        profile_url,
        user,
        profile,
        another_profile,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.get(profile_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == profile.pk
        assert response.data["id"] != another_profile.pk

    def test_get_profile_returns_correct_user_information(
        self,
        api_client,
        profile_url,
        user,
        profile,
        another_user,
        another_profile,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.get(profile_url)

        assert response.data["first_name"] == user.first_name
        assert response.data["last_name"] == user.last_name
        assert response.data["email"] == user.email

        assert response.data["first_name"] != another_user.first_name
        assert response.data["last_name"] != another_user.last_name
        assert response.data["email"] != another_user.email

    def test_get_profile_does_not_use_url_parameters_to_select_profile(
        self,
        api_client,
        profile_url,
        user,
        profile,
        another_profile,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.get(
            profile_url,
            data={"id": another_profile.pk},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == profile.pk

    def test_get_profile_ignores_arbitrary_query_parameters(
        self,
        api_client,
        profile_url,
        user,
        profile,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.get(
            profile_url,
            data={
                "user": "999999",
                "profile": "999999",
                "id": "999999",
                "username": "another_user",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == profile.pk

    # ------------------------------------------------------------------
    # Serializer shape through the API
    # ------------------------------------------------------------------

    def test_get_profile_contains_all_serializer_fields(
        self,
        api_client,
        profile_url,
        user,
        profile,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.get(profile_url)

        expected_fields = {
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

        assert set(response.data.keys()) == expected_fields

    def test_get_profile_returns_empty_related_collections_when_none_exist(
        self,
        api_client,
        profile_url,
        user,
        profile,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.get(profile_url)

        assert response.data["skills"] == []
        assert response.data["educations"] == []
        assert response.data["experiences"] == []
        assert response.data["languages"] == []
        assert response.data["social_links"] == []

    def test_get_profile_returns_null_avatar_when_not_set(
        self,
        api_client,
        profile_url,
        user,
        profile,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.get(profile_url)

        assert response.data["avatar"] in ("", None)

    # ------------------------------------------------------------------
    # Read-only behavior
    # ------------------------------------------------------------------

    def test_post_is_not_allowed(
        self,
        api_client,
        profile_url,
        user,
        profile,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.post(
            profile_url,
            data={"country": "Germany"},
            format="json",
        )

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_put_is_not_allowed(
        self,
        api_client,
        profile_url,
        user,
        profile,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.put(
            profile_url,
            data={"country": "Germany"},
            format="json",
        )

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_patch_is_not_allowed(
        self,
        api_client,
        profile_url,
        user,
        profile,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.patch(
            profile_url,
            data={"country": "Germany"},
            format="json",
        )

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_delete_is_not_allowed(
        self,
        api_client,
        profile_url,
        user,
        profile,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.delete(profile_url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_get_does_not_modify_profile(
        self,
        api_client,
        profile_url,
        user,
        profile,
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

        response = api_client.get(profile_url)

        assert response.status_code == status.HTTP_200_OK

        profile.refresh_from_db()

        assert profile.website == original_values["website"]
        assert profile.country == original_values["country"]
        assert profile.timezone == original_values["timezone"]
        assert profile.language == original_values["language"]
        assert profile.date_of_birth == original_values["date_of_birth"]
        assert profile.company == original_values["company"]
        assert profile.job_title == original_values["job_title"]

    # ------------------------------------------------------------------
    # Multiple authenticated users
    # ------------------------------------------------------------------

    def test_each_authenticated_user_receives_only_their_profile(
        self,
        api_client,
        profile_url,
        user,
        profile,
        another_user,
        another_profile,
    ):
        api_client.force_authenticate(user=user)

        first_response = api_client.get(profile_url)

        assert first_response.status_code == status.HTTP_200_OK
        assert first_response.data["id"] == profile.pk

        api_client.force_authenticate(user=another_user)

        second_response = api_client.get(profile_url)

        assert second_response.status_code == status.HTTP_200_OK
        assert second_response.data["id"] == another_profile.pk

        assert first_response.data["id"] != second_response.data["id"]

    def test_authentication_switch_changes_returned_profile(
        self,
        api_client,
        profile_url,
        user,
        profile,
        another_user,
        another_profile,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.get(profile_url)

        assert response.data["id"] == profile.pk

        api_client.force_authenticate(user=another_user)

        response = api_client.get(profile_url)

        assert response.data["id"] == another_profile.pk


@pytest.mark.django_db
class TestProfileSerializerThroughProfileApiView:
    """Tests for ProfileSerializer behavior as exposed by the profile API."""

    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username="serializer_user",
            email="serializer@example.com",
            password="test-password-123",
            first_name="Serializer",
            last_name="User",
        )

    @pytest.fixture
    def profile(self, user):
        return Profile.objects.create(
            user=user,
            website="https://example.com",
            country="Azerbaijan",
            timezone="Asia/Baku",
            language="en",
            date_of_birth="1994-03-10",
            company="Example Company",
            job_title="Django Developer",
        )

    @pytest.fixture
    def serializer(self, profile):
        return ProfileSerializer(profile)

    # ------------------------------------------------------------------
    # Serializer configuration
    # ------------------------------------------------------------------

    def test_serializer_uses_profile_model(self):
        assert ProfileSerializer.Meta.model is Profile

    def test_serializer_exposes_expected_fields(self, serializer):
        expected_fields = {
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

        assert set(serializer.fields.keys()) == expected_fields

    def test_user_information_fields_are_read_only(self, serializer):
        assert serializer.fields["first_name"].read_only is True
        assert serializer.fields["last_name"].read_only is True
        assert serializer.fields["email"].read_only is True

    def test_related_fields_are_read_only(self, serializer):
        assert serializer.fields["skills"].read_only is True
        assert serializer.fields["educations"].read_only is True
        assert serializer.fields["experiences"].read_only is True
        assert serializer.fields["languages"].read_only is True
        assert serializer.fields["social_links"].read_only is True

    def test_related_fields_are_many(self, serializer):
        assert serializer.fields["skills"].many is True
        assert serializer.fields["educations"].many is True
        assert serializer.fields["experiences"].many is True
        assert serializer.fields["languages"].many is True
        assert serializer.fields["social_links"].many is True

    def test_user_information_comes_from_related_user(
        self,
        serializer,
        user,
    ):
        data = serializer.data

        assert data["first_name"] == user.first_name
        assert data["last_name"] == user.last_name
        assert data["email"] == user.email

    def test_profile_fields_are_serialized(
        self,
        serializer,
        profile,
    ):
        data = serializer.data

        assert data["id"] == profile.pk
        assert data["website"] == "https://example.com"
        assert data["country"] == "Azerbaijan"
        assert data["timezone"] == "Asia/Baku"
        assert data["date_of_birth"] == "1994-03-10"
        assert data["company"] == "Example Company"
        assert data["job_title"] == "Django Developer"

    def test_language_profile_model_field_is_not_exposed(
        self,
        serializer,
    ):
        assert "language" not in serializer.fields

    def test_profile_social_url_fields_are_not_exposed(
        self,
        serializer,
    ):
        assert "linkedin" not in serializer.fields
        assert "github" not in serializer.fields

    def test_timestamps_are_not_exposed(self, serializer):
        assert "created_at" not in serializer.fields
        assert "updated_at" not in serializer.fields

    def test_user_relation_is_not_exposed(self, serializer):
        assert "user" not in serializer.fields

    # ------------------------------------------------------------------
    # Serializer output
    # ------------------------------------------------------------------

    def test_empty_related_managers_are_serialized_as_empty_lists(
        self,
        serializer,
    ):
        data = serializer.data

        assert data["skills"] == []
        assert data["educations"] == []
        assert data["experiences"] == []
        assert data["languages"] == []
        assert data["social_links"] == []

    # ------------------------------------------------------------------
    # Read-only fields cannot be supplied as writable input
    # ------------------------------------------------------------------

    def test_read_only_user_fields_are_not_writable(self, profile):
        serializer = ProfileSerializer(
            profile,
            data={
                "first_name": "Changed",
                "last_name": "Name",
                "email": "changed@example.com",
            },
            partial=True,
        )

        assert serializer.is_valid() is True

        assert "first_name" not in serializer.validated_data
        assert "last_name" not in serializer.validated_data
        assert "email" not in serializer.validated_data

    def test_read_only_related_fields_are_not_writable(self, profile):
        serializer = ProfileSerializer(
            profile,
            data={
                "skills": [],
                "educations": [],
                "experiences": [],
                "languages": [],
                "social_links": [],
            },
            partial=True,
        )

        assert serializer.is_valid() is True

        assert "skills" not in serializer.validated_data
        assert "educations" not in serializer.validated_data
        assert "experiences" not in serializer.validated_data
        assert "languages" not in serializer.validated_data
        assert "social_links" not in serializer.validated_data

    def test_user_fields_are_not_changed_by_read_only_input(
        self,
        profile,
        user,
    ):
        serializer = ProfileSerializer(
            profile,
            data={
                "first_name": "Changed",
                "last_name": "Changed",
                "email": "changed@example.com",
            },
            partial=True,
        )

        assert serializer.is_valid() is True
        serializer.save()

        user.refresh_from_db()

        assert user.first_name == "Serializer"
        assert user.last_name == "User"
        assert user.email == "serializer@example.com"

    # ------------------------------------------------------------------
    # Fields omitted from the serializer
    # ------------------------------------------------------------------

    def test_extra_fields_are_not_exposed_or_written(self, profile):
        serializer = ProfileSerializer(
            profile,
            data={
                "linkedin": "https://linkedin.com/example",
                "github": "https://github.com/example",
                "language": "fa",
                "created_at": "2020-01-01T00:00:00Z",
                "updated_at": "2020-01-01T00:00:00Z",
            },
            partial=True,
        )

        assert serializer.is_valid() is True

        assert "linkedin" not in serializer.validated_data
        assert "github" not in serializer.validated_data
        assert "language" not in serializer.validated_data
        assert "created_at" not in serializer.validated_data
        assert "updated_at" not in serializer.validated_data


@pytest.mark.django_db
class TestProfileApiViewMethods:
    """HTTP method behavior for the read-only profile endpoint."""

    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username="method_user",
            email="method-user@example.com",
            password="test-password-123",
        )

    @pytest.fixture
    def profile(self, user):
        return Profile.objects.create(user=user)

    @pytest.fixture
    def api_client(self):
        from rest_framework.test import APIClient

        return APIClient()

    @pytest.fixture
    def url(self):
        return reverse("profile-api:profile")

    def test_head_is_allowed(
        self,
        api_client,
        url,
        user,
        profile,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.head(url)

        assert response.status_code == status.HTTP_200_OK

    def test_options_is_allowed(
        self,
        api_client,
        url,
        user,
        profile,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.options(url)

        assert response.status_code == status.HTTP_200_OK
        assert "GET" in response.headers["Allow"]
