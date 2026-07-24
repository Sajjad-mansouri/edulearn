from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from .lesson_content import LessonContent


class QuizContent(models.Model):
    content = models.OneToOneField(
        LessonContent,
        on_delete=models.CASCADE,
        related_name="quiz",
        verbose_name=_("Lesson Content"),
    )

    instructions = models.TextField(
        _("Instructions"),
        blank=True,
    )

    passing_score = models.PositiveSmallIntegerField(
        _("Passing Score (%)"),
        default=70,
        help_text=_("Required score (0-100) to pass."),
    )

    time_limit = models.PositiveIntegerField(
        _("Time Limit (minutes)"),
        null=True,
        blank=True,
        help_text=_("Leave empty for unlimited time."),
    )

    max_attempts = models.PositiveSmallIntegerField(
        _("Maximum Attempts"),
        default=1,
        help_text=_("Set to 0 for unlimited attempts."),
    )

    shuffle_questions = models.BooleanField(
        _("Shuffle Questions"),
        default=False,
    )

    shuffle_choices = models.BooleanField(
        _("Shuffle Choices"),
        default=False,
    )

    show_correct_answers = models.BooleanField(
        _("Show Correct Answers"),
        default=True,
    )

    class Meta:
        verbose_name = _("Quiz Content")
        verbose_name_plural = _("Quiz Contents")

    def __str__(self):
        return self.content.title

    def clean(self):
        super().clean()

        if self.passing_score > 100:
            raise ValidationError(
                {"passing_score": _("Passing score must be between 0 and 100.")}
            )


class Question(models.Model):
    class Type(models.TextChoices):
        SINGLE_CHOICE = "single_choice", _("Single Choice")
        MULTIPLE_CHOICE = "multiple_choice", _("Multiple Choice")
        TRUE_FALSE = "true_false", _("True / False")
        SHORT_ANSWER = "short_answer", _("Short Answer")

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

    order = models.PositiveSmallIntegerField()

    points = models.PositiveSmallIntegerField(default=1)

    explanation = models.TextField(blank=True)

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
        ]


class Choice(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="choices",
    )

    text = models.CharField(
        max_length=500,
    )

    is_correct = models.BooleanField(
        default=False,
    )

    order = models.PositiveSmallIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["question", "order"],
                name="unique_choice_order_per_question",
            )
        ]

        ordering = ("order",)


class AcceptedAnswer(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="accepted_answers",
    )

    answer = models.CharField(
        max_length=255,
    )
