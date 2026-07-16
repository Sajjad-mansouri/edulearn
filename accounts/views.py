from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import (
    PasswordResetConfirmView as DjangoPasswordResetConfirmView,
)
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import TemplateView

from profiles.models import Profile

UserModel = get_user_model()
INTERNAL_REGISTRATION_SESSION_TOKEN = "_registration_token"


class LoginView(TemplateView):
    template_name = "accounts/login.html"


class RegisterStudentView(TemplateView):
    template_name = "accounts/register_student.html"


@transaction.atomic
def confirm_registration(user):
    """
    Activate a user account and ensure the user profile exists.

    This operation is idempotent.
    """
    if not user.is_active:
        user.is_active = True
        user.save(update_fields=["is_active"])
    Profile.objects.get_or_create(user=user)
    return user


@method_decorator(login_not_required, name="dispatch")
class RegisterConfirmView(TemplateView):
    template_name = "register/registration_complete.html"
    token_generator = default_token_generator
    title = "registration complete"
    confirm_registration_url_token = "confirm-registration"

    @method_decorator(sensitive_post_parameters())
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        if "uidb64" not in kwargs or "token" not in kwargs:
            raise ImproperlyConfigured(
                "The URL path must contain 'uidb64' and 'token' parameters."
            )

        self.validlink = False
        self.user = self.get_user(kwargs["uidb64"])
        if self.user is not None:
            token = kwargs["token"]
            if token == self.confirm_registration_url_token:
                session_token = self.request.session.get(
                    INTERNAL_REGISTRATION_SESSION_TOKEN
                )
                if self.token_generator.check_token(self.user, session_token):
                    self.validlink = True
                    confirm_registration(self.user)
                    return super().dispatch(*args, **kwargs)
            else:
                if self.token_generator.check_token(self.user, token):
                    # Store the token in the session and redirect to the
                    # password reset form at a URL without the token. That
                    # avoids the possibility of leaking the token in the
                    # HTTP Referer header.
                    self.request.session[INTERNAL_REGISTRATION_SESSION_TOKEN] = token

                    redirect_url = self.request.path.replace(
                        token, self.confirm_registration_url_token
                    )
                    return HttpResponseRedirect(redirect_url)

        # Display the "Password reset unsuccessful" page.
        return self.render_to_response(self.get_context_data())

    def get_user(self, uidb64):
        try:
            # urlsafe_base64_decode() decodes to bytestring
            uid = urlsafe_base64_decode(uidb64).decode()
            pk = UserModel._meta.pk.to_python(uid)
            user = UserModel._default_manager.get(pk=pk)
        except (
            TypeError,
            ValueError,
            OverflowError,
            UserModel.DoesNotExist,
            ValidationError,
        ):
            user = None
        return user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.validlink:
            context["validlink"] = True
        else:
            context.update(
                {
                    "title": _("Password reset unsuccessful"),
                    "validlink": False,
                }
            )
        return context


class PasswordResetView(TemplateView):
    template_name = "accounts/password_reset_form.html"


class PasswordResetConfirmView(DjangoPasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")


class PasswordResetCompleteView(TemplateView):
    template_name = "accounts/password_reset_complete.html"
