from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from courses.models import Course

from .enrollment import Enrollment


class CourseProgress(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = "not_started", _("Not Started")
        IN_PROGRESS = "in_progress", _("In Progress")
        COMPLETED = "completed", _("Completed")

    enrollment = models.OneToOneField(
        Enrollment,
        on_delete=models.CASCADE,
        related_name="course_progress",
        verbose_name=_("Enrollment"),
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="progress_records",
        verbose_name=_("Course"),
    )

    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.NOT_STARTED,
    )

    progress_percentage = models.PositiveSmallIntegerField(
        _("Progress Percentage"),
        default=0,
        help_text=_("Overall completion percentage of the course (0-100)."),
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
            "course",
            "enrollment",
        )

        indexes = [
            models.Index(fields=["course"]),
            models.Index(fields=["status"]),
        ]

        verbose_name = _("Course Progress")
        verbose_name_plural = _("Course Progress")

    def __str__(self):
        return f"{self.enrollment.user} - {self.course}"

    def clean(self):
        super().clean()

        if self.enrollment.course_id != self.course_id:
            raise ValidationError(
                {"course": _("Course must match the enrollment course.")}
            )

        if not 0 <= self.progress_percentage <= 100:
            raise ValidationError(
                {
                    "progress_percentage": _(
                        "Progress percentage must be between 0 and 100."
                    )
                }
            )

        if (
            self.started_at
            and self.completed_at
            and self.completed_at < self.started_at
        ):
            raise ValidationError(
                {"completed_at": _("Completion time cannot be before the start time.")}
            )
