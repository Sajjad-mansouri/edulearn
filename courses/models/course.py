from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from .category import Category
from .tag import Tag


class Course(models.Model):
    class Level(models.TextChoices):
        BEGINNER = "beginner", _("Beginner")
        INTERMEDIATE = "intermediate", _("Intermediate")
        ADVANCED = "advanced", _("Advanced")
        ALL_LEVELS = "all_levels", _("All Levels")

    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        READY_FOR_REVIEW = "ready_for_review", _("Ready for Review")
        UNDER_REVIEW = "under_review", _("Under Review")
        PUBLISHED = "published", _("Published")
        UPDATED = "updated", _("Updated")
        ARCHIVED = "archived", _("Archived")

    class Visibility(models.TextChoices):
        PUBLIC = "public", _("Public")
        PRIVATE = "private", _("Private")
        UNLISTED = "unlisted", _("Unlisted")

    title = models.CharField(
        _("Title"),
        max_length=255,
    )

    subtitle = models.CharField(
        _("Subtitle"),
        max_length=255,
        blank=True,
    )

    slug = models.SlugField(
        _("Slug"),
        max_length=280,
        unique=True,
    )

    description = models.TextField(
        _("Description"),
    )

    thumbnail = models.ImageField(
        _("Thumbnail"),
        upload_to="courses/thumbnails/",
        blank=True,
    )

    promotional_video = models.URLField(
        _("Promotional Video"),
        blank=True,
    )

    language = models.CharField(
        _("Language"),
        max_length=50,
        default="English",
    )

    level = models.CharField(
        _("Level"),
        max_length=20,
        choices=Level.choices,
        default=Level.ALL_LEVELS,
    )

    status = models.CharField(
        _("Status"),
        max_length=30,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    visibility = models.CharField(
        _("Visibility"),
        max_length=20,
        choices=Visibility.choices,
        default=Visibility.PUBLIC,
    )

    version = models.CharField(
        _("Version"),
        max_length=20,
        default="1.0.0",
    )

    published_at = models.DateTimeField(
        _("Published At"),
        null=True,
        blank=True,
    )

    last_updated = models.DateTimeField(
        _("Last Updated"),
        auto_now=True,
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_courses",
        verbose_name=_("Owner"),
    )

    collaborators = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="CourseCollaborator",
        related_name="teaching_courses",
        verbose_name=_("Collaborators"),
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="courses",
        verbose_name=_("Category"),
    )

    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name="courses",
        verbose_name=_("Tags"),
    )

    class Meta:
        ordering = (
            "-published_at",
            "title",
        )

        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["status"]),
            models.Index(fields=["category"]),
            models.Index(fields=["language"]),
            models.Index(fields=["published_at"]),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()

        if not self.title.strip():
            raise ValidationError(
                {
                    "title": _("Title is required."),
                }
            )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        self.full_clean()

        super().save(*args, **kwargs)


class LearningOutcome(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="learning_outcomes",
        verbose_name=_("Course"),
    )

    order = models.PositiveSmallIntegerField(
        _("Order"),
        default=1,
    )

    description = models.CharField(
        _("Description"),
        max_length=500,
    )

    class Meta:
        ordering = ("course", "order")
        constraints = [
            models.UniqueConstraint(
                fields=["course", "order"],
                name="unique_learning_outcome_order_per_course",
            )
        ]
        indexes = [
            models.Index(fields=["course", "order"]),
        ]

    def __str__(self):
        return f"{self.course.title} - {self.order}"


class Prerequisite(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="prerequisites",
        verbose_name=_("Course"),
    )

    order = models.PositiveSmallIntegerField(
        _("Order"),
        default=1,
    )

    description = models.CharField(
        _("Description"),
        max_length=500,
    )

    class Meta:
        ordering = ("course", "order")
        constraints = [
            models.UniqueConstraint(
                fields=["course", "order"],
                name="unique_prerequisite_order_per_course",
            )
        ]
        indexes = [
            models.Index(fields=["course", "order"]),
        ]

    def __str__(self):
        return f"{self.course.title} - {self.order}"


class TargetAudience(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="target_audiences",
        verbose_name=_("Course"),
    )

    description = models.CharField(
        _("Description"),
        max_length=500,
    )

    order = models.PositiveSmallIntegerField(
        _("Order"),
        default=1,
    )

    class Meta:
        ordering = ("course", "order")
        constraints = [
            models.UniqueConstraint(
                fields=["course", "order"],
                name="unique_target_audience_order_per_course",
            )
        ]
        indexes = [
            models.Index(fields=["course", "order"]),
        ]

    def __str__(self):
        return f"{self.course.title} - {self.order}"


class CourseCollaborator(models.Model):
    class Role(models.TextChoices):
        LEAD_INSTRUCTOR = "lead_instructor", _("Lead Instructor")
        INSTRUCTOR = "instructor", _("Instructor")
        TEACHING_ASSISTANT = "teaching_assistant", _("Teaching Assistant")

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="course_collaborators",
        verbose_name=_("Course"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="course_collaborations",
        verbose_name=_("User"),
    )

    role = models.CharField(
        _("Role"),
        max_length=25,
        choices=Role.choices,
        default=Role.INSTRUCTOR,
    )

    class Meta:
        ordering = (
            "course",
            "role",
            "user__username",
        )
        constraints = [
            models.UniqueConstraint(
                fields=("course", "user"),
                name="unique_course_collaborator",
            )
        ]

    def __str__(self):
        return f"{self.user} ({self.get_role_display()})"
