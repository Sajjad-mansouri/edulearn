from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from instructors.api.serializers.transaction import TransactionSerializer
from payments.models import Payment


@pytest.mark.django_db
class TestTransactionSerializer:
    def test_serializer_has_expected_fields(self):
        serializer = TransactionSerializer()

        assert set(serializer.fields) == {
            "id",
            "type",
            "amount",
            "date",
            "status",
            "course",
        }

    def test_id_is_read_only(self):
        serializer = TransactionSerializer()

        assert serializer.fields["id"].read_only is True

    def test_type_is_read_only(self):
        serializer = TransactionSerializer()

        assert serializer.fields["type"].read_only is True

    def test_date_is_read_only(self):
        serializer = TransactionSerializer()

        assert serializer.fields["date"].read_only is True

    def test_course_is_read_only(self):
        serializer = TransactionSerializer()

        assert serializer.fields["course"].read_only is True

    def test_amount_is_required(self):
        serializer = TransactionSerializer(data={})

        assert not serializer.is_valid()
        assert "amount" in serializer.errors

    def test_status_is_not_required_because_model_has_default(self):
        serializer = TransactionSerializer(data={"amount": "100.00"})

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["amount"] == Decimal("100.00")
        assert "status" not in serializer.validated_data

    def test_amount_accepts_valid_decimal(self):
        serializer = TransactionSerializer(
            data={
                "amount": "125.50",
                "status": Payment.Status.SUCCEEDED,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["amount"] == Decimal("125.50")

    def test_amount_rejects_null(self):
        serializer = TransactionSerializer(
            data={
                "amount": None,
                "status": Payment.Status.SUCCEEDED,
            }
        )

        assert not serializer.is_valid()
        assert "amount" in serializer.errors

    def test_amount_rejects_blank_string(self):
        serializer = TransactionSerializer(
            data={
                "amount": "",
                "status": Payment.Status.SUCCEEDED,
            }
        )

        assert not serializer.is_valid()
        assert "amount" in serializer.errors

    def test_amount_rejects_more_than_two_decimal_places(self):
        serializer = TransactionSerializer(
            data={
                "amount": "100.123",
                "status": Payment.Status.SUCCEEDED,
            }
        )

        assert not serializer.is_valid()
        assert "amount" in serializer.errors

    def test_amount_rejects_more_than_ten_total_digits(self):
        serializer = TransactionSerializer(
            data={
                "amount": "1234567890.00",
                "status": Payment.Status.SUCCEEDED,
            }
        )

        assert not serializer.is_valid()
        assert "amount" in serializer.errors

    def test_amount_accepts_zero(self):
        serializer = TransactionSerializer(
            data={
                "amount": "0.00",
                "status": Payment.Status.SUCCEEDED,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["amount"] == Decimal("0.00")

    def test_amount_accepts_negative_value_at_serializer_level(self):
        serializer = TransactionSerializer(
            data={
                "amount": "-10.00",
                "status": Payment.Status.SUCCEEDED,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["amount"] == Decimal("-10.00")

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
    def test_status_accepts_valid_payment_statuses(self, status):
        serializer = TransactionSerializer(
            data={
                "amount": "100.00",
                "status": status,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["status"] == status

    def test_status_rejects_invalid_value(self):
        serializer = TransactionSerializer(
            data={
                "amount": "100.00",
                "status": "invalid-status",
            }
        )

        assert not serializer.is_valid()
        assert "status" in serializer.errors

    def test_type_always_returns_sale(self, instructor_enrollment):
        payment = Payment(
            enrollment=instructor_enrollment,
            amount=Decimal("100.00"),
            status=Payment.Status.SUCCEEDED,
        )
        serializer = TransactionSerializer()

        assert serializer.get_type(payment) == "sale"

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
    def test_type_is_sale_for_every_status(
        self,
        instructor_enrollment,
        status,
    ):
        payment = Payment(
            enrollment=instructor_enrollment,
            amount=Decimal("100.00"),
            status=status,
        )
        serializer = TransactionSerializer()

        assert serializer.get_type(payment) == "sale"

    def test_date_returns_paid_at_for_succeeded_payment(
        self,
        instructor_enrollment,
    ):
        paid_at = timezone.now()
        payment = Payment(
            enrollment=instructor_enrollment,
            amount=Decimal("100.00"),
            status=Payment.Status.SUCCEEDED,
            paid_at=paid_at,
        )
        serializer = TransactionSerializer()

        assert serializer.get_date(payment) == paid_at

    def test_date_does_not_use_updated_at_when_succeeded_payment_has_paid_at(
        self,
        instructor_enrollment,
    ):
        paid_at = timezone.now() - timedelta(days=2)
        updated_at = timezone.now()

        payment = Payment(
            enrollment=instructor_enrollment,
            amount=Decimal("100.00"),
            status=Payment.Status.SUCCEEDED,
            paid_at=paid_at,
            updated_at=updated_at,
        )
        serializer = TransactionSerializer()

        assert serializer.get_date(payment) == paid_at
        assert serializer.get_date(payment) != updated_at

    def test_date_returns_refunded_at_for_refunded_payment(
        self,
        instructor_enrollment,
    ):
        refunded_at = timezone.now()
        payment = Payment(
            enrollment=instructor_enrollment,
            amount=Decimal("100.00"),
            status=Payment.Status.REFUNDED,
            refunded_at=refunded_at,
        )
        serializer = TransactionSerializer()

        assert serializer.get_date(payment) == refunded_at

    def test_date_does_not_use_updated_at_when_refunded_payment_has_refunded_at(
        self,
        instructor_enrollment,
    ):
        refunded_at = timezone.now() - timedelta(days=2)
        updated_at = timezone.now()

        payment = Payment(
            enrollment=instructor_enrollment,
            amount=Decimal("100.00"),
            status=Payment.Status.REFUNDED,
            refunded_at=refunded_at,
            updated_at=updated_at,
        )
        serializer = TransactionSerializer()

        assert serializer.get_date(payment) == refunded_at
        assert serializer.get_date(payment) != updated_at

    @pytest.mark.parametrize(
        "status",
        [
            Payment.Status.SUCCEEDED,
            Payment.Status.REFUNDED,
        ],
    )
    def test_date_falls_back_to_updated_at_when_status_specific_date_is_missing(
        self,
        instructor_enrollment,
        status,
    ):
        updated_at = timezone.now()

        payment = Payment(
            enrollment=instructor_enrollment,
            amount=Decimal("100.00"),
            status=status,
            updated_at=updated_at,
        )
        serializer = TransactionSerializer()

        assert serializer.get_date(payment) == updated_at

    @pytest.mark.parametrize(
        "status",
        [
            Payment.Status.PENDING,
            Payment.Status.PROCESSING,
            Payment.Status.FAILED,
            Payment.Status.PARTIALLY_REFUNDED,
            Payment.Status.CANCELLED,
        ],
    )
    def test_date_returns_updated_at_for_other_statuses(
        self,
        instructor_enrollment,
        status,
    ):
        updated_at = timezone.now()

        payment = Payment(
            enrollment=instructor_enrollment,
            amount=Decimal("100.00"),
            status=status,
            updated_at=updated_at,
        )
        serializer = TransactionSerializer()

        assert serializer.get_date(payment) == updated_at

    def test_date_returns_updated_at_when_paid_at_is_none(
        self,
        instructor_enrollment,
    ):
        updated_at = timezone.now()

        payment = Payment(
            enrollment=instructor_enrollment,
            amount=Decimal("100.00"),
            status=Payment.Status.SUCCEEDED,
            paid_at=None,
            updated_at=updated_at,
        )
        serializer = TransactionSerializer()

        assert serializer.get_date(payment) == updated_at

    def test_date_returns_updated_at_when_refunded_at_is_none(
        self,
        instructor_enrollment,
    ):
        updated_at = timezone.now()

        payment = Payment(
            enrollment=instructor_enrollment,
            amount=Decimal("100.00"),
            status=Payment.Status.REFUNDED,
            refunded_at=None,
            updated_at=updated_at,
        )
        serializer = TransactionSerializer()

        assert serializer.get_date(payment) == updated_at

    def test_read_only_fields_are_ignored_on_input(self):
        serializer = TransactionSerializer(
            data={
                "id": str(uuid4()),
                "type": "refund",
                "date": timezone.now().isoformat(),
                "course": "Injected Course",
                "amount": "100.00",
                "status": Payment.Status.SUCCEEDED,
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert "id" not in serializer.validated_data
        assert "type" not in serializer.validated_data
        assert "date" not in serializer.validated_data
        assert "course" not in serializer.validated_data

    def test_serializes_amount_and_status(self, instructor_enrollment):
        payment = Payment(
            enrollment=instructor_enrollment,
            amount=Decimal("125.50"),
            status=Payment.Status.SUCCEEDED,
        )
        serializer = TransactionSerializer(instance=payment)

        assert serializer.data["amount"] == "125.50"
        assert serializer.data["status"] == Payment.Status.SUCCEEDED

    def test_serializes_type_as_sale(self, instructor_enrollment):
        payment = Payment(
            enrollment=instructor_enrollment,
            amount=Decimal("125.50"),
            status=Payment.Status.SUCCEEDED,
        )
        serializer = TransactionSerializer(instance=payment)

        assert serializer.data["type"] == "sale"

    def test_serializes_paid_at_as_date_for_succeeded_payment(
        self,
        instructor_enrollment,
    ):
        paid_at = timezone.now()

        payment = Payment(
            enrollment=instructor_enrollment,
            amount=Decimal("125.50"),
            status=Payment.Status.SUCCEEDED,
            paid_at=paid_at,
        )
        serializer = TransactionSerializer(instance=payment)

        assert serializer.data["date"] == paid_at

    def test_serializes_refunded_at_as_date_for_refunded_payment(
        self,
        instructor_enrollment,
    ):
        refunded_at = timezone.now()

        payment = Payment(
            enrollment=instructor_enrollment,
            amount=Decimal("125.50"),
            status=Payment.Status.REFUNDED,
            refunded_at=refunded_at,
        )
        serializer = TransactionSerializer(instance=payment)

        assert serializer.data["date"] == refunded_at

    def test_serializes_updated_at_when_date_specific_to_status_is_missing(
        self,
        instructor_enrollment,
    ):
        updated_at = timezone.now()

        payment = Payment(
            enrollment=instructor_enrollment,
            amount=Decimal("125.50"),
            status=Payment.Status.SUCCEEDED,
            paid_at=None,
            updated_at=updated_at,
        )
        serializer = TransactionSerializer(instance=payment)

        assert serializer.data["date"] == updated_at

    def test_read_only_course_is_not_written_to_payment(
        self,
        instructor_enrollment,
    ):
        serializer = TransactionSerializer(
            data={
                "amount": "100.00",
                "status": Payment.Status.SUCCEEDED,
                "course": "Django Fundamentals",
            }
        )

        assert serializer.is_valid(), serializer.errors

        payment = Payment(
            enrollment=instructor_enrollment,
            amount=serializer.validated_data["amount"],
            status=serializer.validated_data["status"],
        )

        assert "course" not in serializer.validated_data
        assert payment.amount == Decimal("100.00")
        assert payment.status == Payment.Status.SUCCEEDED

    def test_update_changes_amount_and_status(self, instructor_enrollment):
        payment = Payment.objects.create(
            enrollment=instructor_enrollment,
            amount=Decimal("100.00"),
            status=Payment.Status.PENDING,
        )

        serializer = TransactionSerializer(
            instance=payment,
            data={
                "amount": "125.50",
                "status": Payment.Status.SUCCEEDED,
            },
        )

        assert serializer.is_valid(), serializer.errors

        updated_payment = serializer.save()

        assert updated_payment is payment
        assert updated_payment.amount == Decimal("125.50")
        assert updated_payment.status == Payment.Status.SUCCEEDED

    def test_update_does_not_change_read_only_course(
        self,
        instructor_enrollment,
    ):
        payment = Payment.objects.create(
            enrollment=instructor_enrollment,
            amount=Decimal("100.00"),
            status=Payment.Status.PENDING,
        )

        serializer = TransactionSerializer(
            instance=payment,
            data={
                "amount": "125.00",
                "status": Payment.Status.SUCCEEDED,
                "course": "Different Course",
            },
        )

        assert serializer.is_valid(), serializer.errors

        updated_payment = serializer.save()

        assert updated_payment.amount == Decimal("125.00")
        assert updated_payment.status == Payment.Status.SUCCEEDED
        assert updated_payment.enrollment_id == instructor_enrollment.id

    def test_update_does_not_change_type(self, instructor_enrollment):
        payment = Payment.objects.create(
            enrollment=instructor_enrollment,
            amount=Decimal("100.00"),
            status=Payment.Status.PENDING,
        )

        serializer = TransactionSerializer(
            instance=payment,
            data={
                "amount": "125.00",
                "status": Payment.Status.SUCCEEDED,
                "type": "refund",
            },
        )

        assert serializer.is_valid(), serializer.errors

        updated_payment = serializer.save()

        assert serializer.get_type(updated_payment) == "sale"

    def test_update_does_not_change_id(self, instructor_enrollment):
        payment_id = uuid4()

        payment = Payment.objects.create(
            id=payment_id,
            enrollment=instructor_enrollment,
            amount=Decimal("100.00"),
            status=Payment.Status.PENDING,
        )

        serializer = TransactionSerializer(
            instance=payment,
            data={
                "id": str(uuid4()),
                "amount": "125.00",
                "status": Payment.Status.SUCCEEDED,
            },
        )

        assert serializer.is_valid(), serializer.errors

        updated_payment = serializer.save()

        assert updated_payment.id == payment_id

    def test_partial_update_requires_only_supplied_fields(
        self,
        instructor_enrollment,
    ):
        payment = Payment.objects.create(
            enrollment=instructor_enrollment,
            amount=Decimal("100.00"),
            status=Payment.Status.PENDING,
        )

        serializer = TransactionSerializer(
            instance=payment,
            data={"amount": "150.00"},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        updated_payment = serializer.save()

        assert updated_payment.amount == Decimal("150.00")
        assert updated_payment.status == Payment.Status.PENDING

    def test_partial_update_can_change_status_without_amount(
        self,
        instructor_enrollment,
    ):
        payment = Payment.objects.create(
            enrollment=instructor_enrollment,
            amount=Decimal("100.00"),
            status=Payment.Status.PENDING,
        )

        serializer = TransactionSerializer(
            instance=payment,
            data={"status": Payment.Status.SUCCEEDED},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        updated_payment = serializer.save()

        assert updated_payment.amount == Decimal("100.00")
        assert updated_payment.status == Payment.Status.SUCCEEDED

    def test_full_update_without_amount_is_invalid(
        self,
        instructor_enrollment,
    ):
        payment = Payment.objects.create(
            enrollment=instructor_enrollment,
            amount=Decimal("100.00"),
            status=Payment.Status.PENDING,
        )

        serializer = TransactionSerializer(
            instance=payment,
            data={"status": Payment.Status.SUCCEEDED},
        )

        assert not serializer.is_valid()
        assert "amount" in serializer.errors

    def test_serializer_save_persists_updated_values(
        self,
        instructor_enrollment,
    ):
        payment = Payment.objects.create(
            enrollment=instructor_enrollment,
            amount=Decimal("100.00"),
            status=Payment.Status.PENDING,
        )

        serializer = TransactionSerializer(
            instance=payment,
            data={
                "amount": "200.00",
                "status": Payment.Status.SUCCEEDED,
            },
        )

        assert serializer.is_valid(), serializer.errors
        serializer.save()

        payment.refresh_from_db()

        assert payment.amount == Decimal("200.00")
        assert payment.status == Payment.Status.SUCCEEDED

    def test_invalid_status_does_not_update_payment(
        self,
        instructor_enrollment,
    ):
        payment = Payment.objects.create(
            enrollment=instructor_enrollment,
            amount=Decimal("100.00"),
            status=Payment.Status.PENDING,
        )

        serializer = TransactionSerializer(
            instance=payment,
            data={
                "amount": "200.00",
                "status": "invalid-status",
            },
        )

        assert not serializer.is_valid()

        payment.refresh_from_db()

        assert payment.amount == Decimal("100.00")
        assert payment.status == Payment.Status.PENDING

    def test_invalid_amount_does_not_update_payment(
        self,
        instructor_enrollment,
    ):
        payment = Payment.objects.create(
            enrollment=instructor_enrollment,
            amount=Decimal("100.00"),
            status=Payment.Status.PENDING,
        )

        serializer = TransactionSerializer(
            instance=payment,
            data={
                "amount": "100.123",
                "status": Payment.Status.SUCCEEDED,
            },
        )

        assert not serializer.is_valid()

        payment.refresh_from_db()

        assert payment.amount == Decimal("100.00")
        assert payment.status == Payment.Status.PENDING

    def test_serializer_raises_validation_error_when_is_valid_is_called_with_raise_exception(
        self,
    ):
        serializer = TransactionSerializer(
            data={
                "amount": "invalid",
                "status": Payment.Status.SUCCEEDED,
            }
        )

        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_serialized_course_uses_instance_attribute_if_present(
        self,
        instructor_enrollment,
    ):
        payment = Payment(
            enrollment=instructor_enrollment,
            amount=Decimal("100.00"),
            status=Payment.Status.SUCCEEDED,
        )
        payment.course = "Django Fundamentals"

        serializer = TransactionSerializer(instance=payment)

        assert serializer.data["course"] == "Django Fundamentals"

    def test_serializer_output_contains_expected_keys(
        self,
        instructor_enrollment,
    ):
        payment = Payment(
            enrollment=instructor_enrollment,
            amount=Decimal("100.00"),
            status=Payment.Status.SUCCEEDED,
        )

        serializer = TransactionSerializer(instance=payment)

        assert set(serializer.data.keys()) == {
            "id",
            "type",
            "amount",
            "date",
            "status",
        }
