from unittest.mock import MagicMock, Mock, patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.settings import api_settings
from rest_framework.test import APIRequestFactory
from rest_framework_simplejwt.exceptions import TokenError

from accounts.api.services import (
    create_loging_history,
    create_user_session,
    get_client_device,
    get_ident,
    get_location,
    logout_user,
    perform_login,
    register_user,
    send_registration_email,
)
from accounts.models import LoginHistory, Role, UserSession
from accounts.tests.factories import UserFactory

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
    @patch("accounts.api.services.send_email")
    def test_calls_celery_task_when_enabled(
        self,
        mock_send_email,
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
            "recipient": user.email,
            "subject": "Verify your email address",
            "text_template": "register/student_register_confirm_email.txt",
            "html_template": "register/student_register_confirm_email.html",
            "context": {
                "email": user.email,
                "protocol": "http",
                "domain": current_site.domain,
                "site_name": current_site.name,
                "uid": urlsafe_base64_encode(
                    force_bytes(user._meta.pk.value_to_string(user))
                ),
                "token": default_token_generator.make_token(user),
            },
        }

        mock_send_email.delay.assert_called_once_with(**expected_context)

        mock_send_email.assert_not_called()

    @patch("accounts.api.services.get_current_site")
    @patch("accounts.api.services.send_email")
    def test_calls_task_directly_when_celery_is_disabled(
        self,
        mock_send_email,
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
            "recipient": user.email,
            "subject": "Verify your email address",
            "text_template": "register/student_register_confirm_email.txt",
            "html_template": "register/student_register_confirm_email.html",
            "context": {
                "email": user.email,
                "protocol": "http",
                "domain": current_site.domain,
                "site_name": current_site.name,
                "uid": urlsafe_base64_encode(
                    force_bytes(user._meta.pk.value_to_string(user))
                ),
                "token": default_token_generator.make_token(user),
            },
        }

        mock_send_email.assert_called_once_with(**expected_context)

        assert not mock_send_email.delay.called

    @patch("accounts.api.services.get_current_site")
    @patch("accounts.api.services.send_email")
    def test_uses_https_for_secure_requests(
        self,
        mock_send_email,
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

        kwargs = mock_send_email.call_args.kwargs
        context = kwargs["context"]
        assert context["protocol"] == "https"

    @patch("accounts.api.services.get_current_site")
    @patch("accounts.api.services.send_email")
    def test_builds_expected_email_context(
        self,
        mock_send_email,
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

        kwargs = mock_send_email.call_args.kwargs
        context = kwargs["context"]
        assert context["email"] == user.email
        assert context["domain"] == current_site.domain
        assert context["site_name"] == current_site.name
        assert context["uid"] == urlsafe_base64_encode(
            force_bytes(user._meta.pk.value_to_string(user))
        )
        assert context["token"] == default_token_generator.make_token(user)


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


@pytest.mark.django_db
class TestCreateLoginHistory:
    """Tests for create_loging_history()."""

    @patch("accounts.api.services.get_location")
    @patch("accounts.api.services.get_ident")
    def test_creates_successful_login_history(
        self,
        mock_get_ident,
        mock_get_location,
    ):
        user = UserFactory()
        request_obj = Mock()

        mock_get_ident.return_value = "192.168.1.10"
        mock_get_location.return_value = "Germany"

        create_loging_history(
            request=request_obj,
            user=user,
            is_successful=True,
        )

        mock_get_ident.assert_called_once_with(request_obj)
        mock_get_location.assert_called_once_with("192.168.1.10")

        login_history = LoginHistory.objects.get()

        assert login_history.user == user
        assert login_history.ip_address == "192.168.1.10"
        assert login_history.location == "Germany"
        assert login_history.is_successful is True

    @patch("accounts.api.services.get_location")
    @patch("accounts.api.services.get_ident")
    def test_creates_failed_login_history(
        self,
        mock_get_ident,
        mock_get_location,
    ):
        user = UserFactory()
        request_obj = Mock()

        mock_get_ident.return_value = "10.0.0.1"
        mock_get_location.return_value = ""

        create_loging_history(
            request=request_obj,
            user=user,
            is_successful=False,
        )

        login_history = LoginHistory.objects.get()

        assert login_history.user == user
        assert login_history.ip_address == "10.0.0.1"
        assert login_history.location == ""
        assert login_history.is_successful is False


@pytest.mark.django_db
class TestCreateUserSession:
    """Tests for create_user_session()."""

    @patch("accounts.api.services.get_client_device")
    @patch("accounts.api.services.get_ident")
    def test_creates_user_session(
        self,
        mock_get_ident,
        mock_get_client_device,
    ):
        user = UserFactory()

        request_obj = Mock()
        request_obj.META = {
            "HTTP_USER_AGENT": "Mozilla/5.0",
        }

        mock_get_ident.return_value = "203.0.113.5"
        mock_get_client_device.return_value = "Linux"

        create_user_session(
            request=request_obj,
            user=user,
        )

        mock_get_ident.assert_called_once_with(request_obj)
        mock_get_client_device.assert_called_once_with(request_obj)

        session = UserSession.objects.get()

        assert session.user == user
        assert session.ip_address == "203.0.113.5"
        assert session.device == "Linux"
        assert session.user_agent == "Mozilla/5.0"

    @patch("accounts.api.services.get_client_device")
    @patch("accounts.api.services.get_ident")
    def test_creates_user_session_with_empty_user_agent(
        self,
        mock_get_ident,
        mock_get_client_device,
    ):
        user = UserFactory()

        request_obj = Mock()
        request_obj.META = {}

        mock_get_ident.return_value = "127.0.0.1"
        mock_get_client_device.return_value = "Other"

        create_user_session(
            request=request_obj,
            user=user,
        )

        session = UserSession.objects.get()

        assert session.user == user
        assert session.ip_address == "127.0.0.1"
        assert session.device == "Other"
        assert session.user_agent == ""


class TestLogoutUser:
    """Tests for logout_user()."""

    @patch("accounts.api.services.RefreshToken")
    def test_blacklists_refresh_token(
        self,
        mock_refresh_token,
    ):
        refresh_token = "refresh-token"

        token = MagicMock()
        mock_refresh_token.return_value = token

        logout_user(refresh_token)

        mock_refresh_token.assert_called_once_with(refresh_token)
        token.blacklist.assert_called_once_with()

    @patch("accounts.api.services.RefreshToken")
    def test_raises_validation_error_for_invalid_refresh_token(
        self,
        mock_refresh_token,
    ):
        refresh_token = "invalid-refresh-token"

        mock_refresh_token.side_effect = TokenError("Invalid token")

        with pytest.raises(ValidationError) as exc_info:
            logout_user(refresh_token)

        assert exc_info.value.detail == {"refresh": "Invalid refresh token."}

        mock_refresh_token.assert_called_once_with(refresh_token)

    @patch("accounts.api.services.RefreshToken")
    def test_preserves_original_exception_as_cause(
        self,
        mock_refresh_token,
    ):
        refresh_token = "invalid-refresh-token"

        original_error = TokenError("Invalid token")
        mock_refresh_token.side_effect = original_error

        with pytest.raises(ValidationError) as exc_info:
            logout_user(refresh_token)

        assert exc_info.value.__cause__ is original_error
