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
    path(
        "courses/<slug:slug>/<int:pk>/edit/",
        views.CourseUpateTemplateView.as_view(),
        name="update_course",
    ),
    path("analytics/", views.InstructorAnalytics.as_view(), name="analytics"),
    path("revenue/", views.InstructorRevenue.as_view(), name="revenue"),
]
