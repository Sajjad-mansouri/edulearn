import logging
import uuid
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from django.core.exceptions import ValidationError

from enrollments.models import Enrollment
from payments.models import Payment
from payments.services.webhook import handle_checkout_session_completed


@pytest.fixture
def payment(db, enrollment):
    return Payment.objects.create(
        enrollment=enrollment,
        amount=Decimal("49.99"),
        currency="usd",
        status=Payment.Status.PENDING,
        payment_type=Payment.Type.ONE_TIME,
        description="Enrollment payment",
    )


@pytest.fixture
def checkout_session():
    session = MagicMock()
    session.to_dict.return_value = {
        "metadata": {
            "payment_id": "",
        },
        "payment_intent": "pi_test_123",
    }
    return session


@pytest.mark.django_db
class TestHandleCheckoutSessionCompleted:
    def test_missing_payment_id_is_ignored_and_logged(
        self,
        checkout_session,
        caplog,
    ):
        checkout_session.to_dict.return_value = {
            "metadata": {},
            "payment_intent": "pi_test_123",
        }

        with caplog.at_level(logging.ERROR):
            result = handle_checkout_session_completed(checkout_session)

        assert result is None
        assert (
            "checkout.session.completed missing payment_id in metadata"
        ) in caplog.text

    def test_empty_payment_id_is_ignored_and_logged(
        self,
        checkout_session,
        caplog,
    ):
        checkout_session.to_dict.return_value = {
            "metadata": {
                "payment_id": "",
            },
            "payment_intent": "pi_test_123",
        }

        with caplog.at_level(logging.ERROR):
            result = handle_checkout_session_completed(checkout_session)

        assert result is None
        assert (
            "checkout.session.completed missing payment_id in metadata"
        ) in caplog.text

    def test_missing_metadata_is_ignored_and_logged(
        self,
        checkout_session,
        caplog,
    ):
        checkout_session.to_dict.return_value = {
            "payment_intent": "pi_test_123",
        }

        with caplog.at_level(logging.ERROR):
            result = handle_checkout_session_completed(checkout_session)

        assert result is None
        assert (
            "checkout.session.completed missing payment_id in metadata"
        ) in caplog.text

    def test_missing_payment_is_ignored_and_logged(
        self,
        checkout_session,
        caplog,
    ):
        payment_id = uuid.uuid4()

        checkout_session.to_dict.return_value = {
            "metadata": {
                "payment_id": str(payment_id),
            },
            "payment_intent": "pi_test_123",
        }

        with caplog.at_level(logging.ERROR):
            result = handle_checkout_session_completed(checkout_session)

        assert result is None
        assert (f"Payment {payment_id} not found for completed session") in caplog.text

    def test_pending_payment_is_marked_succeeded(
        self,
        payment,
        checkout_session,
    ):
        checkout_session.to_dict.return_value = {
            "metadata": {
                "payment_id": str(payment.id),
            },
            "payment_intent": "pi_test_123",
        }

        result = handle_checkout_session_completed(checkout_session)

        assert result is None

        payment.refresh_from_db()

        assert payment.status == Payment.Status.SUCCEEDED
        assert payment.stripe_payment_intent_id == "pi_test_123"

    def test_pending_enrollment_is_activated_when_payment_succeeds(
        self,
        payment,
        checkout_session,
    ):
        payment.enrollment.status = Enrollment.Status.PENDING
        payment.enrollment.save(update_fields=["status"])

        checkout_session.to_dict.return_value = {
            "metadata": {
                "payment_id": str(payment.id),
            },
            "payment_intent": "pi_test_123",
        }

        handle_checkout_session_completed(checkout_session)

        payment.enrollment.refresh_from_db()

        assert payment.enrollment.status == Enrollment.Status.ACTIVE

    def test_active_enrollment_remains_active(
        self,
        payment,
        checkout_session,
    ):
        assert payment.enrollment.status == Enrollment.Status.ACTIVE

        checkout_session.to_dict.return_value = {
            "metadata": {
                "payment_id": str(payment.id),
            },
            "payment_intent": "pi_test_123",
        }

        handle_checkout_session_completed(checkout_session)

        payment.enrollment.refresh_from_db()

        assert payment.enrollment.status == Enrollment.Status.ACTIVE

    def test_payment_intent_is_saved_from_stripe_session(
        self,
        payment,
        checkout_session,
    ):
        checkout_session.to_dict.return_value = {
            "metadata": {
                "payment_id": str(payment.id),
            },
            "payment_intent": "pi_test_456",
        }

        handle_checkout_session_completed(checkout_session)

        payment.refresh_from_db()

        assert payment.stripe_payment_intent_id == "pi_test_456"

    def test_missing_payment_intent_clears_payment_intent_id(
        self,
        payment,
        checkout_session,
    ):
        payment.stripe_payment_intent_id = "pi_existing"
        payment.save(update_fields=["stripe_payment_intent_id"])

        checkout_session.to_dict.return_value = {
            "metadata": {
                "payment_id": str(payment.id),
            },
        }

        handle_checkout_session_completed(checkout_session)

        payment.refresh_from_db()

        assert payment.status == Payment.Status.SUCCEEDED
        assert payment.stripe_payment_intent_id is None

    def test_already_succeeded_payment_is_idempotent(
        self,
        payment,
        checkout_session,
    ):
        payment.status = Payment.Status.SUCCEEDED
        payment.stripe_payment_intent_id = "pi_original"
        payment.save(
            update_fields=[
                "status",
                "stripe_payment_intent_id",
            ]
        )

        checkout_session.to_dict.return_value = {
            "metadata": {
                "payment_id": str(payment.id),
            },
            "payment_intent": "pi_new",
        }

        handle_checkout_session_completed(checkout_session)

        payment.refresh_from_db()

        assert payment.status == Payment.Status.SUCCEEDED
        assert payment.stripe_payment_intent_id == "pi_original"

    def test_already_succeeded_payment_does_not_activate_pending_enrollment(
        self,
        payment,
        checkout_session,
    ):
        payment.status = Payment.Status.SUCCEEDED
        payment.stripe_payment_intent_id = "pi_original"
        payment.save(
            update_fields=[
                "status",
                "stripe_payment_intent_id",
            ]
        )

        payment.enrollment.status = Enrollment.Status.PENDING
        payment.enrollment.save(update_fields=["status"])

        checkout_session.to_dict.return_value = {
            "metadata": {
                "payment_id": str(payment.id),
            },
            "payment_intent": "pi_new",
        }

        handle_checkout_session_completed(checkout_session)

        payment.refresh_from_db()
        payment.enrollment.refresh_from_db()

        assert payment.status == Payment.Status.SUCCEEDED
        assert payment.stripe_payment_intent_id == "pi_original"
        assert payment.enrollment.status == Enrollment.Status.PENDING

    def test_processing_payment_is_marked_succeeded(
        self,
        payment,
        checkout_session,
    ):
        payment.status = Payment.Status.PROCESSING
        payment.save(update_fields=["status"])

        checkout_session.to_dict.return_value = {
            "metadata": {
                "payment_id": str(payment.id),
            },
            "payment_intent": "pi_processing",
        }

        handle_checkout_session_completed(checkout_session)

        payment.refresh_from_db()

        assert payment.status == Payment.Status.SUCCEEDED
        assert payment.stripe_payment_intent_id == "pi_processing"

    def test_failed_payment_is_marked_succeeded_when_completion_event_arrives(
        self,
        payment,
        checkout_session,
    ):
        payment.status = Payment.Status.FAILED
        payment.error_message = "Temporary Stripe failure"
        payment.save(
            update_fields=[
                "status",
                "error_message",
            ]
        )

        checkout_session.to_dict.return_value = {
            "metadata": {
                "payment_id": str(payment.id),
            },
            "payment_intent": "pi_recovered",
        }

        handle_checkout_session_completed(checkout_session)

        payment.refresh_from_db()

        assert payment.status == Payment.Status.SUCCEEDED
        assert payment.stripe_payment_intent_id == "pi_recovered"
        assert payment.error_message == "Temporary Stripe failure"

    def test_cancelled_payment_is_marked_succeeded_when_completion_event_arrives(
        self,
        payment,
        checkout_session,
    ):
        payment.status = Payment.Status.CANCELLED
        payment.save(update_fields=["status"])

        checkout_session.to_dict.return_value = {
            "metadata": {
                "payment_id": str(payment.id),
            },
            "payment_intent": "pi_cancelled",
        }

        handle_checkout_session_completed(checkout_session)

        payment.refresh_from_db()

        assert payment.status == Payment.Status.SUCCEEDED
        assert payment.stripe_payment_intent_id == "pi_cancelled"

    def test_only_payment_matching_metadata_is_updated(
        self,
        payment,
        checkout_session,
        another_enrollment,
    ):
        other_payment = Payment.objects.create(
            enrollment=another_enrollment,
            amount=Decimal("79.99"),
            currency="usd",
            status=Payment.Status.PENDING,
            payment_type=Payment.Type.ONE_TIME,
            description="Other enrollment payment",
        )

        checkout_session.to_dict.return_value = {
            "metadata": {
                "payment_id": str(payment.id),
            },
            "payment_intent": "pi_specific",
        }

        handle_checkout_session_completed(checkout_session)

        payment.refresh_from_db()
        other_payment.refresh_from_db()

        assert payment.status == Payment.Status.SUCCEEDED
        assert payment.stripe_payment_intent_id == "pi_specific"

        assert other_payment.status == Payment.Status.PENDING
        assert other_payment.stripe_payment_intent_id is None

    def test_payment_id_is_read_from_session_metadata(
        self,
        payment,
        checkout_session,
    ):
        checkout_session.to_dict.return_value = {
            "metadata": {
                "payment_id": str(payment.id),
                "unrelated_value": "ignored",
            },
            "payment_intent": "pi_metadata",
        }

        handle_checkout_session_completed(checkout_session)

        payment.refresh_from_db()

        assert payment.status == Payment.Status.SUCCEEDED
        assert payment.stripe_payment_intent_id == "pi_metadata"

    def test_session_is_converted_with_to_dict(
        self,
        payment,
        checkout_session,
    ):
        checkout_session.to_dict.return_value = {
            "metadata": {
                "payment_id": str(payment.id),
            },
            "payment_intent": "pi_dict",
        }

        handle_checkout_session_completed(checkout_session)

        checkout_session.to_dict.assert_called_once_with()

    def test_payment_update_does_not_change_amount_or_currency(
        self,
        payment,
        checkout_session,
    ):
        original_amount = payment.amount
        original_currency = payment.currency

        checkout_session.to_dict.return_value = {
            "metadata": {
                "payment_id": str(payment.id),
            },
            "payment_intent": "pi_immutable_fields",
        }

        handle_checkout_session_completed(checkout_session)

        payment.refresh_from_db()

        assert payment.amount == original_amount
        assert payment.currency == original_currency

    def test_payment_update_does_not_change_enrollment(
        self,
        payment,
        checkout_session,
    ):
        original_enrollment_id = payment.enrollment_id

        checkout_session.to_dict.return_value = {
            "metadata": {
                "payment_id": str(payment.id),
            },
            "payment_intent": "pi_enrollment",
        }

        handle_checkout_session_completed(checkout_session)

        payment.refresh_from_db()

        assert payment.enrollment_id == original_enrollment_id

    def test_invalid_payment_id_format_is_not_silently_ignored(
        self,
        checkout_session,
    ):
        checkout_session.to_dict.return_value = {
            "metadata": {
                "payment_id": "not-a-valid-payment-id",
            },
            "payment_intent": "pi_invalid_id",
        }

        with pytest.raises(ValidationError):
            handle_checkout_session_completed(checkout_session)
