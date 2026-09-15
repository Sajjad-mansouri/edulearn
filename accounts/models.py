from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    email = models.EmailField(_("Email Address"), unique=True)

    REQUIRED_FIELDS = ["email"]
    email_verified = models.BooleanField(_("Email verified"), default=False)

    class Meta(AbstractUser.Meta):
        indexes = [models.Index(fields=["username"])]

    @property
    def avatar(self):
        profile = getattr(self, "profile", None)
        if profile and profile.avatar:
            return profile.avatar.url
        return None


class Role(models.Model):
    class Roles(models.TextChoices):
        STUDENT = "student", _("Student")
        INSTRUCTOR = "instructor", _("Instructor")
        # if needed add more

    users = models.ManyToManyField(User, related_name="roles", verbose_name=_("Users"))
    name = models.CharField(_("Name"), choices=Roles, max_length=18)
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


class LoginHistory(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="login_history",
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    is_successful = models.BooleanField()
    ip_address = models.GenericIPAddressField()
    device = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["timestamp"]),
        ]

    def __str__(self):
        status = "Success" if self.is_successful else "Failed"
        return f"{self.user} - {status} ({self.timestamp:%Y-%m-%d %H:%M:%S})"
