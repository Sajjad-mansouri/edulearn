import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from courses.models import Tag


@pytest.mark.django_db
class TestTagModel:
    def test_create_tag_with_valid_data(self):
        tag = Tag.objects.create(
            name="Django",
            slug="django",
        )

        assert tag.name == "Django"
        assert tag.slug == "django"
        assert tag.pk is not None

    def test_str_returns_name(self):
        tag = Tag.objects.create(
            name="Django",
            slug="django",
        )

        assert str(tag) == "Django"

    def test_slug_is_generated_from_name_when_slug_is_empty(self):
        tag = Tag.objects.create(
            name="Django REST Framework",
            slug="",
        )

        assert tag.slug == "django-rest-framework"

    def test_slug_is_not_overwritten_when_provided(self):
        tag = Tag.objects.create(
            name="Django REST Framework",
            slug="drf",
        )

        assert tag.slug == "drf"

    def test_slug_generation_handles_spaces_and_special_characters(self):
        tag = Tag.objects.create(
            name="Python & Django!",
            slug="",
        )

        assert tag.slug == "python-django"

    def test_name_is_required(self):
        tag = Tag(slug="django")

        with pytest.raises(ValidationError):
            tag.full_clean()

    def test_slug_is_required(self):
        tag = Tag(name="Django")

        with pytest.raises(ValidationError):
            tag.full_clean()

    def test_name_cannot_exceed_max_length(self):
        tag = Tag(
            name="a" * 101,
            slug="django",
        )

        with pytest.raises(ValidationError):
            tag.full_clean()

    def test_slug_cannot_exceed_max_length(self):
        tag = Tag(
            name="Django",
            slug="a" * 121,
        )

        with pytest.raises(ValidationError):
            tag.full_clean()

    def test_duplicate_slug_is_rejected(self):
        Tag.objects.create(
            name="Django",
            slug="django",
        )

        duplicate = Tag(
            name="Django Framework",
            slug="django",
        )

        with pytest.raises(IntegrityError):
            duplicate.save()

    def test_same_name_is_allowed_when_slug_is_different(self):
        first = Tag.objects.create(
            name="Django",
            slug="django",
        )

        second = Tag.objects.create(
            name="Django",
            slug="django-framework",
        )

        assert first.pk != second.pk
        assert Tag.objects.filter(name="Django").count() == 2

    def test_different_names_are_allowed(self):
        first = Tag.objects.create(
            name="Django",
            slug="django",
        )

        second = Tag.objects.create(
            name="Python",
            slug="python",
        )

        assert first.pk != second.pk
        assert Tag.objects.count() == 2

    def test_model_ordering_is_by_name(self):
        Tag.objects.create(
            name="Python",
            slug="python",
        )
        Tag.objects.create(
            name="Django",
            slug="django",
        )
        Tag.objects.create(
            name="Algorithms",
            slug="algorithms",
        )

        tags = list(Tag.objects.all())

        assert [tag.name for tag in tags] == [
            "Algorithms",
            "Django",
            "Python",
        ]

    def test_name_index_exists(self):
        indexes = Tag._meta.indexes

        assert any(index.fields == ["name"] for index in indexes)

    def test_slug_is_unique_at_database_level(self):
        Tag.objects.create(
            name="Django",
            slug="django",
        )

        with pytest.raises(IntegrityError):
            Tag.objects.create(
                name="Another Django",
                slug="django",
            )

    def test_slug_is_generated_when_tag_is_saved_without_slug(self):
        tag = Tag(
            name="Machine Learning",
        )

        tag.save()

        assert tag.slug == "machine-learning"

    def test_updating_name_does_not_automatically_change_existing_slug(self):
        tag = Tag.objects.create(
            name="Django",
            slug="django",
        )

        tag.name = "Django REST Framework"
        tag.save()

        tag.refresh_from_db()

        assert tag.name == "Django REST Framework"
        assert tag.slug == "django"

    def test_updating_tag_with_existing_slug_preserves_slug(self):
        tag = Tag.objects.create(
            name="Django",
            slug="django",
        )

        tag.name = "Django Framework"
        tag.save()

        assert tag.slug == "django"

    def test_empty_slug_is_replaced_before_save(self):
        tag = Tag(
            name="Web Development",
            slug="",
        )

        tag.save()

        assert tag.slug == "web-development"
        assert Tag.objects.filter(slug="web-development").exists()
