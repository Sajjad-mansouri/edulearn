import uuid
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

User = get_user_model()


def profile_image_upload_to(instance, filename):
    extension = Path(filename).suffix.lower()
    filename = f"{uuid.uuid4()}{extension}"

    return f"profiles/{instance.image_directory}/{instance.user_id}/{filename}"


class Profile(models.Model):
    image_directory = "avatar"
    avatar = models.ImageField(
        _("Avatar"),
        upload_to=profile_image_upload_to,
        blank=True,
    )
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile", verbose_name=_("User")
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

    def get_avatar(self):
        return self.avatar.url if self.avatar else ""


class AbstractRoledProfile(models.Model):
    cover = models.ImageField(
        _("Cover"),
        upload_to=profile_image_upload_to,
        blank=True,
    )

    headline = models.CharField(
        _("Headline"),
        max_length=255,
        blank=True,
        help_text="Short professional summary",
    )

    biography = models.TextField(_("Instructor Biography"), blank=True)

    class Meta:
        abstract = True


class InstructorProfile(AbstractRoledProfile):
    image_directory = "instructors/cover"
    profile = models.OneToOneField(
        Profile, on_delete=models.CASCADE, related_name="instructor_profile"
    )
    professional_title = models.CharField(_("Professional Title"), max_length=255)
    organization = models.CharField(_("Organization"), max_length=255, blank=True)

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("pending", "Pending Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]
    application_status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )

    is_verified = models.BooleanField(default=False)
    verification_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    introduction_video = models.FileField(upload_to="instructors/videos/", blank=True)
    resume = models.FileField(upload_to="instructors/resumes/", blank=True)

    years_of_experience = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["profile__user__username"]
        indexes = [
            models.Index(fields=["is_verified"]),
            models.Index(fields=["years_of_experience"]),
        ]

    def __str__(self):
        return f"{self.profile.user.username} - {self.professional_title}"


class StudentProfile(AbstractRoledProfile):
    image_directory = "students/cover"
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

    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="skills",
        verbose_name=_("Profile"),
    )

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name", "profile"]),
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
        related_name="educations",
        verbose_name=_("Profile"),
    )

    institution = models.CharField(_("Institution"), max_length=255)
    degree = models.CharField(_("Degree"), max_length=255)
    field_of_study = models.CharField(_("Field Of Study"), max_length=255)
    description = models.TextField(_("Description"), blank=True)

    start_date = models.DateField(_("Start Date"), blank=True, null=True)
    end_date = models.DateField(
        _("End Year"),
        null=True,
        blank=True,
        help_text="Leave blank if currently studying.",
    )

    class Meta:
        ordering = ["-start_date", "-end_date", "institution"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_date__isnull=True)
                | models.Q(end_date__gte=models.F("start_date")),
                name="education_end_date_gte_start_date",
            )
        ]

    def clean(self):
        super().clean()

        if (
            self.end_date is not None
            and self.start_date is not None
            and self.end_date < self.start_date
        ):
            raise ValidationError(
                {"end_date": ("End date must be greater than or equal to start date.")}
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
    location = models.CharField(_("Location"), max_length=250, blank=True)
    description = models.TextField(_("Description"), blank=True)

    start_date = models.DateField(_("Start Date"), blank=True, null=True)

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


class SocialLink(models.Model):
    class Platform(models.TextChoices):
        TELEGRAM = "telegram", _("Telegram")
        INSTAGRAM = "instagram", _("Instagram")
        TWITTER = "twitter", _("Twitter")
        LINKEDIN = "linkedin", _("LinkedIn")
        YOUTUBE = "youtube", _("YouTube")
        GITHUB = "github", _("GitHub")
        FACEBOOK = "facebook", _("Facebook")
        EMAIL = "email", _("Email")

    class Visibility(models.TextChoices):
        PUBLIC = "public", _("Public")
        PRIVATE = "private", _("Private")

    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="social_links",
        verbose_name=_("Profile"),
    )

    platform = models.CharField(
        _("Platform"),
        max_length=20,
        choices=Platform.choices,
    )

    address = models.URLField(
        _("Address"),
    )

    visibility = models.CharField(
        _("Visibility"),
        max_length=20,
        choices=Visibility.choices,
        default=Visibility.PUBLIC,
    )

    display_order = models.PositiveSmallIntegerField(
        _("Display Order"),
        default=0,
    )

    class Meta:
        ordering = ["display_order", "platform"]

    def __str__(self):
        return f"{self.platform} ({self.profile.user.username})"


class Language(models.Model):
    PROFICIENCIES = [
        ("Native", "Native"),
        ("C2", "Proficient"),
        ("C1", "Advanced"),
        ("B2", "Upper Intermediate"),
        ("B1", "Intermediate"),
        ("A2", "Elementary"),
        ("A1", "Beginner"),
    ]
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="languages",
        verbose_name=_("Profile"),
    )
    language = models.TextField(_("Language"), max_length=250)
    proficiency = models.CharField(
        _("Proficiency"), choices=PROFICIENCIES, max_length=6
    )
