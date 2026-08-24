import logging
from datetime import timedelta
from decimal import Decimal

import stripe
from django.conf import settings
from django.db import transaction
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

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY


class CheckoutService:
    @staticmethod
    @transaction.atomic
    def create_checkout_session(*, enrollment: Enrollment, user) -> Payment:
        """
        Create a pending Payment record and a Stripe Checkout Session.
        Raises domain exceptions on validation/bussiness rule failures.
        """

        enrollment = (
            Enrollment.objects.select_for_update()
            .select_related("course", "user")
            .get(pk=enrollment.pk)
        )
        if enrollment.user_id != user.id:
            raise EnrollmentAccessDenied("You do not have access to this enrollment.")

        if enrollment.status != Enrollment.Status.PENDING:
            raise EnrollmentNotPayable("This enrollment is not available for payment.")

        course = enrollment.course

        if course.price is None:
            raise CourseNotPriced("This course does not have a price.")

        if course.price <= Decimal("0"):
            raise CourseNotPriced("This course does not require payment.")

        if enrollment.payments.filter(status=Payment.Status.SUCCEEDED).exists():
            raise EnrollmentAlreadyPaid("A payment for this enrollment already exists.")
        existing_pending = (
            enrollment.payments.filter(status=Payment.Status.PENDING)
            .order_by("-created_at")
            .first()
        )

        if existing_pending:
            if timezone.now() - existing_pending.created_at > timedelta(minutes=1):
                existing_pending.status = Payment.Status.CANCELLED
                existing_pending.save(update_fields=["status", "updated_at"])

            else:
                if existing_pending.stripe_checkout_url:
                    return existing_pending

        currency = getattr(course, "currency", "usd").lower()
        payment = Payment.objects.create(
            enrollment=enrollment,
            amount=course.price,
            currency=currency,
            status=Payment.Status.PENDING,
            payment_type=Payment.Type.ONE_TIME,
            description=f"Enrollment payment for {course.title}",
            metadata={
                "enrollment_id": str(enrollment.id),
                "course_id": str(course.id),
                "user_id": str(user.id),
            },
        )

        try:
            session = stripe.checkout.Session.create(
                mode="payment",
                line_items=[
                    {
                        "price_data": {
                            "currency": payment.currency,
                            "product_data": {"name": course.title},
                            "unit_amount": int(
                                (payment.amount * Decimal("100")).quantize(Decimal("1"))
                            ),
                        },
                        "quantity": 1,
                    }
                ],
                metadata={
                    "payment_id": str(payment.id),
                    "enrollment_id": str(enrollment.id),
                    "course_id": str(course.id),
                    "user_id": str(user.id),
                },
                customer_email=getattr(user, "email", None),
                client_reference_id=str(payment.id),
                success_url=(
                    f"{settings.FRONTEND_URL}"
                    "/payment/success"
                    "?session_id={CHECKOUT_SESSION_ID}"
                ),
                cancel_url=(f"{settings.FRONTEND_URL}/payment/cancel"),
            )
        except stripe.StripeError as exc:
            logger.exception(
                "Stripe checkout session creation failed for payment_id%s", payment.id
            )
            payment.status = Payment.Status.FAILED
            payment.error_message = str(exc)
            payment.save(update_fields=["status", "error_message", "updated_at"])

            raise StripeSessionCreationFailed(
                "Unable to create then payment session."
            ) from exc

        payment.stripe_checkout_session_id = session.id
        payment.stripe_checkout_url = session.url
        payment.save(
            update_fields=[
                "stripe_checkout_session_id",
                "stripe_checkout_url",
                "updated_at",
            ]
        )
        return payment
