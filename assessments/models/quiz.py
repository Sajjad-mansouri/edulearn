from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from curriculums.models import LessonContent


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
