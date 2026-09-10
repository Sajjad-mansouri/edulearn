import uuid
from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.utils import timezone

from payments.models import Payment


class TestPayment:
    def test_creates_payment_with_required_fields(
        self,
        db,
        enrollment,
    ):
        payment = Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("49.99"),
        )

        assert payment.enrollment == enrollment
        assert payment.amount == Decimal("49.99")

    def test_id_is_uuid(
        self,
        db,
        enrollment,
    ):
        payment = Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("49.99"),
        )

        assert isinstance(payment.id, uuid.UUID)

    def test_id_is_primary_key(
        self,
        db,
        enrollment,
    ):
        payment = Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("49.99"),
        )

        assert payment._meta.pk.name == "id"
        assert payment.pk == payment.id

    def test_id_is_unique(
        self,
        db,
        enrollment,
        another_enrollment,
    ):
        first = Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("49.99"),
        )

        second = Payment.objects.create(
            enrollment=another_enrollment,
            amount=Decimal("99.99"),
        )

        assert first.id != second.id

    def test_currency_defaults_to_usd(
        self,
        db,
        enrollment,
    ):
        payment = Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("49.99"),
        )

        assert payment.currency == "usd"

    def test_status_defaults_to_pending(
        self,
        db,
        enrollment,
    ):
        payment = Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("49.99"),
        )

        assert payment.status == Payment.Status.PENDING

    def test_payment_type_defaults_to_one_time(
        self,
        db,
        enrollment,
    ):
        payment = Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("49.99"),
        )

        assert payment.payment_type == Payment.Type.ONE_TIME

    @pytest.mark.parametrize(
        "status",
        [
            Payment.Status.PENDING,
            Payment.Status.PROCESSING,
            Payment.Status.SUCCEEDED,
            Payment.Status.FAILED,
            Payment.Status.REFUNDED,
            Payment.Status.PARTIALLY_REFUNDED,
            Payment.Status.CANCELLED,
        ],
    )
    def test_accepts_all_defined_status_values(
        self,
        db,
        enrollment,
        status,
    ):
        payment = Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("49.99"),
            status=status,
        )

        assert payment.status == status

    @pytest.mark.parametrize(
        "payment_type",
        [
            Payment.Type.ONE_TIME,
            Payment.Type.SUBSCRIPTION,
            Payment.Type.INSTALLMENT,
        ],
    )
    def test_accepts_all_defined_payment_types(
        self,
        db,
        enrollment,
        payment_type,
    ):
        payment = Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("49.99"),
            payment_type=payment_type,
        )

        assert payment.payment_type == payment_type

    def test_str_returns_expected_representation(
        self,
        db,
        enrollment,
    ):
        payment = Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("49.99"),
            currency="usd",
            status=Payment.Status.SUCCEEDED,
        )

        assert str(payment) == (f"Payment {payment.id} - 49.99 usd - succeeded")

    def test_enrollment_reverse_relation(
        self,
        db,
        enrollment,
    ):
        payment = Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("49.99"),
        )

        assert list(enrollment.payments.all()) == [payment]

    def test_multiple_payments_can_belong_to_same_enrollment(
        self,
        db,
        enrollment,
    ):
        first = Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("49.99"),
        )

        second = Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("19.99"),
        )

        payments = list(enrollment.payments.all())

        assert len(payments) == 2
        assert {payment.pk for payment in payments} == {
            first.pk,
            second.pk,
        }

    def test_enrollment_is_required(
        self,
        db,
    ):
        payment = Payment(
            amount=Decimal("49.99"),
        )

        with pytest.raises(ValidationError) as exc_info:
            Payment._meta.get_field("enrollment").validate(
                payment.enrollment_id,
                payment,
            )

        assert exc_info.value.messages

    def test_amount_is_required(
        self,
        db,
        enrollment,
    ):
        payment = Payment(
            enrollment=enrollment,
        )

        with pytest.raises(ValidationError) as exc_info:
            Payment._meta.get_field("amount").validate(
                payment.amount,
                payment,
            )

        assert exc_info.value.messages

    def test_amount_preserves_decimal_precision(
        self,
        db,
        enrollment,
    ):
        payment = Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("1234.56"),
        )

        payment.refresh_from_db()

        assert payment.amount == Decimal("1234.56")

    def test_currency_can_be_customized(
        self,
        db,
        enrollment,
    ):
        payment = Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("49.99"),
            currency="eur",
        )

        assert payment.currency == "eur"

    def test_stripe_fields_are_optional(
        self,
        db,
        enrollment,
    ):
        payment = Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("49.99"),
        )

        assert payment.stripe_checkout_session_id is None
        assert payment.stripe_checkout_url is None
        assert payment.stripe_payment_intent_id is None
        assert payment.stripe_event_id is None
        assert payment.stripe_customer_id is None

    def test_optional_timestamps_are_none_by_default(
        self,
        db,
        enrollment,
    ):
        payment = Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("49.99"),
        )

        assert payment.paid_at is None
        assert payment.refunded_at is None

    def test_description_defaults_to_empty_string(
        self,
        db,
        enrollment,
    ):
        payment = Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("49.99"),
        )

        assert payment.description == ""

    def test_error_message_defaults_to_empty_string(
        self,
        db,
        enrollment,
    ):
        payment = Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("49.99"),
        )

        assert payment.error_message == ""

    def test_metadata_defaults_to_empty_dict(
        self,
        db,
        enrollment,
    ):
        payment = Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("49.99"),
        )

        assert payment.metadata == {}

    def test_metadata_stores_json_data(
        self,
        db,
        enrollment,
    ):
        metadata = {
            "source": "checkout",
            "attempt": 1,
            "customer_reference": "customer-123",
            "flags": ["test", "web"],
        }

        payment = Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("49.99"),
            metadata=metadata,
        )

        payment.refresh_from_db()

        assert payment.metadata == metadata

    def test_metadata_default_is_not_shared_between_instances(
        self,
        db,
        enrollment,
        another_enrollment,
    ):
        first = Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("49.99"),
        )

        second = Payment.objects.create(
            enrollment=another_enrollment,
            amount=Decimal("19.99"),
        )

        first.metadata["source"] = "checkout"

        assert first.metadata == {"source": "checkout"}
        assert second.metadata == {}

    def test_stripe_checkout_session_id_is_unique(
        self,
        db,
        enrollment,
        another_enrollment,
    ):
        Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("49.99"),
            stripe_checkout_session_id="cs_test_123",
        )

        with pytest.raises(IntegrityError):
            Payment.objects.create(
                enrollment=another_enrollment,
                amount=Decimal("19.99"),
                stripe_checkout_session_id="cs_test_123",
            )

    def test_stripe_payment_intent_id_is_unique(
        self,
        db,
        enrollment,
        another_enrollment,
    ):
        Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("49.99"),
            stripe_payment_intent_id="pi_test_123",
        )

        with pytest.raises(IntegrityError):
            Payment.objects.create(
                enrollment=another_enrollment,
                amount=Decimal("19.99"),
                stripe_payment_intent_id="pi_test_123",
            )

    def test_stripe_event_id_is_unique(
        self,
        db,
        enrollment,
        another_enrollment,
    ):
        Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("49.99"),
            stripe_event_id="evt_test_123",
        )

        with pytest.raises(IntegrityError):
            Payment.objects.create(
                enrollment=another_enrollment,
                amount=Decimal("19.99"),
                stripe_event_id="evt_test_123",
            )

    def test_nullable_stripe_unique_fields_allow_multiple_nulls(
        self,
        db,
        enrollment,
        another_enrollment,
    ):
        first = Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("49.99"),
        )

        second = Payment.objects.create(
            enrollment=another_enrollment,
            amount=Decimal("19.99"),
        )

        assert first.stripe_checkout_session_id is None
        assert second.stripe_checkout_session_id is None

    def test_stripe_checkout_url_is_stored(
        self,
        db,
        enrollment,
    ):
        payment = Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("49.99"),
            stripe_checkout_url="https://example.com/checkout/session",
        )

        payment.refresh_from_db()

        assert payment.stripe_checkout_url == "https://example.com/checkout/session"

    def test_stripe_customer_id_can_be_reused_across_payments(
        self,
        db,
        enrollment,
        another_enrollment,
    ):
        first = Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("49.99"),
            stripe_customer_id="cus_test_123",
        )

        second = Payment.objects.create(
            enrollment=another_enrollment,
            amount=Decimal("19.99"),
            stripe_customer_id="cus_test_123",
        )

        assert first.stripe_customer_id == second.stripe_customer_id

    def test_created_at_is_set_automatically(
        self,
        db,
        enrollment,
    ):
        before = timezone.now()

        payment = Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("49.99"),
        )

        after = timezone.now()

        assert before <= payment.created_at <= after

    def test_updated_at_is_set_automatically(
        self,
        db,
        enrollment,
    ):
        before = timezone.now()

        payment = Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("49.99"),
        )

        after = timezone.now()

        assert before <= payment.updated_at <= after

    def test_updated_at_changes_when_payment_is_updated(
        self,
        db,
        enrollment,
    ):
        payment = Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("49.99"),
        )

        original_updated_at = payment.updated_at

        payment.description = "Updated description"
        payment.save()
        payment.refresh_from_db()

        assert payment.updated_at >= original_updated_at

    def test_paid_at_can_be_set(
        self,
        db,
        enrollment,
    ):
        paid_at = timezone.now()

        payment = Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("49.99"),
            paid_at=paid_at,
        )

        payment.refresh_from_db()

        assert payment.paid_at == paid_at

    def test_refunded_at_can_be_set(
        self,
        db,
        enrollment,
    ):
        refunded_at = timezone.now()

        payment = Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("49.99"),
            refunded_at=refunded_at,
        )

        payment.refresh_from_db()

        assert payment.refunded_at == refunded_at

    def test_ordering_is_latest_created_first(
        self,
        db,
        enrollment,
        another_enrollment,
    ):
        first = Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("49.99"),
        )

        second = Payment.objects.create(
            enrollment=another_enrollment,
            amount=Decimal("19.99"),
        )

        earlier = timezone.now() - timedelta(minutes=1)
        later = timezone.now()

        Payment.objects.filter(pk=first.pk).update(
            created_at=earlier,
        )
        Payment.objects.filter(pk=second.pk).update(
            created_at=later,
        )

        payments = list(Payment.objects.all())

        assert payments == [second, first]

    def test_deleting_enrollment_is_protected(
        self,
        db,
        enrollment,
    ):
        Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("49.99"),
        )

        with pytest.raises(ProtectedError):
            enrollment.delete()

        assert enrollment.__class__.objects.filter(pk=enrollment.pk).exists()

    def test_payment_persists_after_reload(
        self,
        db,
        enrollment,
    ):
        payment = Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("49.99"),
            currency="usd",
            status=Payment.Status.SUCCEEDED,
            payment_type=Payment.Type.ONE_TIME,
            stripe_checkout_session_id="cs_test_123",
            stripe_payment_intent_id="pi_test_123",
            stripe_event_id="evt_test_123",
            stripe_customer_id="cus_test_123",
            description="Course payment",
            metadata={"source": "checkout"},
        )

        payment.refresh_from_db()

        assert payment.amount == Decimal("49.99")
        assert payment.currency == "usd"
        assert payment.status == Payment.Status.SUCCEEDED
        assert payment.payment_type == Payment.Type.ONE_TIME
        assert payment.stripe_checkout_session_id == "cs_test_123"
        assert payment.stripe_payment_intent_id == "pi_test_123"
        assert payment.stripe_event_id == "evt_test_123"
        assert payment.stripe_customer_id == "cus_test_123"
        assert payment.description == "Course payment"
        assert payment.metadata == {"source": "checkout"}
