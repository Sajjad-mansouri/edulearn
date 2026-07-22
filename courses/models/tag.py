from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class Tag(models.Model):
    name = models.CharField(
        _("Name"),
        max_length=100,
    )

    slug = models.SlugField(
        _("Slug"),
        max_length=120,
        unique=True,
    )

    class Meta:
        ordering = ("name",)
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)
