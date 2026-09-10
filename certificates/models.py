from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from courses.models import Course
from enrollments.models import Enrollment


def file_upload_path(instance, filename):
    user_id = instance.enrollment.user_id
    course_id = instance.enrollment.course_id

    return f"certificates/{user_id}/{course_id}/{filename}"


class Certificate(models.Model):
    enrollment = models.OneToOneField(
        Enrollment,
        on_delete=models.CASCADE,
        related_name="certificate",
        verbose_name=_("Enrollment"),
    )

    certificate_number = models.CharField(
        _("Certificate Number"),
        max_length=100,
        unique=True,
    )

    verification_code = models.CharField(
        _("Verification Code"),
        max_length=64,
        unique=True,
    )

    issued_at = models.DateTimeField(
        _("Issued At"),
        auto_now_add=True,
    )

    file = models.FileField(
        _("Certificate File"),
        upload_to=file_upload_path,
    )

    class Meta:
        ordering = ("-issued_at",)

        indexes = [
            models.Index(fields=["verification_code"]),
        ]

        verbose_name = _("Certificate")
        verbose_name_plural = _("Certificates")

    def __str__(self):
        return f"{self.enrollment.user} - {self.enrollment.course}"


class CertificateTemplate(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="certificate_templates",
        null=True,
        blank=True,
    )
    name = models.CharField(
        _("Name"),
        max_length=100,
    )

    version = models.PositiveSmallIntegerField(
        _("Version"),
        default=1,
    )

    background = models.FileField(
        _("Background"),
        upload_to="certificates/templates/",
        help_text=_("Certificate background (PDF or image)."),
    )

    is_active = models.BooleanField(
        _("Active"),
        default=False,
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
            "-is_active",
            "name",
            "-version",
        )

        constraints = [
            models.UniqueConstraint(
                fields=["name", "version"],
                name="unique_certificate_template_version",
            )
        ]

        indexes = [
            models.Index(fields=["is_active"]),
        ]

        verbose_name = _("Certificate Template")
        verbose_name_plural = _("Certificate Templates")

    def __str__(self):
        return f"{self.name} v{self.version}"

    def clean(self):
        super().clean()

        if self.is_active:
            qs = CertificateTemplate.objects.filter(
                is_active=True,
            )

            if self.pk:
                qs = qs.exclude(pk=self.pk)

            if qs.exists():
                raise ValidationError(
                    {"is_active": _("Only one certificate template can be active.")}
                )
