# accounts/tests/views/test_register_confirm.py

from unittest.mock import patch

import pytest
from django.contrib.auth.tokens import default_token_generator
from django.test import Client
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from accounts.tests.factories import UserFactory
from accounts.views import INTERNAL_REGISTRATION_SESSION_TOKEN


@pytest.mark.django_db
class TestRegisterConfirmView:
    """Tests for RegisterConfirmView."""

    @pytest.fixture
    def client(self):
        return Client()

    @pytest.fixture
    def user(self):
        return UserFactory(is_active=False)

    @pytest.fixture
    def uidb64(self, user):
        return urlsafe_base64_encode(force_bytes(user.pk))

    @pytest.fixture
    def token(self, user):
        return default_token_generator.make_token(user)

    @pytest.fixture
    def url(self, uidb64, token):
        return reverse(
            "accounts:register_confirm",
            kwargs={
                "uidb64": uidb64,
                "token": token,
            },
        )

    @patch("accounts.views.confirm_registration")
    def test_redirects_to_confirmation_url(
        self,
        mock_confirm_registration,
        client,
        url,
        token,
    ):
        response = client.get(url)

        assert response.status_code == 302

        assert response.url.endswith(
            url.replace(
                token,
                "confirm-registration",
            )
        )

        session = client.session
        assert session[INTERNAL_REGISTRATION_SESSION_TOKEN] == token

        mock_confirm_registration.assert_not_called()

    @patch("accounts.views.confirm_registration")
    def test_confirms_registration_when_session_token_is_valid(
        self,
        mock_confirm_registration,
        client,
        user,
        uidb64,
        token,
    ):
        session = client.session
        session[INTERNAL_REGISTRATION_SESSION_TOKEN] = token
        session.save()

        response = client.get(
            reverse(
                "accounts:register_confirm",
                kwargs={
                    "uidb64": uidb64,
                    "token": "confirm-registration",
                },
            )
        )

        assert response.status_code == 200
        assert response.context["validlink"] is True

        mock_confirm_registration.assert_called_once_with(user)

    def test_returns_invalid_context_for_invalid_token(
        self,
        client,
        uidb64,
    ):
        response = client.get(
            reverse(
                "accounts:register_confirm",
                kwargs={
                    "uidb64": uidb64,
                    "token": "invalid-token",
                },
            )
        )

        assert response.status_code == 200
        assert response.context["validlink"] is False

    def test_returns_invalid_context_for_invalid_uid(
        self,
        client,
        token,
    ):
        response = client.get(
            reverse(
                "accounts:register_confirm",
                kwargs={
                    "uidb64": "invalid",
                    "token": token,
                },
            )
        )

        assert response.status_code == 200
        assert response.context["validlink"] is False

    @patch("accounts.views.confirm_registration")
    def test_does_not_confirm_when_session_token_is_missing(
        self,
        mock_confirm_registration,
        client,
        uidb64,
    ):
        response = client.get(
            reverse(
                "accounts:register_confirm",
                kwargs={
                    "uidb64": uidb64,
                    "token": "confirm-registration",
                },
            )
        )

        assert response.status_code == 200
        assert response.context["validlink"] is False

        mock_confirm_registration.assert_not_called()
