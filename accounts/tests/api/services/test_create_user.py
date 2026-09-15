from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from rest_framework.settings import api_settings

from accounts.api.services import (
    create_loging_history,
    create_user_session,
    get_client_device,
    get_ident,
    get_location,
)
from accounts.models import LoginHistory, UserSession

User = get_user_model()


@pytest.fixture
def request_factory():
    return RequestFactory()


@pytest.fixture
def test_user(db):
    return User.objects.create_user(
        username="test_user",
        email="test_user@example.com",
        password="test-password",
    )


@pytest.fixture
def request_without_headers(request_factory):
    return request_factory.get(
        "/test/",
        REMOTE_ADDR="192.0.2.10",
    )


@pytest.fixture
def request_with_user_agent(request_factory):
    return request_factory.get(
        "/test/",
        REMOTE_ADDR="192.0.2.10",
        HTTP_USER_AGENT=(
            "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0"
        ),
    )


class TestGetIdent:
    def test_returns_remote_addr_when_num_proxies_is_zero(
        self,
        request_factory,
        monkeypatch,
    ):
        request = request_factory.get(
            "/test/",
            REMOTE_ADDR="192.0.2.10",
            HTTP_X_FORWARDED_FOR="198.51.100.10",
        )

        monkeypatch.setattr(
            api_settings,
            "NUM_PROXIES",
            0,
        )

        result = get_ident(request)

        assert result == "192.0.2.10"

    def test_returns_remote_addr_when_xff_is_missing(
        self,
        request_factory,
        monkeypatch,
    ):
        request = request_factory.get(
            "/test/",
            REMOTE_ADDR="192.0.2.10",
        )

        monkeypatch.setattr(
            api_settings,
            "NUM_PROXIES",
            1,
        )

        result = get_ident(request)

        assert result == "192.0.2.10"

    def test_returns_client_address_with_one_proxy(
        self,
        request_factory,
        monkeypatch,
    ):
        request = request_factory.get(
            "/test/",
            REMOTE_ADDR="192.0.2.10",
            HTTP_X_FORWARDED_FOR="198.51.100.20",
        )

        monkeypatch.setattr(
            api_settings,
            "NUM_PROXIES",
            1,
        )

        result = get_ident(request)

        assert result == "198.51.100.20"

    def test_returns_correct_address_with_multiple_proxies(
        self,
        request_factory,
        monkeypatch,
    ):
        request = request_factory.get(
            "/test/",
            REMOTE_ADDR="192.0.2.10",
            HTTP_X_FORWARDED_FOR=("198.51.100.20, 203.0.113.30, 192.0.2.40"),
        )

        monkeypatch.setattr(
            api_settings,
            "NUM_PROXIES",
            2,
        )

        result = get_ident(request)

        assert result == "203.0.113.30"

    def test_strips_whitespace_from_selected_forwarded_address(
        self,
        request_factory,
        monkeypatch,
    ):
        request = request_factory.get(
            "/test/",
            REMOTE_ADDR="192.0.2.10",
            HTTP_X_FORWARDED_FOR=("198.51.100.20,   203.0.113.30,   192.0.2.40"),
        )

        monkeypatch.setattr(
            api_settings,
            "NUM_PROXIES",
            1,
        )

        result = get_ident(request)

        assert result == "192.0.2.40"

    def test_uses_available_forwarded_addresses_when_proxy_count_exceeds_list(
        self,
        request_factory,
        monkeypatch,
    ):
        request = request_factory.get(
            "/test/",
            REMOTE_ADDR="192.0.2.10",
            HTTP_X_FORWARDED_FOR="198.51.100.20, 203.0.113.30",
        )

        monkeypatch.setattr(
            api_settings,
            "NUM_PROXIES",
            5,
        )

        result = get_ident(request)

        assert result == "198.51.100.20"

    def test_removes_all_whitespace_when_num_proxies_is_none(
        self,
        request_factory,
        monkeypatch,
    ):
        request = request_factory.get(
            "/test/",
            REMOTE_ADDR="192.0.2.10",
            HTTP_X_FORWARDED_FOR=("198.51.100.20, 203.0.113.30, 192.0.2.40"),
        )

        monkeypatch.setattr(
            api_settings,
            "NUM_PROXIES",
            None,
        )

        result = get_ident(request)

        assert result == "198.51.100.20,203.0.113.30,192.0.2.40"

    def test_falls_back_to_remote_addr_when_xff_is_empty(
        self,
        request_factory,
        monkeypatch,
    ):
        request = request_factory.get(
            "/test/",
            REMOTE_ADDR="192.0.2.10",
            HTTP_X_FORWARDED_FOR="",
        )

        monkeypatch.setattr(
            api_settings,
            "NUM_PROXIES",
            None,
        )

        result = get_ident(request)

        assert result == "192.0.2.10"

    def test_falls_back_to_remote_addr_when_xff_is_missing_and_num_proxies_is_none(
        self,
        request_factory,
        monkeypatch,
    ):
        request = request_factory.get(
            "/test/",
            REMOTE_ADDR="192.0.2.10",
        )

        monkeypatch.setattr(
            api_settings,
            "NUM_PROXIES",
            None,
        )

        result = get_ident(request)

        assert result == "192.0.2.10"

    def test_returns_none_when_remote_addr_and_xff_are_missing(
        self,
        request_factory,
        monkeypatch,
    ):
        request = request_factory.get("/test/")

        # RequestFactory adds REMOTE_ADDR=127.0.0.1 by default.
        request.META.pop("REMOTE_ADDR", None)

        monkeypatch.setattr(
            api_settings,
            "NUM_PROXIES",
            0,
        )

        result = get_ident(request)

        assert result is None


