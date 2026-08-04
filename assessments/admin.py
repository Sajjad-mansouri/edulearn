# Register your models here.
from django.contrib import admin

from assessments.models import (
    AcceptedAnswer,
    Assignment,
    AssignmentSubmission,
    AssignmentSubmissionFile,
    BooleanAnswer,
    Choice,
    Question,
    QuizContent,
)

admin.site.register(QuizContent)
admin.site.register(Question)
admin.site.register(Choice)
admin.site.register(AcceptedAnswer)
admin.site.register(BooleanAnswer)
admin.site.register(Assignment)
admin.site.register(AssignmentSubmission)
admin.site.register(AssignmentSubmissionFile)
