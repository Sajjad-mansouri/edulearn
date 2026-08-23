from django.db import models

from .question import Question


class AcceptedAnswer(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="accepted_answers",
    )

    answer = models.CharField(
        max_length=255,
    )

    def __str__(self):
        return self.answer
