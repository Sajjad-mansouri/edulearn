import pytest
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.test import APIRequestFactory

from courses.api.serializers import CategorySerializer
from courses.api.views import SubcategoriesApiView
from courses.models import Category


@pytest.fixture
def child_category(category):
    return Category.objects.create(
        name="Django",
        slug="django",
        description="Django courses",
        parent=category,
    )


@pytest.fixture
def another_child_category(category):
    return Category.objects.create(
        name="REST API",
        slug="rest-api",
        description="REST API courses",
        parent=category,
    )


@pytest.fixture
def another_root_category(db):
    return Category.objects.create(
        name="Python",
        slug="python",
        description="Python courses",
    )


@pytest.fixture
def unrelated_child_category(another_root_category):
    return Category.objects.create(
        name="Python Web",
        slug="python-web",
        description="Python web courses",
        parent=another_root_category,
    )


class TestSubcategoriesApiView:
    def test_get_queryset_returns_subcategories_of_requested_category(
        self,
        category,
        child_category,
        another_child_category,
    ):
        view = SubcategoriesApiView()
        view.kwargs = {"categorySlug": category.slug}

        queryset = view.get_queryset()

        assert set(queryset) == {
            child_category,
            another_child_category,
        }

    def test_get_queryset_returns_only_direct_children(
        self,
        category,
        child_category,
    ):
        grandchild_category = Category.objects.create(
            name="Django REST Framework",
            slug="django-rest-framework",
            description="DRF courses",
            parent=child_category,
        )

        view = SubcategoriesApiView()
        view.kwargs = {"categorySlug": category.slug}

        queryset = view.get_queryset()

        assert list(queryset) == [child_category]
        assert grandchild_category not in queryset

    def test_get_queryset_excludes_subcategories_of_other_categories(
        self,
        category,
        child_category,
        another_root_category,
        unrelated_child_category,
    ):
        view = SubcategoriesApiView()
        view.kwargs = {"categorySlug": category.slug}

        queryset = view.get_queryset()

        assert list(queryset) == [child_category]
        assert unrelated_child_category not in queryset

    def test_get_queryset_returns_empty_queryset_when_category_has_no_children(
        self,
        category,
    ):
        view = SubcategoriesApiView()
        view.kwargs = {"categorySlug": category.slug}

        queryset = view.get_queryset()

        assert not queryset.exists()

    def test_get_queryset_returns_empty_queryset_for_unknown_slug(
        self,
        db,
    ):
        view = SubcategoriesApiView()
        view.kwargs = {"categorySlug": "non-existent-category"}

        queryset = view.get_queryset()

        assert not queryset.exists()

    def test_get_queryset_returns_empty_queryset_when_category_slug_is_none(
        self,
        db,
    ):
        view = SubcategoriesApiView()
        view.kwargs = {"categorySlug": None}

        queryset = view.get_queryset()

        assert not queryset.exists()

    def test_get_queryset_uses_category_slug(
        self,
        category,
        child_category,
        another_root_category,
        unrelated_child_category,
    ):
        view = SubcategoriesApiView()

        view.kwargs = {"categorySlug": category.slug}
        queryset = view.get_queryset()

        assert list(queryset) == [child_category]

        view.kwargs = {"categorySlug": another_root_category.slug}
        queryset = view.get_queryset()

        assert list(queryset) == [unrelated_child_category]

    def test_serializer_class(self):
        assert SubcategoriesApiView.serializer_class is CategorySerializer

    def test_permission_classes_allow_any(self):
        assert SubcategoriesApiView.permission_classes == [AllowAny]

    def test_get_returns_200(
        self,
        category,
        child_category,
    ):
        factory = APIRequestFactory()
        request = factory.get(f"/courses/categories/{category.slug}/subcategories/")

        response = SubcategoriesApiView.as_view()(
            request,
            categorySlug=category.slug,
        )

        assert response.status_code == status.HTTP_200_OK

    def test_get_serializes_subcategories(
        self,
        category,
        child_category,
        another_child_category,
    ):
        factory = APIRequestFactory()
        request = factory.get(f"/courses/categories/{category.slug}/subcategories/")

        response = SubcategoriesApiView.as_view()(
            request,
            categorySlug=category.slug,
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2
        assert response.data["results"] == [
            {
                "name": child_category.name,
                "slug": child_category.slug,
            },
            {
                "name": another_child_category.name,
                "slug": another_child_category.slug,
            },
        ]

    def test_get_returns_empty_results_when_category_has_no_subcategories(
        self,
        category,
    ):
        factory = APIRequestFactory()
        request = factory.get(f"/courses/categories/{category.slug}/subcategories/")

        response = SubcategoriesApiView.as_view()(
            request,
            categorySlug=category.slug,
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0
        assert response.data["results"] == []

    def test_get_allows_anonymous_users(
        self,
        category,
        child_category,
    ):
        factory = APIRequestFactory()
        request = factory.get(f"/courses/categories/{category.slug}/subcategories/")

        response = SubcategoriesApiView.as_view()(
            request,
            categorySlug=category.slug,
        )

        assert response.status_code == status.HTTP_200_OK
