import pytest
from django.db import IntegrityError

from courses.models import Tag
from courses.tests.factories import TagFactory


@pytest.mark.django_db
class TestTagModel:
    """Tests for the Tag model."""

    def test_create_tag(self):
        """A tag can be created."""
        tag = Tag.objects.create(
            name="Python",
            slug="python",
        )

        assert tag.name == "Python"
        assert tag.slug == "python"

    def test_string_representation(self):
        """The string representation returns the tag name."""
        tag = TagFactory(name="Python")

        assert str(tag) == "Python"

    def test_slug_must_be_unique(self):
        """Two tags cannot share the same slug."""
        TagFactory(slug="python")

        with pytest.raises(IntegrityError):
            TagFactory(slug="python")

    def test_generates_slug_when_slug_not_provided(self):
        """Slug is generated automatically from the name."""
        tag = Tag.objects.create(
            name="Machine Learning",
        )

        assert tag.slug == "machine-learning"

    def test_preserves_existing_slug(self):
        """An explicitly provided slug is not overwritten."""
        tag = Tag.objects.create(
            name="Machine Learning",
            slug="ml",
        )

        assert tag.slug == "ml"

    def test_slug_does_not_change_after_name_update(self):
        """Changing the name does not modify the existing slug."""
        tag = TagFactory(
            name="Python",
            slug="python",
        )

        original_slug = tag.slug

        tag.name = "Advanced Python"
        tag.save()
        tag.refresh_from_db()

        assert tag.slug == original_slug
