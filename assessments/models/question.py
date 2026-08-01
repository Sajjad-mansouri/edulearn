from django.db import models
from django.utils.translation import gettext_lazy as _

from .quiz import QuizContent


class Question(models.Model):
    class Type(models.TextChoices):
        SINGLE_CHOICE = "single_choice", _("Single Choice")
        MULTIPLE_CHOICE = "multiple_choice", _("Multiple Choice")
        TRUE_FALSE = "true_false", _("True / False")
        SHORT_ANSWER = "short_answer", _("Short Answer")

    class Difficulty(models.TextChoices):
        EASY = "easy", _("Easy")
        MEDIUM = "medium", _("Medium")
        HARD = "hard", _("Hard")

    quiz = models.ForeignKey(
        QuizContent,
        on_delete=models.CASCADE,
        related_name="questions",
    )

    text = models.TextField()

    question_type = models.CharField(
        max_length=30,
        choices=Type.choices,
        default=Type.SINGLE_CHOICE,
    )

    difficulty = models.CharField(
        _("Difficulty"),
        max_length=10,
        choices=Difficulty.choices,
        default=Difficulty.MEDIUM,
        help_text=_("Difficulty level of the question."),
    )

    order = models.PositiveSmallIntegerField()

    points = models.PositiveSmallIntegerField(
        default=1,
    )

    explanation = models.TextField(
        blank=True,
    )

    is_required = models.BooleanField(default=True)
    estimated_time = models.DurationField(
        null=True,
        blank=True,
        help_text=_("Estimated time to answer."),
    )

    def __str__(self):
        return self.text

    class Meta:
        ordering = ("order",)

        constraints = [
            models.UniqueConstraint(
                fields=["quiz", "order"],
                name="unique_question_order_per_quiz",
            )
        ]

        indexes = [
            models.Index(fields=["quiz"]),
            models.Index(fields=["order"]),
            models.Index(fields=["difficulty"]),
        ]
