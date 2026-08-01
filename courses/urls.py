from django.urls import path

from . import views

app_name = "courses"
urlpatterns = [
    path("", views.InstructorCourse.as_view(), name="instructor_course_list"),
    path("create/", views.CourseCreateTemplateView.as_view(), name="create_course"),
]
