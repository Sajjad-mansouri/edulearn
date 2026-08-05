from django.urls import path

from . import views

app_name = "courses_api"
urlpatterns = [
    path("", views.CoursesApiView.as_view(), name="courses"),
    path("categories/", views.CategoriesApiView.as_view(), name="categories"),
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
]
