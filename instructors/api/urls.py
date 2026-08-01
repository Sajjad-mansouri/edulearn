from django.urls import path

from . import views

app_name = "instructor_api"
urlpatterns = [
    path("categories/", views.CategoriesApiView.as_view(), name="categories"),
    path(
        "category/<categorySlug>/subcategories/",
        views.SubcategoriesApiView.as_view(),
        name="subcategories",
    ),
    path("create/", views.CourseBuilder.as_view(), name="create_course"),
    path(
        "courses/",
        views.InstructorCoursesApiView.as_view(),
        name="instructor_course_list",
    ),
]
