from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Profile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile", verbose_name=_("User")
    )
    avatar = models.ImageField(
        _("Avatar"),
        upload_to="avatars/",
        blank=True,
    )
    biography = models.TextField(_("Biography"), blank=True)
    headline = models.CharField(
        _("Headline"),
        max_length=255,
        blank=True,
        help_text="Short professional summary",
    )
    website = models.URLField(_("Website"), blank=True)

    country = models.CharField(_("Country"), max_length=100, blank=True)
    timezone = models.CharField(_("Timezone"), max_length=100, blank=True)
    language = models.CharField(_("Language"), max_length=20, blank=True)

    linkedin = models.URLField(_("Linkedin"), blank=True)
    github = models.URLField(_("Github"), blank=True)

    date_of_birth = models.DateField(
        _("Birthday"),
        blank=True,
        null=True,
    )

    company = models.CharField(_("Company"), max_length=255, blank=True)
    job_title = models.CharField(_("Job Title"), max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user"]

    def __str__(self):
        return f"{self.user.username}'s Profile"
