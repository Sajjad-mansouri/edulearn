from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.gis.geoip2 import GeoIP2
from django.contrib.sites.shortcuts import get_current_site
from django.db import transaction
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken
from user_agents import parse

from accounts.models import LoginHistory, Role, UserSession
from accounts.tasks import send_verification_email
from profiles.models import Profile

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


def get_ident(request):
    """
    Identify the machine making the request by parsing HTTP_X_FORWARDED_FOR
    if present and number of proxies is > 0. If not use all of
    HTTP_X_FORWARDED_FOR if it is available, if not use REMOTE_ADDR.
    """
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    remote_addr = request.META.get("REMOTE_ADDR")
    num_proxies = api_settings.NUM_PROXIES

    if num_proxies is not None:
        if num_proxies == 0 or xff is None:
            return remote_addr
        addrs = xff.split(",")
        client_addr = addrs[-min(num_proxies, len(addrs))]
        return client_addr.strip()

    return "".join(xff.split()) if xff else remote_addr


def get_client_device(request):
    ua_string = request.META.get("HTTP_USER_AGENT", "")
    ua = parse(ua_string)
    return ua.os.family


def get_location(client_ip_address):
    g = GeoIP2()
    try:
        return g.country(client_ip_address)
    except Exception:
        return ""


def create_loging_history(request, user, is_successful):
    client_ip_address = get_ident(request)
    client_location = get_location(client_ip_address)
    LoginHistory.objects.create(
        user=user,
        ip_address=client_ip_address,
        location=client_location,
        is_successful=is_successful,
    )


def create_user_session(request, user):
    client_ip_address = get_ident(request)
    client_device = get_client_device(request)

    UserSession.objects.create(
        user=user,
        ip_address=client_ip_address,
        device=client_device,
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
    )


@transaction.atomic
def perform_login(validated_data, request) -> dict:
    username = validated_data["username"]
    password = validated_data["password"]

    user = authenticate(request=request, username=username, password=password)
    if user is None:
        try:
            user = User.objects.get(username=username)
            create_loging_history(request, user, False)
        except User.DoesNotExist:
            pass

        raise AuthenticationFailed("Invalid username or password.")

    refresh = RefreshToken.for_user(user)
    create_loging_history(request, user, True)
    create_user_session(request, user)

    data = {"access": str(refresh.access_token), "refresh": str(refresh)}

    return data
