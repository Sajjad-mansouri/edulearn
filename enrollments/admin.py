# Register your models here.
from django.contrib import admin

from .models import (
    CourseLessonBookmark,
    Enrollment,
    LessonContentProgress,
    LessonProgress,
    VideoProgress,
    VideoWatchEvent,
)

admin.site.register(Enrollment)
admin.site.register(LessonProgress)
admin.site.register(VideoProgress)
admin.site.register(CourseLessonBookmark)
admin.site.register(VideoWatchEvent)
admin.site.register(LessonContentProgress)
