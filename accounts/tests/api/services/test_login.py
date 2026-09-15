from unittest.mock import Mock, patch

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from rest_framework.exceptions import AuthenticationFailed

from accounts.api.services import perform_login
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
def login_request(request_factory):
    return request_factory.post(
        "/login/",
        REMOTE_ADDR="192.0.2.10",
        HTTP_USER_AGENT=(
            "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0"
        ),
    )


@pytest.fixture
def valid_login_data():
    return {
        "username": "test_user",
        "password": "test-password",
    }


@pytest.fixture
def invalid_login_data():
    return {
        "username": "test_user",
        "password": "wrong-password",
    }


class TestPerformLogin:
    @patch("accounts.api.services.create_loging_history")
    @patch("accounts.api.services.create_user_session")
    @patch("accounts.api.services.login")
    @patch("accounts.api.services.RefreshToken.for_user")
    @patch("accounts.api.services.authenticate")
    def test_returns_access_and_refresh_tokens_for_valid_credentials(
        self,
        authenticate_mock,
        refresh_token_mock,
        login_mock,
        create_user_session_mock,
        create_loging_history_mock,
        test_user,
        login_request,
        valid_login_data,
    ):
        authenticate_mock.return_value = test_user

        refresh_mock = Mock()
        access_token_mock = Mock()

        refresh_mock.access_token = access_token_mock

        refresh_mock.__str__ = Mock(return_value="refresh-token")
        access_token_mock.__str__ = Mock(return_value="access-token")

        refresh_token_mock.return_value = refresh_mock

        result = perform_login(
            validated_data=valid_login_data,
            request=login_request,
        )

        assert result == {
            "access": "access-token",
            "refresh": "refresh-token",
        }

    @patch("accounts.api.services.create_loging_history")
    @patch("accounts.api.services.create_user_session")
    @patch("accounts.api.services.login")
    @patch("accounts.api.services.RefreshToken.for_user")
    @patch("accounts.api.services.authenticate")
    def test_authenticates_with_request_username_and_password(
        self,
        authenticate_mock,
        refresh_token_mock,
        login_mock,
        create_user_session_mock,
        create_loging_history_mock,
        test_user,
        login_request,
        valid_login_data,
    ):
        authenticate_mock.return_value = test_user

        refresh_mock = Mock()
        access_token_mock = Mock()

        refresh_mock.access_token = access_token_mock

        refresh_mock.__str__ = Mock(return_value="refresh-token")
        access_token_mock.__str__ = Mock(return_value="access-token")

        refresh_token_mock.return_value = refresh_mock

        perform_login(
            validated_data=valid_login_data,
            request=login_request,
        )

        authenticate_mock.assert_called_once_with(
            request=login_request,
            username="test_user",
            password="test-password",
        )

    @patch("accounts.api.services.create_loging_history")
    @patch("accounts.api.services.create_user_session")
    @patch("accounts.api.services.login")
    @patch("accounts.api.services.RefreshToken.for_user")
    @patch("accounts.api.services.authenticate")
    def test_creates_refresh_token_for_authenticated_user(
        self,
        authenticate_mock,
        refresh_token_mock,
        login_mock,
        create_user_session_mock,
        create_loging_history_mock,
        test_user,
        login_request,
        valid_login_data,
    ):
        authenticate_mock.return_value = test_user

        refresh_mock = Mock()
        access_token_mock = Mock()

        refresh_mock.access_token = access_token_mock

        refresh_mock.__str__ = Mock(return_value="refresh-token")
        access_token_mock.__str__ = Mock(return_value="access-token")

        refresh_token_mock.return_value = refresh_mock

        perform_login(
            validated_data=valid_login_data,
            request=login_request,
        )

        refresh_token_mock.assert_called_once_with(test_user)

    @patch("accounts.api.services.create_loging_history")
    @patch("accounts.api.services.create_user_session")
    @patch("accounts.api.services.login")
    @patch("accounts.api.services.RefreshToken.for_user")
    @patch("accounts.api.services.authenticate")
    def test_calls_django_login_with_authenticated_user(
        self,
        authenticate_mock,
        refresh_token_mock,
        login_mock,
        create_user_session_mock,
        create_loging_history_mock,
        test_user,
        login_request,
        valid_login_data,
    ):
        authenticate_mock.return_value = test_user

        refresh_mock = Mock()
        access_token_mock = Mock()

        refresh_mock.access_token = access_token_mock

        refresh_mock.__str__ = Mock(return_value="refresh-token")
        access_token_mock.__str__ = Mock(return_value="access-token")

        refresh_token_mock.return_value = refresh_mock

        perform_login(
            validated_data=valid_login_data,
            request=login_request,
        )

        login_mock.assert_called_once_with(
            login_request,
            test_user,
        )

    @patch("accounts.api.services.create_loging_history")
    @patch("accounts.api.services.create_user_session")
    @patch("accounts.api.services.login")
    @patch("accounts.api.services.RefreshToken.for_user")
    @patch("accounts.api.services.authenticate")
    def test_creates_successful_login_history(
        self,
        authenticate_mock,
        refresh_token_mock,
        login_mock,
        create_user_session_mock,
        create_loging_history_mock,
        test_user,
        login_request,
        valid_login_data,
    ):
        authenticate_mock.return_value = test_user

        refresh_mock = Mock()
        access_token_mock = Mock()

        refresh_mock.access_token = access_token_mock

        refresh_mock.__str__ = Mock(return_value="refresh-token")
        access_token_mock.__str__ = Mock(return_value="access-token")

        refresh_token_mock.return_value = refresh_mock

        perform_login(
            validated_data=valid_login_data,
            request=login_request,
        )

        create_loging_history_mock.assert_called_once_with(
            login_request,
            test_user,
            True,
        )

    @patch("accounts.api.services.create_loging_history")
    @patch("accounts.api.services.create_user_session")
    @patch("accounts.api.services.login")
    @patch("accounts.api.services.RefreshToken.for_user")
    @patch("accounts.api.services.authenticate")
    def test_creates_user_session_for_authenticated_user(
        self,
        authenticate_mock,
        refresh_token_mock,
        login_mock,
        create_user_session_mock,
        create_loging_history_mock,
        test_user,
        login_request,
        valid_login_data,
    ):
        authenticate_mock.return_value = test_user

        refresh_mock = Mock()
        access_token_mock = Mock()

        refresh_mock.access_token = access_token_mock

        refresh_mock.__str__ = Mock(return_value="refresh-token")
        access_token_mock.__str__ = Mock(return_value="access-token")

        refresh_token_mock.return_value = refresh_mock

        perform_login(
            validated_data=valid_login_data,
            request=login_request,
        )

        create_user_session_mock.assert_called_once_with(
            login_request,
            test_user,
        )

    @patch("accounts.api.services.create_loging_history")
    @patch("accounts.api.services.create_user_session")
    @patch("accounts.api.services.login")
    @patch("accounts.api.services.RefreshToken.for_user")
    @patch("accounts.api.services.authenticate")
    def test_does_not_create_failed_login_history_on_success(
        self,
        authenticate_mock,
        refresh_token_mock,
        login_mock,
        create_user_session_mock,
        create_loging_history_mock,
        test_user,
        login_request,
        valid_login_data,
    ):
        authenticate_mock.return_value = test_user

        refresh_mock = Mock()
        access_token_mock = Mock()

        refresh_mock.access_token = access_token_mock

        refresh_mock.__str__ = Mock(return_value="refresh-token")
        access_token_mock.__str__ = Mock(return_value="access-token")

        refresh_token_mock.return_value = refresh_mock

        perform_login(
            validated_data=valid_login_data,
            request=login_request,
        )

        create_loging_history_mock.assert_called_once_with(
            login_request,
            test_user,
            True,
        )

        assert create_loging_history_mock.call_args.args[2] is True

    @pytest.mark.django_db
    @patch("accounts.api.services.create_loging_history")
    @patch("accounts.api.services.authenticate")
    def test_raises_authentication_failed_for_existing_user_with_wrong_password(
        self,
        authenticate_mock,
        create_loging_history_mock,
        test_user,
        login_request,
        invalid_login_data,
    ):
        authenticate_mock.return_value = None

        with pytest.raises(
            AuthenticationFailed,
            match="Invalid username or password.",
        ):
            perform_login(
                validated_data=invalid_login_data,
                request=login_request,
            )

        create_loging_history_mock.assert_called_once_with(
            login_request,
            test_user,
            False,
        )

    @pytest.mark.django_db
    @patch("accounts.api.services.create_loging_history")
    @patch("accounts.api.services.authenticate")
    def test_does_not_create_login_history_for_nonexistent_user(
        self,
        authenticate_mock,
        create_loging_history_mock,
        login_request,
    ):
        authenticate_mock.return_value = None

        data = {
            "username": "missing_user",
            "password": "wrong-password",
        }

        with pytest.raises(
            AuthenticationFailed,
            match="Invalid username or password.",
        ):
            perform_login(
                validated_data=data,
                request=login_request,
            )

        create_loging_history_mock.assert_not_called()

    @pytest.mark.django_db
    @patch("accounts.api.services.create_loging_history")
    @patch("accounts.api.services.authenticate")
    def test_does_not_return_token_data_when_authentication_fails(
        self,
        authenticate_mock,
        create_loging_history_mock,
        test_user,
        login_request,
        invalid_login_data,
    ):
        authenticate_mock.return_value = None

        with pytest.raises(AuthenticationFailed):
            perform_login(
                validated_data=invalid_login_data,
                request=login_request,
            )

        assert not LoginHistory.objects.filter(
            user=test_user,
            is_successful=True,
        ).exists()

    @pytest.mark.django_db
    @patch("accounts.api.services.create_loging_history")
    @patch("accounts.api.services.authenticate")
    def test_failed_login_history_is_created_for_existing_user(
        self,
        authenticate_mock,
        create_loging_history_mock,
        test_user,
        login_request,
        invalid_login_data,
    ):
        authenticate_mock.return_value = None

        with pytest.raises(AuthenticationFailed):
            perform_login(
                validated_data=invalid_login_data,
                request=login_request,
            )

        create_loging_history_mock.assert_called_once_with(
            login_request,
            test_user,
            False,
        )

    @patch("accounts.api.services.create_loging_history")
    @patch("accounts.api.services.create_user_session")
    @patch("accounts.api.services.login")
    @patch("accounts.api.services.RefreshToken.for_user")
    @patch("accounts.api.services.authenticate")
    def test_access_token_is_converted_to_string(
        self,
        authenticate_mock,
        refresh_token_mock,
        login_mock,
        create_user_session_mock,
        create_loging_history_mock,
        test_user,
        login_request,
        valid_login_data,
    ):
        authenticate_mock.return_value = test_user

        refresh_mock = Mock()
        access_token_mock = Mock()

        refresh_mock.access_token = access_token_mock

        refresh_mock.__str__ = Mock(return_value="access-token")
        access_token_mock.__str__ = Mock(return_value="access-token")

        refresh_token_mock.return_value = refresh_mock

        result = perform_login(
            validated_data=valid_login_data,
            request=login_request,
        )

        assert result["access"] == "access-token"
        assert isinstance(result["access"], str)

    @patch("accounts.api.services.create_loging_history")
    @patch("accounts.api.services.create_user_session")
    @patch("accounts.api.services.login")
    @patch("accounts.api.services.RefreshToken.for_user")
    @patch("accounts.api.services.authenticate")
    def test_refresh_token_is_converted_to_string(
        self,
        authenticate_mock,
        refresh_token_mock,
        login_mock,
        create_user_session_mock,
        create_loging_history_mock,
        test_user,
        login_request,
        valid_login_data,
    ):
        authenticate_mock.return_value = test_user

        refresh_mock = Mock()
        access_token_mock = Mock()

        refresh_mock.access_token = access_token_mock

        refresh_mock.__str__ = Mock(return_value="refresh-token")
        access_token_mock.__str__ = Mock(return_value="access-token")

        refresh_token_mock.return_value = refresh_mock

        result = perform_login(
            validated_data=valid_login_data,
            request=login_request,
        )

        assert result["refresh"] == "refresh-token"
        assert isinstance(result["refresh"], str)

    @patch("accounts.api.services.create_loging_history")
    @patch("accounts.api.services.create_user_session")
    @patch("accounts.api.services.login")
    @patch("accounts.api.services.RefreshToken.for_user")
    @patch("accounts.api.services.authenticate")
    def test_successful_login_creates_no_failed_history(
        self,
        authenticate_mock,
        refresh_token_mock,
        login_mock,
        create_user_session_mock,
        create_loging_history_mock,
        test_user,
        login_request,
        valid_login_data,
    ):
        authenticate_mock.return_value = test_user

        refresh_mock = Mock()
        access_token_mock = Mock()

        refresh_mock.access_token = access_token_mock

        refresh_mock.__str__ = Mock(return_value="refresh-token")
        access_token_mock.__str__ = Mock(return_value="access-token")

        refresh_token_mock.return_value = refresh_mock

        perform_login(
            validated_data=valid_login_data,
            request=login_request,
        )

        assert create_loging_history_mock.call_count == 1
        create_loging_history_mock.assert_called_once_with(
            login_request,
            test_user,
            True,
        )


