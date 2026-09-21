# payments/tests/services/test_checkout.py

from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

import pytest
import stripe
from django.utils import timezone

from enrollments.models import Enrollment
from payments.exceptions import (
    CourseNotPriced,
    EnrollmentAccessDenied,
    EnrollmentAlreadyPaid,
    EnrollmentNotPayable,
    StripeSessionCreationFailed,
)
from payments.models import Payment
from payments.services.checkout import CheckoutService


@pytest.fixture
def payable_enrollment(db, test_user, course):
    course.price = Decimal("49.99")
    course.save(update_fields=["price"])

    return Enrollment.objects.create(
        user=test_user,
        course=course,
        status=Enrollment.Status.PENDING,
    )


@pytest.fixture
def other_user(db):
    from django.contrib.auth import get_user_model

    user_model = get_user_model()

    return user_model.objects.create_user(
        username="other_user",
        email="other_user@example.com",
        password="other-password",
    )


@pytest.fixture
def successful_stripe_session():
    return SimpleNamespace(
        id="cs_test_123",
        url="https://checkout.stripe.com/c/pay/cs_test_123",
    )


class TestCheckoutServiceCreateCheckoutSession:
    def test_creates_pending_payment_and_stripe_session(
        self,
        payable_enrollment,
        test_user,
        successful_stripe_session,
    ):
        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
            return_value=successful_stripe_session,
        ) as stripe_create:
            payment = CheckoutService.create_checkout_session(
                enrollment=payable_enrollment,
                user=test_user,
            )

        assert payment.enrollment_id == payable_enrollment.id
        assert payment.amount == Decimal("49.99")
        assert payment.currency == "usd"
        assert payment.status == Payment.Status.PENDING
        assert payment.payment_type == Payment.Type.ONE_TIME

        assert (
            payment.description
            == f"Enrollment payment for {payable_enrollment.course.title}"
        )

        assert payment.metadata == {
            "enrollment_id": str(payable_enrollment.id),
            "course_id": str(payable_enrollment.course.id),
            "user_id": str(test_user.id),
        }

        assert payment.stripe_checkout_session_id == (successful_stripe_session.id)
        assert payment.stripe_checkout_url == successful_stripe_session.url

        stripe_create.assert_called_once()

    def test_returns_persisted_payment_instance(
        self,
        payable_enrollment,
        test_user,
        successful_stripe_session,
    ):
        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
            return_value=successful_stripe_session,
        ):
            payment = CheckoutService.create_checkout_session(
                enrollment=payable_enrollment,
                user=test_user,
            )

        persisted_payment = Payment.objects.get(pk=payment.pk)

        assert persisted_payment.id == payment.id
        assert persisted_payment.status == Payment.Status.PENDING
        assert persisted_payment.amount == Decimal("49.99")

    def test_creates_only_one_payment_for_first_checkout(
        self,
        payable_enrollment,
        test_user,
        successful_stripe_session,
    ):
        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
            return_value=successful_stripe_session,
        ):
            payment = CheckoutService.create_checkout_session(
                enrollment=payable_enrollment,
                user=test_user,
            )

        assert (
            Payment.objects.filter(
                enrollment=payable_enrollment,
            ).count()
            == 1
        )

        assert (
            Payment.objects.get(
                pk=payment.pk,
            ).status
            == Payment.Status.PENDING
        )

    def test_passes_payment_mode_to_stripe(
        self,
        payable_enrollment,
        test_user,
        successful_stripe_session,
    ):
        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
            return_value=successful_stripe_session,
        ) as stripe_create:
            CheckoutService.create_checkout_session(
                enrollment=payable_enrollment,
                user=test_user,
            )

        assert stripe_create.call_args.kwargs["mode"] == "payment"

    def test_passes_single_line_item_to_stripe(
        self,
        payable_enrollment,
        test_user,
        successful_stripe_session,
    ):
        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
            return_value=successful_stripe_session,
        ) as stripe_create:
            CheckoutService.create_checkout_session(
                enrollment=payable_enrollment,
                user=test_user,
            )

        line_items = stripe_create.call_args.kwargs["line_items"]

        assert len(line_items) == 1
        assert line_items[0]["quantity"] == 1

    def test_stripe_line_item_contains_course_title(
        self,
        payable_enrollment,
        test_user,
        successful_stripe_session,
    ):
        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
            return_value=successful_stripe_session,
        ) as stripe_create:
            CheckoutService.create_checkout_session(
                enrollment=payable_enrollment,
                user=test_user,
            )

        line_item = stripe_create.call_args.kwargs["line_items"][0]

        assert (
            line_item["price_data"]["product_data"]["name"]
            == payable_enrollment.course.title
        )

    def test_stripe_line_item_contains_payment_currency(
        self,
        payable_enrollment,
        test_user,
        successful_stripe_session,
    ):
        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
            return_value=successful_stripe_session,
        ) as stripe_create:
            CheckoutService.create_checkout_session(
                enrollment=payable_enrollment,
                user=test_user,
            )

        line_item = stripe_create.call_args.kwargs["line_items"][0]

        assert line_item["price_data"]["currency"] == "usd"

    def test_stripe_line_item_converts_amount_to_minor_units(
        self,
        payable_enrollment,
        test_user,
        successful_stripe_session,
    ):
        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
            return_value=successful_stripe_session,
        ) as stripe_create:
            CheckoutService.create_checkout_session(
                enrollment=payable_enrollment,
                user=test_user,
            )

        line_item = stripe_create.call_args.kwargs["line_items"][0]

        assert line_item["price_data"]["unit_amount"] == 4999

    def test_stripe_metadata_contains_payment_id(
        self,
        payable_enrollment,
        test_user,
        successful_stripe_session,
    ):
        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
            return_value=successful_stripe_session,
        ) as stripe_create:
            payment = CheckoutService.create_checkout_session(
                enrollment=payable_enrollment,
                user=test_user,
            )

        metadata = stripe_create.call_args.kwargs["metadata"]

        assert metadata["payment_id"] == str(payment.id)

    def test_stripe_metadata_contains_enrollment_id(
        self,
        payable_enrollment,
        test_user,
        successful_stripe_session,
    ):
        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
            return_value=successful_stripe_session,
        ) as stripe_create:
            CheckoutService.create_checkout_session(
                enrollment=payable_enrollment,
                user=test_user,
            )

        metadata = stripe_create.call_args.kwargs["metadata"]

        assert metadata["enrollment_id"] == str(payable_enrollment.id)

    def test_stripe_metadata_contains_course_id(
        self,
        payable_enrollment,
        test_user,
        successful_stripe_session,
    ):
        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
            return_value=successful_stripe_session,
        ) as stripe_create:
            CheckoutService.create_checkout_session(
                enrollment=payable_enrollment,
                user=test_user,
            )

        metadata = stripe_create.call_args.kwargs["metadata"]

        assert metadata["course_id"] == str(
            payable_enrollment.course.id,
        )

    def test_stripe_metadata_contains_user_id(
        self,
        payable_enrollment,
        test_user,
        successful_stripe_session,
    ):
        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
            return_value=successful_stripe_session,
        ) as stripe_create:
            CheckoutService.create_checkout_session(
                enrollment=payable_enrollment,
                user=test_user,
            )

        metadata = stripe_create.call_args.kwargs["metadata"]

        assert metadata["user_id"] == str(test_user.id)

    def test_stripe_client_reference_id_is_payment_id(
        self,
        payable_enrollment,
        test_user,
        successful_stripe_session,
    ):
        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
            return_value=successful_stripe_session,
        ) as stripe_create:
            payment = CheckoutService.create_checkout_session(
                enrollment=payable_enrollment,
                user=test_user,
            )

        assert stripe_create.call_args.kwargs["client_reference_id"] == (
            str(payment.id)
        )

    def test_stripe_customer_email_uses_user_email(
        self,
        payable_enrollment,
        test_user,
        successful_stripe_session,
    ):
        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
            return_value=successful_stripe_session,
        ) as stripe_create:
            CheckoutService.create_checkout_session(
                enrollment=payable_enrollment,
                user=test_user,
            )

        assert stripe_create.call_args.kwargs["customer_email"] == (test_user.email)

    def test_success_url_contains_frontend_payment_success_path(
        self,
        payable_enrollment,
        test_user,
        successful_stripe_session,
        settings,
    ):
        settings.FRONTEND_URL = "https://frontend.example.com"

        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
            return_value=successful_stripe_session,
        ) as stripe_create:
            CheckoutService.create_checkout_session(
                enrollment=payable_enrollment,
                user=test_user,
            )

        success_url = stripe_create.call_args.kwargs["success_url"]

        assert success_url.startswith("https://frontend.example.com/payment/success")
        assert "session_id={CHECKOUT_SESSION_ID}" in success_url

    def test_cancel_url_contains_frontend_payment_cancel_path(
        self,
        payable_enrollment,
        test_user,
        successful_stripe_session,
        settings,
    ):
        settings.FRONTEND_URL = "https://frontend.example.com"

        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
            return_value=successful_stripe_session,
        ) as stripe_create:
            CheckoutService.create_checkout_session(
                enrollment=payable_enrollment,
                user=test_user,
            )

        assert (
            stripe_create.call_args.kwargs["cancel_url"]
            == "https://frontend.example.com/payment/cancel"
        )


