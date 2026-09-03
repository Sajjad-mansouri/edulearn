from django.urls import path

from . import views

app_name = "landing_page"
urlpatterns = [path("", views.LandingPage.as_view(), name="main")]
