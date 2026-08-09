from django.urls import path

from . import views

app_name = "enrollment_api"
urlpatterns = [
    path(
        "user-enrollment-status/<int:course_id>/",
        views.CurrentUserEnrollmentStatus.as_view(),
        name="user_enrollment_status",
    )
]