class TestCheckoutServiceAuthorization:
    def test_rejects_enrollment_owned_by_another_user(
        self,
        payable_enrollment,
        other_user,
    ):
        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
        ) as stripe_create:
            with pytest.raises(EnrollmentAccessDenied):
                CheckoutService.create_checkout_session(
                    enrollment=payable_enrollment,
                    user=other_user,
                )

        stripe_create.assert_not_called()

    def test_does_not_create_payment_for_unauthorized_user(
        self,
        payable_enrollment,
        other_user,
    ):
        with pytest.raises(EnrollmentAccessDenied):
            CheckoutService.create_checkout_session(
                enrollment=payable_enrollment,
                user=other_user,
            )

        assert not Payment.objects.filter(
            enrollment=payable_enrollment,
        ).exists()


class TestCheckoutServiceEnrollmentState:
    @pytest.mark.parametrize(
        "status",
        [
            Enrollment.Status.ACTIVE,
            Enrollment.Status.COMPLETED,
            Enrollment.Status.CANCELLED,
            Enrollment.Status.SUSPENDED,
        ],
    )
    def test_rejects_non_pending_enrollment(
        self,
        payable_enrollment,
        test_user,
        status,
    ):
        payable_enrollment.status = status
        payable_enrollment.save(update_fields=["status"])

        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
        ) as stripe_create:
            with pytest.raises(EnrollmentNotPayable):
                CheckoutService.create_checkout_session(
                    enrollment=payable_enrollment,
                    user=test_user,
                )

        stripe_create.assert_not_called()

        assert not Payment.objects.filter(
            enrollment=payable_enrollment,
        ).exists()

    def test_accepts_pending_enrollment(
        self,
        payable_enrollment,
        test_user,
        successful_stripe_session,
    ):
        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
            return_value=successful_stripe_session,
        ):
            payment = CheckoutService.create_checkout_session(
                enrollment=payable_enrollment,
                user=test_user,
            )

        assert payment.status == Payment.Status.PENDING


