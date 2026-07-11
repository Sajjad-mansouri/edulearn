from django.conf import settings

from accounts.tasks import send_verification_email


def send_registration_email(context):
    if settings.USE_CELERY:
        send_verification_email.delay(**context)
    else:
        send_verification_email(**context)
