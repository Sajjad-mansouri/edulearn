import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from profiles.api.serializers import ProfileSerializer, TopNavUserSerializer
from profiles.tests.factories import ProfileFactory, SkillFactory


@pytest.mark.django_db
class TestProfileApiView:
    """Tests for ProfileApiView."""

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def url(self):
        return reverse("profile-api:student_profile")

    def test_returns_authenticated_user_profile(
        self,
        api_client,
        url,
    ):
        """Authenticated users receive their profile."""
        profile = ProfileFactory()

        api_client.force_authenticate(user=profile.user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == ProfileSerializer(profile).data

    def test_returns_unauthorized_for_anonymous_user(
        self,
        api_client,
        url,
    ):
        """Anonymous users cannot access the endpoint."""
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestCurrentUserApiView:
    """Tests for CurrentUserApiView."""

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def url(self):
        return reverse("profile-api:current_user")

    def test_returns_authenticated_user(
        self,
        api_client,
        url,
    ):
        """Authenticated users receive their own information."""
        profile = ProfileFactory()

        api_client.force_authenticate(user=profile.user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == TopNavUserSerializer(profile.user).data

    def test_returns_unauthorized_for_anonymous_user(
        self,
        api_client,
        url,
    ):
        """Anonymous users cannot access the endpoint."""
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestSkillViewSet:
    """Tests for SkillViewSet."""

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def user(self):
        return ProfileFactory().user

    @pytest.fixture
    def delete_url(self):
        return reverse("profile-api:skill-delete")

    @pytest.fixture
    def create_url(self):
        return reverse("profile-api:skill-list")

    def test_creates_skill(
        self,
        api_client,
        user,
        create_url,
    ):
        """Authenticated users can create a skill."""
        api_client.force_authenticate(user=user)

        payload = {
            "name": "Python",
            "description": "Programming language",
        }

        response = api_client.post(create_url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED

        skill = user.profile.skills.get(name="Python")
        assert skill.description == "Programming language"

    def test_created_skill_belongs_to_authenticated_user(
        self,
        api_client,
        user,
        create_url,
    ):
        """perform_create() associates the skill with the authenticated profile."""
        api_client.force_authenticate(user=user)

        response = api_client.post(
            create_url,
            {
                "name": "Django",
                "description": "",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        skill = user.profile.skills.get(name="Django")
        assert skill.profile == user.profile

    def test_deletes_existing_skill(
        self,
        api_client,
        user,
        delete_url,
    ):
        """Users can delete one of their own skills."""
        skill = SkillFactory(
            profile=user.profile,
            name="Python",
        )

        api_client.force_authenticate(user=user)

        response = api_client.delete(
            delete_url,
            {"name": skill.name},
            format="json",
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not user.profile.skills.filter(pk=skill.pk).exists()

    def test_returns_bad_request_when_name_is_missing(
        self,
        api_client,
        user,
        delete_url,
    ):
        """Skill name is required."""
        api_client.force_authenticate(user=user)

        response = api_client.delete(
            delete_url,
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            "error": "Skill name is required",
        }

    def test_returns_not_found_for_unknown_skill(
        self,
        api_client,
        user,
        delete_url,
    ):
        """Deleting a nonexistent skill returns 404."""
        api_client.force_authenticate(user=user)

        response = api_client.delete(
            delete_url,
            {"name": "Unknown"},
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cannot_delete_another_users_skill(
        self,
        api_client,
        delete_url,
    ):
        """Users cannot delete another user's skill."""
        owner = ProfileFactory().user
        attacker = ProfileFactory().user

        skill = SkillFactory(
            profile=owner.profile,
            name="Python",
        )

        api_client.force_authenticate(user=attacker)

        response = api_client.delete(
            delete_url,
            {"name": skill.name},
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert owner.profile.skills.filter(pk=skill.pk).exists()

    def test_requires_authentication_for_create(
        self,
        api_client,
        create_url,
    ):
        """Anonymous users cannot create skills."""
        response = api_client.post(
            create_url,
            {
                "name": "Python",
                "description": "",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_requires_authentication_for_delete(
        self,
        api_client,
        delete_url,
    ):
        """Anonymous users cannot delete skills."""
        response = api_client.delete(
            delete_url,
            {"name": "Python"},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