class TestCheckoutServiceCoursePricing:
    def test_rejects_course_without_price(
        self,
        payable_enrollment,
        test_user,
    ):
        payable_enrollment.course.price = None
        payable_enrollment.course.save(update_fields=["price"])

        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
        ) as stripe_create:
            with pytest.raises(CourseNotPriced):
                CheckoutService.create_checkout_session(
                    enrollment=payable_enrollment,
                    user=test_user,
                )

        stripe_create.assert_not_called()

        assert not Payment.objects.filter(
            enrollment=payable_enrollment,
        ).exists()

    @pytest.mark.parametrize(
        "price",
        [
            Decimal("0.00"),
            Decimal("0.01") * Decimal("-1"),
            Decimal("-1.00"),
            Decimal("-49.99"),
        ],
    )
    def test_rejects_non_positive_course_price(
        self,
        payable_enrollment,
        test_user,
        price,
    ):
        payable_enrollment.course.price = price
        payable_enrollment.course.save(update_fields=["price"])

        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
        ) as stripe_create:
            with pytest.raises(CourseNotPriced):
                CheckoutService.create_checkout_session(
                    enrollment=payable_enrollment,
                    user=test_user,
                )

        stripe_create.assert_not_called()

        assert not Payment.objects.filter(
            enrollment=payable_enrollment,
        ).exists()

    @pytest.mark.parametrize(
        "price",
        [
            Decimal("0.01"),
            Decimal("1.00"),
            Decimal("49.99"),
            Decimal("9999.99"),
        ],
    )
    def test_accepts_positive_course_price(
        self,
        payable_enrollment,
        test_user,
        successful_stripe_session,
        price,
    ):
        payable_enrollment.course.price = price
        payable_enrollment.course.save(update_fields=["price"])

        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
            return_value=successful_stripe_session,
        ):
            payment = CheckoutService.create_checkout_session(
                enrollment=payable_enrollment,
                user=test_user,
            )

        assert payment.amount == price


