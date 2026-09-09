# tasks.py
import smtplib

from celery import shared_task
from django.db import transaction

from certificates.services.certificate_service import create_certificate

from .models import Enrollment


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(smtplib.SMTPException, TimeoutError),
)
def create_certificate_task(self, enrollment_id: int):
    try:
        with transaction.atomic():
            enrollment = (
                Enrollment.objects.select_for_update()
                .select_related("user", "course")
                .get(id=enrollment_id)
            )

            # Double-check (idempotent)
            if hasattr(enrollment, "certificate") or enrollment.progress < 100:
                return

            create_certificate(enrollment)

    except Enrollment.DoesNotExist:
        return