@pytest.mark.django_db
class TestPerformLoginDatabaseBehavior:
    @patch("accounts.api.services.get_location")
    @patch("accounts.api.services.get_client_device")
    @patch("accounts.api.services.RefreshToken.for_user")
    @patch("accounts.api.services.login")
    @patch("accounts.api.services.authenticate")
    def test_successful_login_persists_login_history_and_session(
        self,
        authenticate_mock,
        login_mock,
        refresh_token_mock,
        get_client_device_mock,
        get_location_mock,
        test_user,
        login_request,
    ):
        authenticate_mock.return_value = test_user

        refresh_mock = Mock()
        access_token_mock = Mock()

        refresh_mock.access_token = access_token_mock

        refresh_mock.__str__ = Mock(return_value="refresh-token")
        access_token_mock.__str__ = Mock(return_value="access-token")

        refresh_token_mock.return_value = refresh_mock

        get_location_mock.return_value = "Azerbaijan"
        get_client_device_mock.return_value = "Linux"

        result = perform_login(
            validated_data={
                "username": "test_user",
                "password": "test-password",
            },
            request=login_request,
        )

        assert result == {
            "access": "access-token",
            "refresh": "refresh-token",
        }

        history = LoginHistory.objects.get(
            user=test_user,
        )

        assert history.is_successful is True
        assert history.ip_address == "192.0.2.10"
        assert history.location == "Azerbaijan"

        session = UserSession.objects.get(
            user=test_user,
        )

        assert session.ip_address == "192.0.2.10"
        assert session.device == "Linux"
        assert session.user_agent == (
            "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0"
        )

    @patch("accounts.api.services.create_user_session")
    @patch("accounts.api.services.create_loging_history")
    @patch("accounts.api.services.login")
    @patch("accounts.api.services.RefreshToken.for_user")
    @patch("accounts.api.services.authenticate")
    def test_session_is_created_after_successful_login_history(
        self,
        authenticate_mock,
        refresh_token_mock,
        login_mock,
        create_loging_history_mock,
        create_user_session_mock,
        test_user,
        login_request,
    ):
        authenticate_mock.return_value = test_user

        refresh_mock = Mock()
        access_token_mock = Mock()

        refresh_mock.access_token = access_token_mock

        refresh_mock.__str__ = Mock(return_value="refresh-token")
        access_token_mock.__str__ = Mock(return_value="access-token")

        refresh_token_mock.return_value = refresh_mock

        call_order = []

        def record_history(*args):
            call_order.append("history")

        def record_session(*args):
            call_order.append("session")

        create_loging_history_mock.side_effect = record_history
        create_user_session_mock.side_effect = record_session

        perform_login(
            validated_data={
                "username": "test_user",
                "password": "test-password",
            },
            request=login_request,
        )

        assert call_order == [
            "history",
            "session",
        ]

    @patch("accounts.api.services.create_user_session")
    @patch("accounts.api.services.create_loging_history")
    @patch("accounts.api.services.login")
    @patch("accounts.api.services.RefreshToken.for_user")
    @patch("accounts.api.services.authenticate")
    def test_user_session_is_not_created_when_authentication_fails(
        self,
        authenticate_mock,
        refresh_token_mock,
        login_mock,
        create_loging_history_mock,
        create_user_session_mock,
        test_user,
        login_request,
    ):
        authenticate_mock.return_value = None

        with pytest.raises(AuthenticationFailed):
            perform_login(
                validated_data={
                    "username": "test_user",
                    "password": "wrong-password",
                },
                request=login_request,
            )

        create_user_session_mock.assert_not_called()
        login_mock.assert_not_called()
        refresh_token_mock.assert_not_called()

        create_loging_history_mock.assert_called_once_with(
            login_request,
            test_user,
            False,
        )
