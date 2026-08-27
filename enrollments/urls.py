from django.urls import path

from . import views

app_name = "enrollments"
urlpatterns = [
    path("<enrollment_id>/learn/", views.CourseLearningView.as_view(), name="learn"),
    path("courses/", views.StudentCoursesView.as_view(), name="student_courses"),
]
