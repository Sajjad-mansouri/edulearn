import smtplib

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import loader


@shared_task(
    acks_late=True,
    autoretry_for=(smtplib.SMTPException, TimeoutError),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def send_verification_email(email, protocol, domain, site_name, uid, token, role_name):
    context = {
        "email": email,
        "protocol": protocol,
        "domain": domain,
        "site_name": site_name,
        "uid": uid,
        "token": token,
    }
    template_map = {
        "student": "student_register_confirm_email",
        "teacher": "instructor_register_confirm_email",
    }

    if role_name not in template_map:
        raise ValueError(f"Unsupported role: {role_name}")
    template_name = template_map[role_name]

    text_content = loader.render_to_string(f"register/{template_name}.txt", context)
    html_content = loader.render_to_string(f"register/{template_name}.html", context)

    email = EmailMultiAlternatives(
        subject="Verify your email address",
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email],
    )

    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=False)
