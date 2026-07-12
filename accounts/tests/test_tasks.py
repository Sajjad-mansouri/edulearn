# accounts/tests/tasks/test_send_verification_email.py

from unittest.mock import MagicMock, call, patch

import pytest

from accounts.tasks import send_verification_email


@pytest.mark.django_db
class TestSendVerificationEmail:
    """Tests for send_verification_email task."""

    @pytest.fixture
    def email_context(self):
        return {
            "email": "test@example.com",
            "protocol": "https",
            "domain": "example.com",
            "site_name": "SM-LMS",
            "uid": "encoded-user-id",
            "token": "verification-token",
        }

    @patch("accounts.tasks.EmailMultiAlternatives")
    @patch("accounts.tasks.loader.render_to_string")
    def test_sends_student_registration_email(
        self,
        mock_render_to_string,
        mock_email_class,
        email_context,
        settings,
    ):
        """Student registration email is rendered and sent."""
        settings.DEFAULT_FROM_EMAIL = "noreply@example.com"

        mock_render_to_string.side_effect = [
            "text content",
            "html content",
        ]

        email_message = MagicMock()
        mock_email_class.return_value = email_message

        send_verification_email(
            role_name="student",
            **email_context,
        )

        mock_render_to_string.assert_has_calls(
            [
                call(
                    "register/student_register_confirm_email.txt",
                    email_context,
                ),
                call(
                    "register/student_register_confirm_email.html",
                    email_context,
                ),
            ]
        )

        mock_email_class.assert_called_once_with(
            subject="Verify your email address",
            body="text content",
            from_email="noreply@example.com",
            to=["test@example.com"],
        )

        email_message.attach_alternative.assert_called_once_with(
            "html content",
            "text/html",
        )

        email_message.send.assert_called_once_with(
            fail_silently=False,
        )

    @patch("accounts.tasks.EmailMultiAlternatives")
    @patch("accounts.tasks.loader.render_to_string")
    def test_sends_instructor_registration_email(
        self,
        mock_render_to_string,
        mock_email_class,
        email_context,
        settings,
    ):
        """Instructor registration email uses instructor templates."""
        settings.DEFAULT_FROM_EMAIL = "noreply@example.com"

        mock_render_to_string.side_effect = [
            "text content",
            "html content",
        ]

        mock_email_class.return_value = MagicMock()

        send_verification_email(
            role_name="teacher",
            **email_context,
        )

        mock_render_to_string.assert_has_calls(
            [
                call(
                    "register/instructor_register_confirm_email.txt",
                    email_context,
                ),
                call(
                    "register/instructor_register_confirm_email.html",
                    email_context,
                ),
            ]
        )

    def test_raises_error_for_unsupported_role(
        self,
        email_context,
    ):
        """Unsupported roles are rejected."""
        with pytest.raises(
            ValueError,
            match="Unsupported role: admin",
        ):
            send_verification_email(
                role_name="admin",
                **email_context,
            )
