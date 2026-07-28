from pathlib import Path

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from courses.models import Course

from .lesson_content import LessonContent


def attachment_upload_path(instance, filename):
    """
    Upload path examples:

    Course attachment:
    courses/15/42/attachments/syllabus.pdf

    Lesson attachment:
    courses/15/42/lesson_contents/18/attachments/example.zip
    """
    owner_id = instance.course.owner_id
    course_id = instance.course_id

    if instance.lesson_content_id:
        return (
            f"courses/"
            f"{owner_id}/"
            f"{course_id}/"
            f"lesson_contents/"
            f"{instance.lesson_content_id}/"
            f"attachments/"
            f"{filename}"
        )

    return f"courses/{owner_id}/{course_id}/attachments/{filename}"


class Attachment(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="attachments",
        verbose_name=_("Course"),
    )

    lesson_content = models.ForeignKey(
        LessonContent,
        on_delete=models.CASCADE,
        related_name="attachments",
        null=True,
        blank=True,
        verbose_name=_("Lesson Content"),
        help_text=_("Leave empty if this is a course-level attachment."),
    )

    file = models.FileField(
        _("File"),
        upload_to=attachment_upload_path,
        blank=True,
    )

    file_url = models.URLField(
        _("External URL"),
        blank=True,
    )

    title = models.CharField(
        _("Title"),
        max_length=255,
        help_text=_("Name displayed to learners."),
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

    created_at = models.DateTimeField(
        _("Created At"),
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        _("Updated At"),
        auto_now=True,
    )

    class Meta:
        ordering = (
            "title",
            "created_at",
        )

        indexes = [
            models.Index(fields=["course"]),
            models.Index(fields=["lesson_content"]),
            models.Index(fields=["is_downloadable"]),
        ]

        constraints = [
            models.CheckConstraint(
                condition=(
                    (Q(file__gt="") & Q(file_url=""))
                    | (Q(file="") & Q(file_url__gt=""))
                ),
                name="attachment_exactly_one_source",
            )
        ]

        verbose_name = _("Attachment")
        verbose_name_plural = _("Attachments")

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()

        if (
            self.lesson_content
            and self.lesson_content.lesson.section.course_id != self.course_id
        ):
            raise ValidationError(
                {
                    "lesson_content": _(
                        "Lesson content must belong to the selected course."
                    )
                }
            )

    def save(self, *args, **kwargs):
        self.full_clean()

        if self.file:
            self.file_size = self.file.size

        super().save(*args, **kwargs)

    @property
    def filename(self):
        if not self.file:
            return ""

        return Path(self.file.name).name