class TestGetClientDevice:
    def test_returns_linux_for_linux_user_agent(
        self,
        request_factory,
    ):
        request = request_factory.get(
            "/test/",
            HTTP_USER_AGENT=(
                "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0"
            ),
        )

        result = get_client_device(request)

        assert result == "Linux"

    def test_returns_windows_for_windows_user_agent(
        self,
        request_factory,
    ):
        request = request_factory.get(
            "/test/",
            HTTP_USER_AGENT=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/140.0.0.0 Safari/537.36"
            ),
        )

        result = get_client_device(request)

        assert result == "Windows"

    def test_returns_ios_for_ios_user_agent(
        self,
        request_factory,
    ):
        request = request_factory.get(
            "/test/",
            HTTP_USER_AGENT=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 "
                "(KHTML, like Gecko) "
                "Version/17.0 Mobile/15E148 Safari/604.1"
            ),
        )

        result = get_client_device(request)

        assert result == "iOS"

    def test_returns_other_for_missing_user_agent(
        self,
        request_factory,
    ):
        request = request_factory.get("/test/")

        request.META.pop("HTTP_USER_AGENT", None)

        result = get_client_device(request)

        assert result == "Other"

    def test_returns_other_for_empty_user_agent(
        self,
        request_factory,
    ):
        request = request_factory.get(
            "/test/",
            HTTP_USER_AGENT="",
        )

        result = get_client_device(request)

        assert result == "Other"


class TestGetLocation:
    @patch("accounts.api.services.GeoIP2")
    def test_returns_geoip_country_result(
        self,
        geoip_class,
    ):
        expected_location = {
            "country_code": "AZ",
            "country_name": "Azerbaijan",
        }

        geoip_instance = geoip_class.return_value
        geoip_instance.country.return_value = expected_location

        result = get_location("192.0.2.10")

        assert result == expected_location
        geoip_instance.country.assert_called_once_with("192.0.2.10")

    @patch("accounts.api.services.GeoIP2")
    def test_returns_empty_string_when_geoip_lookup_fails(
        self,
        geoip_class,
    ):
        geoip_instance = geoip_class.return_value
        geoip_instance.country.side_effect = RuntimeError("GeoIP database unavailable")

        result = get_location("192.0.2.10")

        assert result == ""

    @patch("accounts.api.services.GeoIP2")
    def test_creates_geoip_instance(
        self,
        geoip_class,
    ):
        geoip_instance = geoip_class.return_value
        geoip_instance.country.return_value = {
            "country_code": "AZ",
        }

        get_location("192.0.2.10")

        geoip_class.assert_called_once_with()


