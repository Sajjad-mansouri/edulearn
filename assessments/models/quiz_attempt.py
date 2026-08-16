from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from assessments.models import QuizContent
from enrollments.models import Enrollment


class QuizAttempt(models.Model):
    quiz = models.ForeignKey(
        QuizContent,
        on_delete=models.CASCADE,
        related_name="attempts",
        verbose_name=_("Quiz"),
    )

    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name="quiz_attempts",
        verbose_name=_("Enrollment"),
    )

    attempt_number = models.PositiveSmallIntegerField(
        _("Attempt Number"),
    )

    score = models.DecimalField(
        _("Score (%)"),
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text=_("Quiz score as a percentage (0-100)."),
    )

    started_at = models.DateTimeField(
        _("Started At"),
        auto_now_add=True,
    )

    submitted_at = models.DateTimeField(
        _("Submitted At"),
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ("-started_at",)

        constraints = [
            models.UniqueConstraint(
                fields=["quiz", "enrollment", "attempt_number"],
                name="unique_attempt_number_per_enrollment",
            )
        ]

        indexes = [
            models.Index(fields=["enrollment"]),
            models.Index(fields=["quiz"]),
        ]

        verbose_name = _("Quiz Attempt")
        verbose_name_plural = _("Quiz Attempts")

    def __str__(self):
        return f"{self.enrollment.user} - {self.quiz} (Attempt {self.attempt_number})"

    def clean(self):
        super().clean()

        if self.enrollment.course_id != self.quiz.content.lesson.section.course_id:
            raise ValidationError(
                {"enrollment": _("Enrollment must belong to the quiz course.")}
            )

        if self.score is not None and not 0 <= self.score <= 100:
            raise ValidationError({"score": _("Score must be between 0 and 100.")})

        if (
            self.submitted_at
            and self.started_at
            and self.submitted_at < self.started_at
        ):
            raise ValidationError(
                {"submitted_at": _("Submission time cannot be before the start time.")}
            )
