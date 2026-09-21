import logging

from django.db import transaction

from enrollments.models import Enrollment
from payments.models import Payment

logger = logging.getLogger(__name__)


@transaction.atomic
def handle_checkout_session_completed(session: dict) -> None:
    session = session.to_dict()
    payment_id = session.get("metadata", {}).get("payment_id")
    if not payment_id:
        logger.error("checkout.session.completed missing payment_id in metadata")
        return

    try:
        payment = (
            Payment.objects.select_for_update()
            .select_related("enrollment")
            .get(id=payment_id)
        )
    except Payment.DoesNotExist:
        logger.error("Payment %s not found for completed session", payment_id)
        return
    if payment.status == Payment.Status.SUCCEEDED:
        return

    payment.status = Payment.Status.SUCCEEDED
    payment.stripe_payment_intent_id = session.get("payment_intent")
    payment.save(update_fields=["status", "stripe_payment_intent_id", "updated_at"])
    enrollment = payment.enrollment

    if enrollment.status == Enrollment.Status.PENDING:
        enrollment.status = Enrollment.Status.ACTIVE
        enrollment.save(update_fields=["status", "updated_at"])
