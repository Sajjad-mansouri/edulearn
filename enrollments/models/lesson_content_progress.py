from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from curriculums.models import LessonContent

from .enrollment import Enrollment


class LessonContentProgress(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = "not_started", _("Not Started")
        IN_PROGRESS = "in_progress", _("In Progress")
        COMPLETED = "completed", _("Completed")

    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name="content_progress",
        verbose_name=_("Enrollment"),
    )

    content = models.ForeignKey(
        LessonContent,
        on_delete=models.CASCADE,
        related_name="progress_records",
        verbose_name=_("Lesson Content"),
    )

    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.NOT_STARTED,
    )

    watch_percentage = models.PositiveSmallIntegerField(
        _("Watch Percentage"),
        default=0,
        help_text=_("Video watch progress (0-100). Ignored for non-video content."),
    )

    resume_position = models.DurationField(
        _("Resume Position"),
        null=True,
        blank=True,
        help_text=_("Playback position for video content."),
    )

    started_at = models.DateTimeField(
        _("Started At"),
        null=True,
        blank=True,
    )

    completed_at = models.DateTimeField(
        _("Completed At"),
        null=True,
        blank=True,
    )

    class Meta:
        ordering = (
            "enrollment",
            "content",
        )

        constraints = [
            models.UniqueConstraint(
                fields=["enrollment", "content"],
                name="unique_content_progress_per_enrollment",
            )
        ]

        indexes = [
            models.Index(fields=["enrollment"]),
            models.Index(fields=["content"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.enrollment.user} - {self.content.title}"

    def clean(self):
        super().clean()

        if not 0 <= self.watch_percentage <= 100:
            raise ValidationError(
                {"watch_percentage": _("Watch percentage must be between 0 and 100.")}
            )

        if (
            self.started_at
            and self.completed_at
            and self.completed_at < self.started_at
        ):
            raise ValidationError(
                {"completed_at": _("Completion time cannot be before the start time.")}
            )

    def mark_started(self):
        """Mark the content as started."""
        if self.started_at is None:
            self.started_at = timezone.now()

        if self.status == self.Status.NOT_STARTED:
            self.status = self.Status.IN_PROGRESS

    def mark_completed(self):
        """Mark the content as completed."""
        if self.started_at is None:
            self.started_at = timezone.now()

        self.status = self.Status.COMPLETED
        self.watch_percentage = 100
        self.completed_at = timezone.now()
