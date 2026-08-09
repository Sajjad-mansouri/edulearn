from django.db import models
from django.utils.translation import gettext_lazy as _

from .lesson import Lesson


class LessonContent(models.Model):
    class Type(models.TextChoices):
        VIDEO = "video", _("Video")
        ARTICLE = "article", _("Article")
        FILE = "file", _("File")
        QUIZ = "quiz", _("Quiz")
        ASSIGNMENT = "assignment", _("Assignment")
        LIVE_SESSION = "live_session", _("Live Session")
        CODING_EXERCISE = "coding_exercise", _("Coding Exercise")

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="contents",
        verbose_name=_("Lesson"),
    )
    is_main_content = models.BooleanField(default=False)

    title = models.CharField(
        _("Title"),
        max_length=255,
    )

    content_type = models.CharField(
        _("Content Type"),
        max_length=30,
        choices=Type.choices,
    )

    order = models.PositiveSmallIntegerField(
        _("Order"),
    )

    class Meta:
        ordering = ("lesson", "order")

        constraints = [
            models.UniqueConstraint(
                fields=["lesson", "order"],
                name="unique_content_order_per_lesson",
            ),
            models.UniqueConstraint(
                fields=["lesson"],
                condition=models.Q(is_main_content=True),
                name="unique_main_content_per_lesson",
            ),
        ]

    def __str__(self):
        if self.title:
            return self.title
        else:
            return f"{self.lesson.title} content"
