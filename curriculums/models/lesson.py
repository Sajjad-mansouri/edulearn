from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from .section import Section


class Lesson(models.Model):
    class CompletionCriteria(models.TextChoices):
        MANUAL = "manual", _("Manual")
        WATCH_VIDEO = "watch_video", _("Watch Video")
        READ_ARTICLE = "read_article", _("Read Article")
        PASS_QUIZ = "pass_quiz", _("Pass Quiz")
        SUBMIT_ASSIGNMENT = "submit_assignment", _("Submit Assignment")

    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name="lessons",
        verbose_name=_("Section"),
    )

    title = models.CharField(
        _("Title"),
        max_length=255,
    )

    description = models.TextField(_("Description"), blank=True)

    slug = models.SlugField(
        _("Slug"),
        max_length=280,
    )

    duration = models.DurationField(
        _("Duration"),
        null=True,
        blank=True,
        help_text=_("Estimated duration of this lesson."),
    )

    order = models.PositiveSmallIntegerField(
        _("Order"),
        default=1,
    )

    is_published = models.BooleanField(
        _("Published"),
        default=False,
    )

    is_preview = models.BooleanField(
        _("Preview Enabled"),
        default=False,
        help_text=_("Whether this lesson is accessible without enrollment."),
    )

    completion_criteria = models.CharField(
        _("Completion Criteria"),
        max_length=30,
        choices=CompletionCriteria.choices,
        default=CompletionCriteria.MANUAL,
    )

    class Meta:
        ordering = (
            "section",
            "order",
        )

        constraints = [
            models.UniqueConstraint(
                fields=["section", "order"],
                name="unique_lesson_order_per_section",
            )
        ]

        indexes = [
            models.Index(fields=["section"]),
            models.Index(fields=["is_published"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        super().save(*args, **kwargs)
