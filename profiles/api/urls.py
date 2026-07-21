from django.urls import path

from . import views

app_name = "profile-api"
urlpatterns = [
    path("profile/", views.ProfileApiView.as_view(), name="student-profile"),
    path("current-user/", views.CurrentUserApiView.as_view(), name="current_user"),
]
