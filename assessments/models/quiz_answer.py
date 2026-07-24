from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from .choice import Choice
from .question import Question
from .quiz_attempt import QuizAttempt


class QuizAnswer(models.Model):
    attempt = models.ForeignKey(
        QuizAttempt,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name=_("Quiz Attempt"),
    )

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name=_("Question"),
    )

    selected_choices = models.ManyToManyField(
        Choice,
        blank=True,
        related_name="quiz_answers",
        verbose_name=_("Selected Choices"),
    )

    text_answer = models.TextField(
        _("Text Answer"),
        blank=True,
        help_text=_("Student's answer for short-answer questions."),
    )

    score_awarded = models.DecimalField(
        _("Score Awarded"),
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    class Meta:
        ordering = (
            "attempt",
            "question__order",
        )

        constraints = [
            models.UniqueConstraint(
                fields=["attempt", "question"],
                name="unique_question_answer_per_attempt",
            )
        ]

        indexes = [
            models.Index(fields=["attempt"]),
            models.Index(fields=["question"]),
        ]

        verbose_name = _("Quiz Answer")
        verbose_name_plural = _("Quiz Answers")

    def __str__(self):
        return f"{self.attempt} - Question {self.question.order}"

    def clean(self):
        super().clean()

        if self.question.quiz_id != self.attempt.quiz_id:
            raise ValidationError(
                {"question": _("Question must belong to the quiz being attempted.")}
            )

        if self.score_awarded < 0:
            raise ValidationError(
                {"score_awarded": _("Score awarded cannot be negative.")}
            )

        if self.score_awarded > self.question.points:
            raise ValidationError(
                {"score_awarded": _("Score awarded cannot exceed the question points.")}
            )
