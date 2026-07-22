import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from profiles.api.serializers import ProfileSerializer, TopNavUserSerializer
from profiles.tests.factories import ProfileFactory


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
