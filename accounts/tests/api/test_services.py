from unittest.mock import Mock, patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.settings import api_settings
from rest_framework.test import APIRequestFactory

from accounts.api.services import (
    confirm_registration,
    get_client_device,
    get_ident,
    get_location,
    perform_login,
    register_user,
    send_registration_email,
)
from accounts.models import Role
from accounts.tests.factories import UserFactory
from profiles.models import Profile

User = get_user_model()


@pytest.mark.django_db
class TestRegisterUser:
    """Tests for register_user service."""

    @pytest.fixture
    def registration_data(self):
        return {
            "first_name": "Test",
            "last_name": "User",
            "username": "test_user",
            "email": "test@example.com",
            "password1": "StrongPassword123!",
            "password2": "StrongPassword123!",
        }

    @pytest.fixture
    def request_mock(self):
        return Mock()

    @patch("accounts.api.services.send_registration_email")
    def test_register_user_creates_inactive_user(
        self,
        mock_send_registration_email,
        registration_data,
        request_mock,
    ):
        """The service creates an inactive user."""
        register_user(
            data=registration_data.copy(),
            role_name="student",
            request=request_mock,
        )

        user = User.objects.get(username="test_user")

        assert user.is_active is False
        assert user.email == "test@example.com"
        assert user.check_password("StrongPassword123!")

    @patch("accounts.api.services.send_registration_email")
    def test_register_user_assigns_role(
        self,
        mock_send_registration_email,
        registration_data,
        request_mock,
    ):
        """The created user is assigned to the requested role."""
        register_user(
            data=registration_data.copy(),
            role_name="student",
            request=request_mock,
        )

        user = User.objects.get(username="test_user")

        assert user.roles.filter(name="student").exists()

    @patch("accounts.api.services.send_registration_email")
    def test_register_user_creates_role_when_missing(
        self,
        mock_send_registration_email,
        registration_data,
        request_mock,
    ):
        """The requested role is created if it does not already exist."""
        assert not Role.objects.filter(name="student").exists()

        register_user(
            data=registration_data.copy(),
            role_name="student",
            request=request_mock,
        )

        assert Role.objects.filter(name="student").exists()

    @patch("accounts.api.services.send_registration_email")
    def test_register_user_uses_existing_role(
        self,
        mock_send_registration_email,
        registration_data,
        request_mock,
    ):
        """An existing role is reused instead of creating a duplicate."""
        Role.objects.create(name="student")

        register_user(
            data=registration_data.copy(),
            role_name="student",
            request=request_mock,
        )

        assert Role.objects.filter(name="student").count() == 1

    @patch("accounts.api.services.send_registration_email")
    def test_register_user_sends_registration_email(
        self,
        mock_send_registration_email,
        registration_data,
        request_mock,
    ):
        """A registration email is sent after successful registration."""
        register_user(
            data=registration_data.copy(),
            role_name="student",
            request=request_mock,
        )

        user = User.objects.get(username="test_user")

        mock_send_registration_email.assert_called_once_with(
            user=user,
            request=request_mock,
            role_name="student",
        )


@pytest.mark.django_db
class TestSendRegistrationEmail:
    """Tests for send_registration_email."""

    @pytest.fixture
    def user(self):
        return UserFactory(email="test@example.com")

    @pytest.fixture
    def mock_request(self):
        request = Mock()
        request.is_secure.return_value = False
        return request

    @pytest.fixture
    def current_site(self):
        site = Mock()
        site.domain = "example.com"
        site.name = "SM-LMS"
        return site

    @patch("accounts.api.services.get_current_site")
    @patch("accounts.api.services.send_verification_email")
    def test_calls_celery_task_when_enabled(
        self,
        mock_send_verification_email,
        mock_get_current_site,
        user,
        mock_request,
        current_site,
        settings,
    ):
        """The Celery task is queued when Celery is enabled."""
        settings.USE_CELERY = True
        mock_get_current_site.return_value = current_site

        send_registration_email(
            user=user,
            request=mock_request,
            role_name="student",
        )

        expected_context = {
            "email": user.email,
            "protocol": "http",
            "domain": current_site.domain,
            "site_name": current_site.name,
            "uid": urlsafe_base64_encode(
                force_bytes(user._meta.pk.value_to_string(user))
            ),
            "token": default_token_generator.make_token(user),
            "role_name": "student",
        }

        mock_send_verification_email.delay.assert_called_once_with(**expected_context)

        mock_send_verification_email.assert_not_called()

    @patch("accounts.api.services.get_current_site")
    @patch("accounts.api.services.send_verification_email")
    def test_calls_task_directly_when_celery_is_disabled(
        self,
        mock_send_verification_email,
        mock_get_current_site,
        user,
        mock_request,
        current_site,
        settings,
    ):
        """The task is executed synchronously when Celery is disabled."""
        settings.USE_CELERY = False
        mock_get_current_site.return_value = current_site

        send_registration_email(
            user=user,
            request=mock_request,
            role_name="student",
        )

        expected_context = {
            "email": user.email,
            "protocol": "http",
            "domain": current_site.domain,
            "site_name": current_site.name,
            "uid": urlsafe_base64_encode(
                force_bytes(user._meta.pk.value_to_string(user))
            ),
            "token": default_token_generator.make_token(user),
            "role_name": "student",
        }

        mock_send_verification_email.assert_called_once_with(**expected_context)

        assert not mock_send_verification_email.delay.called

    @patch("accounts.api.services.get_current_site")
    @patch("accounts.api.services.send_verification_email")
    def test_uses_https_for_secure_requests(
        self,
        mock_send_verification_email,
        mock_get_current_site,
        user,
        mock_request,
        current_site,
        settings,
    ):
        """HTTPS is used when the incoming request is secure."""
        settings.USE_CELERY = False
        mock_request.is_secure.return_value = True
        mock_get_current_site.return_value = current_site

        send_registration_email(
            user=user,
            request=mock_request,
            role_name="teacher",
        )

        context = mock_send_verification_email.call_args.kwargs

        assert context["protocol"] == "https"

    @patch("accounts.api.services.get_current_site")
    @patch("accounts.api.services.send_verification_email")
    def test_builds_expected_email_context(
        self,
        mock_send_verification_email,
        mock_get_current_site,
        user,
        mock_request,
        current_site,
        settings,
    ):
        """The generated email context contains all expected values."""
        settings.USE_CELERY = False
        mock_get_current_site.return_value = current_site

        send_registration_email(
            user=user,
            request=mock_request,
            role_name="student",
        )

        context = mock_send_verification_email.call_args.kwargs

        assert context["email"] == user.email
        assert context["domain"] == current_site.domain
        assert context["site_name"] == current_site.name
        assert context["role_name"] == "student"
        assert context["uid"] == urlsafe_base64_encode(
            force_bytes(user._meta.pk.value_to_string(user))
        )
        assert context["token"] == default_token_generator.make_token(user)


