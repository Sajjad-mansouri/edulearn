from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from assessments.models import Assignment
from enrollments.models import Enrollment


def assignment_submission_upload_path(instance, filename):
    owner_id = instance.submission.enrollment.course.owner_id
    course_id = instance.submission.enrollment.course_id
    user_id = instance.submission.enrollment.user_id

    return (
        f"courses/"
        f"{owner_id}/"
        f"{course_id}/"
        f"lesson_contents/"
        f"{instance.submission.assignment.content_id}/"
        f"assignment_submission/"
        f"user_{user_id}"
        f"{filename}"
    )


class AssignmentSubmission(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        SUBMITTED = "submitted", _("Submitted")
        GRADED = "graded", _("Graded")
        RETURNED = "returned", _("Returned")
        LATE = "late", _("Late")

    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="submissions",
        verbose_name=_("Assignment"),
    )

    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name="assignment_submissions",
        verbose_name=_("Enrollment"),
    )

    attempt_number = models.PositiveSmallIntegerField(
        _("Attempt Number"),
    )

    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    submission_text = models.TextField(
        _("Submission Text"),
        blank=True,
        help_text=_("Optional written submission."),
    )

    score = models.DecimalField(
        _("Score"),
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )

    feedback = models.TextField(
        _("Feedback"),
        blank=True,
    )

    submitted_at = models.DateTimeField(
        _("Submitted At"),
        null=True,
        blank=True,
    )

    graded_at = models.DateTimeField(
        _("Graded At"),
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ("-submitted_at",)

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "assignment",
                    "enrollment",
                    "attempt_number",
                ],
                name="unique_assignment_attempt_per_enrollment",
            )
        ]

        indexes = [
            models.Index(fields=["assignment"]),
            models.Index(fields=["enrollment"]),
            models.Index(fields=["status"]),
        ]

        verbose_name = _("Assignment Submission")
        verbose_name_plural = _("Assignment Submissions")

    def __str__(self):
        return (
            f"{self.enrollment.user} - "
            f"{self.assignment} "
            f"(Attempt {self.attempt_number})"
        )

    def clean(self):
        super().clean()

        if (
            self.enrollment.course_id
            != self.assignment.content.lesson.section.course_id
        ):
            raise ValidationError(
                {"assignment": _("Assignment must belong to the enrollment course.")}
            )

        if self.score is not None and (
            self.score < 0 or self.score > self.assignment.max_score
        ):
            raise ValidationError(
                {
                    "score": _(
                        "Score must be between 0 and the assignment maximum score."
                    )
                }
            )

        if self.graded_at and self.submitted_at and self.graded_at < self.submitted_at:
            raise ValidationError(
                {"graded_at": _("Grading time cannot be before submission time.")}
            )

    def submit(self):
        """Mark the submission as submitted."""
        self.status = self.Status.SUBMITTED

        if self.submitted_at is None:
            self.submitted_at = timezone.now()

    def mark_graded(
        self,
        score,
        feedback="",
    ):
        """Mark the submission as graded."""
        self.score = score
        self.feedback = feedback
        self.status = self.Status.GRADED
        self.graded_at = timezone.now()

    def get_letter_grade(self):
        if self.score is not None:
            max_score = self.assignment.max_score
            if self.score >= Decimal("0.9") * max_score:
                return "A"
            elif self.score >= Decimal("0.8") * max_score:
                return "B"
            elif self.score >= Decimal("0.7") * max_score:
                return "C"
            else:
                return "D"
        else:
            return ""

    def save(self, *args, **kwargs):
        print(
            self.submitted_at,
            self.assignment.due_date,
            self.submitted_at > self.assignment.due_date,
        )
        if self.submitted_at > self.assignment.due_date:
            self.status = self.Status.LATE
        super().save(*args, **kwargs)


class AssignmentSubmissionFile(models.Model):
    submission = models.ForeignKey(
        AssignmentSubmission,
        on_delete=models.CASCADE,
        related_name="files",
        verbose_name=_("Submission"),
    )

    file = models.FileField(
        _("File"),
        upload_to=assignment_submission_upload_path,
        max_length=255,
    )

    original_filename = models.CharField(
        _("Original Filename"),
        max_length=255,
    )

    uploaded_at = models.DateTimeField(
        _("Uploaded At"),
        auto_now_add=True,
    )

    class Meta:
        ordering = ("uploaded_at",)

        indexes = [
            models.Index(fields=["submission"]),
        ]

        verbose_name = _("Assignment Submission File")
        verbose_name_plural = _("Assignment Submission Files")

    def __str__(self):
        return self.original_filename

    @property
    def file_name(self):
        return self.file.name.split("/")[-1]
