import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode

from accounts.views import (
    INTERNAL_REGISTRATION_SESSION_TOKEN,
    RegisterConfirmView,
    confirm_registration,
)
from profiles.models import Profile, StudentProfile

User = get_user_model()


@pytest.fixture
def request_factory():
    return RequestFactory()


@pytest.fixture
def inactive_user(db):
    return User.objects.create_user(
        username="test_user",
        email="test_user@example.com",
        password="test-password",
        is_active=False,
    )


@pytest.fixture
def active_user(db):
    return User.objects.create_user(
        username="active_user",
        email="active_user@example.com",
        password="test-password",
        is_active=True,
    )


@pytest.fixture
def inactive_user_uid(inactive_user):
    return urlsafe_base64_encode(str(inactive_user.pk).encode())


@pytest.fixture
def registration_token(inactive_user):
    return default_token_generator.make_token(inactive_user)


@pytest.fixture
def registration_url(inactive_user_uid, registration_token):
    return reverse(
        "accounts:register_confirm",
        kwargs={
            "uidb64": inactive_user_uid,
            "token": registration_token,
        },
    )


@pytest.mark.django_db
class TestConfirmRegistration:
    def test_activates_inactive_user(self, inactive_user):
        assert inactive_user.is_active is False

        result = confirm_registration(inactive_user)

        inactive_user.refresh_from_db()

        assert result == inactive_user
        assert inactive_user.is_active is True

    def test_creates_profile_for_user(self, inactive_user):
        assert not Profile.objects.filter(user=inactive_user).exists()

        confirm_registration(inactive_user)

        profile = Profile.objects.get(user=inactive_user)

        assert profile.user == inactive_user

    def test_creates_student_profile_for_user(self, inactive_user):
        confirm_registration(inactive_user)

        profile = Profile.objects.get(user=inactive_user)
        student_profile = StudentProfile.objects.get(profile=profile)

        assert student_profile.profile == profile

    def test_does_not_create_duplicate_profile(
        self,
        inactive_user,
    ):
        confirm_registration(inactive_user)

        first_profile = Profile.objects.get(user=inactive_user)

        confirm_registration(inactive_user)

        profiles = Profile.objects.filter(user=inactive_user)

        assert profiles.count() == 1
        assert profiles.get().pk == first_profile.pk

    def test_does_not_create_duplicate_student_profile(
        self,
        inactive_user,
    ):
        confirm_registration(inactive_user)

        profile = Profile.objects.get(user=inactive_user)
        first_student_profile = StudentProfile.objects.get(profile=profile)

        confirm_registration(inactive_user)

        student_profiles = StudentProfile.objects.filter(profile=profile)

        assert student_profiles.count() == 1
        assert student_profiles.get().pk == first_student_profile.pk

    def test_is_idempotent_for_already_active_user(
        self,
        active_user,
    ):
        assert active_user.is_active is True

        result = confirm_registration(active_user)

        active_user.refresh_from_db()

        assert result == active_user
        assert active_user.is_active is True

        assert Profile.objects.filter(user=active_user).count() == 1
        profile = Profile.objects.get(user=active_user)

        assert StudentProfile.objects.filter(profile=profile).count() == 1

    def test_preserves_existing_profile(
        self,
        inactive_user,
    ):
        profile = Profile.objects.create(user=inactive_user)

        confirm_registration(inactive_user)

        inactive_user.refresh_from_db()

        assert inactive_user.is_active is True
        assert Profile.objects.filter(user=inactive_user).count() == 1
        assert Profile.objects.get(user=inactive_user).pk == profile.pk

    def test_preserves_existing_student_profile(
        self,
        inactive_user,
    ):
        profile = Profile.objects.create(user=inactive_user)
        student_profile = StudentProfile.objects.create(profile=profile)

        confirm_registration(inactive_user)

        assert StudentProfile.objects.filter(profile=profile).count() == 1

        assert StudentProfile.objects.get(profile=profile).pk == student_profile.pk


