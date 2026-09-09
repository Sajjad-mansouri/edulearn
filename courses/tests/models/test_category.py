import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from courses.models import Category


@pytest.fixture
def category(db):
    return Category.objects.create(
        name="Programming",
        slug="programming",
        description="Programming courses",
    )


@pytest.fixture
def child_category(db, category):
    return Category.objects.create(
        parent=category,
        name="Python",
        slug="python",
        description="Python courses",
    )


class TestCategoryCreation:
    def test_category_can_be_created(self, db):
        category = Category.objects.create(
            name="Programming",
            slug="programming",
        )

        assert category.pk is not None
        assert category.name == "Programming"
        assert category.slug == "programming"

    def test_category_string_representation_returns_name(self, category):
        assert str(category) == "Programming"


class TestCategoryDefaults:
    def test_description_defaults_to_empty_string(self, db):
        category = Category.objects.create(
            name="Programming",
            slug="programming",
        )

        assert category.description == ""

    def test_display_order_defaults_to_zero(self, db):
        category = Category.objects.create(
            name="Programming",
            slug="programming",
        )

        assert category.display_order == 0

    def test_is_active_defaults_to_true(self, db):
        category = Category.objects.create(
            name="Programming",
            slug="programming",
        )

        assert category.is_active is True

    def test_icon_defaults_to_empty_string(self, db):
        category = Category.objects.create(
            name="Programming",
            slug="programming",
        )

        assert category.icon == ""

    def test_parent_defaults_to_none(self, db):
        category = Category.objects.create(
            name="Programming",
            slug="programming",
        )

        assert category.parent is None


class TestCategorySlug:
    def test_slug_is_generated_from_name_when_missing(self, db):
        category = Category.objects.create(
            name="Web Development",
        )

        assert category.slug == "web-development"

    def test_slug_is_generated_from_complex_name(self, db):
        category = Category.objects.create(
            name="Python & Django",
        )

        assert category.slug == "python-django"

    def test_explicit_slug_is_preserved(self, db):
        category = Category.objects.create(
            name="Web Development",
            slug="custom-development",
        )

        assert category.slug == "custom-development"

    def test_slug_must_be_unique(self, category, db):
        duplicate = Category(
            name="Another Category",
            slug=category.slug,
        )

        with pytest.raises(ValidationError):
            duplicate.full_clean()

    def test_database_rejects_duplicate_slug(self, category):
        duplicate = Category(
            name="Another Category",
            slug=category.slug,
        )

        with pytest.raises(IntegrityError):
            duplicate.save()


class TestCategoryHierarchy:
    def test_category_can_have_parent(self, category, child_category):
        assert child_category.parent == category

    def test_parent_exposes_children_through_related_name(
        self,
        category,
        child_category,
    ):
        assert list(category.children.all()) == [child_category]

    def test_top_level_category_has_no_parent(self, category):
        assert category.parent is None

    def test_multiple_children_can_belong_to_same_parent(
        self,
        category,
        db,
    ):
        python = Category.objects.create(
            parent=category,
            name="Python",
            slug="python",
        )

        django = Category.objects.create(
            parent=category,
            name="Django",
            slug="django",
        )

        assert set(category.children.all()) == {python, django}

    def test_deleting_parent_cascades_to_children(
        self,
        category,
        child_category,
    ):
        category_id = category.pk
        child_id = child_category.pk

        category.delete()

        assert not Category.objects.filter(pk=category_id).exists()
        assert not Category.objects.filter(pk=child_id).exists()


class TestCategoryOrdering:
    def test_categories_are_ordered_by_display_order(
        self,
        db,
    ):
        second = Category.objects.create(
            name="Second",
            slug="second",
            display_order=2,
        )

        first = Category.objects.create(
            name="First",
            slug="first",
            display_order=1,
        )

        categories = list(Category.objects.all())

        assert categories == [first, second]

    def test_categories_with_same_display_order_are_ordered_by_name(
        self,
        db,
    ):
        z_category = Category.objects.create(
            name="Z Category",
            slug="z-category",
            display_order=1,
        )

        a_category = Category.objects.create(
            name="A Category",
            slug="a-category",
            display_order=1,
        )

        categories = list(Category.objects.all())

        assert categories == [a_category, z_category]


class TestCategoryFields:
    def test_description_can_be_stored(self, db):
        category = Category.objects.create(
            name="Programming",
            slug="programming",
            description="Programming related courses.",
        )

        assert category.description == "Programming related courses."

    def test_icon_can_be_stored(self, db):
        category = Category.objects.create(
            name="Programming",
            slug="programming",
            icon="code-icon",
        )

        assert category.icon == "code-icon"

    def test_display_order_can_be_changed(self, category):
        category.display_order = 10
        category.save()

        category.refresh_from_db()

        assert category.display_order == 10

    def test_category_can_be_deactivated(self, category):
        category.is_active = False
        category.save()

        category.refresh_from_db()

        assert category.is_active is False


class TestCategoryValidation:
    def test_name_max_length_is_150(self, db):
        category = Category(
            name="x" * 151,
            slug="category",
        )

        with pytest.raises(ValidationError):
            category.full_clean()

    def test_slug_max_length_is_170(self, db):
        category = Category(
            name="Category",
            slug="x" * 171,
        )

        with pytest.raises(ValidationError):
            category.full_clean()

    def test_icon_max_length_is_100(self, db):
        category = Category(
            name="Category",
            slug="category",
            icon="x" * 101,
        )

        with pytest.raises(ValidationError):
            category.full_clean()

    def test_display_order_cannot_be_negative(self, db):
        category = Category(
            name="Category",
            slug="category",
            display_order=-1,
        )

        with pytest.raises(ValidationError):
            category.full_clean()
