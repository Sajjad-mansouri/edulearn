# tests/accounts/test_jwt.py

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestTokenObtainPair:
    endpoint = reverse("accounts-api:token_obtain_pair")

    def test_returns_access_and_refresh_tokens(
        self,
        api_client,
        user,
    ):
        response = api_client.post(
            self.endpoint,
            {
                "username": "test_user",
                "password": "password123",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert "access" in data
        assert "refresh" in data

    def test_returns_401_for_invalid_password(
        self,
        api_client,
        user,
    ):
        response = api_client.post(
            self.endpoint,
            {
                "username": "test_user",
                "password": "wrong-password",
            },
        )

        assert response.status_code == 401

    def test_returns_401_for_unknown_user(
        self,
        api_client,
    ):
        response = api_client.post(
            self.endpoint,
            {
                "username": "unknown",
                "password": "password123",
            },
        )

        assert response.status_code == 401


@pytest.mark.django_db
class TestTokenRefresh:
    obtain_url = reverse("accounts-api:token_obtain_pair")
    refresh_url = reverse("accounts-api:token_refresh")

    def test_returns_new_access_token(
        self,
        api_client,
        user,
    ):
        tokens = api_client.post(
            self.obtain_url,
            {
                "username": "test_user",
                "password": "password123",
            },
        ).json()

        response = api_client.post(
            self.refresh_url,
            {
                "refresh": tokens["refresh"],
            },
        )

        assert response.status_code == 200
        assert "access" in response.json()

    def test_returns_401_for_invalid_refresh_token(
        self,
        api_client,
    ):
        response = api_client.post(
            self.refresh_url,
            {
                "refresh": "invalid-token",
            },
        )

        assert response.status_code == 401


@pytest.mark.django_db
class TestTokenVerify:
    obtain_url = reverse("accounts-api:token_obtain_pair")
    verify_url = reverse("accounts-api:token_verify")

    def test_verifies_valid_access_token(
        self,
        api_client,
        user,
    ):
        tokens = api_client.post(
            self.obtain_url,
            {
                "username": "test_user",
                "password": "password123",
            },
        ).json()

        response = api_client.post(
            self.verify_url,
            {
                "token": tokens["access"],
            },
        )

        assert response.status_code == 200
        assert response.json() == {}

    def test_returns_401_for_invalid_token(
        self,
        api_client,
    ):
        response = api_client.post(
            self.verify_url,
            {
                "token": "invalid-token",
            },
        )

        assert response.status_code == 401
