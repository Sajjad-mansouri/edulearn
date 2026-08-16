from django.db import models
from django.utils.translation import gettext_lazy as _


class CourseLessonBookmark(models.Model):
    enrollment = models.ForeignKey(
        "enrollments.Enrollment",
        on_delete=models.CASCADE,
        related_name="bookmarks",
        verbose_name=_("Enrollment"),
    )

    lesson = models.ForeignKey(
        "curriculums.Lesson",
        on_delete=models.CASCADE,
        related_name="bookmarks",
        verbose_name=_("Lesson"),
    )

    def __str__(self):
        return f"{self.enrollment.user.username} bookmark '{self.lesson.title}' lesson"
