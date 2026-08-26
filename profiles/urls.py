from django.urls import path

from . import views

app_name = "profiles"
urlpatterns = [
    path(
        "student/profile/", views.StudentProfileView.as_view(), name="student_profile"
    ),
    path(
        "instructor/profile/",
        views.InstructorProfileView.as_view(),
        name="instructor_profile",
    ),
]
