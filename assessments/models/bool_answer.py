from django.db import models

from .question import Question


class BooleanAnswer(models.Model):
    question = models.OneToOneField(
        Question,
        on_delete=models.CASCADE,
        related_name="boolean_answers",
    )

    answer = models.BooleanField(default=False)

    def __str__(self):
        if self.answer:
            return "True"
        else:
            return "False"
