from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from . import views

app_name = "accounts-api"
urlpatterns = [
    path("current-user/", views.CurrentUserApiView.as_view(), name="current_user"),
    # jwt
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    # registration
    path("register/", views.RegisterApiView.as_view(), name="register"),
    path(
        "register/instructor/",
        views.RegisterInstructorApiView.as_view(),
        name="register_instructor",
    ),
    path("login/", views.LoginApiView.as_view(), name="login"),
    path("logout/", views.LogoutApiView.as_view(), name="logout"),
    path(
        "password_reset/", views.PasswordResetApiView.as_view(), name="password_reset"
    ),
]
