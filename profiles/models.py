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


class InstructorProfile(models.Model):
    profile = models.OneToOneField(
        Profile,
        on_delete=models.CASCADE,
        related_name="instructor_profile",
        verbose_name=_("Profile"),
    )

    professional_title = models.CharField(_("Professional Title"), max_length=255)
    organization = models.CharField(_("Organization"), max_length=255, blank=True)

    is_verified = models.BooleanField(_("Is Verified"), default=False)

    introduction_video = models.FileField(
        _("Introduction Video"),
        upload_to="instructors/introduction_videos/",
        blank=True,
    )

    years_of_experience = models.PositiveSmallIntegerField(
        _("Years of Experience"), default=0
    )

    class Meta:
        ordering = ["profile__user__username"]
        indexes = [
            models.Index(fields=["is_verified"]),
            models.Index(fields=["years_of_experience"]),
        ]

    def __str__(self):
        return f"{self.profile.user.username} - {self.professional_title}"


class StudentProfile(models.Model):
    profile = models.OneToOneField(
        Profile,
        on_delete=models.CASCADE,
        related_name="student_profile",
        verbose_name=_("Profile"),
    )

    learning_goal = models.CharField(
        max_length=255,
        blank=True,
        help_text="Student's primary learning objective.",
    )

    current_streak = models.PositiveIntegerField(_("Current Streak"), default=0)
    longest_streak = models.PositiveIntegerField(_("Longest Streak"), default=0)

    class Meta:
        ordering = ["profile__user__username"]

    def __str__(self):
        return f"{self.profile.user.username}'s Student Profile"
