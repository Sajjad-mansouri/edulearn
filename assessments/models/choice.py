from django.db import models

from .question import Question


class Choice(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="choices",
    )

    text = models.CharField(
        max_length=500,
    )

    is_correct = models.BooleanField(
        default=False,
    )

    order = models.PositiveSmallIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["question", "order"],
                name="unique_choice_order_per_question",
            )
        ]

        ordering = ("order",)

    def __str__(self):
        return self.text
