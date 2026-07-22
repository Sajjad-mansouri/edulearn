import pytest
from django.db import IntegrityError

from courses.models import Category
from courses.tests.factories import CategoryFactory


@pytest.mark.django_db
class TestCategoryModel:
    """Tests for the Category model."""

    def test_create_category(self):
        """A category can be created."""
        category = Category.objects.create(
            name="Programming",
            slug="programming",
            description="Programming courses",
            display_order=10,
            is_active=True,
        )

        assert category.name == "Programming"
        assert category.slug == "programming"
        assert category.description == "Programming courses"
        assert category.display_order == 10
        assert category.is_active is True
        assert category.parent is None

    def test_string_representation(self):
        """The string representation returns the category name."""
        category = CategoryFactory(name="Programming")

        assert str(category) == "Programming"

    def test_description_is_optional(self):
        """A category may be created without a description."""
        category = Category.objects.create(
            name="Programming",
            slug="programming",
        )

        assert category.description == ""

    def test_defaults_are_applied(self):
        """Default values are applied."""
        category = Category.objects.create(
            name="Programming",
            slug="programming",
        )

        assert category.display_order == 0
        assert category.is_active is True
        assert category.parent is None

    def test_can_create_child_category(self):
        """A category can belong to another category."""
        parent = CategoryFactory(name="Programming")

        child = CategoryFactory(
            parent=parent,
            name="Python",
        )

        assert child.parent == parent

    def test_parent_returns_children(self):
        """A parent category exposes its child categories."""
        parent = CategoryFactory()

        child1 = CategoryFactory(parent=parent)
        child2 = CategoryFactory(parent=parent)

        assert set(parent.children.all()) == {child1, child2}

    def test_deleting_parent_deletes_children(self):
        """Deleting a parent category cascades to its children."""
        parent = CategoryFactory()

        child = CategoryFactory(parent=parent)

        parent.delete()

        assert not Category.objects.filter(pk=child.pk).exists()

    def test_slug_must_be_unique(self):
        """Slug values must be unique."""
        CategoryFactory(slug="python")

        with pytest.raises(IntegrityError):
            CategoryFactory(slug="python")

    def test_generates_slug_when_slug_not_provided(self):
        """Slug is generated automatically."""
        category = Category.objects.create(
            name="Machine Learning",
        )

        assert category.slug == "machine-learning"

    def test_preserves_existing_slug(self):
        """A provided slug is not overwritten."""
        category = Category.objects.create(
            name="Machine Learning",
            slug="ml",
        )

        assert category.slug == "ml"

    def test_slug_does_not_change_after_name_update(self):
        """Changing the name does not change the slug."""
        category = CategoryFactory(
            name="Python",
            slug="python",
        )

        original_slug = category.slug

        category.name = "Advanced Python"
        category.save()
        category.refresh_from_db()

        assert category.slug == original_slug
