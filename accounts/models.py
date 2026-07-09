from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    email = models.EmailField(_("Email Address"), blank=True, unique=True)

    REQUIRED_FIELDS = ["email"]
    email_verified = models.BooleanField(_("Email verified"), default=False)

    class Meta(AbstractUser.Meta):
        indexes = [models.Index(fields=["username"])]


class Role(models.Model):
    ROLE_CHOICES = [
        ("guest", "Guest"),
        ("student", "Student"),
        ("instructor", "Instructor"),
        ("teaching assistant", "Teaching Assistant"),
        ("moderator", "Moderator"),
        ("support agent", "Support Agent"),
        ("admin", "Admin"),
    ]
    user = models.ManyToManyField(User, related_name="roles", verbose_name=_("User"))
    name = models.CharField(_("Name"), choices=ROLE_CHOICES, max_length=18)
    description = models.TextField(_("Description"))

    def __str__(self):
        return f"{self.get_name_display()}"


class UserSession(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sessions", verbose_name=_("User")
    )
    device = models.CharField(_("Device"), max_length=255)
    ip_address = models.GenericIPAddressField(_("IP Address"))
    user_agent = models.TextField(_("User Agent"))

    login_at = models.DateTimeField(auto_now_add=True)
    last_activity_at = models.DateTimeField(auto_now=True)

    is_revoked = models.BooleanField(_("Is Revoked"), default=False)

    class Meta:
        ordering = ["-login_at"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["last_activity_at"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.device}"
