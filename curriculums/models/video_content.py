from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from .lesson_content import LessonContent


class VideoContent(models.Model):
    class Source(models.TextChoices):
        FILE = "file", _("Uploaded File")
        URL = "url", _("External URL")

    content = models.OneToOneField(
        LessonContent,
        on_delete=models.CASCADE,
        related_name="video",
    )

    source = models.CharField(
        max_length=20,
        choices=Source.choices,
        default=Source.FILE,
    )

    uploaded_video = models.FileField(
        upload_to="courses/videos/",
        blank=True,
    )

    external_url = models.URLField(
        blank=True,
    )

    duration = models.DurationField(
        null=True,
        blank=True,
    )

    transcript = models.TextField(
        blank=True,
    )

    captions = models.FileField(
        upload_to="courses/captions/",
        blank=True,
    )

    def clean(self):
        if self.source == self.Source.FILE and not self.uploaded_video:
            raise ValidationError(
                {"uploaded_video": _("An uploaded video is required.")}
            )

        if self.source != self.Source.FILE and not self.external_url:
            raise ValidationError({"external_url": _("A video URL is required.")})

    class Meta:
        verbose_name = _("Video Content")
        verbose_name_plural = _("Video Contents")

    def __str__(self):
        return self.content.title
