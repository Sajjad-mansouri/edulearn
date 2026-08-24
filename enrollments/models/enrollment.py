# Create your models here.
from datetime import timedelta

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from courses.models import Course
from curriculums.models import Lesson


class Enrollment(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", _("Active")
        COMPLETED = "completed", _("Completed")
        CANCELLED = "cancelled", _("Cancelled")
        SUSPENDED = "suspended", _("Suspended")
        PENDING = "pending", _("Pending")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="enrollments",
        verbose_name=_("User"),
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="enrollments",
        verbose_name=_("Course"),
    )

    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    enrolled_at = models.DateTimeField(
        _("Enrollment Date"),
        auto_now_add=True,
    )

    started_at = models.DateTimeField(
        _("Started at"),
        null=True,
        blank=True,
    )

    last_activity_at = models.DateTimeField(
        _("Last activity at"),
        null=True,
        blank=True,
        db_index=True,
    )
    completed_at = models.DateTimeField(
        _("Completion Date"),
        null=True,
        blank=True,
    )
    progress = models.DecimalField(
        _("Progress Percentage"),
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_("Overall completion percentage of the course (0-100)."),
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-enrolled_at",)

        constraints = [
            models.UniqueConstraint(
                fields=["user", "course"],
                name="unique_user_course_enrollment",
            )
        ]

        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["course"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.user} → {self.course}"

    @property
    def activity_status(self):
        if self.status == self.Status.COMPLETED:
            return "completed"

        if self.last_activity_at is None:
            return "not_started"

        delta = timezone.now() - self.last_activity_at

        if delta <= timedelta(days=7):
            return "active"

        if delta <= timedelta(days=30):
            return "idle"

        return "stale"

    def recalculate_progress(self):
        from .lesson_progress import LessonProgress

        """recalculate course progress from completed lessons."""
        lessons = Lesson.objects.filter(section__course=self.course)
        total = lessons.count()
        if total == 0:
            self.progress = 0
        else:
            completed = LessonProgress.objects.filter(
                enrollment=self, lesson__in=lessons, status="completed"
            ).count()
            self.progress = round((completed / total) * 100, 2)

        if self.progress >= 100 and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.progress < 100:
            self.completed_at = None

        self.save(update_fields=["progress", "completed_at"])
