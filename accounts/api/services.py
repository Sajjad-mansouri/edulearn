from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from accounts.models import Role
from accounts.tasks import send_verification_email

User = get_user_model()


def register_user(data, role_name, request):
    data.pop("password2")
    password = data.pop("password1")
    user = User.objects.create_user(password=password, is_active=False, **data)
    role, _ = Role.objects.get_or_create(name=role_name)
    role.users.add(user)
    send_registration_email(user=user, request=request, role_name=role_name)


def send_registration_email(user, request, role_name):
    protocol = "https" if request.is_secure() else "http"
    current_site = get_current_site(request)
    user_pk_bytes = force_bytes(User._meta.pk.value_to_string(user))
    email_context = {
        "email": user.email,
        "protocol": protocol,
        "domain": current_site.domain,
        "site_name": current_site.name,
        "uid": urlsafe_base64_encode(user_pk_bytes),
        "token": default_token_generator.make_token(user),
        "role_name": role_name,
    }
    if settings.USE_CELERY:
        send_verification_email.delay(**email_context)
    else:
        send_verification_email(**email_context)
