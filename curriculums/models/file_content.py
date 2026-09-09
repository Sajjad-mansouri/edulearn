from django.db import models
from django.utils.translation import gettext_lazy as _

from .lesson_content import LessonContent


def file_upload_path(instance, filename):
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
        f"file/"
        f"{filename}"
    )


class FileContent(models.Model):
    content = models.OneToOneField(
        LessonContent,
        on_delete=models.CASCADE,
        related_name="file",
        verbose_name=_("Lesson Content"),
    )

    file = models.FileField(
        _("File"), upload_to=file_upload_path, null=True, blank=True
    )
    file_url = models.URLField(
        blank=True,
    )

    display_name = models.CharField(
        _("Display Name"),
        max_length=255,
        blank=True,
        help_text=_("Optional name shown to learners instead of the filename."),
    )

    description = models.TextField(
        _("Description"),
        blank=True,
    )

    is_downloadable = models.BooleanField(
        _("Downloadable"),
        default=True,
    )

    file_size = models.PositiveBigIntegerField(
        _("File Size (bytes)"),
        null=True,
        blank=True,
        editable=False,
    )

    class Meta:
        verbose_name = _("File Content")
        verbose_name_plural = _("File Contents")

    def __str__(self):
        return self.display_name or self.content.title

    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size

        super().save(*args, **kwargs)
