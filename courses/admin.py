# Register your models here.
from django.contrib import admin

from .models import (
    Category,
    Course,
    CourseFeature,
    CourseFeedback,
    CourseFeedbackInteraction,
    CourseWishlist,
    LearningOutcome,
    Prerequisite,
    TargetAudience,
)

admin.site.register(Category)
admin.site.register(Course)
admin.site.register(CourseFeedback)
admin.site.register(LearningOutcome)
admin.site.register(Prerequisite)
admin.site.register(TargetAudience)
admin.site.register(CourseFeature)
admin.site.register(CourseFeedbackInteraction)
admin.site.register(CourseWishlist)
