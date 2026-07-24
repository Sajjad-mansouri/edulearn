from django.db import models
from django.utils.translation import gettext_lazy as _

from enrollments.models import Enrollment


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
        upload_to="certificates/",
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
