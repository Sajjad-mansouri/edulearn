from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from curriculums.models import Lesson, LessonContent

from .enrollment import Enrollment
from .lesson_content_progress import LessonContentProgress


class LessonProgress(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = "not_started", _("Not Started")
        IN_PROGRESS = "in_progress", _("In Progress")
        COMPLETED = "completed", _("Completed")

    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name="lesson_progress",
        verbose_name=_("Enrollment"),
    )

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="progress_records",
        verbose_name=_("Lesson"),
    )

    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.NOT_STARTED,
    )

    progress = models.DecimalField(
        _("Progress Percentage"),
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_("Overall completion percentage of the lesson (0-100)."),
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
            "lesson",
        )

        constraints = [
            models.UniqueConstraint(
                fields=["enrollment", "lesson"],
                name="unique_lesson_progress_per_enrollment",
            )
        ]

        indexes = [
            models.Index(fields=["enrollment"]),
            models.Index(fields=["lesson"]),
            models.Index(fields=["status"]),
        ]

        verbose_name = _("Lesson Progress")
        verbose_name_plural = _("Lesson Progress")

    def __str__(self):
        return f"{self.enrollment.user} - {self.lesson}"

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

    def mark_completed(self):
        """
        Mark Lesson as completed and trigger parent progress update.
        """
        now = timezone.now()

        update_fields = []

        if self.started_at is None:
            self.started_at = now
            update_fields.append("started_at")

        self.status = self.Status.COMPLETED
        self.progress = Decimal("100.00")

        update_fields.extend(["status", "progress"])

        if self.completed_at is None:
            self.completed_at = now
            update_fields.append("completed_at")

        self.save(update_fields=update_fields)

        self.enrollment.recalculate_progress()

    def recalculate_progress(self):
        """recalculate lesson progress from completed lessons."""
        lesson_contents = LessonContent.objects.filter(lesson=self.lesson).values_list(
            "pk", flat=True
        )
        total = lesson_contents.count()
        if total == 0:
            self.progress = 0
        else:
            completed = LessonContentProgress.objects.filter(
                enrollment=self.enrollment,
                content__in=lesson_contents,
                status=self.Status.COMPLETED,
            ).count()
            self.progress = (Decimal(completed) * Decimal("100")) / Decimal(total)

        if self.progress < Decimal("100"):
            self.status = self.Status.IN_PROGRESS

            if self.started_at is None:
                self.started_at = timezone.now()

            self.completed_at = None

        else:
            self.status = self.Status.COMPLETED

            if self.started_at is None:
                self.started_at = timezone.now()

            if self.completed_at is None:
                self.completed_at = timezone.now()
        self.save(update_fields=["progress", "completed_at", "status", "started_at"])
        self.enrollment.recalculate_progress()
