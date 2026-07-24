# Create your models here.
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from courses.models import Course


class Enrollment(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", _("Active")
        COMPLETED = "completed", _("Completed")
        CANCELLED = "cancelled", _("Cancelled")
        SUSPENDED = "suspended", _("Suspended")

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
        default=Status.ACTIVE,
    )

    enrolled_at = models.DateTimeField(
        _("Enrollment Date"),
        auto_now_add=True,
    )

    completed_at = models.DateTimeField(
        _("Completion Date"),
        null=True,
        blank=True,
    )

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
