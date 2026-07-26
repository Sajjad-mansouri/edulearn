from django.urls import path

from . import views

app_name = "courses"
urlpatterns = [
    path("create/", views.CourseCreateTemplateView.as_view(), name="create_course")
]
