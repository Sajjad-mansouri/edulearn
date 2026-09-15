from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import Site
from django.test import RequestFactory
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from accounts.api.services import (
    get_users,
    send_password_reset_email,
)

User = get_user_model()


@pytest.fixture
def request_factory():
    return RequestFactory()


@pytest.fixture
def registration_site(db, settings):
    site = Site.objects.filter(domain="example.com").first()

    if site is None:
        site = Site.objects.create(
            domain="example.com",
            name="Example LMS",
        )
    elif site.name != "Example LMS":
        site.name = "Example LMS"
        site.save(update_fields=["name"])

    settings.SITE_ID = site.pk

    return site


@pytest.fixture
def password_reset_request(request_factory, registration_site):
    return request_factory.post(
        "/password-reset/",
        HTTP_HOST=registration_site.domain,
        REMOTE_ADDR="192.0.2.10",
    )


@pytest.fixture
def secure_password_reset_request(
    request_factory,
    registration_site,
):
    return request_factory.post(
        "/password-reset/",
        secure=True,
        HTTP_HOST=registration_site.domain,
        REMOTE_ADDR="192.0.2.10",
    )


@pytest.fixture
def test_user(db):
    return User.objects.create_user(
        username="test_user",
        email="test_user@example.com",
        password="test-password",
        is_active=True,
    )


@pytest.fixture
def another_user(db):
    return User.objects.create_user(
        username="another_user",
        email="another_user@example.com",
        password="another-password",
        is_active=True,
    )


@pytest.fixture
def inactive_user(db):
    return User.objects.create_user(
        username="inactive_user",
        email="inactive_user@example.com",
        password="test-password",
        is_active=False,
    )


@pytest.fixture
def unusable_password_user(db):
    user = User.objects.create_user(
        username="unusable_password_user",
        email="unusable@example.com",
        password="test-password",
        is_active=True,
    )

    user.set_unusable_password()
    user.save(update_fields=["password"])

    return user


@pytest.mark.django_db
class TestGetUsers:
    def test_returns_active_user_with_usable_password(
        self,
        test_user,
    ):
        result = list(get_users(test_user.email))

        assert result == [test_user]

    def test_returns_generator(
        self,
        test_user,
    ):
        result = get_users(test_user.email)

        assert hasattr(result, "__iter__")
        assert hasattr(result, "__next__")

    def test_returns_empty_generator_for_nonexistent_email(
        self,
    ):
        result = list(get_users("does-not-exist@example.com"))

        assert result == []

    def test_email_matching_is_case_insensitive(
        self,
        test_user,
    ):
        result = list(get_users(test_user.email.upper()))

        assert result == [test_user]

    def test_excludes_inactive_user(
        self,
        inactive_user,
    ):
        result = list(get_users(inactive_user.email))

        assert result == []

    def test_excludes_user_with_unusable_password(
        self,
        unusable_password_user,
    ):
        result = list(get_users(unusable_password_user.email))

        assert result == []

    def test_excludes_user_with_different_email(
        self,
        test_user,
    ):
        result = list(get_users("another@example.com"))

        assert result == []

    def test_does_not_strip_whitespace_from_email(
        self,
        test_user,
    ):
        result = list(get_users(f" {test_user.email} "))

        assert result == []

    def test_does_not_return_inactive_user_even_when_email_matches_case_insensitively(
        self,
        inactive_user,
    ):
        result = list(get_users(inactive_user.email.upper()))

        assert result == []

    def test_does_not_return_unusable_password_user_even_when_email_matches_case_insensitively(
        self,
        unusable_password_user,
    ):
        result = list(get_users(unusable_password_user.email.upper()))

        assert result == []

    def test_returns_only_user_matching_requested_email(
        self,
        test_user,
        another_user,
    ):
        result = list(get_users(test_user.email))

        assert result == [test_user]
        assert another_user not in result