class TestCheckoutServiceExistingPayments:
    def test_rejects_enrollment_with_successful_payment(
        self,
        payable_enrollment,
        test_user,
    ):
        Payment.objects.create(
            enrollment=payable_enrollment,
            amount=payable_enrollment.course.price,
            currency="usd",
            status=Payment.Status.SUCCEEDED,
            payment_type=Payment.Type.ONE_TIME,
        )

        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
        ) as stripe_create:
            with pytest.raises(EnrollmentAlreadyPaid):
                CheckoutService.create_checkout_session(
                    enrollment=payable_enrollment,
                    user=test_user,
                )

        stripe_create.assert_not_called()

        assert (
            Payment.objects.filter(
                enrollment=payable_enrollment,
            ).count()
            == 1
        )

    def test_recent_pending_payment_with_checkout_url_is_reused(
        self,
        payable_enrollment,
        test_user,
    ):
        existing_payment = Payment.objects.create(
            enrollment=payable_enrollment,
            amount=payable_enrollment.course.price,
            currency="usd",
            status=Payment.Status.PENDING,
            payment_type=Payment.Type.ONE_TIME,
            stripe_checkout_session_id="cs_existing",
            stripe_checkout_url=("https://checkout.stripe.com/c/pay/cs_existing"),
        )

        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
        ) as stripe_create:
            result = CheckoutService.create_checkout_session(
                enrollment=payable_enrollment,
                user=test_user,
            )

        assert result.id == existing_payment.id
        assert result.status == Payment.Status.PENDING
        assert result.stripe_checkout_session_id == "cs_existing"

        stripe_create.assert_not_called()

        assert (
            Payment.objects.filter(
                enrollment=payable_enrollment,
            ).count()
            == 1
        )

    def test_recent_pending_payment_without_checkout_url_creates_new_payment(
        self,
        payable_enrollment,
        test_user,
        successful_stripe_session,
    ):
        existing_payment = Payment.objects.create(
            enrollment=payable_enrollment,
            amount=payable_enrollment.course.price,
            currency="usd",
            status=Payment.Status.PENDING,
            payment_type=Payment.Type.ONE_TIME,
        )

        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
            return_value=successful_stripe_session,
        ) as stripe_create:
            new_payment = CheckoutService.create_checkout_session(
                enrollment=payable_enrollment,
                user=test_user,
            )

        assert new_payment.id != existing_payment.id
        assert new_payment.status == Payment.Status.PENDING

        stripe_create.assert_called_once()

        assert (
            Payment.objects.filter(
                enrollment=payable_enrollment,
            ).count()
            == 2
        )

    def test_stale_pending_payment_is_cancelled_before_new_payment(
        self,
        payable_enrollment,
        test_user,
        successful_stripe_session,
    ):
        old_payment = Payment.objects.create(
            enrollment=payable_enrollment,
            amount=payable_enrollment.course.price,
            currency="usd",
            status=Payment.Status.PENDING,
            payment_type=Payment.Type.ONE_TIME,
            stripe_checkout_session_id="cs_old",
            stripe_checkout_url="https://checkout.stripe.com/c/pay/cs_old",
        )

        stale_time = timezone.now() - timedelta(minutes=2)

        Payment.objects.filter(pk=old_payment.pk).update(
            created_at=stale_time,
        )

        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
            return_value=successful_stripe_session,
        ):
            new_payment = CheckoutService.create_checkout_session(
                enrollment=payable_enrollment,
                user=test_user,
            )

        old_payment.refresh_from_db()

        assert old_payment.status == Payment.Status.CANCELLED
        assert new_payment.id != old_payment.id
        assert new_payment.status == Payment.Status.PENDING

    def test_recent_pending_payment_is_reused(
        self,
        payable_enrollment,
        test_user,
    ):
        existing_payment = Payment.objects.create(
            enrollment=payable_enrollment,
            amount=payable_enrollment.course.price,
            currency="usd",
            status=Payment.Status.PENDING,
            payment_type=Payment.Type.ONE_TIME,
            stripe_checkout_session_id="cs_recent",
            stripe_checkout_url="https://checkout.stripe.com/c/pay/cs_recent",
        )

        recent_time = timezone.now() - timedelta(seconds=30)

        Payment.objects.filter(pk=existing_payment.pk).update(
            created_at=recent_time,
        )

        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
        ) as stripe_create:
            result = CheckoutService.create_checkout_session(
                enrollment=payable_enrollment,
                user=test_user,
            )

        assert result.id == existing_payment.id
        stripe_create.assert_not_called()

    def test_successful_payment_takes_precedence_over_pending_payment(
        self,
        payable_enrollment,
        test_user,
    ):
        Payment.objects.create(
            enrollment=payable_enrollment,
            amount=payable_enrollment.course.price,
            currency="usd",
            status=Payment.Status.SUCCEEDED,
            payment_type=Payment.Type.ONE_TIME,
        )

        Payment.objects.create(
            enrollment=payable_enrollment,
            amount=payable_enrollment.course.price,
            currency="usd",
            status=Payment.Status.PENDING,
            payment_type=Payment.Type.ONE_TIME,
            stripe_checkout_session_id="cs_pending",
            stripe_checkout_url=("https://checkout.stripe.com/c/pay/cs_pending"),
        )

        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
        ) as stripe_create:
            with pytest.raises(EnrollmentAlreadyPaid):
                CheckoutService.create_checkout_session(
                    enrollment=payable_enrollment,
                    user=test_user,
                )

        stripe_create.assert_not_called()


