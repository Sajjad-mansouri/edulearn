import pytest
from rest_framework import status
from rest_framework.test import APIRequestFactory

from courses.api.views import CategoriesApiViews
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


class Tests:
    def test_get_returns_200(
        self,
        category,
    ):
        factory = APIRequestFactory()
        request = factory.get("/courses/categories/")

        response = CategoriesApiViews.as_view()(request)

        assert response.status_code == status.HTTP_200_OK

    def test_get_returns_root_categories(
        self,
        category,
    ):
        factory = APIRequestFactory()
        request = factory.get("/courses/categories/")

        response = CategoriesApiViews.as_view()(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == [
            {
                "name": category.name,
                "slug": category.slug,
                "subcategories": [],
            }
        ]

    def test_get_includes_subcategories(
        self,
        category,
        child_category,
    ):
        factory = APIRequestFactory()
        request = factory.get("/courses/categories/")

        response = CategoriesApiViews.as_view()(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == [
            {
                "name": category.name,
                "slug": category.slug,
                "subcategories": [
                    {
                        "name": child_category.name,
                        "slug": child_category.slug,
                    }
                ],
            }
        ]

    def test_get_returns_all_subcategories(
        self,
        category,
        child_category,
        another_child_category,
    ):
        factory = APIRequestFactory()
        request = factory.get("/courses/categories/")

        response = CategoriesApiViews.as_view()(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data[0]["name"] == category.name
        assert response.data[0]["slug"] == category.slug

        assert response.data[0]["subcategories"] == [
            {
                "name": child_category.name,
                "slug": child_category.slug,
            },
            {
                "name": another_child_category.name,
                "slug": another_child_category.slug,
            },
        ]

    def test_get_excludes_child_categories_from_top_level(
        self,
        category,
        child_category,
    ):
        factory = APIRequestFactory()
        request = factory.get("/courses/categories/")

        response = CategoriesApiViews.as_view()(request)

        returned_slugs = {item["slug"] for item in response.data}

        assert category.slug in returned_slugs
        assert child_category.slug not in returned_slugs

    def test_get_returns_multiple_root_categories(
        self,
        category,
        another_root_category,
    ):
        factory = APIRequestFactory()
        request = factory.get("/courses/categories/")

        response = CategoriesApiViews.as_view()(request)

        assert response.status_code == status.HTTP_200_OK

        assert response.data == [
            {
                "name": category.name,
                "slug": category.slug,
                "subcategories": [],
            },
            {
                "name": another_root_category.name,
                "slug": another_root_category.slug,
                "subcategories": [],
            },
        ]

    def test_get_returns_empty_list_when_no_root_categories_exist(
        self,
        category,
    ):
        category.delete()

        factory = APIRequestFactory()
        request = factory.get("/courses/categories/")

        response = CategoriesApiViews.as_view()(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_get_allows_anonymous_users(
        self,
        category,
    ):
        factory = APIRequestFactory()
        request = factory.get("/courses/categories/")

        response = CategoriesApiViews.as_view()(request)

        assert response.status_code == status.HTTP_200_OK

    def test_get_returns_only_expected_fields(
        self,
        category,
        child_category,
    ):
        factory = APIRequestFactory()
        request = factory.get("/courses/categories/")

        response = CategoriesApiViews.as_view()(request)

        category_data = response.data[0]

        assert set(category_data.keys()) == {
            "name",
            "slug",
            "subcategories",
        }

        assert set(category_data["subcategories"][0].keys()) == {
            "name",
            "slug",
        }

    def test_get_does_not_include_grandchildren(
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

        factory = APIRequestFactory()
        request = factory.get("/courses/categories/")

        response = CategoriesApiViews.as_view()(request)

        assert response.status_code == status.HTTP_200_OK

        assert response.data == [
            {
                "name": category.name,
                "slug": category.slug,
                "subcategories": [
                    {
                        "name": child_category.name,
                        "slug": child_category.slug,
                    }
                ],
            }
        ]

        assert grandchild_category.slug not in {
            child["slug"] for child in response.data[0]["subcategories"]
        }
