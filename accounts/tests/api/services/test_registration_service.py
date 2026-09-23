from unittest.mock import Mock

import pytest
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.test import RequestFactory, override_settings
from django.utils.http import urlsafe_base64_decode

from accounts.api.services import register_user, send_registration_email
from accounts.models import Role

User = get_user_model()


@pytest.fixture
def request_factory():
    return RequestFactory()


@pytest.fixture
def registration_request(request_factory):
    return request_factory.get("/accounts/register/")


@pytest.fixture
def secure_registration_request(request_factory):
    return request_factory.get("/accounts/register/", secure=True)


@pytest.fixture
def registration_site(db, settings):
    """
    Configure the Django Sites framework for registration-service tests.

    Reuse an existing example.com site when present because django_site.domain
    is unique.
    """
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
def registration_user(db):
    return User.objects.create_user(
        username="registered_user",
        email="registered_user@example.com",
        password="test-password",
        is_active=False,
    )


class TestSendRegistrationEmail:
    @pytest.fixture(autouse=True)
    def _current_site(self, registration_site):
        """
        Ensure every test in this class has a valid current Site.
        """
        return registration_site

    def test_student_role_builds_correct_email_payload(
        self,
        registration_request,
        registration_user,
        monkeypatch,
    ):
        send_email = Mock()

        monkeypatch.setattr(
            "accounts.api.services.send_email",
            send_email,
        )

        send_registration_email(
            user=registration_user,
            request=registration_request,
            role_name="student",
        )

        send_email.assert_called_once()

        kwargs = send_email.call_args.kwargs

        assert kwargs["recipient"] == registration_user.email
        assert kwargs["subject"] == "Verify your email address"

        assert kwargs["text_template"] == (
            "register/student_register_confirm_email.txt"
        )

        assert kwargs["html_template"] == (
            "register/student_register_confirm_email.html"
        )

        context = kwargs["context"]

        assert context["email"] == registration_user.email
        assert context["protocol"] == "http"
        assert context["domain"] == "example.com"
        assert context["site_name"] == "Example LMS"

        decoded_uid = urlsafe_base64_decode(context["uid"]).decode()

        assert decoded_uid == str(registration_user.pk)
        assert context["token"]

    def test_teacher_role_builds_correct_email_payload(
        self,
        registration_request,
        registration_user,
        monkeypatch,
    ):
        send_email = Mock()

        monkeypatch.setattr(
            "accounts.api.services.send_email",
            send_email,
        )

        send_registration_email(
            user=registration_user,
            request=registration_request,
            role_name="teacher",
        )

        send_email.assert_called_once()

        kwargs = send_email.call_args.kwargs

        assert kwargs["recipient"] == registration_user.email
        assert kwargs["subject"] == "Verify your email address"

        assert kwargs["text_template"] == (
            "register/instructor_register_confirm_email.txt"
        )

        assert kwargs["html_template"] == (
            "register/instructor_register_confirm_email.html"
        )

        context = kwargs["context"]

        assert context["email"] == registration_user.email
        assert context["protocol"] == "http"
        assert context["domain"] == "example.com"
        assert context["site_name"] == "Example LMS"

        decoded_uid = urlsafe_base64_decode(context["uid"]).decode()

        assert decoded_uid == str(registration_user.pk)
        assert context["token"]

    def test_http_request_uses_http_protocol(
        self,
        registration_request,
        registration_user,
        monkeypatch,
    ):
        send_email = Mock()

        monkeypatch.setattr(
            "accounts.api.services.send_email",
            send_email,
        )

        assert registration_request.is_secure() is False

        send_registration_email(
            user=registration_user,
            request=registration_request,
            role_name="student",
        )

        kwargs = send_email.call_args.kwargs

        assert kwargs["context"]["protocol"] == "http"

    def test_https_request_uses_https_protocol(
        self,
        secure_registration_request,
        registration_user,
        monkeypatch,
    ):
        send_email = Mock()

        monkeypatch.setattr(
            "accounts.api.services.send_email",
            send_email,
        )

        assert secure_registration_request.is_secure() is True

        send_registration_email(
            user=registration_user,
            request=secure_registration_request,
            role_name="student",
        )

        kwargs = send_email.call_args.kwargs

        assert kwargs["context"]["protocol"] == "https"

    @pytest.mark.parametrize(
        "role_name",
        [
            "invalid",
            "admin",
            "instructor",
            "",
        ],
    )
    def test_unsupported_role_raises_value_error(
        self,
        registration_request,
        registration_user,
        role_name,
    ):
        with pytest.raises(ValueError) as exc_info:
            send_registration_email(
                user=registration_user,
                request=registration_request,
                role_name=role_name,
            )

        assert str(exc_info.value) == (f"Unsupported role: {role_name}")

    def test_unsupported_role_does_not_send_email(
        self,
        registration_request,
        registration_user,
        monkeypatch,
    ):
        send_email = Mock()

        monkeypatch.setattr(
            "accounts.api.services.send_email",
            send_email,
        )

        with pytest.raises(ValueError) as exc_info:
            send_registration_email(
                user=registration_user,
                request=registration_request,
                role_name="admin",
            )

        assert str(exc_info.value) == "Unsupported role: admin"
        send_email.assert_not_called()

    @override_settings(HOST_ASYNC_ABILITY=True)
    def test_async_delivery_uses_delay(
        self,
        registration_request,
        registration_user,
        monkeypatch,
    ):
        send_email = Mock()
        send_email.delay = Mock()

        monkeypatch.setattr(
            "accounts.api.services.send_email",
            send_email,
        )

        send_registration_email(
            user=registration_user,
            request=registration_request,
            role_name="student",
        )

        send_email.delay.assert_called_once()
        send_email.assert_not_called()

        kwargs = send_email.delay.call_args.kwargs

        assert kwargs["recipient"] == registration_user.email
        assert kwargs["subject"] == "Verify your email address"

        assert kwargs["text_template"] == (
            "register/student_register_confirm_email.txt"
        )

        assert kwargs["html_template"] == (
            "register/student_register_confirm_email.html"
        )

        assert kwargs["context"]["email"] == registration_user.email

    @override_settings(HOST_ASYNC_ABILITY=False)
    def test_sync_delivery_calls_task_directly(
        self,
        registration_request,
        registration_user,
        monkeypatch,
    ):
        send_email = Mock()
        send_email.delay = Mock()

        monkeypatch.setattr(
            "accounts.api.services.send_email",
            send_email,
        )

        send_registration_email(
            user=registration_user,
            request=registration_request,
            role_name="student",
        )

        send_email.assert_called_once()
        send_email.delay.assert_not_called()

        kwargs = send_email.call_args.kwargs

        assert kwargs["recipient"] == registration_user.email
        assert kwargs["subject"] == "Verify your email address"

        assert kwargs["text_template"] == (
            "register/student_register_confirm_email.txt"
        )

        assert kwargs["html_template"] == (
            "register/student_register_confirm_email.html"
        )


