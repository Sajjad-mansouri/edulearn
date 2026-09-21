from decimal import Decimal

import pytest

from payments.api.serializers import CheckoutSessionResponseSerializer
from payments.models import Payment


@pytest.fixture
def payment(db, enrollment):
    return Payment.objects.create(
        enrollment=enrollment,
        amount=Decimal("49.99"),
        currency="usd",
        status=Payment.Status.PENDING,
        payment_type=Payment.Type.ONE_TIME,
        stripe_checkout_session_id="cs_test_123",
        stripe_checkout_url="https://checkout.stripe.com/c/pay/cs_test_123",
        stripe_payment_intent_id="pi_test_123",
        stripe_customer_id="cus_test_123",
        description="Enrollment payment",
        metadata={"source": "checkout"},
    )


@pytest.mark.django_db
class TestCheckoutSessionResponseSerializer:
    def test_serializes_expected_fields(self, payment):
        serializer = CheckoutSessionResponseSerializer(payment)

        assert set(serializer.data) == {
            "id",
            "checkout_url",
            "amount",
            "currency",
        }

    def test_serializes_payment_id_as_string(self, payment):
        serializer = CheckoutSessionResponseSerializer(payment)

        assert serializer.data["id"] == str(payment.id)

    def test_maps_stripe_checkout_url_to_checkout_url(self, payment):
        serializer = CheckoutSessionResponseSerializer(payment)

        assert serializer.data["checkout_url"] == payment.stripe_checkout_url

    def test_serializes_amount_with_two_decimal_places(self, payment):
        serializer = CheckoutSessionResponseSerializer(payment)

        assert serializer.data["amount"] == "49.99"

    def test_serializes_currency(self, payment):
        serializer = CheckoutSessionResponseSerializer(payment)

        assert serializer.data["currency"] == "usd"

    def test_does_not_expose_internal_payment_fields(self, payment):
        serializer = CheckoutSessionResponseSerializer(payment)

        exposed_fields = set(serializer.data)

        internal_fields = {
            "enrollment",
            "status",
            "payment_type",
            "stripe_checkout_session_id",
            "stripe_payment_intent_id",
            "stripe_event_id",
            "stripe_customer_id",
            "created_at",
            "updated_at",
            "paid_at",
            "refunded_at",
            "description",
            "metadata",
            "error_message",
        }

        assert exposed_fields.isdisjoint(internal_fields)

    def test_checkout_url_is_null_when_payment_has_no_checkout_url(
        self,
        enrollment,
    ):
        payment = Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("25.00"),
            currency="usd",
            stripe_checkout_url=None,
        )

        serializer = CheckoutSessionResponseSerializer(payment)

        assert serializer.data["checkout_url"] is None

    def test_empty_checkout_url_is_serialized_as_empty_string(
        self,
        enrollment,
    ):
        payment = Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("25.00"),
            currency="usd",
            stripe_checkout_url="",
        )

        serializer = CheckoutSessionResponseSerializer(payment)

        assert serializer.data["checkout_url"] == ""

    @pytest.mark.parametrize(
        ("amount", "expected"),
        [
            (Decimal("0.00"), "0.00"),
            (Decimal("1.00"), "1.00"),
            (Decimal("10.50"), "10.50"),
            (Decimal("99999999.99"), "99999999.99"),
        ],
    )
    def test_serializes_valid_amounts(
        self,
        enrollment,
        amount,
        expected,
    ):
        payment = Payment.objects.create(
            enrollment=enrollment,
            amount=amount,
            currency="usd",
        )

        serializer = CheckoutSessionResponseSerializer(payment)

        assert serializer.data["amount"] == expected

    @pytest.mark.parametrize(
        "currency",
        [
            "usd",
            "eur",
            "gbp",
        ],
    )
    def test_serializes_currency_without_modification(
        self,
        enrollment,
        currency,
    ):
        payment = Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("49.99"),
            currency=currency,
        )

        serializer = CheckoutSessionResponseSerializer(payment)

        assert serializer.data["currency"] == currency

    def test_all_serializer_fields_are_read_only(self):
        serializer = CheckoutSessionResponseSerializer()

        assert serializer.fields["id"].read_only is True
        assert serializer.fields["checkout_url"].read_only is True
        assert serializer.fields["amount"].read_only is True
        assert serializer.fields["currency"].read_only is True

    def test_meta_fields_are_configured_correctly(self):
        serializer = CheckoutSessionResponseSerializer()

        assert serializer.Meta.fields == [
            "id",
            "checkout_url",
            "amount",
            "currency",
        ]

    def test_meta_read_only_fields_include_all_exposed_fields(self):
        serializer = CheckoutSessionResponseSerializer()

        assert serializer.Meta.read_only_fields == [
            "id",
            "checkout_url",
            "amount",
            "currency",
        ]

    def test_input_data_cannot_modify_read_only_fields(
        self,
        payment,
    ):
        original_values = {
            "id": str(payment.id),
            "checkout_url": payment.stripe_checkout_url,
            "amount": payment.amount,
            "currency": payment.currency,
        }

        serializer = CheckoutSessionResponseSerializer(
            payment,
            data={
                "id": "00000000-0000-0000-0000-000000000000",
                "checkout_url": "https://attacker.example/checkout",
                "amount": "1.00",
                "currency": "eur",
            },
        )

        assert serializer.is_valid()

        assert serializer.validated_data == {}

        payment.refresh_from_db()

        assert str(payment.id) == original_values["id"]
        assert payment.stripe_checkout_url == original_values["checkout_url"]
        assert payment.amount == original_values["amount"]
        assert payment.currency == original_values["currency"]

    def test_partial_input_also_cannot_modify_read_only_fields(
        self,
        payment,
    ):
        serializer = CheckoutSessionResponseSerializer(
            payment,
            data={
                "amount": "1.00",
                "currency": "eur",
            },
            partial=True,
        )

        assert serializer.is_valid()

        assert serializer.validated_data == {}

        payment.refresh_from_db()

        assert payment.amount == Decimal("49.99")
        assert payment.currency == "usd"

    def test_unknown_input_field_is_ignored(
        self,
        payment,
    ):
        serializer = CheckoutSessionResponseSerializer(
            payment,
            data={
                "amount": "10.00",
                "unexpected_field": "unexpected-value",
            },
        )

        assert serializer.is_valid()

        assert serializer.validated_data == {}

    def test_serialization_does_not_change_payment_instance(self, payment):
        original_values = {
            "id": payment.id,
            "amount": payment.amount,
            "currency": payment.currency,
            "checkout_url": payment.stripe_checkout_url,
            "status": payment.status,
            "payment_type": payment.payment_type,
        }

        serializer = CheckoutSessionResponseSerializer(payment)

        _ = serializer.data

        assert payment.id == original_values["id"]
        assert payment.amount == original_values["amount"]
        assert payment.currency == original_values["currency"]
        assert payment.stripe_checkout_url == original_values["checkout_url"]
        assert payment.status == original_values["status"]
        assert payment.payment_type == original_values["payment_type"]

    def test_serializer_output_matches_checkout_response_contract(
        self,
        payment,
    ):
        serializer = CheckoutSessionResponseSerializer(payment)

        assert serializer.data == {
            "id": str(payment.id),
            "checkout_url": payment.stripe_checkout_url,
            "amount": "49.99",
            "currency": "usd",
        }
