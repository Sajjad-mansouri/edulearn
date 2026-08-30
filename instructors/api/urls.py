from django.urls import path

from . import views

app_name = "instructor_api"
urlpatterns = [
    path(
        "courses/create/<course_status>/",
        views.CourseBuilder.as_view(),
        name="create_course",
    ),
    path("courses/<int:pk>/", views.CourseApiView.as_view(), name="course_data"),
    path(
        "courses/<int:pk>/update/<course_status>/",
        views.CourseUpdateApiView.as_view(),
        name="update_course",
    ),
    path(
        "courses/",
        views.InstructorCoursesApiView.as_view(),
        name="instructor_course_list",
    ),
    path("students/", views.InstructorStudentsApiView.as_view(), name="students"),
    path("assignments/", views.InstructorAssignmentsApiView.as_view(), name="students"),
    path(
        "assignments/<int:id>/download/",
        views.SubmissionDownloadView.as_view(),
        name="submission_download",
    ),
    path(
        "assignments/bulk-download/",
        views.BulkDownloadView.as_view(),
        name="bulk-download",
    ),
    path(
        "courses/compact/",
        views.InstructorFilterCoursesApiView.as_view(),
        name="instructor_filter_courses",
    ),
    path(
        "assignments/grade/<int:pk>/",
        views.GradeAssignmentApiView.as_view(),
        name="grade_assignment",
    ),
    path(
        "analytics/",
        views.InstructorAnalyticsApiView.as_view(),
        name="analytics",
    ),
    path(
        "analytics/courses/",
        views.InstructorAnalyticsCoursesApiView.as_view(),
        name="analytics_courses",
    ),
]
