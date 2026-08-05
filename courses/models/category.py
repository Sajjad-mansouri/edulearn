from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="children",
        null=True,
        blank=True,
        verbose_name=_("Parent Category"),
        help_text=_("Leave empty for a top-level category."),
    )

    name = models.CharField(
        _("Name"),
        max_length=150,
    )

    slug = models.SlugField(
        _("Slug"),
        unique=True,
        max_length=170,
    )

    description = models.TextField(
        _("Description"),
        blank=True,
    )

    display_order = models.PositiveIntegerField(
        _("Display Order"),
        default=0,
    )

    is_active = models.BooleanField(
        _("Active"),
        default=True,
    )
    icon = models.CharField(_("Icon"), max_length=100, blank=True)

    class Meta:
        ordering = ("display_order", "name")
        indexes = [
            models.Index(fields=["display_order"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)