@pytest.mark.django_db
class TestSendPasswordResetEmail:
    @pytest.fixture(autouse=True)
    def _current_site(self, registration_site):
        return registration_site

    def test_sends_password_reset_email_for_matching_user(
        self,
        password_reset_request,
        test_user,
    ):
        with patch("accounts.api.services.send_email") as mock_send_email:
            send_password_reset_email(
                password_reset_request,
                test_user.email,
            )

        mock_send_email.assert_called_once()

    def test_uses_http_for_insecure_request(
        self,
        password_reset_request,
        test_user,
    ):
        with patch("accounts.api.services.send_email") as mock_send_email:
            send_password_reset_email(
                password_reset_request,
                test_user.email,
            )

        kwargs = mock_send_email.call_args.kwargs

        assert kwargs["context"]["protocol"] == "http"

    def test_uses_https_for_secure_request(
        self,
        secure_password_reset_request,
        test_user,
    ):
        with patch("accounts.api.services.send_email") as mock_send_email:
            send_password_reset_email(
                secure_password_reset_request,
                test_user.email,
            )

        kwargs = mock_send_email.call_args.kwargs

        assert kwargs["context"]["protocol"] == "https"

    def test_uses_current_site_domain(
        self,
        password_reset_request,
        registration_site,
        test_user,
    ):
        with patch("accounts.api.services.send_email") as mock_send_email:
            send_password_reset_email(
                password_reset_request,
                test_user.email,
            )

        kwargs = mock_send_email.call_args.kwargs

        assert kwargs["context"]["domain"] == registration_site.domain

    def test_uses_current_site_name(
        self,
        password_reset_request,
        registration_site,
        test_user,
    ):
        with patch("accounts.api.services.send_email") as mock_send_email:
            send_password_reset_email(
                password_reset_request,
                test_user.email,
            )

        kwargs = mock_send_email.call_args.kwargs

        assert kwargs["context"]["site_name"] == registration_site.name

    def test_uses_user_email_in_context(
        self,
        password_reset_request,
        test_user,
    ):
        with patch("accounts.api.services.send_email") as mock_send_email:
            send_password_reset_email(
                password_reset_request,
                test_user.email,
            )

        kwargs = mock_send_email.call_args.kwargs

        assert kwargs["context"]["email"] == test_user.email

    def test_uses_user_email_as_recipient(
        self,
        password_reset_request,
        test_user,
    ):
        with patch("accounts.api.services.send_email") as mock_send_email:
            send_password_reset_email(
                password_reset_request,
                test_user.email,
            )

        kwargs = mock_send_email.call_args.kwargs

        assert kwargs["recipient"] == test_user.email

    def test_uses_expected_subject(
        self,
        password_reset_request,
        registration_site,
        test_user,
    ):
        with patch("accounts.api.services.send_email") as mock_send_email:
            send_password_reset_email(
                password_reset_request,
                test_user.email,
            )

        kwargs = mock_send_email.call_args.kwargs

        assert kwargs["subject"] == f"Password reset on {registration_site.name}"

    def test_uses_expected_text_template(
        self,
        password_reset_request,
        test_user,
    ):
        with patch("accounts.api.services.send_email") as mock_send_email:
            send_password_reset_email(
                password_reset_request,
                test_user.email,
            )

        kwargs = mock_send_email.call_args.kwargs

        assert kwargs["text_template"] == "register/password_reset_confirm_email.txt"

    def test_uses_expected_html_template(
        self,
        password_reset_request,
        test_user,
    ):
        with patch("accounts.api.services.send_email") as mock_send_email:
            send_password_reset_email(
                password_reset_request,
                test_user.email,
            )

        kwargs = mock_send_email.call_args.kwargs

        assert kwargs["html_template"] == "register/password_reset_confirm_email.html"

    def test_generates_uid_from_user_primary_key(
        self,
        password_reset_request,
        test_user,
    ):
        with patch("accounts.api.services.send_email") as mock_send_email:
            send_password_reset_email(
                password_reset_request,
                test_user.email,
            )

        kwargs = mock_send_email.call_args.kwargs

        expected_uid = urlsafe_base64_encode(
            force_bytes(User._meta.pk.value_to_string(test_user))
        )

        assert kwargs["context"]["uid"] == expected_uid

    def test_generates_valid_password_reset_token(
        self,
        password_reset_request,
        test_user,
    ):
        with patch("accounts.api.services.send_email") as mock_send_email:
            send_password_reset_email(
                password_reset_request,
                test_user.email,
            )

        kwargs = mock_send_email.call_args.kwargs

        token = kwargs["context"]["token"]

        assert default_token_generator.check_token(
            test_user,
            token,
        )

    def test_generates_token_for_the_matching_user(
        self,
        password_reset_request,
        test_user,
    ):
        with patch(
            "accounts.api.services.default_token_generator.make_token",
            return_value="test-reset-token",
        ) as mock_make_token:
            with patch("accounts.api.services.send_email") as mock_send_email:
                send_password_reset_email(
                    password_reset_request,
                    test_user.email,
                )

        mock_make_token.assert_called_once_with(test_user)

        kwargs = mock_send_email.call_args.kwargs

        assert kwargs["context"]["token"] == "test-reset-token"

    def test_calls_get_users_with_exact_email(
        self,
        password_reset_request,
        test_user,
    ):
        with patch(
            "accounts.api.services.get_users",
            return_value=iter([test_user]),
        ) as mock_get_users:
            with patch("accounts.api.services.send_email"):
                send_password_reset_email(
                    password_reset_request,
                    test_user.email,
                )

        mock_get_users.assert_called_once_with(test_user.email)

    def test_does_not_send_email_when_no_users_match(
        self,
        password_reset_request,
    ):
        with patch("accounts.api.services.send_email") as mock_send_email:
            send_password_reset_email(
                password_reset_request,
                "does-not-exist@example.com",
            )

        mock_send_email.assert_not_called()

    def test_does_not_send_email_to_inactive_user(
        self,
        password_reset_request,
        inactive_user,
    ):
        with patch("accounts.api.services.send_email") as mock_send_email:
            send_password_reset_email(
                password_reset_request,
                inactive_user.email,
            )

        mock_send_email.assert_not_called()

    def test_does_not_send_email_to_user_with_unusable_password(
        self,
        password_reset_request,
        unusable_password_user,
    ):
        with patch("accounts.api.services.send_email") as mock_send_email:
            send_password_reset_email(
                password_reset_request,
                unusable_password_user.email,
            )

        mock_send_email.assert_not_called()

    def test_email_lookup_is_case_insensitive(
        self,
        password_reset_request,
        test_user,
    ):
        with patch("accounts.api.services.send_email") as mock_send_email:
            send_password_reset_email(
                password_reset_request,
                test_user.email.upper(),
            )

        mock_send_email.assert_called_once()

        kwargs = mock_send_email.call_args.kwargs

        assert kwargs["recipient"] == test_user.email

    def test_uses_synchronous_send_email_when_async_disabled(
        self,
        password_reset_request,
        test_user,
        settings,
    ):
        settings.HOST_ASYNC_ABILITY = False

        with patch("accounts.api.services.send_email") as mock_send_email:
            send_password_reset_email(
                password_reset_request,
                test_user.email,
            )

        mock_send_email.assert_called_once()

        mock_send_email.delay.assert_not_called()

    def test_uses_async_send_email_when_async_enabled(
        self,
        password_reset_request,
        test_user,
        settings,
    ):
        settings.HOST_ASYNC_ABILITY = True

        with patch("accounts.api.services.send_email") as mock_send_email:
            send_password_reset_email(
                password_reset_request,
                test_user.email,
            )

        mock_send_email.assert_not_called()

        mock_send_email.delay.assert_called_once()

    def test_async_send_receives_expected_arguments(
        self,
        password_reset_request,
        registration_site,
        test_user,
        settings,
    ):
        settings.HOST_ASYNC_ABILITY = True

        with patch("accounts.api.services.send_email") as mock_send_email:
            with patch(
                "accounts.api.services.default_token_generator.make_token",
                return_value="test-reset-token",
            ):
                send_password_reset_email(
                    password_reset_request,
                    test_user.email,
                )

        mock_send_email.delay.assert_called_once()

        kwargs = mock_send_email.delay.call_args.kwargs

        expected_uid = urlsafe_base64_encode(
            force_bytes(User._meta.pk.value_to_string(test_user))
        )

        assert kwargs == {
            "recipient": test_user.email,
            "subject": (f"Password reset on {registration_site.name}"),
            "text_template": ("register/password_reset_confirm_email.txt"),
            "html_template": ("register/password_reset_confirm_email.html"),
            "context": {
                "email": test_user.email,
                "protocol": "http",
                "domain": registration_site.domain,
                "site_name": registration_site.name,
                "uid": expected_uid,
                "token": "test-reset-token",
            },
        }

    def test_sync_send_receives_expected_arguments(
        self,
        password_reset_request,
        registration_site,
        test_user,
        settings,
    ):
        settings.HOST_ASYNC_ABILITY = False

        with patch("accounts.api.services.send_email") as mock_send_email:
            with patch(
                "accounts.api.services.default_token_generator.make_token",
                return_value="test-reset-token",
            ):
                send_password_reset_email(
                    password_reset_request,
                    test_user.email,
                )

        mock_send_email.assert_called_once()

        kwargs = mock_send_email.call_args.kwargs

        expected_uid = urlsafe_base64_encode(
            force_bytes(User._meta.pk.value_to_string(test_user))
        )

        assert kwargs == {
            "recipient": test_user.email,
            "subject": (f"Password reset on {registration_site.name}"),
            "text_template": ("register/password_reset_confirm_email.txt"),
            "html_template": ("register/password_reset_confirm_email.html"),
            "context": {
                "email": test_user.email,
                "protocol": "http",
                "domain": registration_site.domain,
                "site_name": registration_site.name,
                "uid": expected_uid,
                "token": "test-reset-token",
            },
        }

    def test_does_not_send_email_when_email_contains_unmatched_whitespace(
        self,
        password_reset_request,
        test_user,
    ):
        with patch("accounts.api.services.send_email") as mock_send_email:
            send_password_reset_email(
                password_reset_request,
                f" {test_user.email} ",
            )

        mock_send_email.assert_not_called()

    def test_password_reset_email_uses_user_email_not_requested_email(
        self,
        password_reset_request,
        test_user,
    ):
        requested_email = test_user.email.upper()

        with patch("accounts.api.services.send_email") as mock_send_email:
            send_password_reset_email(
                password_reset_request,
                requested_email,
            )

        kwargs = mock_send_email.call_args.kwargs

        assert kwargs["recipient"] == test_user.email
        assert kwargs["context"]["email"] == test_user.email

    def test_password_reset_context_contains_only_expected_values(
        self,
        password_reset_request,
        registration_site,
        test_user,
    ):
        with patch("accounts.api.services.send_email") as mock_send_email:
            with patch(
                "accounts.api.services.default_token_generator.make_token",
                return_value="test-reset-token",
            ):
                send_password_reset_email(
                    password_reset_request,
                    test_user.email,
                )

        kwargs = mock_send_email.call_args.kwargs

        assert set(kwargs["context"]) == {
            "email",
            "protocol",
            "domain",
            "site_name",
            "uid",
            "token",
        }

    def test_does_not_call_send_email_delay_when_async_disabled(
        self,
        password_reset_request,
        test_user,
        settings,
    ):
        settings.HOST_ASYNC_ABILITY = False

        with patch("accounts.api.services.send_email") as mock_send_email:
            send_password_reset_email(
                password_reset_request,
                test_user.email,
            )

        mock_send_email.assert_called_once()
        mock_send_email.delay.assert_not_called()

    def test_does_not_call_sync_send_when_async_enabled(
        self,
        password_reset_request,
        test_user,
        settings,
    ):
        settings.HOST_ASYNC_ABILITY = True

        with patch("accounts.api.services.send_email") as mock_send_email:
            send_password_reset_email(
                password_reset_request,
                test_user.email,
            )

        mock_send_email.assert_not_called()
        mock_send_email.delay.assert_called_once()

    def test_uses_default_token_generator(
        self,
        password_reset_request,
        test_user,
    ):
        with patch(
            "accounts.api.services.default_token_generator.make_token",
            return_value="generated-token",
        ) as mock_make_token:
            with patch("accounts.api.services.send_email"):
                send_password_reset_email(
                    password_reset_request,
                    test_user.email,
                )

        mock_make_token.assert_called_once_with(test_user)

    def test_does_not_generate_token_when_no_user_matches(
        self,
        password_reset_request,
    ):
        with patch(
            "accounts.api.services.default_token_generator.make_token"
        ) as mock_make_token:
            with patch("accounts.api.services.send_email") as mock_send_email:
                send_password_reset_email(
                    password_reset_request,
                    "does-not-exist@example.com",
                )

        mock_make_token.assert_not_called()
        mock_send_email.assert_not_called()