@pytest.mark.django_db
class TestRegisterUser:
    @pytest.fixture
    def registration_request(self, request_factory):
        return request_factory.get("/accounts/register/")

    @pytest.fixture
    def request_factory(self):
        return RequestFactory()

    @pytest.fixture
    def registration_data(self):
        return {
            "username": "new_user",
            "email": "new_user@example.com",
            "password1": "test-password",
            "password2": "test-password",
            "first_name": "Test",
            "last_name": "User",
        }

    def test_creates_inactive_user(
        self,
        registration_data,
        registration_request,
        monkeypatch,
    ):
        monkeypatch.setattr(
            "accounts.api.services.send_registration_email",
            Mock(),
        )

        register_user(
            data=registration_data,
            role_name=Role.Roles.STUDENT,
            request=registration_request,
        )

        user = User.objects.get(username="new_user")

        assert user.email == "new_user@example.com"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.is_active is False

    def test_uses_password1_as_user_password(
        self,
        registration_data,
        registration_request,
        monkeypatch,
    ):
        monkeypatch.setattr(
            "accounts.api.services.send_registration_email",
            Mock(),
        )

        register_user(
            data=registration_data,
            role_name=Role.Roles.STUDENT,
            request=registration_request,
        )

        user = User.objects.get(username="new_user")

        assert user.check_password("test-password") is True

    def test_does_not_store_password2(
        self,
        registration_data,
        registration_request,
        monkeypatch,
    ):
        monkeypatch.setattr(
            "accounts.api.services.send_registration_email",
            Mock(),
        )

        register_user(
            data=registration_data,
            role_name=Role.Roles.STUDENT,
            request=registration_request,
        )

        user = User.objects.get(username="new_user")

        assert not hasattr(user, "password1")
        assert not hasattr(user, "password2")
        assert user.check_password("test-password") is True

    def test_removes_password_fields_from_input_data(
        self,
        registration_data,
        registration_request,
        monkeypatch,
    ):
        monkeypatch.setattr(
            "accounts.api.services.send_registration_email",
            Mock(),
        )

        register_user(
            data=registration_data,
            role_name=Role.Roles.STUDENT,
            request=registration_request,
        )

        assert "password1" not in registration_data
        assert "password2" not in registration_data

    def test_creates_requested_role_when_role_does_not_exist(
        self,
        registration_data,
        registration_request,
        monkeypatch,
    ):
        monkeypatch.setattr(
            "accounts.api.services.send_registration_email",
            Mock(),
        )

        assert not Role.objects.filter(
            name=Role.Roles.STUDENT,
        ).exists()

        register_user(
            data=registration_data,
            role_name=Role.Roles.STUDENT,
            request=registration_request,
        )

        role = Role.objects.get(name=Role.Roles.STUDENT)
        user = User.objects.get(username="new_user")

        assert role.users.filter(pk=user.pk).exists()

    def test_reuses_existing_role(
        self,
        registration_data,
        registration_request,
        monkeypatch,
    ):
        existing_role = Role.objects.create(
            name=Role.Roles.STUDENT,
        )

        monkeypatch.setattr(
            "accounts.api.services.send_registration_email",
            Mock(),
        )

        register_user(
            data=registration_data,
            role_name=Role.Roles.STUDENT,
            request=registration_request,
        )

        assert (
            Role.objects.filter(
                name=Role.Roles.STUDENT,
            ).count()
            == 1
        )

        user = User.objects.get(username="new_user")

        existing_role.refresh_from_db()

        assert existing_role.users.filter(pk=user.pk).exists()

    def test_assigns_requested_role_to_created_user(
        self,
        registration_data,
        registration_request,
        monkeypatch,
    ):
        monkeypatch.setattr(
            "accounts.api.services.send_registration_email",
            Mock(),
        )

        register_user(
            data=registration_data,
            role_name=Role.Roles.STUDENT,
            request=registration_request,
        )

        user = User.objects.get(username="new_user")

        assert user.roles.filter(
            name=Role.Roles.STUDENT,
        ).exists()

    def test_sends_registration_email_after_user_creation(
        self,
        registration_data,
        registration_request,
        monkeypatch,
    ):
        send_registration_email_mock = Mock()

        monkeypatch.setattr(
            "accounts.api.services.send_registration_email",
            send_registration_email_mock,
        )

        register_user(
            data=registration_data,
            role_name=Role.Roles.STUDENT,
            request=registration_request,
        )

        send_registration_email_mock.assert_called_once()

        kwargs = send_registration_email_mock.call_args.kwargs

        assert kwargs["request"] is registration_request
        assert kwargs["role_name"] == Role.Roles.STUDENT

        created_user = kwargs["user"]

        assert created_user.pk is not None
        assert created_user.username == "new_user"
        assert created_user.email == "new_user@example.com"

    def test_registration_email_receives_created_user(
        self,
        registration_data,
        registration_request,
        monkeypatch,
    ):
        send_registration_email_mock = Mock()

        monkeypatch.setattr(
            "accounts.api.services.send_registration_email",
            send_registration_email_mock,
        )

        register_user(
            data=registration_data,
            role_name=Role.Roles.STUDENT,
            request=registration_request,
        )

        user = User.objects.get(username="new_user")

        send_registration_email_mock.assert_called_once_with(
            user=user,
            request=registration_request,
            role_name=Role.Roles.STUDENT,
        )

    def test_email_is_sent_after_user_exists(
        self,
        registration_data,
        registration_request,
        monkeypatch,
    ):
        def assert_user_exists(*, user, request, role_name):
            assert user.pk is not None
            assert User.objects.filter(pk=user.pk).exists()
            assert user.username == "new_user"
            assert role_name == Role.Roles.STUDENT
            assert request is registration_request

        monkeypatch.setattr(
            "accounts.api.services.send_registration_email",
            assert_user_exists,
        )

        register_user(
            data=registration_data,
            role_name=Role.Roles.STUDENT,
            request=registration_request,
        )

    def test_created_user_is_inactive_before_email_dispatch(
        self,
        registration_data,
        registration_request,
        monkeypatch,
    ):
        def assert_user_is_inactive(*, user, request, role_name):
            assert user.is_active is False

        monkeypatch.setattr(
            "accounts.api.services.send_registration_email",
            assert_user_is_inactive,
        )

        register_user(
            data=registration_data,
            role_name=Role.Roles.STUDENT,
            request=registration_request,
        )

    def test_different_role_is_assigned_when_requested(
        self,
        registration_data,
        registration_request,
        monkeypatch,
    ):
        monkeypatch.setattr(
            "accounts.api.services.send_registration_email",
            Mock(),
        )

        register_user(
            data=registration_data,
            role_name=Role.Roles.INSTRUCTOR,
            request=registration_request,
        )

        user = User.objects.get(username="new_user")

        assert user.roles.filter(
            name=Role.Roles.INSTRUCTOR,
        ).exists()

        assert not user.roles.filter(
            name=Role.Roles.STUDENT,
        ).exists()

    def test_email_failure_does_not_change_created_user_behavior(
        self,
        registration_data,
        registration_request,
        monkeypatch,
    ):
        """
        Documents the current behavior of register_user().

        User creation and role assignment occur before email dispatch.
        Therefore, if email dispatch raises, the user remains persisted.
        """
        send_registration_email_mock = Mock(
            side_effect=RuntimeError("email service failed"),
        )

        monkeypatch.setattr(
            "accounts.api.services.send_registration_email",
            send_registration_email_mock,
        )

        with pytest.raises(RuntimeError) as exc_info:
            register_user(
                data=registration_data,
                role_name=Role.Roles.STUDENT,
                request=registration_request,
            )

        assert str(exc_info.value) == "email service failed"

        user = User.objects.get(username="new_user")

        assert user.is_active is False
        assert user.roles.filter(
            name=Role.Roles.STUDENT,
        ).exists()
