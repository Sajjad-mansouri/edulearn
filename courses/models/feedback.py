from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from enrollments.models import Enrollment

User = get_user_model()


class CourseFeedback(models.Model):
    enrollment = models.OneToOneField(
        Enrollment,
        on_delete=models.CASCADE,
        related_name="feedback",
        verbose_name=_("Enrollment"),
    )

    rating = models.PositiveSmallIntegerField()

    title = models.CharField(max_length=150, blank=True)

    review = models.TextField(blank=True)

    is_public = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return _("{user} feedback for {course} ({rating}/5)").format(
            user=self.enrollment.user.get_full_name() or self.enrollment.user.username,
            course=self.enrollment.course.title,
            rating=self.rating,
        )
