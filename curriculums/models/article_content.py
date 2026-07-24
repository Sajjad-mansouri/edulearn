from django.db import models
from django.utils.translation import gettext_lazy as _

from .lesson_content import LessonContent


class ArticleContent(models.Model):
    content = models.OneToOneField(
        LessonContent,
        on_delete=models.CASCADE,
        related_name="article",
        verbose_name=_("Lesson Content"),
    )

    body = models.TextField(
        _("Body"),
        help_text=_("The article content in Markdown or HTML format."),
    )

    estimated_read_time = models.PositiveSmallIntegerField(
        _("Estimated Read Time"),
        null=True,
        blank=True,
        help_text=_("Estimated reading time in minutes."),
    )

    class Meta:
        verbose_name = _("Article Content")
        verbose_name_plural = _("Article Contents")

    def __str__(self):
        return self.content.title