@pytest.mark.django_db
class TestConfirmRegistration:
    """Tests for confirm_registration service."""

    @pytest.fixture
    def inactive_user(self):
        return UserFactory(is_active=False)

    @pytest.fixture
    def active_user(self):
        return UserFactory(is_active=True)

    def test_activates_inactive_user(self, inactive_user):
        """An inactive user is activated."""
        confirm_registration(inactive_user)

        inactive_user.refresh_from_db()

        assert inactive_user.is_active is True

    def test_creates_profile_when_missing(self, inactive_user):
        """A profile is created if the user does not already have one."""
        assert not Profile.objects.filter(user=inactive_user).exists()

        confirm_registration(inactive_user)

        assert Profile.objects.filter(user=inactive_user).exists()

    def test_does_not_create_duplicate_profile(self, active_user):
        """Existing profiles are reused."""
        profile = Profile.objects.create(user=active_user)

        confirm_registration(active_user)

        assert Profile.objects.count() == 1
        assert Profile.objects.get(user=active_user) == profile

    def test_returns_user_instance(self, inactive_user):
        """The activated user is returned."""
        returned_user = confirm_registration(inactive_user)

        assert returned_user == inactive_user

    def test_is_idempotent(self, inactive_user):
        """Calling the service multiple times produces the same result."""
        confirm_registration(inactive_user)
        confirm_registration(inactive_user)

        inactive_user.refresh_from_db()

        assert inactive_user.is_active is True
        assert Profile.objects.filter(user=inactive_user).count() == 1

    def test_keeps_active_user_active(self, active_user):
        """An already active user remains active."""
        confirm_registration(active_user)

        active_user.refresh_from_db()

        assert active_user.is_active is True


class TestGetIdent:
    """Tests for get_ident()."""

    @pytest.fixture
    def request_factory(self):
        return APIRequestFactory()

    def test_returns_remote_addr_when_no_forwarded_header(
        self,
        request_factory,
    ):
        request = request_factory.get("/")
        request.META["REMOTE_ADDR"] = "192.168.1.10"

        with patch.object(api_settings, "NUM_PROXIES", 1):
            assert get_ident(request) == "192.168.1.10"

    def test_returns_remote_addr_when_num_proxies_is_zero(
        self,
        request_factory,
    ):
        request = request_factory.get("/")
        request.META["REMOTE_ADDR"] = "10.0.0.1"
        request.META["HTTP_X_FORWARDED_FOR"] = "1.1.1.1, 2.2.2.2"

        with patch.object(api_settings, "NUM_PROXIES", 0):
            assert get_ident(request) == "10.0.0.1"

    def test_returns_client_ip_from_forwarded_header(
        self,
        request_factory,
    ):
        request = request_factory.get("/")
        request.META["REMOTE_ADDR"] = "10.0.0.1"
        request.META["HTTP_X_FORWARDED_FOR"] = "1.1.1.1, 2.2.2.2"

        with patch.object(api_settings, "NUM_PROXIES", 1):
            assert get_ident(request) == "2.2.2.2"

    def test_returns_correct_ip_when_multiple_proxies_exist(
        self,
        request_factory,
    ):
        request = request_factory.get("/")
        request.META["HTTP_X_FORWARDED_FOR"] = "1.1.1.1, 2.2.2.2, 3.3.3.3"

        with patch.object(api_settings, "NUM_PROXIES", 2):
            assert get_ident(request) == "2.2.2.2"

    def test_returns_forwarded_header_without_spaces_when_num_proxies_is_none(
        self,
        request_factory,
    ):
        request = request_factory.get("/")
        request.META["HTTP_X_FORWARDED_FOR"] = "1.1.1.1, 2.2.2.2"

        with patch.object(api_settings, "NUM_PROXIES", None):
            assert get_ident(request) == "1.1.1.1,2.2.2.2"

    def test_returns_remote_addr_when_forwarded_header_missing_and_num_proxies_is_none(
        self,
        request_factory,
    ):
        request = request_factory.get("/")
        request.META["REMOTE_ADDR"] = "127.0.0.1"

        with patch.object(api_settings, "NUM_PROXIES", None):
            assert get_ident(request) == "127.0.0.1"


