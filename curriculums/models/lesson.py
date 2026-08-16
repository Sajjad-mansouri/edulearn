from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from .section import Section


class Lesson(models.Model):
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


class LessonCompletionCriteria(models.Model):
    """Stores specific criteria for completing a lesson."""

    class CriteriaType(models.TextChoices):
        MANUAL = "manual", _("Manual")
        WATCH_VIDEO = "watch_video", _("Watch Video")
        READ_ARTICLE = "read_article", _("Read Article")
        PASS_QUIZ = "pass_quiz", _("Pass Quiz")
        SUBMIT_ASSIGNMENT = "submit_assignment", _("Submit Assignment")

    lesson = models.OneToOneField(
        Lesson,
        on_delete=models.CASCADE,
        related_name="completion_criteria",
        verbose_name=_("Lesson"),
    )

    criteria_type = models.CharField(
        _("Criteria Type"),
        max_length=30,
        choices=CriteriaType.choices,
        default=CriteriaType.MANUAL,
    )

    # Criteria-specific fields (nullable, validated by clean())
    video_watch_percentage = models.PositiveSmallIntegerField(
        _("Video Watch Percentage"),
        null=True,
        blank=True,
        help_text=_("Required percentage of video to watch (1-100)."),
    )

    quiz_passing_score = models.PositiveSmallIntegerField(
        _("Quiz Passing Score"),
        null=True,
        blank=True,
        help_text=_("Minimum score to pass the quiz."),
    )

    # Note: For read_article, manual, and submit_assignment types,
    # no additional fields are needed as they're binary states

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Lesson Completion Criteria")
        verbose_name_plural = _("Lesson Completion Criteria")

    def __str__(self):
        return f"Completion criteria for {self.lesson.title}"

    def clean(self):
        """Validate that appropriate fields are set based on criteria_type."""
        super().clean()

        if self.criteria_type == self.CriteriaType.WATCH_VIDEO:
            if not self.video_watch_percentage:
                raise ValidationError(
                    {
                        "video_watch_percentage": _(
                            "Video watch percentage is required for video criteria."
                        )
                    }
                )
            if not 1 <= self.video_watch_percentage <= 100:
                raise ValidationError(
                    {
                        "video_watch_percentage": _(
                            "Video watch percentage must be between 1 and 100."
                        )
                    }
                )
            # Clear other fields
            self.quiz_passing_score = None

        elif self.criteria_type == self.CriteriaType.PASS_QUIZ:
            if not self.quiz_passing_score:
                raise ValidationError(
                    {
                        "quiz_passing_score": _(
                            "Quiz passing score is required for quiz criteria."
                        )
                    }
                )
            # Clear other fields
            self.video_watch_percentage = None

        else:
            # For manual, read_article, submit_assignment - clear specific fields
            self.video_watch_percentage = None
            self.quiz_passing_score = None

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
