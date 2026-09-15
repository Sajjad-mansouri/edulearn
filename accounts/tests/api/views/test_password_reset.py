import pytest
from django.urls import reverse
from rest_framework import status

pytestmark = pytest.mark.django_db


class TestPasswordResetApiView:
    url = reverse("accounts-api:password_reset")

    @pytest.fixture
    def valid_payload(self):
        return {
            "email": "test_user@example.com",
        }

    def test_password_reset_returns_200_for_valid_email(
        self,
        api_client,
        valid_payload,
        mocker,
    ):
        mocker.patch(
            "accounts.api.views.send_password_reset_email",
        )

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

    def test_password_reset_allows_anonymous_users(
        self,
        api_client,
        valid_payload,
        mocker,
    ):
        mocker.patch(
            "accounts.api.views.send_password_reset_email",
        )

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

    def test_password_reset_calls_service_once(
        self,
        api_client,
        valid_payload,
        mocker,
    ):
        send_password_reset_email = mocker.patch(
            "accounts.api.views.send_password_reset_email",
        )

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        send_password_reset_email.assert_called_once()

    def test_password_reset_passes_request_to_service(
        self,
        api_client,
        valid_payload,
        mocker,
    ):
        send_password_reset_email = mocker.patch(
            "accounts.api.views.send_password_reset_email",
        )

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        send_password_reset_email.assert_called_once()

        call_kwargs = send_password_reset_email.call_args.kwargs

        assert call_kwargs["request"] is not None
        assert call_kwargs["request"].method == "POST"

    def test_password_reset_passes_validated_email_to_service(
        self,
        api_client,
        valid_payload,
        mocker,
    ):
        send_password_reset_email = mocker.patch(
            "accounts.api.views.send_password_reset_email",
        )

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        send_password_reset_email.assert_called_once_with(
            request=mocker.ANY,
            email="test_user@example.com",
        )

    def test_password_reset_returns_expected_message(
        self,
        api_client,
        valid_payload,
        mocker,
    ):
        mocker.patch(
            "accounts.api.views.send_password_reset_email",
        )

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            "detail": (
                "If an account with that email exists, "
                "a password reset link has been sent."
            ),
        }

    def test_password_reset_response_contains_only_detail(
        self,
        api_client,
        valid_payload,
        mocker,
    ):
        mocker.patch(
            "accounts.api.views.send_password_reset_email",
        )

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert set(response.data.keys()) == {"detail"}

    def test_password_reset_does_not_reveal_account_existence(
        self,
        api_client,
        mocker,
    ):
        send_password_reset_email = mocker.patch(
            "accounts.api.views.send_password_reset_email",
        )

        response = api_client.post(
            self.url,
            {"email": "nonexistent@example.com"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            "detail": (
                "If an account with that email exists, "
                "a password reset link has been sent."
            ),
        }

        send_password_reset_email.assert_called_once_with(
            request=mocker.ANY,
            email="nonexistent@example.com",
        )

    def test_password_reset_rejects_missing_email(
        self,
        api_client,
        mocker,
    ):
        send_password_reset_email = mocker.patch(
            "accounts.api.views.send_password_reset_email",
        )

        response = api_client.post(
            self.url,
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        send_password_reset_email.assert_not_called()

    def test_password_reset_rejects_empty_email(
        self,
        api_client,
        mocker,
    ):
        send_password_reset_email = mocker.patch(
            "accounts.api.views.send_password_reset_email",
        )

        response = api_client.post(
            self.url,
            {"email": ""},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        send_password_reset_email.assert_not_called()

    def test_password_reset_rejects_invalid_email(
        self,
        api_client,
        mocker,
    ):
        send_password_reset_email = mocker.patch(
            "accounts.api.views.send_password_reset_email",
        )

        response = api_client.post(
            self.url,
            {"email": "not-an-email"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        send_password_reset_email.assert_not_called()

    def test_password_reset_rejects_null_email(
        self,
        api_client,
        mocker,
    ):
        send_password_reset_email = mocker.patch(
            "accounts.api.views.send_password_reset_email",
        )

        response = api_client.post(
            self.url,
            {"email": None},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        send_password_reset_email.assert_not_called()

    def test_password_reset_does_not_call_service_when_serializer_is_invalid(
        self,
        api_client,
        mocker,
    ):
        send_password_reset_email = mocker.patch(
            "accounts.api.views.send_password_reset_email",
        )

        response = api_client.post(
            self.url,
            {"email": "invalid-email"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        send_password_reset_email.assert_not_called()

    def test_password_reset_accepts_uppercase_email(
        self,
        api_client,
        mocker,
    ):
        send_password_reset_email = mocker.patch(
            "accounts.api.views.send_password_reset_email",
        )

        response = api_client.post(
            self.url,
            {"email": "TEST_USER@EXAMPLE.COM"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        send_password_reset_email.assert_called_once_with(
            request=mocker.ANY,
            email="TEST_USER@EXAMPLE.COM",
        )

    def test_password_reset_preserves_email_passed_to_serializer(
        self,
        api_client,
        mocker,
    ):
        email = "User.Name+reset@example.com"

        send_password_reset_email = mocker.patch(
            "accounts.api.views.send_password_reset_email",
        )

        response = api_client.post(
            self.url,
            {"email": email},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        send_password_reset_email.assert_called_once_with(
            request=mocker.ANY,
            email=email,
        )

    def test_password_reset_does_not_mutate_request_payload(
        self,
        api_client,
        valid_payload,
        mocker,
    ):
        mocker.patch(
            "accounts.api.views.send_password_reset_email",
        )

        original_payload = valid_payload.copy()

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert valid_payload == original_payload

    def test_password_reset_propagates_unexpected_service_error(
        self,
        api_client,
        valid_payload,
        mocker,
    ):
        mocker.patch(
            "accounts.api.views.send_password_reset_email",
            side_effect=RuntimeError("Unexpected error"),
        )

        with pytest.raises(RuntimeError, match="Unexpected error"):
            api_client.post(
                self.url,
                valid_payload,
                format="json",
            )

    def test_password_reset_propagates_service_validation_error(
        self,
        api_client,
        valid_payload,
        mocker,
    ):
        from rest_framework.exceptions import ValidationError

        mocker.patch(
            "accounts.api.views.send_password_reset_email",
            side_effect=ValidationError(
                {"email": "Unable to process password reset."},
            ),
        )

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data
        assert str(response.data["email"]) == ("Unable to process password reset.")

    def test_password_reset_rejects_put_request(
        self,
        api_client,
    ):
        response = api_client.put(
            self.url,
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_password_reset_rejects_patch_request(
        self,
        api_client,
    ):
        response = api_client.patch(
            self.url,
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_password_reset_rejects_delete_request(
        self,
        api_client,
    ):
        response = api_client.delete(self.url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_password_reset_rejects_get_request(
        self,
        api_client,
    ):
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