class TestGetClientDevice:
    """Tests for get_client_device()."""

    @patch("accounts.api.services.parse")
    def test_returns_operating_system_family(self, mock_parse):
        request = Mock()
        request.META = {"HTTP_USER_AGENT": ("Mozilla/5.0 (X11; Linux x86_64)")}

        mock_parse.return_value.os.family = "Linux"

        assert get_client_device(request) == "Linux"

        mock_parse.assert_called_once_with("Mozilla/5.0 (X11; Linux x86_64)")

    @patch("accounts.api.services.parse")
    def test_returns_other_operating_system(self, mock_parse):
        request = Mock()
        request.META = {"HTTP_USER_AGENT": "Some Agent"}

        mock_parse.return_value.os.family = "Windows"

        assert get_client_device(request) == "Windows"

    @patch("accounts.api.services.parse")
    def test_returns_other_when_user_agent_missing(self, mock_parse):
        request = Mock()
        request.META = {}

        mock_parse.return_value.os.family = "Other"

        assert get_client_device(request) == "Other"

        mock_parse.assert_called_once_with("")


class TestGetLocation:
    """Tests for get_location()."""

    @patch("accounts.api.services.GeoIP2")
    def test_returns_country_information(self, mock_geoip):
        mock_geoip.return_value.country.return_value = {"country_name": "Germany"}

        result = get_location("8.8.8.8")

        assert result == {"country_name": "Germany"}

        mock_geoip.return_value.country.assert_called_once_with("8.8.8.8")

    @patch("accounts.api.services.GeoIP2")
    def test_returns_empty_string_when_lookup_fails(
        self,
        mock_geoip,
    ):
        mock_geoip.return_value.country.side_effect = Exception

        assert get_location("8.8.8.8") == ""


@pytest.mark.django_db
class TestPerformLogin:
    """Tests for perform_login()."""

    @patch("accounts.api.services.create_user_session")
    @patch("accounts.api.services.create_loging_history")
    @patch("accounts.api.services.RefreshToken")
    @patch("accounts.api.services.authenticate")
    def test_returns_tokens_after_successful_login(
        self,
        mock_authenticate,
        mock_refresh_token,
        mock_create_history,
        mock_create_session,
    ):
        user = UserFactory()

        request = Mock()

        validated_data = {
            "username": user.username,
            "password": "secure_pass_1234",
        }

        mock_authenticate.return_value = user

        refresh = Mock()
        refresh.access_token = "access-token"

        mock_refresh_token.for_user.return_value = refresh
        refresh.__str__ = Mock(return_value="refresh-token")

        tokens = perform_login(
            validated_data=validated_data,
            request=request,
        )

        assert tokens == {
            "access": "access-token",
            "refresh": "refresh-token",
        }

        mock_authenticate.assert_called_once_with(
            request=request,
            username=user.username,
            password="secure_pass_1234",
        )

        mock_create_history.assert_called_once_with(
            request,
            user,
            True,
        )

        mock_create_session.assert_called_once_with(
            request,
            user,
        )

    @patch("accounts.api.services.create_loging_history")
    @patch("accounts.api.services.authenticate")
    def test_logs_failed_login_for_existing_user(
        self,
        mock_authenticate,
        mock_create_history,
    ):
        user = UserFactory(password="secure_pass_1234")

        request = Mock()

        validated_data = {
            "username": user.username,
            "password": "wrong-password",
        }

        mock_authenticate.return_value = None

        with pytest.raises(AuthenticationFailed):
            perform_login(
                validated_data,
                request,
            )

        mock_create_history.assert_called_once_with(
            request,
            user,
            False,
        )

    @patch("accounts.api.services.create_loging_history")
    @patch("accounts.api.services.authenticate")
    def test_does_not_create_history_when_user_does_not_exist(
        self,
        mock_authenticate,
        mock_create_history,
    ):
        request = Mock()

        validated_data = {
            "username": "unknown_user",
            "password": "secret",
        }

        mock_authenticate.return_value = None

        with pytest.raises(AuthenticationFailed):
            perform_login(
                validated_data,
                request,
            )

        mock_create_history.assert_not_called()
