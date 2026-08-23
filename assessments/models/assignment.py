from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from curriculums.models import LessonContent


class Assignment(models.Model):
    content = models.OneToOneField(
        LessonContent,
        on_delete=models.CASCADE,
        related_name="assignment",
        verbose_name=_("Lesson Content"),
    )

    instructions = models.TextField(_("Instructions"), blank=True)

    max_score = models.PositiveSmallIntegerField(
        _("Maximum Score"), default=100, null=True
    )

    due_date = models.DateTimeField(
        _("Due Date"),
        null=True,
        blank=True,
    )

    allow_late_submission = models.BooleanField(
        _("Allow Late Submission"),
        default=False,
    )

    max_attempts = models.PositiveSmallIntegerField(
        _("Maximum Attempts"),
        default=1,
        help_text=_("Set to 0 for unlimited attempts."),
    )

    accepted_file_types = models.CharField(
        _("Accepted File Types"),
        max_length=255,
        blank=True,
        help_text=_(
            "Comma-separated list (e.g. pdf,docx,zip). Leave blank to allow any."
        ),
    )

    max_file_size_mb = models.PositiveSmallIntegerField(
        _("Maximum File Size (MB)"),
        default=50,
    )

    class Meta:
        verbose_name = _("Assignment")
        verbose_name_plural = _("Assignments")

    def __str__(self):
        return self.content.title

    def clean(self):
        super().clean()

        if self.max_score < 1:
            raise ValidationError(
                {"max_score": _("Maximum score must be greater than zero.")}
            )

        if self.max_file_size_mb < 1:
            raise ValidationError(
                {"max_file_size_mb": _("Maximum file size must be greater than zero.")}
            )
