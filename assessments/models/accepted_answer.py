from django.db import models

from .question import Question


class AcceptedAnswer(models.Model):
    question = models.OneToOneField(
        Question,
        on_delete=models.CASCADE,
        related_name="accepted_answer",
    )

    answer = models.CharField(
        max_length=255,
    )

    def __str__(self):
        return self.answer
