# Register your models here.
from django.contrib import admin

from .models import CourseLessonBookmark, Enrollment, LessonProgress, VideoProgress

admin.site.register(Enrollment)
admin.site.register(LessonProgress)
admin.site.register(VideoProgress)
admin.site.register(CourseLessonBookmark)
