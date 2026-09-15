import smtplib
from unittest.mock import MagicMock, patch

import pytest
from django.conf import settings

from accounts.tasks import send_email


@pytest.mark.django_db
class TestSendEmail:
    def test_sends_email_with_rendered_text_and_html_content(self):
        context = {
            "username": "test_user",
            "verification_url": "https://example.com/verify/",
        }

        text_content = "Hello test_user"
        html_content = "<p>Hello test_user</p>"

        with (
            patch(
                "accounts.tasks.loader.render_to_string",
                side_effect=[text_content, html_content],
            ) as render_to_string,
            patch("accounts.tasks.EmailMultiAlternatives") as email_class,
        ):
            message = MagicMock()
            email_class.return_value = message

            send_email(
                recipient="test_user@example.com",
                subject="Verify your account",
                text_template="accounts/emails/verification.txt",
                html_template="accounts/emails/verification.html",
                context=context,
            )

        assert render_to_string.call_count == 2

        render_to_string.assert_any_call(
            "accounts/emails/verification.txt",
            context,
        )
        render_to_string.assert_any_call(
            "accounts/emails/verification.html",
            context,
        )

        email_class.assert_called_once_with(
            subject="Verify your account",
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=["test_user@example.com"],
        )

        message.attach_alternative.assert_called_once_with(
            html_content,
            "text/html",
        )
        message.send.assert_called_once_with(fail_silently=False)

    def test_renders_text_template_before_html_template(self):
        context = {"username": "test_user"}

        calls = []

        def render_template(template_name, template_context):
            calls.append((template_name, template_context))

            if template_name.endswith(".txt"):
                return "Plain text"

            return "<p>HTML</p>"

        with (
            patch(
                "accounts.tasks.loader.render_to_string",
                side_effect=render_template,
            ) as render_to_string,
            patch("accounts.tasks.EmailMultiAlternatives") as email_class,
        ):
            message = MagicMock()
            email_class.return_value = message

            send_email(
                recipient="test_user@example.com",
                subject="Test",
                text_template="emails/test.txt",
                html_template="emails/test.html",
                context=context,
            )

        assert calls == [
            ("emails/test.txt", context),
            ("emails/test.html", context),
        ]

        assert render_to_string.call_count == 2

    def test_email_send_exception_is_propagated(self):
        with (
            patch(
                "accounts.tasks.loader.render_to_string",
                side_effect=["Plain text", "<p>HTML</p>"],
            ),
            patch("accounts.tasks.EmailMultiAlternatives") as email_class,
        ):
            message = MagicMock()
            message.send.side_effect = smtplib.SMTPException("SMTP failure")
            email_class.return_value = message

            with pytest.raises(smtplib.SMTPException, match="SMTP failure"):
                send_email(
                    recipient="test_user@example.com",
                    subject="Test",
                    text_template="emails/test.txt",
                    html_template="emails/test.html",
                    context={},
                )

    def test_timeout_exception_is_propagated(self):
        with (
            patch(
                "accounts.tasks.loader.render_to_string",
                side_effect=["Plain text", "<p>HTML</p>"],
            ),
            patch("accounts.tasks.EmailMultiAlternatives") as email_class,
        ):
            message = MagicMock()
            message.send.side_effect = TimeoutError("Email timeout")
            email_class.return_value = message

            with pytest.raises(TimeoutError, match="Email timeout"):
                send_email(
                    recipient="test_user@example.com",
                    subject="Test",
                    text_template="emails/test.txt",
                    html_template="emails/test.html",
                    context={},
                )

    def test_non_retryable_exception_is_propagated(self):
        with (
            patch(
                "accounts.tasks.loader.render_to_string",
                side_effect=["Plain text", "<p>HTML</p>"],
            ),
            patch("accounts.tasks.EmailMultiAlternatives") as email_class,
        ):
            message = MagicMock()
            message.send.side_effect = ValueError("Invalid email configuration")
            email_class.return_value = message

            with pytest.raises(ValueError, match="Invalid email configuration"):
                send_email(
                    recipient="test_user@example.com",
                    subject="Test",
                    text_template="emails/test.txt",
                    html_template="emails/test.html",
                    context={},
                )

    def test_task_is_configured_for_expected_retry_behavior(self):
        assert send_email.acks_late is True
        assert send_email.max_retries == 5

        assert set(send_email.autoretry_for) == {
            smtplib.SMTPException,
            TimeoutError,
        }

        assert send_email.retry_backoff is True
        assert send_email.retry_jitter is True
