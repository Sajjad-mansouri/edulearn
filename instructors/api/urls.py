from django.urls import path

from . import views

app_name = "instructor_api"
urlpatterns = [
    path("create/", views.CourseBuilder.as_view(), name="create_course"),
    path(
        "courses/",
        views.InstructorCoursesApiView.as_view(),
        name="instructor_course_list",
    ),
    path("students/", views.InstructorStudentsApiView.as_view(), name="students"),
]
