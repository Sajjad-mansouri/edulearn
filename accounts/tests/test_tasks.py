# accounts/tests/tasks/test_send_verification_email.py
import smtplib
from unittest.mock import MagicMock, call, patch

import pytest

from accounts.tasks import send_email


@pytest.mark.django_db
class TestSendEmail:
    """Tests for the generic send_email task."""

    @pytest.fixture
    def email_kwargs(self):
        return {
            "recipient": "test@example.com",
            "subject": "Verify your email address",
            "text_template": "register/student_register_confirm_email.txt",
            "html_template": "register/student_register_confirm_email.html",
            "context": {
                "email": "test@example.com",
                "protocol": "https",
                "domain": "example.com",
                "site_name": "SM-LMS",
                "uid": "encoded-user-id",
                "token": "verification-token",
            },
        }

    @patch("accounts.tasks.EmailMultiAlternatives")
    @patch("accounts.tasks.loader.render_to_string")
    def test_renders_templates_and_sends_email(
        self,
        mock_render_to_string,
        mock_email_class,
        email_kwargs,
        settings,
    ):
        """Email is rendered and sent successfully."""
        settings.DEFAULT_FROM_EMAIL = "noreply@example.com"

        mock_render_to_string.side_effect = [
            "text content",
            "html content",
        ]

        message = MagicMock()
        mock_email_class.return_value = message

        send_email(**email_kwargs)

        mock_render_to_string.assert_has_calls(
            [
                call(
                    email_kwargs["text_template"],
                    email_kwargs["context"],
                ),
                call(
                    email_kwargs["html_template"],
                    email_kwargs["context"],
                ),
            ]
        )

        mock_email_class.assert_called_once_with(
            subject=email_kwargs["subject"],
            body="text content",
            from_email="noreply@example.com",
            to=[email_kwargs["recipient"]],
        )

        message.attach_alternative.assert_called_once_with(
            "html content",
            "text/html",
        )

        message.send.assert_called_once_with(
            fail_silently=False,
        )

    @patch("accounts.tasks.EmailMultiAlternatives")
    @patch("accounts.tasks.loader.render_to_string")
    def test_raises_smtp_exception_when_sending_fails(
        self,
        mock_render_to_string,
        mock_email_class,
        email_kwargs,
    ):
        """SMTP exceptions are propagated for Celery to retry."""
        mock_render_to_string.side_effect = [
            "text content",
            "html content",
        ]

        message = MagicMock()
        message.send.side_effect = smtplib.SMTPException("SMTP failure")
        mock_email_class.return_value = message

        with pytest.raises(smtplib.SMTPException):
            send_email(**email_kwargs)
