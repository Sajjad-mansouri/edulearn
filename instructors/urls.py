from django.urls import path

from . import views

app_name = "instructor"
urlpatterns = [
    path("courses/", views.InstructorCourse.as_view(), name="instructor_course_list"),
    path(
        "courses/create/",
        views.CourseCreateTemplateView.as_view(),
        name="create_course",
    ),
    path("students/", views.Students.as_view(), name="students"),
    path("assignments/", views.Assignments.as_view(), name="assignments"),
]
