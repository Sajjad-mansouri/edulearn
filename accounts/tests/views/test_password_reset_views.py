import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode

from accounts.views import (
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetView,
)

User = get_user_model()


@pytest.mark.django_db
class TestPasswordResetView:
    url_name = "accounts:password_reset"
    template_name = "accounts/password_reset_form.html"

    def test_get_returns_200(self, client):
        url = reverse(self.url_name)

        response = client.get(url)

        assert response.status_code == 200

    def test_uses_correct_template(self, client):
        url = reverse(self.url_name)

        response = client.get(url)

        assert response.template_name == [self.template_name]

    def test_view_uses_expected_template(self):
        assert PasswordResetView.template_name == self.template_name

    def test_does_not_require_authentication(self, client):
        url = reverse(self.url_name)

        response = client.get(url)

        assert response.status_code == 200


@pytest.mark.django_db
class TestPasswordResetConfirmView:
    url_name = "accounts:password_reset_confirm"
    template_name = "accounts/password_reset_confirm.html"

    @pytest.fixture
    def user(self, db):
        return User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="old-password",
        )

    @pytest.fixture
    def uidb64(self, user):
        return urlsafe_base64_encode(str(user.pk).encode())

    @pytest.fixture
    def token(self, user):
        return default_token_generator.make_token(user)

    def get_url(self, uidb64, token):
        return reverse(
            self.url_name,
            kwargs={
                "uidb64": uidb64,
                "token": token,
            },
        )

    def test_get_with_valid_token_redirects_to_internal_password_form(
        self,
        client,
        uidb64,
        token,
    ):
        url = self.get_url(uidb64, token)

        response = client.get(url)

        assert response.status_code == 302
        assert response.url.endswith("/set-password/")

    def test_valid_token_redirects_then_renders_password_form(
        self,
        client,
        uidb64,
        token,
    ):
        url = self.get_url(uidb64, token)

        response = client.get(url)

        assert response.status_code == 302

        response = client.get(response.url)

        assert response.status_code == 200
        assert response.template_name == [self.template_name]

    def test_view_uses_expected_template(self):
        assert PasswordResetConfirmView.template_name == self.template_name

    def test_success_url_is_password_reset_complete(self):
        expected_url = reverse("accounts:password_reset_complete")

        assert PasswordResetConfirmView.success_url == expected_url

    def test_invalid_token_does_not_allow_password_reset(
        self,
        client,
        uidb64,
    ):
        url = self.get_url(uidb64, "invalid-token")

        response = client.get(url)

        assert response.status_code == 200
        assert response.context["validlink"] is False

    def test_expired_token_does_not_allow_password_reset(
        self,
        client,
        user,
        uidb64,
        token,
    ):
        user.set_password("changed-password")
        user.save(update_fields=["password"])

        url = self.get_url(uidb64, token)

        response = client.get(url)

        assert response.status_code == 200
        assert response.context["validlink"] is False

    def test_valid_token_sets_validlink_after_redirect(
        self,
        client,
        uidb64,
        token,
    ):
        url = self.get_url(uidb64, token)

        response = client.get(url)

        assert response.status_code == 302

        response = client.get(response.url)

        assert response.status_code == 200
        assert response.context["validlink"] is True

    def test_post_with_valid_token_changes_password(
        self,
        client,
        user,
        uidb64,
        token,
    ):
        url = self.get_url(uidb64, token)
        new_password = "new-secure-password"

        response = client.get(url)

        assert response.status_code == 302

        form_url = response.url

        response = client.post(
            form_url,
            data={
                "new_password1": new_password,
                "new_password2": new_password,
            },
        )

        assert response.status_code == 302
        assert response.url == reverse("accounts:password_reset_complete")

        user.refresh_from_db()

        assert user.check_password(new_password)

    def test_post_with_invalid_token_does_not_change_password(
        self,
        client,
        user,
        uidb64,
    ):
        url = self.get_url(uidb64, "invalid-token")
        original_password = user.password

        response = client.post(
            url,
            data={
                "new_password1": "new-secure-password",
                "new_password2": "new-secure-password",
            },
        )

        assert response.status_code == 200
        assert response.context["validlink"] is False

        user.refresh_from_db()

        assert user.password == original_password

    def test_post_with_mismatched_passwords_does_not_reset_password(
        self,
        client,
        user,
        uidb64,
        token,
    ):
        url = self.get_url(uidb64, token)
        original_password = user.password

        response = client.get(url)

        assert response.status_code == 302

        form_url = response.url

        response = client.post(
            form_url,
            data={
                "new_password1": "new-secure-password",
                "new_password2": "different-password",
            },
        )

        assert response.status_code == 200

        user.refresh_from_db()

        assert user.password == original_password

    def test_password_reset_does_not_require_authentication(
        self,
        client,
        uidb64,
        token,
    ):
        url = self.get_url(uidb64, token)

        response = client.get(url)

        assert response.status_code == 302

        response = client.get(response.url)

        assert response.status_code == 200


@pytest.mark.django_db
class TestPasswordResetCompleteView:
    url_name = "accounts:password_reset_complete"
    template_name = "accounts/password_reset_complete.html"

    def test_get_returns_200(self, client):
        url = reverse(self.url_name)

        response = client.get(url)

        assert response.status_code == 200

    def test_uses_correct_template(self, client):
        url = reverse(self.url_name)

        response = client.get(url)

        assert response.template_name == [self.template_name]

    def test_view_uses_expected_template(self):
        assert PasswordResetCompleteView.template_name == self.template_name

    def test_does_not_require_authentication(self, client):
        url = reverse(self.url_name)

        response = client.get(url)

        assert response.status_code == 200