class TestCheckoutServiceStripeFailure:
    def test_stripe_error_is_translated_to_domain_exception(
        self,
        payable_enrollment,
        test_user,
    ):
        stripe_error = stripe.StripeError("Stripe API failed")

        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
            side_effect=stripe_error,
        ):
            with pytest.raises(StripeSessionCreationFailed) as exc_info:
                CheckoutService.create_checkout_session(
                    enrollment=payable_enrollment,
                    user=test_user,
                )

        assert str(exc_info.value) == "Unable to create the payment session."
        assert exc_info.value.__cause__ is stripe_error

    def test_stripe_error_does_not_escape_service(
        self,
        payable_enrollment,
        test_user,
    ):
        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
            side_effect=stripe.StripeError("Stripe failure"),
        ):
            with pytest.raises(StripeSessionCreationFailed):
                CheckoutService.create_checkout_session(
                    enrollment=payable_enrollment,
                    user=test_user,
                )

    def test_stripe_failure_attempts_to_mark_payment_failed(
        self,
        payable_enrollment,
        test_user,
    ):
        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
            side_effect=stripe.StripeError("Stripe failure"),
        ):
            with pytest.raises(StripeSessionCreationFailed):
                CheckoutService.create_checkout_session(
                    enrollment=payable_enrollment,
                    user=test_user,
                )

        # This assertion documents the intended business behavior:
        # a failed Stripe attempt should leave an auditable FAILED payment.
        #
        # With the current @transaction.atomic implementation this will
        # currently fail because the raised exception rolls back the
        # transaction, including the Payment.objects.create().
        payment = Payment.objects.get(
            enrollment=payable_enrollment,
        )

        assert payment.status == Payment.Status.FAILED
        assert payment.error_message == "Stripe failure"

    def test_stripe_failure_does_not_leave_checkout_session_data(
        self,
        payable_enrollment,
        test_user,
    ):
        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
            side_effect=stripe.StripeError("Stripe failure"),
        ):
            with pytest.raises(StripeSessionCreationFailed):
                CheckoutService.create_checkout_session(
                    enrollment=payable_enrollment,
                    user=test_user,
                )

        payment = Payment.objects.filter(
            enrollment=payable_enrollment,
        ).first()

        if payment is not None:
            assert payment.stripe_checkout_session_id is None
            assert payment.stripe_checkout_url is None