@pytest.mark.django_db
class TestCreateLoginHistory:
    @patch("accounts.api.services.get_location")
    @patch("accounts.api.services.get_ident")
    def test_creates_successful_login_history(
        self,
        get_ident_mock,
        get_location_mock,
        request_without_headers,
        test_user,
    ):
        get_ident_mock.return_value = "192.0.2.10"
        get_location_mock.return_value = {
            "country_code": "AZ",
            "country_name": "Azerbaijan",
        }

        create_loging_history(
            request=request_without_headers,
            user=test_user,
            is_successful=True,
        )

        history = LoginHistory.objects.get(
            user=test_user,
        )

        assert history.ip_address == "192.0.2.10"
        assert history.location == (
            "{'country_code': 'AZ', 'country_name': 'Azerbaijan'}"
        )
        assert history.is_successful is True

    @patch("accounts.api.services.get_location")
    @patch("accounts.api.services.get_ident")
    def test_creates_failed_login_history(
        self,
        get_ident_mock,
        get_location_mock,
        request_without_headers,
        test_user,
    ):
        get_ident_mock.return_value = "192.0.2.20"
        get_location_mock.return_value = {
            "country_code": "US",
            "country_name": "United States",
        }

        create_loging_history(
            request=request_without_headers,
            user=test_user,
            is_successful=False,
        )

        history = LoginHistory.objects.get(
            user=test_user,
        )

        assert history.ip_address == "192.0.2.20"
        assert history.location == (
            "{'country_code': 'US', 'country_name': 'United States'}"
        )
        assert history.is_successful is False

    @patch("accounts.api.services.get_location")
    @patch("accounts.api.services.get_ident")
    def test_uses_identified_ip_for_location_lookup(
        self,
        get_ident_mock,
        get_location_mock,
        request_without_headers,
        test_user,
    ):
        get_ident_mock.return_value = "203.0.113.25"
        get_location_mock.return_value = {
            "country_code": "DE",
        }

        create_loging_history(
            request=request_without_headers,
            user=test_user,
            is_successful=True,
        )

        get_ident_mock.assert_called_once_with(
            request_without_headers,
        )
        get_location_mock.assert_called_once_with(
            "203.0.113.25",
        )

        history = LoginHistory.objects.get(
            user=test_user,
        )

        assert history.ip_address == "203.0.113.25"
        assert history.location == "{'country_code': 'DE'}"

    @patch("accounts.api.services.get_location")
    @patch("accounts.api.services.get_ident")
    def test_passes_success_status_unchanged(
        self,
        get_ident_mock,
        get_location_mock,
        request_without_headers,
        test_user,
    ):
        get_ident_mock.return_value = "192.0.2.30"
        get_location_mock.return_value = ""

        create_loging_history(
            request=request_without_headers,
            user=test_user,
            is_successful=False,
        )

        history = LoginHistory.objects.get(
            user=test_user,
        )

        assert history.is_successful is False

    @patch("accounts.api.services.get_location")
    @patch("accounts.api.services.get_ident")
    def test_creates_exactly_one_history_record(
        self,
        get_ident_mock,
        get_location_mock,
        request_without_headers,
        test_user,
    ):
        get_ident_mock.return_value = "192.0.2.40"
        get_location_mock.return_value = ""

        create_loging_history(
            request=request_without_headers,
            user=test_user,
            is_successful=True,
        )

        assert (
            LoginHistory.objects.filter(
                user=test_user,
            ).count()
            == 1
        )

    @patch("accounts.api.services.get_location")
    @patch("accounts.api.services.get_ident")
    def test_stores_empty_location_when_location_lookup_fails(
        self,
        get_ident_mock,
        get_location_mock,
        request_without_headers,
        test_user,
    ):
        get_ident_mock.return_value = "192.0.2.50"
        get_location_mock.return_value = ""

        create_loging_history(
            request=request_without_headers,
            user=test_user,
            is_successful=True,
        )

        history = LoginHistory.objects.get(
            user=test_user,
        )

        assert history.location == ""