@pytest.mark.django_db
class TestRegisterConfirmView:
    def test_valid_registration_token_redirects_to_internal_token_url(
        self,
        client,
        inactive_user,
        inactive_user_uid,
        registration_token,
    ):
        url = reverse(
            "accounts:register_confirm",
            kwargs={
                "uidb64": inactive_user_uid,
                "token": registration_token,
            },
        )

        response = client.get(url)

        expected_url = reverse(
            "accounts:register_confirm",
            kwargs={
                "uidb64": inactive_user_uid,
                "token": RegisterConfirmView.confirm_registration_url_token,
            },
        )

        assert response.status_code == 302
        assert response.url == expected_url

    def test_valid_registration_token_is_stored_in_session(
        self,
        client,
        inactive_user,
        inactive_user_uid,
        registration_token,
    ):
        url = reverse(
            "accounts:register_confirm",
            kwargs={
                "uidb64": inactive_user_uid,
                "token": registration_token,
            },
        )

        client.get(url)

        session = client.session

        assert session[INTERNAL_REGISTRATION_SESSION_TOKEN] == registration_token

    def test_valid_registration_token_does_not_activate_user_during_redirect(
        self,
        client,
        inactive_user,
        inactive_user_uid,
        registration_token,
    ):
        url = reverse(
            "accounts:register_confirm",
            kwargs={
                "uidb64": inactive_user_uid,
                "token": registration_token,
            },
        )

        client.get(url)

        inactive_user.refresh_from_db()

        assert inactive_user.is_active is False
        assert not Profile.objects.filter(user=inactive_user).exists()
        assert not StudentProfile.objects.filter(profile__user=inactive_user).exists()

    def test_internal_confirmation_token_activates_user(
        self,
        client,
        inactive_user,
        inactive_user_uid,
        registration_token,
    ):
        first_url = reverse(
            "accounts:register_confirm",
            kwargs={
                "uidb64": inactive_user_uid,
                "token": registration_token,
            },
        )

        client.get(first_url)

        confirmation_url = reverse(
            "accounts:register_confirm",
            kwargs={
                "uidb64": inactive_user_uid,
                "token": RegisterConfirmView.confirm_registration_url_token,
            },
        )

        response = client.get(confirmation_url)

        inactive_user.refresh_from_db()

        assert response.status_code == 200
        assert inactive_user.is_active is True

    def test_internal_confirmation_token_creates_profile(
        self,
        client,
        inactive_user,
        inactive_user_uid,
        registration_token,
    ):
        first_url = reverse(
            "accounts:register_confirm",
            kwargs={
                "uidb64": inactive_user_uid,
                "token": registration_token,
            },
        )

        client.get(first_url)

        confirmation_url = reverse(
            "accounts:register_confirm",
            kwargs={
                "uidb64": inactive_user_uid,
                "token": RegisterConfirmView.confirm_registration_url_token,
            },
        )

        client.get(confirmation_url)

        profile = Profile.objects.get(user=inactive_user)

        assert profile.user == inactive_user

    def test_internal_confirmation_token_creates_student_profile(
        self,
        client,
        inactive_user,
        inactive_user_uid,
        registration_token,
    ):
        first_url = reverse(
            "accounts:register_confirm",
            kwargs={
                "uidb64": inactive_user_uid,
                "token": registration_token,
            },
        )

        client.get(first_url)

        confirmation_url = reverse(
            "accounts:register_confirm",
            kwargs={
                "uidb64": inactive_user_uid,
                "token": RegisterConfirmView.confirm_registration_url_token,
            },
        )

        client.get(confirmation_url)

        profile = Profile.objects.get(user=inactive_user)
        student_profile = StudentProfile.objects.get(profile=profile)

        assert student_profile.profile == profile

    def test_internal_confirmation_token_requires_valid_session_token(
        self,
        client,
        inactive_user,
        inactive_user_uid,
    ):
        confirmation_url = reverse(
            "accounts:register_confirm",
            kwargs={
                "uidb64": inactive_user_uid,
                "token": RegisterConfirmView.confirm_registration_url_token,
            },
        )

        response = client.get(confirmation_url)

        inactive_user.refresh_from_db()

        assert response.status_code == 200
        assert inactive_user.is_active is False
        assert not Profile.objects.filter(user=inactive_user).exists()

    def test_internal_confirmation_token_does_not_work_with_wrong_session_token(
        self,
        client,
        inactive_user,
        inactive_user_uid,
    ):
        session = client.session
        session[INTERNAL_REGISTRATION_SESSION_TOKEN] = "invalid-token"
        session.save()

        confirmation_url = reverse(
            "accounts:register_confirm",
            kwargs={
                "uidb64": inactive_user_uid,
                "token": RegisterConfirmView.confirm_registration_url_token,
            },
        )

        response = client.get(confirmation_url)

        inactive_user.refresh_from_db()

        assert response.status_code == 200
        assert inactive_user.is_active is False

    def test_invalid_token_renders_unsuccessful_page(
        self,
        client,
        inactive_user,
        inactive_user_uid,
    ):
        url = reverse(
            "accounts:register_confirm",
            kwargs={
                "uidb64": inactive_user_uid,
                "token": "invalid-token",
            },
        )

        response = client.get(url)

        assert response.status_code == 200
        assert response.template_name == ["register/registration_complete.html"]

    def test_invalid_token_does_not_activate_user(
        self,
        client,
        inactive_user,
        inactive_user_uid,
    ):
        url = reverse(
            "accounts:register_confirm",
            kwargs={
                "uidb64": inactive_user_uid,
                "token": "invalid-token",
            },
        )

        client.get(url)

        inactive_user.refresh_from_db()

        assert inactive_user.is_active is False

    def test_invalid_token_does_not_create_profile(
        self,
        client,
        inactive_user,
        inactive_user_uid,
    ):
        url = reverse(
            "accounts:register_confirm",
            kwargs={
                "uidb64": inactive_user_uid,
                "token": "invalid-token",
            },
        )

        client.get(url)

        assert not Profile.objects.filter(user=inactive_user).exists()

    def test_invalid_uid_renders_unsuccessful_page(
        self,
        client,
    ):
        url = reverse(
            "accounts:register_confirm",
            kwargs={
                "uidb64": "invalid-uid",
                "token": "invalid-token",
            },
        )

        response = client.get(url)

        assert response.status_code == 200
        assert response.template_name == ["register/registration_complete.html"]

    def test_invalid_uid_does_not_create_any_user_data(
        self,
        client,
    ):
        url = reverse(
            "accounts:register_confirm",
            kwargs={
                "uidb64": "invalid-uid",
                "token": "invalid-token",
            },
        )

        response = client.get(url)

        assert response.status_code == 200

    def test_invalid_link_context_contains_expected_values(
        self,
        client,
        inactive_user,
        inactive_user_uid,
    ):
        url = reverse(
            "accounts:register_confirm",
            kwargs={
                "uidb64": inactive_user_uid,
                "token": "invalid-token",
            },
        )

        response = client.get(url)

        assert response.context["validlink"] is False
        assert response.context["title"] == "Password reset unsuccessful"

    def test_valid_link_context_contains_validlink(
        self,
        client,
        inactive_user,
        inactive_user_uid,
        registration_token,
    ):
        first_url = reverse(
            "accounts:register_confirm",
            kwargs={
                "uidb64": inactive_user_uid,
                "token": registration_token,
            },
        )

        client.get(first_url)

        confirmation_url = reverse(
            "accounts:register_confirm",
            kwargs={
                "uidb64": inactive_user_uid,
                "token": RegisterConfirmView.confirm_registration_url_token,
            },
        )

        response = client.get(confirmation_url)

        assert response.status_code == 200
        assert response.context["validlink"] is True

    def test_authenticated_user_can_access_confirmation_page(
        self,
        client,
        active_user,
        inactive_user_uid,
        registration_token,
    ):
        client.force_login(active_user)

        url = reverse(
            "accounts:register_confirm",
            kwargs={
                "uidb64": inactive_user_uid,
                "token": registration_token,
            },
        )

        response = client.get(url)

        assert response.status_code == 302

    def test_missing_uid_parameter_raises_improperly_configured(
        self,
        request_factory,
    ):
        request = request_factory.get("/register/")

        with pytest.raises(
            ImproperlyConfigured,
            match="must contain 'uidb64' and 'token'",
        ):
            RegisterConfirmView.as_view()(
                request,
                token="some-token",
            )

    def test_missing_token_parameter_raises_improperly_configured(
        self,
        request_factory,
        inactive_user_uid,
    ):
        request = request_factory.get("/register/")

        with pytest.raises(
            ImproperlyConfigured,
            match="must contain 'uidb64' and 'token'",
        ):
            RegisterConfirmView.as_view()(
                request,
                uidb64=inactive_user_uid,
            )

    def test_get_user_returns_user_for_valid_uid(
        self,
        inactive_user,
        inactive_user_uid,
    ):
        view = RegisterConfirmView()

        result = view.get_user(inactive_user_uid)

        assert result == inactive_user

    def test_get_user_returns_none_for_nonexistent_user(self):
        nonexistent_pk = "999999999"
        uidb64 = urlsafe_base64_encode(nonexistent_pk.encode())

        view = RegisterConfirmView()

        result = view.get_user(uidb64)

        assert result is None

    def test_get_user_returns_none_for_invalid_uid(self):
        uidb64 = urlsafe_base64_encode(b"not-a-valid-user-id")

        view = RegisterConfirmView()

        result = view.get_user(uidb64)

        assert result is None