class TestCheckoutServicePaymentMetadata:
    def test_payment_description_contains_course_title(
        self,
        payable_enrollment,
        test_user,
        successful_stripe_session,
    ):
        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
            return_value=successful_stripe_session,
        ):
            payment = CheckoutService.create_checkout_session(
                enrollment=payable_enrollment,
                user=test_user,
            )

        assert payable_enrollment.course.title in payment.description

    def test_payment_metadata_uses_string_identifiers(
        self,
        payable_enrollment,
        test_user,
        successful_stripe_session,
    ):
        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
            return_value=successful_stripe_session,
        ):
            payment = CheckoutService.create_checkout_session(
                enrollment=payable_enrollment,
                user=test_user,
            )

        assert all(isinstance(value, str) for value in payment.metadata.values())

    def test_payment_type_is_one_time(
        self,
        payable_enrollment,
        test_user,
        successful_stripe_session,
    ):
        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
            return_value=successful_stripe_session,
        ):
            payment = CheckoutService.create_checkout_session(
                enrollment=payable_enrollment,
                user=test_user,
            )

        assert payment.payment_type == Payment.Type.ONE_TIME

    def test_payment_starts_as_pending(
        self,
        payable_enrollment,
        test_user,
        successful_stripe_session,
    ):
        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
            return_value=successful_stripe_session,
        ):
            payment = CheckoutService.create_checkout_session(
                enrollment=payable_enrollment,
                user=test_user,
            )

        assert payment.status == Payment.Status.PENDING


class TestCheckoutServiceStripeSessionPersistence:
    def test_persists_stripe_session_id(
        self,
        payable_enrollment,
        test_user,
    ):
        session = SimpleNamespace(
            id="cs_persisted",
            url="https://checkout.stripe.com/c/pay/cs_persisted",
        )

        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
            return_value=session,
        ):
            payment = CheckoutService.create_checkout_session(
                enrollment=payable_enrollment,
                user=test_user,
            )

        payment.refresh_from_db()

        assert payment.stripe_checkout_session_id == "cs_persisted"

    def test_persists_stripe_checkout_url(
        self,
        payable_enrollment,
        test_user,
    ):
        session = SimpleNamespace(
            id="cs_persisted_url",
            url="https://checkout.stripe.com/c/pay/cs_persisted_url",
        )

        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
            return_value=session,
        ):
            payment = CheckoutService.create_checkout_session(
                enrollment=payable_enrollment,
                user=test_user,
            )

        payment.refresh_from_db()

        assert payment.stripe_checkout_url == (
            "https://checkout.stripe.com/c/pay/cs_persisted_url"
        )

    def test_does_not_modify_enrollment_status(
        self,
        payable_enrollment,
        test_user,
        successful_stripe_session,
    ):
        original_status = payable_enrollment.status

        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
            return_value=successful_stripe_session,
        ):
            CheckoutService.create_checkout_session(
                enrollment=payable_enrollment,
                user=test_user,
            )

        payable_enrollment.refresh_from_db()

        assert payable_enrollment.status == original_status

    def test_does_not_modify_course_price(
        self,
        payable_enrollment,
        test_user,
        successful_stripe_session,
    ):
        original_price = payable_enrollment.course.price

        with patch(
            "payments.services.checkout.stripe.checkout.Session.create",
            return_value=successful_stripe_session,
        ):
            CheckoutService.create_checkout_session(
                enrollment=payable_enrollment,
                user=test_user,
            )

        payable_enrollment.course.refresh_from_db()

        assert payable_enrollment.course.price == original_price
