from unittest.mock import Mock, patch

import pytest
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.exceptions import TokenError

from accounts.api.services import logout_user


class TestLogoutUser:
    @patch("accounts.api.services.RefreshToken")
    def test_blacklists_valid_refresh_token(
        self,
        refresh_token_class,
    ):
        refresh_token = Mock()
        refresh_token_class.return_value = refresh_token

        result = logout_user("valid-refresh-token")

        assert result is None

        refresh_token_class.assert_called_once_with(
            "valid-refresh-token",
        )
        refresh_token.blacklist.assert_called_once_with()

    @patch("accounts.api.services.RefreshToken")
    def test_returns_none_after_successful_blacklist(
        self,
        refresh_token_class,
    ):
        refresh_token = Mock()
        refresh_token_class.return_value = refresh_token

        result = logout_user("valid-refresh-token")

        assert result is None

    @patch("accounts.api.services.RefreshToken")
    def test_creates_refresh_token_with_supplied_token(
        self,
        refresh_token_class,
    ):
        refresh_token = Mock()
        refresh_token_class.return_value = refresh_token

        logout_user("refresh-token-value")

        refresh_token_class.assert_called_once_with(
            "refresh-token-value",
        )

    @patch("accounts.api.services.RefreshToken")
    def test_calls_blacklist_on_refresh_token_instance(
        self,
        refresh_token_class,
    ):
        refresh_token = Mock()
        refresh_token_class.return_value = refresh_token

        logout_user("refresh-token-value")

        refresh_token.blacklist.assert_called_once_with()

    @patch("accounts.api.services.RefreshToken")
    def test_raises_validation_error_when_refresh_token_is_invalid(
        self,
        refresh_token_class,
    ):
        refresh_token_class.side_effect = TokenError(
            "Token is invalid or expired",
        )

        with pytest.raises(
            ValidationError,
            match="Invalid refresh token.",
        ):
            logout_user("invalid-refresh-token")

    @patch("accounts.api.services.RefreshToken")
    def test_validation_error_contains_refresh_field(
        self,
        refresh_token_class,
    ):
        refresh_token_class.side_effect = TokenError(
            "Token is invalid",
        )

        with pytest.raises(ValidationError) as exc_info:
            logout_user("invalid-refresh-token")

        assert exc_info.value.detail == {
            "refresh": "Invalid refresh token.",
        }

    @patch("accounts.api.services.RefreshToken")
    def test_converts_token_error_from_blacklist_to_validation_error(
        self,
        refresh_token_class,
    ):
        refresh_token = Mock()
        refresh_token.blacklist.side_effect = TokenError(
            "Token cannot be blacklisted",
        )
        refresh_token_class.return_value = refresh_token

        with pytest.raises(ValidationError) as exc_info:
            logout_user("refresh-token")

        assert exc_info.value.detail == {
            "refresh": "Invalid refresh token.",
        }

    @patch("accounts.api.services.RefreshToken")
    def test_preserves_token_error_as_validation_error_cause(
        self,
        refresh_token_class,
    ):
        token_error = TokenError("Token is invalid")
        refresh_token_class.side_effect = token_error

        with pytest.raises(ValidationError) as exc_info:
            logout_user("invalid-refresh-token")

        assert exc_info.value.__cause__ is token_error

    @patch("accounts.api.services.RefreshToken")
    def test_preserves_token_error_from_blacklist_as_cause(
        self,
        refresh_token_class,
    ):
        token_error = TokenError("Unable to blacklist token")

        refresh_token = Mock()
        refresh_token.blacklist.side_effect = token_error
        refresh_token_class.return_value = refresh_token

        with pytest.raises(ValidationError) as exc_info:
            logout_user("refresh-token")

        assert exc_info.value.__cause__ is token_error

    @patch("accounts.api.services.RefreshToken")
    def test_does_not_blacklist_when_refresh_token_construction_fails(
        self,
        refresh_token_class,
    ):
        refresh_token_class.side_effect = TokenError(
            "Token is invalid",
        )

        with pytest.raises(ValidationError):
            logout_user("invalid-refresh-token")

        refresh_token_class.assert_called_once_with(
            "invalid-refresh-token",
        )

    @patch("accounts.api.services.RefreshToken")
    def test_does_not_swallow_unexpected_exception(
        self,
        refresh_token_class,
    ):
        refresh_token_class.side_effect = RuntimeError(
            "Unexpected failure",
        )

        with pytest.raises(
            RuntimeError,
            match="Unexpected failure",
        ):
            logout_user("refresh-token")

    @patch("accounts.api.services.RefreshToken")
    def test_does_not_convert_unexpected_blacklist_exception(
        self,
        refresh_token_class,
    ):
        refresh_token = Mock()
        refresh_token.blacklist.side_effect = RuntimeError(
            "Database failure",
        )
        refresh_token_class.return_value = refresh_token

        with pytest.raises(
            RuntimeError,
            match="Database failure",
        ):
            logout_user("refresh-token")