@pytest.mark.django_db
class TestCreateUserSession:
    @patch("accounts.api.services.get_client_device")
    @patch("accounts.api.services.get_ident")
    def test_creates_user_session(
        self,
        get_ident_mock,
        get_client_device_mock,
        request_with_user_agent,
        test_user,
    ):
        get_ident_mock.return_value = "192.0.2.10"
        get_client_device_mock.return_value = "Linux"

        create_user_session(
            request=request_with_user_agent,
            user=test_user,
        )

        session = UserSession.objects.get(
            user=test_user,
        )

        assert session.ip_address == "192.0.2.10"
        assert session.device == "Linux"
        assert session.user_agent == request_with_user_agent.META["HTTP_USER_AGENT"]

    @patch("accounts.api.services.get_client_device")
    @patch("accounts.api.services.get_ident")
    def test_uses_identified_ip(
        self,
        get_ident_mock,
        get_client_device_mock,
        request_with_user_agent,
        test_user,
    ):
        get_ident_mock.return_value = "203.0.113.10"
        get_client_device_mock.return_value = "Windows"

        create_user_session(
            request=request_with_user_agent,
            user=test_user,
        )

        get_ident_mock.assert_called_once_with(
            request_with_user_agent,
        )

        session = UserSession.objects.get(
            user=test_user,
        )

        assert session.ip_address == "203.0.113.10"

    @patch("accounts.api.services.get_client_device")
    @patch("accounts.api.services.get_ident")
    def test_uses_client_device(
        self,
        get_ident_mock,
        get_client_device_mock,
        request_with_user_agent,
        test_user,
    ):
        get_ident_mock.return_value = "192.0.2.20"
        get_client_device_mock.return_value = "Android"

        create_user_session(
            request=request_with_user_agent,
            user=test_user,
        )

        get_client_device_mock.assert_called_once_with(
            request_with_user_agent,
        )

        session = UserSession.objects.get(
            user=test_user,
        )

        assert session.device == "Android"

    @patch("accounts.api.services.get_client_device")
    @patch("accounts.api.services.get_ident")
    def test_stores_exact_user_agent(
        self,
        get_ident_mock,
        get_client_device_mock,
        request_factory,
        test_user,
    ):
        user_agent = (
            "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0"
        )

        request = request_factory.get(
            "/test/",
            REMOTE_ADDR="192.0.2.10",
            HTTP_USER_AGENT=user_agent,
        )

        get_ident_mock.return_value = "192.0.2.10"
        get_client_device_mock.return_value = "Linux"

        create_user_session(
            request=request,
            user=test_user,
        )

        session = UserSession.objects.get(
            user=test_user,
        )

        assert session.user_agent == user_agent

    @patch("accounts.api.services.get_client_device")
    @patch("accounts.api.services.get_ident")
    def test_stores_empty_user_agent_when_header_is_missing(
        self,
        get_ident_mock,
        get_client_device_mock,
        request_factory,
        test_user,
    ):
        request = request_factory.get(
            "/test/",
            REMOTE_ADDR="192.0.2.10",
        )

        request.META.pop("HTTP_USER_AGENT", None)

        get_ident_mock.return_value = "192.0.2.10"
        get_client_device_mock.return_value = ""

        create_user_session(
            request=request,
            user=test_user,
        )

        session = UserSession.objects.get(
            user=test_user,
        )

        assert session.user_agent == ""

    @patch("accounts.api.services.get_client_device")
    @patch("accounts.api.services.get_ident")
    def test_creates_exactly_one_session(
        self,
        get_ident_mock,
        get_client_device_mock,
        request_with_user_agent,
        test_user,
    ):
        get_ident_mock.return_value = "192.0.2.10"
        get_client_device_mock.return_value = "Linux"

        create_user_session(
            request=request_with_user_agent,
            user=test_user,
        )

        assert (
            UserSession.objects.filter(
                user=test_user,
            ).count()
            == 1
        )

    @patch("accounts.api.services.get_client_device")
    @patch("accounts.api.services.get_ident")
    def test_stores_user_relation(
        self,
        get_ident_mock,
        get_client_device_mock,
        request_with_user_agent,
        test_user,
    ):
        get_ident_mock.return_value = "192.0.2.10"
        get_client_device_mock.return_value = "Linux"

        create_user_session(
            request=request_with_user_agent,
            user=test_user,
        )

        session = UserSession.objects.get()

        assert session.user_id == test_user.pk
        assert session.user == test_user
