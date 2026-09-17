import pytest

from courses.api.serializers.category import CategorySerializer
from courses.models.category import Category

pytestmark = pytest.mark.django_db


class TestCategorySerializer:
    def test_serializes_category_with_expected_fields(self, category):
        serializer = CategorySerializer(category)

        assert serializer.data == {
            "name": category.name,
            "slug": category.slug,
        }

    def test_serialized_data_contains_only_declared_fields(self, category):
        serializer = CategorySerializer(category)

        assert set(serializer.data.keys()) == {"name", "slug"}

    def test_serializes_category_name(self, category):
        serializer = CategorySerializer(category)

        assert serializer.data["name"] == category.name

    def test_serializes_category_slug(self, category):
        serializer = CategorySerializer(category)

        assert serializer.data["slug"] == category.slug

    def test_deserializes_valid_data(self):
        data = {
            "name": "Web Development",
            "slug": "web-development",
        }

        serializer = CategorySerializer(data=data)

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data == data

    def test_name_is_required(self):
        data = {
            "slug": "web-development",
        }

        serializer = CategorySerializer(data=data)

        assert not serializer.is_valid()
        assert "name" in serializer.errors

    def test_slug_is_required(self):
        data = {
            "name": "Web Development",
        }

        serializer = CategorySerializer(data=data)

        assert not serializer.is_valid()
        assert "slug" in serializer.errors

    def test_empty_data_is_invalid(self):
        serializer = CategorySerializer(data={})

        assert not serializer.is_valid()
        assert set(serializer.errors.keys()) == {"name", "slug"}

    def test_extra_fields_are_ignored(self):
        data = {
            "name": "Web Development",
            "slug": "web-development",
            "description": "Courses about web development",
            "icon": "web",
        }

        serializer = CategorySerializer(data=data)

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data == {
            "name": "Web Development",
            "slug": "web-development",
        }

    def test_partial_update_allows_name_only(self, category):
        serializer = CategorySerializer(
            category,
            data={"name": "Updated Programming"},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["name"] == "Updated Programming"

    def test_partial_update_allows_slug_only(self, category):
        serializer = CategorySerializer(
            category,
            data={"slug": "updated-programming"},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["slug"] == "updated-programming"

    def test_partial_update_allows_empty_payload(self, category):
        serializer = CategorySerializer(
            category,
            data={},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data == {}

    def test_updates_existing_category(self, category):
        serializer = CategorySerializer(
            category,
            data={
                "name": "Updated Programming",
                "slug": "updated-programming",
            },
        )

        assert serializer.is_valid(), serializer.errors

        updated_category = serializer.save()

        assert updated_category.pk == category.pk
        assert updated_category.name == "Updated Programming"
        assert updated_category.slug == "updated-programming"

    def test_creates_category_from_valid_data(self):
        serializer = CategorySerializer(
            data={
                "name": "Web Development",
                "slug": "web-development",
            }
        )

        assert serializer.is_valid(), serializer.errors

        category = serializer.save()

        assert category.pk is not None
        assert category.name == "Web Development"
        assert category.slug == "web-development"

    def test_duplicate_slug_is_rejected(self, category):
        serializer = CategorySerializer(
            data={
                "name": "Another Programming Category",
                "slug": category.slug,
            }
        )

        assert not serializer.is_valid()
        assert "slug" in serializer.errors

    def test_duplicate_name_behavior_follows_model_constraints(
        self,
        category,
    ):
        serializer = CategorySerializer(
            data={
                "name": category.name,
                "slug": "another-programming",
            }
        )

        is_valid = serializer.is_valid()

        if not Category._meta.get_field("name").unique:
            assert is_valid
        else:
            assert not is_valid
            assert "name" in serializer.errors
