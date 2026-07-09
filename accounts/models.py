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
