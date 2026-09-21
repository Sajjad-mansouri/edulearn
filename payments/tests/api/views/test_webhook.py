from unittest.mock import patch

import pytest
import stripe
from django.conf import settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def webhook_url():
    return reverse("payment_api:stripe-webhook")


@pytest.fixture
def stripe_signature():
    return "t=1234567890,v1=test_signature"


@pytest.fixture
def webhook_payload():
    return (
        b'{"id":"evt_test_123",'
        b'"type":"checkout.session.completed",'
        b'"data":{"object":{"id":"cs_test_123"}}}'
    )


@pytest.fixture
def checkout_session():
    return {
        "id": "cs_test_123",
        "object": "checkout.session",
        "metadata": {
            "payment_id": "payment_test_123",
        },
        "payment_intent": "pi_test_123",
    }


@pytest.fixture
def checkout_completed_event(checkout_session):
    return {
        "id": "evt_test_123",
        "type": "checkout.session.completed",
        "data": {
            "object": checkout_session,
        },
    }


@pytest.mark.django_db
class TestStripeWebhookApiView:
    def test_checkout_session_completed_returns_200(
        self,
        api_client,
        webhook_url,
        webhook_payload,
        stripe_signature,
        checkout_completed_event,
    ):
        with patch(
            "payments.api.views.stripe.Webhook.construct_event",
            return_value=checkout_completed_event,
        ) as mock_construct_event:
            with patch(
                "payments.api.views.handle_checkout_session_completed"
            ) as mock_handle:
                response = api_client.post(
                    webhook_url,
                    data=webhook_payload,
                    content_type="application/json",
                    HTTP_STRIPE_SIGNATURE=stripe_signature,
                )

        assert response.status_code == status.HTTP_200_OK

        mock_construct_event.assert_called_once_with(
            webhook_payload,
            stripe_signature,
            settings.STRIPE_WEBHOOK_SECRET,
        )

        mock_handle.assert_called_once_with(
            checkout_completed_event["data"]["object"],
        )

    def test_request_body_is_passed_to_stripe_unchanged(
        self,
        api_client,
        webhook_url,
        webhook_payload,
        stripe_signature,
        checkout_completed_event,
    ):
        with patch(
            "payments.api.views.stripe.Webhook.construct_event",
            return_value=checkout_completed_event,
        ) as mock_construct_event:
            with patch("payments.api.views.handle_checkout_session_completed"):
                response = api_client.post(
                    webhook_url,
                    data=webhook_payload,
                    content_type="application/json",
                    HTTP_STRIPE_SIGNATURE=stripe_signature,
                )

        assert response.status_code == status.HTTP_200_OK

        actual_payload = mock_construct_event.call_args.args[0]

        assert actual_payload == webhook_payload
        assert isinstance(actual_payload, bytes)

    def test_stripe_signature_header_is_passed_to_stripe(
        self,
        api_client,
        webhook_url,
        webhook_payload,
        stripe_signature,
        checkout_completed_event,
    ):
        with patch(
            "payments.api.views.stripe.Webhook.construct_event",
            return_value=checkout_completed_event,
        ) as mock_construct_event:
            with patch("payments.api.views.handle_checkout_session_completed"):
                response = api_client.post(
                    webhook_url,
                    data=webhook_payload,
                    content_type="application/json",
                    HTTP_STRIPE_SIGNATURE=stripe_signature,
                )

        assert response.status_code == status.HTTP_200_OK

        actual_signature = mock_construct_event.call_args.args[1]

        assert actual_signature == stripe_signature

    def test_configured_webhook_secret_is_passed_to_stripe(
        self,
        api_client,
        webhook_url,
        webhook_payload,
        stripe_signature,
        checkout_completed_event,
    ):
        with patch(
            "payments.api.views.stripe.Webhook.construct_event",
            return_value=checkout_completed_event,
        ) as mock_construct_event:
            with patch("payments.api.views.handle_checkout_session_completed"):
                response = api_client.post(
                    webhook_url,
                    data=webhook_payload,
                    content_type="application/json",
                    HTTP_STRIPE_SIGNATURE=stripe_signature,
                )

        assert response.status_code == status.HTTP_200_OK

        actual_secret = mock_construct_event.call_args.args[2]

        assert actual_secret == settings.STRIPE_WEBHOOK_SECRET

    def test_missing_signature_header_uses_empty_string(
        self,
        api_client,
        webhook_url,
        webhook_payload,
        checkout_completed_event,
    ):
        with patch(
            "payments.api.views.stripe.Webhook.construct_event",
            return_value=checkout_completed_event,
        ) as mock_construct_event:
            with patch("payments.api.views.handle_checkout_session_completed"):
                response = api_client.post(
                    webhook_url,
                    data=webhook_payload,
                    content_type="application/json",
                )

        assert response.status_code == status.HTTP_200_OK

        assert mock_construct_event.call_args.args[1] == ""

    def test_invalid_payload_returns_400(
        self,
        api_client,
        webhook_url,
        webhook_payload,
        stripe_signature,
    ):
        with patch(
            "payments.api.views.stripe.Webhook.construct_event",
            side_effect=ValueError("Invalid payload"),
        ) as mock_construct_event:
            with patch(
                "payments.api.views.handle_checkout_session_completed"
            ) as mock_handle:
                response = api_client.post(
                    webhook_url,
                    data=webhook_payload,
                    content_type="application/json",
                    HTTP_STRIPE_SIGNATURE=stripe_signature,
                )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.content == b""

        mock_construct_event.assert_called_once()
        mock_handle.assert_not_called()

    def test_invalid_signature_returns_400(
        self,
        api_client,
        webhook_url,
        webhook_payload,
        stripe_signature,
    ):
        signature_error = stripe.SignatureVerificationError(
            "Invalid signature",
            stripe_signature,
        )

        with patch(
            "payments.api.views.stripe.Webhook.construct_event",
            side_effect=signature_error,
        ) as mock_construct_event:
            with patch(
                "payments.api.views.handle_checkout_session_completed"
            ) as mock_handle:
                response = api_client.post(
                    webhook_url,
                    data=webhook_payload,
                    content_type="application/json",
                    HTTP_STRIPE_SIGNATURE=stripe_signature,
                )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.content == b""

        mock_construct_event.assert_called_once()
        mock_handle.assert_not_called()

    def test_invalid_payload_does_not_call_webhook_service(
        self,
        api_client,
        webhook_url,
        webhook_payload,
        stripe_signature,
    ):
        with patch(
            "payments.api.views.stripe.Webhook.construct_event",
            side_effect=ValueError,
        ):
            with patch(
                "payments.api.views.handle_checkout_session_completed"
            ) as mock_handle:
                response = api_client.post(
                    webhook_url,
                    data=webhook_payload,
                    content_type="application/json",
                    HTTP_STRIPE_SIGNATURE=stripe_signature,
                )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        mock_handle.assert_not_called()

    def test_invalid_signature_does_not_call_webhook_service(
        self,
        api_client,
        webhook_url,
        webhook_payload,
        stripe_signature,
    ):
        signature_error = stripe.SignatureVerificationError(
            "Invalid signature",
            stripe_signature,
        )

        with patch(
            "payments.api.views.stripe.Webhook.construct_event",
            side_effect=signature_error,
        ):
            with patch(
                "payments.api.views.handle_checkout_session_completed"
            ) as mock_handle:
                response = api_client.post(
                    webhook_url,
                    data=webhook_payload,
                    content_type="application/json",
                    HTTP_STRIPE_SIGNATURE=stripe_signature,
                )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        mock_handle.assert_not_called()

    def test_checkout_session_completed_passes_exact_session_object(
        self,
        api_client,
        webhook_url,
        webhook_payload,
        stripe_signature,
        checkout_session,
    ):
        event = {
            "id": "evt_test_123",
            "type": "checkout.session.completed",
            "data": {
                "object": checkout_session,
            },
        }

        with patch(
            "payments.api.views.stripe.Webhook.construct_event",
            return_value=event,
        ):
            with patch(
                "payments.api.views.handle_checkout_session_completed"
            ) as mock_handle:
                response = api_client.post(
                    webhook_url,
                    data=webhook_payload,
                    content_type="application/json",
                    HTTP_STRIPE_SIGNATURE=stripe_signature,
                )

        assert response.status_code == status.HTTP_200_OK

        mock_handle.assert_called_once_with(checkout_session)

        passed_session = mock_handle.call_args.args[0]

        assert passed_session is checkout_session

    def test_non_checkout_event_returns_200(
        self,
        api_client,
        webhook_url,
        webhook_payload,
        stripe_signature,
    ):
        event = {
            "id": "evt_payment_intent",
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_test_123",
                    "object": "payment_intent",
                },
            },
        }

        with patch(
            "payments.api.views.stripe.Webhook.construct_event",
            return_value=event,
        ):
            with patch(
                "payments.api.views.handle_checkout_session_completed"
            ) as mock_handle:
                response = api_client.post(
                    webhook_url,
                    data=webhook_payload,
                    content_type="application/json",
                    HTTP_STRIPE_SIGNATURE=stripe_signature,
                )

        assert response.status_code == status.HTTP_200_OK
        mock_handle.assert_not_called()

    @pytest.mark.parametrize(
        "event_type",
        [
            "payment_intent.succeeded",
            "payment_intent.payment_failed",
            "checkout.session.expired",
            "charge.succeeded",
            "charge.refunded",
            "customer.created",
        ],
    )
    def test_unhandled_event_types_are_acknowledged_without_processing(
        self,
        api_client,
        webhook_url,
        webhook_payload,
        stripe_signature,
        event_type,
    ):
        event = {
            "id": "evt_other",
            "type": event_type,
            "data": {
                "object": {
                    "id": "object_test_123",
                },
            },
        }

        with patch(
            "payments.api.views.stripe.Webhook.construct_event",
            return_value=event,
        ):
            with patch(
                "payments.api.views.handle_checkout_session_completed"
            ) as mock_handle:
                response = api_client.post(
                    webhook_url,
                    data=webhook_payload,
                    content_type="application/json",
                    HTTP_STRIPE_SIGNATURE=stripe_signature,
                )

        assert response.status_code == status.HTTP_200_OK
        mock_handle.assert_not_called()

    def test_checkout_session_completed_is_the_only_handled_event_type(
        self,
        api_client,
        webhook_url,
        webhook_payload,
        stripe_signature,
    ):
        event = {
            "id": "evt_test",
            "type": "checkout.session.expired",
            "data": {
                "object": {
                    "id": "cs_test_123",
                },
            },
        }

        with patch(
            "payments.api.views.stripe.Webhook.construct_event",
            return_value=event,
        ):
            with patch(
                "payments.api.views.handle_checkout_session_completed"
            ) as mock_handle:
                response = api_client.post(
                    webhook_url,
                    data=webhook_payload,
                    content_type="application/json",
                    HTTP_STRIPE_SIGNATURE=stripe_signature,
                )

        assert response.status_code == status.HTTP_200_OK
        mock_handle.assert_not_called()

    def test_webhook_service_exception_propagates(
        self,
        api_client,
        webhook_url,
        webhook_payload,
        stripe_signature,
        checkout_completed_event,
    ):
        service_error = RuntimeError("Webhook processing failed")

        with patch(
            "payments.api.views.stripe.Webhook.construct_event",
            return_value=checkout_completed_event,
        ):
            with patch(
                "payments.api.views.handle_checkout_session_completed",
                side_effect=service_error,
            ):
                with pytest.raises(RuntimeError, match="Webhook processing failed"):
                    api_client.post(
                        webhook_url,
                        data=webhook_payload,
                        content_type="application/json",
                        HTTP_STRIPE_SIGNATURE=stripe_signature,
                    )

    def test_webhook_service_is_called_only_once(
        self,
        api_client,
        webhook_url,
        webhook_payload,
        stripe_signature,
        checkout_completed_event,
    ):
        with patch(
            "payments.api.views.stripe.Webhook.construct_event",
            return_value=checkout_completed_event,
        ):
            with patch(
                "payments.api.views.handle_checkout_session_completed"
            ) as mock_handle:
                response = api_client.post(
                    webhook_url,
                    data=webhook_payload,
                    content_type="application/json",
                    HTTP_STRIPE_SIGNATURE=stripe_signature,
                )

        assert response.status_code == status.HTTP_200_OK
        mock_handle.assert_called_once()

    def test_post_accepts_empty_request_body_at_view_level(
        self,
        api_client,
        webhook_url,
        stripe_signature,
    ):
        with patch(
            "payments.api.views.stripe.Webhook.construct_event",
            side_effect=ValueError("Empty payload"),
        ) as mock_construct_event:
            with patch(
                "payments.api.views.handle_checkout_session_completed"
            ) as mock_handle:
                response = api_client.post(
                    webhook_url,
                    data=b"",
                    content_type="application/json",
                    HTTP_STRIPE_SIGNATURE=stripe_signature,
                )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        assert mock_construct_event.call_args.args[0] == b""
        mock_handle.assert_not_called()

    def test_webhook_does_not_require_authentication(
        self,
        api_client,
        webhook_url,
        webhook_payload,
        stripe_signature,
        checkout_completed_event,
    ):
        with patch(
            "payments.api.views.stripe.Webhook.construct_event",
            return_value=checkout_completed_event,
        ):
            with patch("payments.api.views.handle_checkout_session_completed"):
                response = api_client.post(
                    webhook_url,
                    data=webhook_payload,
                    content_type="application/json",
                    HTTP_STRIPE_SIGNATURE=stripe_signature,
                )

        assert response.status_code == status.HTTP_200_OK

    def test_webhook_has_no_authentication_classes(
        self,
    ):
        from payments.api.views import StripeWebhookApiView

        assert StripeWebhookApiView.authentication_classes == []

    def test_webhook_has_no_permission_classes(
        self,
    ):
        from payments.api.views import StripeWebhookApiView

        assert StripeWebhookApiView.permission_classes == []

    def test_webhook_dispatch_is_csrf_exempt(
        self,
    ):
        from payments.api.views import StripeWebhookApiView

        assert (
            getattr(
                StripeWebhookApiView.dispatch,
                "csrf_exempt",
                False,
            )
            is True
        )

    def test_response_has_empty_body_on_success(
        self,
        api_client,
        webhook_url,
        webhook_payload,
        stripe_signature,
        checkout_completed_event,
    ):
        with patch(
            "payments.api.views.stripe.Webhook.construct_event",
            return_value=checkout_completed_event,
        ):
            with patch("payments.api.views.handle_checkout_session_completed"):
                response = api_client.post(
                    webhook_url,
                    data=webhook_payload,
                    content_type="application/json",
                    HTTP_STRIPE_SIGNATURE=stripe_signature,
                )

        assert response.status_code == status.HTTP_200_OK
        assert response.content == b""

    def test_get_method_is_not_allowed(
        self,
        api_client,
        webhook_url,
    ):
        response = api_client.get(webhook_url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_put_method_is_not_allowed(
        self,
        api_client,
        webhook_url,
    ):
        response = api_client.put(webhook_url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_patch_method_is_not_allowed(
        self,
        api_client,
        webhook_url,
    ):
        response = api_client.patch(webhook_url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_delete_method_is_not_allowed(
        self,
        api_client,
        webhook_url,
    ):
        response = api_client.delete(webhook_url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_construct_event_is_not_called_for_non_post_requests(
        self,
        api_client,
        webhook_url,
    ):
        with patch(
            "payments.api.views.stripe.Webhook.construct_event"
        ) as mock_construct_event:
            api_client.get(webhook_url)
            api_client.put(webhook_url)
            api_client.patch(webhook_url)
            api_client.delete(webhook_url)

        mock_construct_event.assert_not_called()
