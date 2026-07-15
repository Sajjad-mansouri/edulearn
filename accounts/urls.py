from django.urls import path

from . import views

app_name = "accounts"
urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path(
        "register/student/",
        views.RegisterStudentView.as_view(),
        name="register_student",
    ),
    path(
        "register/<uidb64>/<token>/",
        views.RegisterConfirmView.as_view(),
        name="register_confirm",
    ),
]
