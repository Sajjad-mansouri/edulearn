import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError

pytestmark = pytest.mark.django_db


class TestLogoutApiView:
    url = reverse("accounts-api:logout")

    @pytest.fixture
    def valid_payload(self):
        return {
            "refresh": "valid-refresh-token",
        }

    @pytest.fixture
    def authenticated_client(self, api_client, test_user):
        api_client.force_authenticate(user=test_user)
        return api_client

    def test_logout_requires_authentication(
        self,
        api_client,
        valid_payload,
        mocker,
    ):
        logout_user = mocker.patch(
            "accounts.api.views.logout_user",
        )

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        logout_user.assert_not_called()

    def test_logout_returns_200_for_valid_refresh_token(
        self,
        authenticated_client,
        valid_payload,
        mocker,
    ):
        mocker.patch(
            "accounts.api.views.logout_user",
        )

        response = authenticated_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

    def test_logout_calls_logout_user_once(
        self,
        authenticated_client,
        valid_payload,
        mocker,
    ):
        logout_user = mocker.patch(
            "accounts.api.views.logout_user",
        )

        response = authenticated_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        logout_user.assert_called_once()

    def test_logout_calls_logout_user_with_refresh_token(
        self,
        authenticated_client,
        valid_payload,
        mocker,
    ):
        logout_user = mocker.patch(
            "accounts.api.views.logout_user",
        )

        response = authenticated_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        logout_user.assert_called_once_with(
            "valid-refresh-token",
        )

    def test_logout_passes_refresh_token_without_modification(
        self,
        authenticated_client,
        mocker,
    ):
        refresh_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.some-refresh-token"

        logout_user = mocker.patch(
            "accounts.api.views.logout_user",
        )

        response = authenticated_client.post(
            self.url,
            {"refresh": refresh_token},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        logout_user.assert_called_once_with(refresh_token)

    def test_logout_returns_expected_response(
        self,
        authenticated_client,
        valid_payload,
        mocker,
    ):
        mocker.patch(
            "accounts.api.views.logout_user",
        )

        response = authenticated_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            "detail": "Successfully logged out.",
        }

    def test_logout_response_contains_only_detail(
        self,
        authenticated_client,
        valid_payload,
        mocker,
    ):
        mocker.patch(
            "accounts.api.views.logout_user",
        )

        response = authenticated_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert set(response.data.keys()) == {"detail"}

    def test_logout_rejects_missing_refresh_field(
        self,
        authenticated_client,
        mocker,
    ):
        logout_user = mocker.patch(
            "accounts.api.views.logout_user",
        )

        response = authenticated_client.post(
            self.url,
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        logout_user.assert_not_called()

    def test_logout_rejects_empty_refresh_value(
        self,
        authenticated_client,
        mocker,
    ):
        logout_user = mocker.patch(
            "accounts.api.views.logout_user",
        )

        response = authenticated_client.post(
            self.url,
            {"refresh": ""},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        logout_user.assert_not_called()

    def test_logout_rejects_null_refresh_value(
        self,
        authenticated_client,
        mocker,
    ):
        logout_user = mocker.patch(
            "accounts.api.views.logout_user",
        )

        response = authenticated_client.post(
            self.url,
            {"refresh": None},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        logout_user.assert_not_called()

    def test_logout_rejects_empty_payload(
        self,
        authenticated_client,
        mocker,
    ):
        logout_user = mocker.patch(
            "accounts.api.views.logout_user",
        )

        response = authenticated_client.post(
            self.url,
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        logout_user.assert_not_called()

    def test_logout_does_not_call_service_when_serializer_is_invalid(
        self,
        authenticated_client,
        mocker,
    ):
        logout_user = mocker.patch(
            "accounts.api.views.logout_user",
        )

        response = authenticated_client.post(
            self.url,
            {"refresh": ""},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        logout_user.assert_not_called()

    def test_logout_returns_400_when_service_raises_validation_error(
        self,
        authenticated_client,
        valid_payload,
        mocker,
    ):
        mocker.patch(
            "accounts.api.views.logout_user",
            side_effect=ValidationError(
                {"refresh": "Invalid refresh token."},
            ),
        )

        response = authenticated_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "refresh" in response.data
        assert str(response.data["refresh"]) == ("Invalid refresh token.")

    def test_logout_does_not_return_success_when_service_fails(
        self,
        authenticated_client,
        valid_payload,
        mocker,
    ):
        mocker.patch(
            "accounts.api.views.logout_user",
            side_effect=ValidationError(
                {"refresh": "Invalid refresh token."},
            ),
        )

        response = authenticated_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.status_code != status.HTTP_200_OK

    def test_logout_service_validation_error_contains_expected_field(
        self,
        authenticated_client,
        valid_payload,
        mocker,
    ):
        mocker.patch(
            "accounts.api.views.logout_user",
            side_effect=ValidationError(
                {"refresh": "Invalid refresh token."},
            ),
        )

        response = authenticated_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert set(response.data.keys()) == {"refresh"}

    def test_logout_does_not_call_service_when_authentication_fails(
        self,
        api_client,
        valid_payload,
        mocker,
    ):
        logout_user = mocker.patch(
            "accounts.api.views.logout_user",
        )

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        logout_user.assert_not_called()

    def test_logout_rejects_get_request(
        self,
        authenticated_client,
    ):
        response = authenticated_client.get(self.url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_logout_rejects_put_request(
        self,
        authenticated_client,
    ):
        response = authenticated_client.put(
            self.url,
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_logout_rejects_patch_request(
        self,
        authenticated_client,
    ):
        response = authenticated_client.patch(
            self.url,
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_logout_rejects_delete_request(
        self,
        authenticated_client,
    ):
        response = authenticated_client.delete(self.url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_logout_does_not_call_service_for_unsupported_method(
        self,
        authenticated_client,
        mocker,
    ):
        logout_user = mocker.patch(
            "accounts.api.views.logout_user",
        )

        authenticated_client.get(self.url)

        authenticated_client.put(
            self.url,
            {},
            format="json",
        )

        authenticated_client.patch(
            self.url,
            {},
            format="json",
        )

        authenticated_client.delete(self.url)

        logout_user.assert_not_called()

    def test_logout_accepts_authenticated_user_without_specific_role(
        self,
        api_client,
        test_user,
        valid_payload,
        mocker,
    ):
        api_client.force_authenticate(user=test_user)

        mocker.patch(
            "accounts.api.views.logout_user",
        )

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

    def test_logout_does_not_mutate_payload(
        self,
        authenticated_client,
        valid_payload,
        mocker,
    ):
        mocker.patch(
            "accounts.api.views.logout_user",
        )

        original_payload = valid_payload.copy()

        response = authenticated_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert valid_payload == original_payload
