# Register your models here.
from django.contrib import admin

from .models import (
    ArticleContent,
    Attachment,
    FileContent,
    Lesson,
    LessonContent,
    Section,
    VideoCaption,
    VideoContent,
)

admin.site.register(Attachment)
admin.site.register(Section)
admin.site.register(Lesson)
admin.site.register(LessonContent)
admin.site.register(ArticleContent)
admin.site.register(VideoContent)
admin.site.register(VideoCaption)
admin.site.register(FileContent)
