from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login
from django.contrib.auth.forms import _unicode_ci_compare
from django.contrib.auth.tokens import default_token_generator
from django.contrib.gis.geoip2 import GeoIP2
from django.contrib.sites.shortcuts import get_current_site
from django.db import transaction
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.settings import api_settings
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from user_agents import parse

from accounts.models import LoginHistory, Role, UserSession
from profiles.models import Education, Experience, InstructorProfile, Profile, Skill

from ..tasks import send_email

User = get_user_model()


def send_registration_email(user, request, role_name):
    protocol = "https" if request.is_secure() else "http"
    current_site = get_current_site(request)
    user_pk_bytes = force_bytes(User._meta.pk.value_to_string(user))
    template_map = {
        "student": "student_register_confirm_email",
        "teacher": "instructor_register_confirm_email",
    }

    if role_name not in template_map:
        raise ValueError(f"Unsupported role: {role_name}")
    template_name = template_map[role_name]
    text_template = f"register/{template_name}.txt"
    html_template = f"register/{template_name}.html"

    context = {
        "email": user.email,
        "protocol": protocol,
        "domain": current_site.domain,
        "site_name": current_site.name,
        "uid": urlsafe_base64_encode(user_pk_bytes),
        "token": default_token_generator.make_token(user),
    }
    email_kwargs = {
        "recipient": user.email,
        "subject": "Verify your email address",
        "text_template": text_template,
        "html_template": html_template,
        "context": context,
    }
    if settings.HOST_ASYNC_ABILITY:
        send_email.delay(**email_kwargs)
    else:
        send_email(**email_kwargs)


def register_user(data, role_name, request):
    data.pop("password2")
    password = data.pop("password1")
    user = User.objects.create_user(password=password, is_active=False, **data)
    role, _ = Role.objects.get_or_create(name=role_name)
    role.users.add(user)
    send_registration_email(user=user, request=request, role_name=role_name)


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
    login(request, user)
    create_loging_history(request, user, True)
    create_user_session(request, user)

    data = {"access": str(refresh.access_token), "refresh": str(refresh)}

    return data


def logout_user(refresh_token: str) -> None:
    try:
        RefreshToken(refresh_token).blacklist()
    except TokenError as err:
        raise ValidationError({"refresh": "Invalid refresh token."}) from err


def get_users(email):
    """Given an email, return matching user(s) who should receive a reset.

    This allows subclasses to more easily customize the default policies
    that prevent inactive users and users with unusable passwords from
    resetting their password.
    """

    active_users = User._default_manager.filter(
        **{
            "email__iexact": email,
            "is_active": True,
        }
    )

    return (
        u
        for u in active_users
        if u.has_usable_password() and _unicode_ci_compare(email, u.email)
    )


def send_password_reset_email(request, email) -> None:
    """
    Generate a one-use only link for resetting password and send it to the
    user.
    """
    protocol = "https" if request.is_secure() else "http"
    current_site = get_current_site(request)
    for user in get_users(email):
        user_pk_bytes = force_bytes(User._meta.pk.value_to_string(user))
        context = {
            "email": user.email,
            "protocol": protocol,
            "domain": current_site.domain,
            "site_name": current_site.name,
            "uid": urlsafe_base64_encode(user_pk_bytes),
            "token": default_token_generator.make_token(user),
        }
        text_template = "register/password_reset_confirm_email.txt"
        html_template = "register/password_reset_confirm_email.html"
        email_kwargs = {
            "recipient": user.email,
            "subject": f"Password reset on {current_site.name}",
            "text_template": text_template,
            "html_template": html_template,
            "context": context,
        }
        if settings.HOST_ASYNC_ABILITY:
            send_email.delay(**email_kwargs)
        else:
            send_email(**email_kwargs)


@transaction.atomic
def register_instructor(
    request,
    educations_data,
    experiences_data,
    skills_data,
    user_data,
    profile_data,
    instructor_data,
):
    if request.user.is_authenticated:
        # Existing student → become / re-apply as instructor (same user)
        user = request.user
        profile = user.profile

        # Optional: block if already approved
        if hasattr(profile, "instructor_profile"):
            existing = profile.instructor_profile
            if existing.application_status == "approved":
                raise ValidationError("You are already an approved instructor.")
            elif existing.application_status == "pending":
                raise ValidationError(
                    "You are already registered. If approved, we will notify you."
                )
        # Update profile fields
        for attr, value in profile_data.items():
            setattr(profile, attr, value)
        profile.save()

        # Replace related objects
        profile.skills.all().delete()
        profile.educations.all().delete()
        profile.experiences.all().delete()

    else:
        # Brand new user
        user = User.objects.create_user(is_active=False, **user_data)
        profile = Profile.objects.create(user=user, **profile_data)

    # Create skills, educations, experiences
    for skill_data in skills_data:
        Skill.objects.create(profile=profile, **skill_data)

    for education_data in educations_data:
        Education.objects.create(profile=profile, **education_data)

    for experience_data in experiences_data:
        Experience.objects.create(profile=profile, **experience_data)

    # Create or update InstructorProfile
    instructor_profile, created = InstructorProfile.objects.update_or_create(
        profile=profile,
        defaults={
            **instructor_data,
            "application_status": "pending",
            "is_verified": False,
            "rejection_reason": "",
        },
    )

    return profile, instructor_profile, created
