from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
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


class Skill(models.Model):
    name = models.CharField(_("Name"), max_length=100)
    slug = models.SlugField(_("Slug"), unique=True, max_length=120)
    description = models.TextField(_("Description"), blank=True)

    profiles = models.ManyToManyField(
        Profile,
        related_name="skills",
        verbose_name=_("Profiles"),
        blank=True,
    )

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Education(models.Model):
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="education",
        verbose_name=_("Profile"),
    )

    institution = models.CharField(_("Institution"), max_length=255)
    degree = models.CharField(_("Degree"), max_length=255)
    field_of_study = models.CharField(_("Field Of Study"), max_length=255)

    start_year = models.PositiveSmallIntegerField(
        _("Start Year"), null=True, blank=True
    )
    end_year = models.PositiveSmallIntegerField(
        _("End Year"),
        null=True,
        blank=True,
        help_text="Leave blank if currently studying.",
    )

    class Meta:
        ordering = ["-start_year", "-end_year", "institution"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_year__isnull=True)
                | models.Q(end_year__gte=models.F("start_year")),
                name="education_end_year_gte_start_year",
            )
        ]

    def clean(self):
        super().clean()

        if (
            self.end_year is not None
            and self.start_year is not None
            and self.end_year < self.start_year
        ):
            raise ValidationError(
                {"end_year": ("End year must be greater than or equal to start year.")}
            )

    def __str__(self):
        return f"{self.degree} in {self.field_of_study} at {self.institution}"


class Experience(models.Model):
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="experiences",
        verbose_name=_("Profile"),
    )

    company = models.CharField(
        _("Company"),
        max_length=255,
    )

    position = models.CharField(
        _("Position"),
        max_length=255,
    )

    start_date = models.DateField(
        _("Start Date"),
    )

    end_date = models.DateField(
        _("End Date"),
        blank=True,
        null=True,
        help_text=_("Leave blank if this is the current position."),
    )

    is_current = models.BooleanField(
        _("Current Position"),
        default=False,
    )

    class Meta:
        ordering = ["-start_date", "-end_date", "company"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(end_date__isnull=True)
                    | models.Q(end_date__gte=models.F("start_date"))
                ),
                name="experience_end_date_gte_start_date",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(is_current=False) | models.Q(end_date__isnull=True)
                ),
                name="experience_current_requires_null_end_date",
            ),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError

        super().clean()

        if self.end_date is not None and self.end_date < self.start_date:
            raise ValidationError(
                {
                    "end_date": _(
                        "End date must be greater than or equal to the start date."
                    )
                }
            )

        if self.is_current and self.end_date is not None:
            raise ValidationError(
                {"end_date": _("Current positions cannot have an end date.")}
            )

    def __str__(self):
        return f"{self.position} at {self.company}"
