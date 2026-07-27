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

    video_file = models.FileField(
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


class VideoCaption(models.Model):
    class Format(models.TextChoices):
        VTT = "vtt", "WebVTT"
        SRT = "srt", "SubRip"

    video = models.ForeignKey(
        VideoContent,
        on_delete=models.CASCADE,
        related_name="captions",
    )

    language = models.CharField(
        max_length=10,
    )

    label = models.CharField(
        max_length=50,
        blank=True,
    )

    file = models.FileField(
        upload_to="courses/captions/",
    )

    file_format = models.CharField(
        max_length=10,
        choices=Format.choices,
    )

    is_default = models.BooleanField(
        default=False,
    )
