from django.urls import path

from . import views

app_name = "instructor_api"
urlpatterns = [
    path("courses/create/", views.CourseBuilder.as_view(), name="create_course"),
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
]
