from django.urls import path

from . import views

app_name = "courses"
urlpatterns = [
    path("", views.CourseCatalog.as_view(), name="catalog"),
    path(
        "<int:pk>/<slug:slug>/",
        views.CourseDetailView.as_view(),
        name="course_detail",
    ),
]
