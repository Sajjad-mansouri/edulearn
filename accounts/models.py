from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    email = models.EmailField(_("Email Address"), blank=True, unique=True)

    REQUIRED_FIELDS = ["email"]
    email_verified = models.BooleanField(_("Email verified"), default=False)

    class Meta(AbstractUser.Meta):
        indexes = [models.Index(fields=["username"])]
