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
        db_index=True,
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
            models.Index(fields=["enrollment", "status"]),
            models.Index(fields=["content", "status"]),
        ]

        verbose_name = _("Lesson Content Progress")
        verbose_name_plural = _("Lesson Content Progress")

    def __str__(self):
        return f"{self.enrollment.user} - {self.content.title}"

    def clean(self):
        super().clean()

        if (
            self.started_at
            and self.completed_at
            and self.completed_at < self.started_at
        ):
            raise ValidationError(
                {"completed_at": _("Completion time cannot be before the start time.")}
            )

        if self.status == self.Status.COMPLETED and self.completed_at is None:
            raise ValidationError(
                {"completed_at": _("Completed content must have a completion date.")}
            )

    def mark_started(self):
        """
        Mark content as started.
        """
        changed_fields = []

        if self.started_at is None:
            self.started_at = timezone.now()
            changed_fields.append("started_at")

        if self.status == self.Status.NOT_STARTED:
            self.status = self.Status.IN_PROGRESS
            changed_fields.append("status")

        if changed_fields:
            self.save(update_fields=changed_fields)

    def mark_completed(self):
        """
        Mark content as completed and trigger parent progress update.
        """
        now = timezone.now()

        update_fields = []

        if self.started_at is None:
            self.started_at = now
            update_fields.append("started_at")

        self.status = self.Status.COMPLETED
        update_fields.append("status")

        if self.completed_at is None:
            self.completed_at = now
            update_fields.append("completed_at")

        self.save(update_fields=update_fields)

        self.update_lesson_progress()

    def update_lesson_progress(self):
        """
        Recalculate parent lesson progress.
        """
        from .lesson_progress import LessonProgress

        lesson_progress = LessonProgress.objects.get(
            enrollment=self.enrollment,
            lesson=self.content.lesson,
        )

        lesson_progress.recalculate_progress()
