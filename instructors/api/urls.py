from django.urls import path

from enrollments.api import views as enrollment_views

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
        "courses/<int:pk>/delete/",
        views.CourseDeleteApiView.as_view(),
        name="course_delete",
    ),
    path(
        "courses/<int:course_id>/submit/",
        views.CourseSubmitApiView.as_view(),
        name="submit_course",
    ),
    path(
        "courses/<int:course_id>/publish/",
        views.CoursePublishApiView.as_view(),
        name="publish_course",
    ),
    path(
        "courses/",
        views.InstructorCoursesApiView.as_view(),
        name="instructor_course_list",
    ),
    path("students/", views.InstructorStudentsApiView.as_view(), name="students"),
    path(
        "assignments/", views.InstructorAssignmentsApiView.as_view(), name="assignments"
    ),
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
    path(
        "revenue/",
        views.InstructorRevenueApiView.as_view(),
        name="revenue",
    ),
    path(
        "transactions/",
        views.InstructorTransactionsApiView.as_view(),
        name="transactions",
    ),
    path(
        "course/<int:course_id>/preview/",
        enrollment_views.EnrollmentCourseApiView.as_view(),
        name="course_preview",
    ),
    path(
        "course/<int:course_id>/lesson/<int:lesson_id>/preview/",
        enrollment_views.LessonContentApiView.as_view(),
        name="course_preview_lesson_content",
    ),
]
