from django.urls import path

from . import views

app_name = "courses_api"
urlpatterns = [
    path("", views.CoursesApiView.as_view(), name="courses"),
    path("metadata/", views.CourseMetadataApiView.as_view(), name="metadata"),
    path("categories1/", views.CategoriesApiView.as_view(), name="categories"),
    path("categories/", views.CategoriesApiViewsV1.as_view(), name="categories"),
    path(
        "category/<categorySlug>/subcategories/",
        views.SubcategoriesApiView.as_view(),
        name="subcategories",
    ),
    path(
        "filters/",
        views.CourseFilterMetadataApiView.as_view(),
        name="course_filter_metadata",
    ),
    path(
        "<int:course_id>/wishlist/",
        views.CourseWishlistToggleApiView.as_view(),
        name="course_wishlist_toggle",
    ),
    path(
        "<int:course_id>/wishlist/status/",
        views.CourseWishlistStatusApiView.as_view(),
        name="course_wishlist_status",
    ),
    path(
        "<int:pk>/", views.CourseDetailInfoApiView.as_view(), name="course_detail_info"
    ),
    path(
        "<int:course_id>/instructor/",
        views.CourseDetailInstructorInfoApiView.as_view(),
        name="course_detail_instructor_info",
    ),
    path(
        "<int:course_id>/curriculum/",
        views.CourseDetailCurriculumApiView.as_view(),
        name="course_detail_curriculum_info",
    ),
    path(
        "<int:course_id>/reviews/",
        views.CourseReviewListApiView.as_view(),
        name="course_reviews",
    ),
    path(
        "<int:course_id>/submit/review/",
        views.CourseReviewApiView.as_view(),
        name="submit_review",
    ),
    path(
        "<int:course_id>/reviews/<int:review_id>/helpful/",
        views.CourseReviewHelpfulApiView.as_view(),
        name="review_helpful",
    ),
    path(
        "<int:course_id>/reviews/<int:review_id>/delete/",
        views.CourseReviewDestroyApiView.as_view(),
        name="remove_review",
    ),
]
