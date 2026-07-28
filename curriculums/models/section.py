from django.db import models
from django.utils.translation import gettext_lazy as _

from courses.models import Course


class Section(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="sections",
        verbose_name=_("Course"),
    )

    title = models.CharField(
        _("Title"),
        max_length=255,
    )

    description = models.TextField(
        _("Description"),
        blank=True,
    )

    order = models.PositiveSmallIntegerField(
        _("Order"),
        default=1,
    )

    is_published = models.BooleanField(
        _("Published"),
        default=False,
    )
    duration = models.DurationField(
        _("Estimated Duration"),
        null=True,
        blank=True,
        help_text=_("Estimated time to complete this section."),
    )

    class Meta:
        ordering = (
            "course",
            "order",
        )
        constraints = [
            models.UniqueConstraint(
                fields=["course", "order"],
                name="unique_section_order_per_course",
            )
        ]
        indexes = [
            models.Index(fields=["course"]),
            models.Index(fields=["order"]),
            models.Index(fields=["course", "order"]),
        ]

    def __str__(self):
        return self.title
