from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from .lesson_content import LessonContent


def file_upload_path(instance, filename, content_type):
    course = instance.content.lesson.section.course

    owner_id = course.owner_id
    course_id = course.id
    lesson_content_id = instance.content_id

    return (
        f"courses/"
        f"{owner_id}/"
        f"{course_id}/"
        f"lesson_contents/"
        f"{lesson_content_id}/"
        f"{content_type}/"
        f"{filename}"
    )


def video_upload_path(instance, filename):
    return file_upload_path(instance, filename, "videos")


def caption_upload_path(instance, filename):
    video_instance = instance.video
    return file_upload_path(video_instance, filename, "captions")


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

    video_file = models.FileField(upload_to=video_upload_path, blank=True, null=True)

    external_url = models.URLField(
        blank=True,
    )
    text = models.TextField(_("Text"), blank=True)

    duration = models.DurationField(
        null=True,
        blank=True,
    )

    transcript = models.TextField(
        blank=True,
    )

    def clean(self):
        super().clean()
        if self.source == self.Source.FILE and not self.video_file:
            raise ValidationError({"video_file": _("An video file is required.")})

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
        upload_to=caption_upload_path,
    )

    file_format = models.CharField(
        max_length=10,
        choices=Format.choices,
    )

    is_default = models.BooleanField(
        default=False,
    )

    def __str__(self):
        return f"{self.video} ({self.language})"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["video", "language"],
                name="unique_caption_language_per_video",
            ),
            models.UniqueConstraint(
                fields=["video"],
                condition=models.Q(is_default=True),
                name="unique_default_caption_per_video",
            ),
        ]
