import pytest

from courses.api.selectors.selectors import (
    get_category_options,
    get_duration_options,
    get_language_options,
    get_level_options,
    get_price_options,
    get_rating_options,
)
from courses.models.category import Category
from courses.models.course import Course

pytestmark = pytest.mark.django_db


class TestGetCategoryOptions:
    def test_returns_empty_list_when_no_categories_exist(self):
        result = get_category_options()

        assert result == []

    def test_excludes_root_category_without_courses(self, category):
        result = get_category_options()

        assert result == []

    def test_includes_root_category_with_direct_course(
        self,
        category,
        course,
    ):
        result = get_category_options()

        assert result == [
            {
                "value": category.slug,
                "label": category.name,
                "count": 1,
                "icon": category.icon,
                "subcategories": [],
            }
        ]

    def test_category_count_includes_direct_courses(
        self,
        test_user,
        category,
    ):
        Course.objects.create(
            title="Python Basics",
            owner=test_user,
            category=category,
        )
        Course.objects.create(
            title="Advanced Python",
            owner=test_user,
            category=category,
        )

        result = get_category_options()

        assert len(result) == 1
        assert result[0]["value"] == category.slug
        assert result[0]["count"] == 2

    def test_category_count_includes_courses_from_children(
        self,
        test_user,
        category,
    ):
        child = Category.objects.create(
            name="Django",
            slug="django",
            parent=category,
        )

        Course.objects.create(
            title="Django Development",
            owner=test_user,
            category=child,
        )

        result = get_category_options()

        assert len(result) == 1
        assert result[0]["value"] == category.slug
        assert result[0]["count"] == 1

    def test_category_count_includes_direct_and_child_courses(
        self,
        test_user,
        category,
    ):
        child = Category.objects.create(
            name="Django",
            slug="django",
            parent=category,
        )

        Course.objects.create(
            title="Programming Fundamentals",
            owner=test_user,
            category=category,
        )
        Course.objects.create(
            title="Django Development",
            owner=test_user,
            category=child,
        )

        result = get_category_options()

        assert len(result) == 1
        assert result[0]["count"] == 2

    def test_excludes_root_category_when_it_and_its_children_have_no_courses(
        self,
        category,
    ):
        Category.objects.create(
            name="Django",
            slug="django",
            parent=category,
        )

        result = get_category_options()

        assert result == []

    def test_excludes_child_category_without_courses(
        self,
        test_user,
        category,
    ):
        child_with_courses = Category.objects.create(
            name="Django",
            slug="django",
            parent=category,
        )
        Category.objects.create(
            name="Flask",
            slug="flask",
            parent=category,
        )

        Course.objects.create(
            title="Django Development",
            owner=test_user,
            category=child_with_courses,
        )

        result = get_category_options()

        assert len(result) == 1
        assert len(result[0]["subcategories"]) == 1
        assert result[0]["subcategories"][0]["value"] == "django"

    def test_subcategory_contains_expected_fields(
        self,
        test_user,
        category,
    ):
        child = Category.objects.create(
            name="Django",
            slug="django",
            parent=category,
        )

        Course.objects.create(
            title="Django Development",
            owner=test_user,
            category=child,
        )

        result = get_category_options()

        assert result[0]["subcategories"] == [
            {
                "value": child.slug,
                "label": child.name,
                "count": 1,
            }
        ]

    def test_subcategory_count_contains_only_courses_assigned_to_that_subcategory(
        self,
        test_user,
        category,
    ):
        first_child = Category.objects.create(
            name="Django",
            slug="django",
            parent=category,
        )
        second_child = Category.objects.create(
            name="Flask",
            slug="flask",
            parent=category,
        )

        Course.objects.create(
            title="Django Development",
            owner=test_user,
            category=first_child,
        )
        Course.objects.create(
            title="Advanced Django",
            owner=test_user,
            category=first_child,
        )
        Course.objects.create(
            title="Flask Development",
            owner=test_user,
            category=second_child,
        )

        result = get_category_options()

        subcategories = result[0]["subcategories"]

        assert subcategories == [
            {
                "value": "django",
                "label": "Django",
                "count": 2,
            },
            {
                "value": "flask",
                "label": "Flask",
                "count": 1,
            },
        ]

    def test_subcategories_are_ordered_by_name(
        self,
        test_user,
        category,
    ):
        zulu = Category.objects.create(
            name="Zulu",
            slug="zulu",
            parent=category,
        )
        alpha = Category.objects.create(
            name="Alpha",
            slug="alpha",
            parent=category,
        )
        middle = Category.objects.create(
            name="Middle",
            slug="middle",
            parent=category,
        )

        Course.objects.create(
            title="Zulu Course",
            owner=test_user,
            category=zulu,
        )
        Course.objects.create(
            title="Alpha Course",
            owner=test_user,
            category=alpha,
        )
        Course.objects.create(
            title="Middle Course",
            owner=test_user,
            category=middle,
        )

        result = get_category_options()

        assert [item["label"] for item in result[0]["subcategories"]] == [
            "Alpha",
            "Middle",
            "Zulu",
        ]

    def test_root_categories_are_ordered_by_name(
        self,
        test_user,
    ):
        zulu = Category.objects.create(
            name="Zulu",
            slug="zulu",
        )
        alpha = Category.objects.create(
            name="Alpha",
            slug="alpha",
        )
        middle = Category.objects.create(
            name="Middle",
            slug="middle",
        )

        Course.objects.create(
            title="Zulu Course",
            owner=test_user,
            category=zulu,
        )
        Course.objects.create(
            title="Alpha Course",
            owner=test_user,
            category=alpha,
        )
        Course.objects.create(
            title="Middle Course",
            owner=test_user,
            category=middle,
        )

        result = get_category_options()

        assert [item["label"] for item in result] == [
            "Alpha",
            "Middle",
            "Zulu",
        ]

    def test_returns_multiple_root_categories_with_their_own_subcategories(
        self,
        test_user,
    ):
        programming = Category.objects.create(
            name="Programming",
            slug="programming",
        )
        design = Category.objects.create(
            name="Design",
            slug="design",
        )

        django = Category.objects.create(
            name="Django",
            slug="django",
            parent=programming,
        )
        ui_ux = Category.objects.create(
            name="UI/UX",
            slug="ui-ux",
            parent=design,
        )

        Course.objects.create(
            title="Django Development",
            owner=test_user,
            category=django,
        )
        Course.objects.create(
            title="UI/UX Design",
            owner=test_user,
            category=ui_ux,
        )

        result = get_category_options()

        assert len(result) == 2

        assert result[0]["label"] == "Design"
        assert result[0]["count"] == 1
        assert result[0]["subcategories"] == [
            {
                "value": "ui-ux",
                "label": "UI/UX",
                "count": 1,
            }
        ]

        assert result[1]["label"] == "Programming"
        assert result[1]["count"] == 1
        assert result[1]["subcategories"] == [
            {
                "value": "django",
                "label": "Django",
                "count": 1,
            }
        ]

    def test_root_category_option_contains_expected_fields(
        self,
        category,
        course,
    ):
        result = get_category_options()

        assert set(result[0].keys()) == {
            "value",
            "label",
            "count",
            "icon",
            "subcategories",
        }

    def test_root_category_value_uses_slug(
        self,
        category,
        course,
    ):
        result = get_category_options()

        assert result[0]["value"] == category.slug

    def test_root_category_label_uses_name(
        self,
        category,
        course,
    ):
        result = get_category_options()

        assert result[0]["label"] == category.name

    def test_root_category_icon_is_returned(
        self,
        category,
        course,
    ):
        result = get_category_options()

        assert result[0]["icon"] == category.icon

    def test_course_is_counted_once_for_root_category(
        self,
        test_user,
        category,
    ):
        course = Course.objects.create(
            title="Django Development",
            owner=test_user,
            category=category,
        )

        result = get_category_options()

        assert result[0]["count"] == 1

        course.refresh_from_db()
        assert course.category_id == category.id


class TestGetLanguageOptions:
    def test_returns_all_language_choices(self):
        result = get_language_options()

        expected = [
            {
                "value": value,
                "label": label,
            }
            for value, label in Course.LANGUAGE.choices
        ]

        assert result == expected

    def test_each_language_option_contains_only_value_and_label(self):
        result = get_language_options()

        assert all(set(option.keys()) == {"value", "label"} for option in result)

    def test_language_option_values_match_model_choices(self):
        result = get_language_options()

        actual_values = [option["value"] for option in result]
        expected_values = [value for value, _label in Course.LANGUAGE.choices]

        assert actual_values == expected_values

    def test_language_option_labels_match_model_choices(self):
        result = get_language_options()

        actual_labels = [option["label"] for option in result]
        expected_labels = [label for _value, label in Course.LANGUAGE.choices]

        assert actual_labels == expected_labels


class TestGetLevelOptions:
    def test_returns_all_level_choices(self):
        result = get_level_options()

        expected = [
            {
                "value": value,
                "label": label,
            }
            for value, label in Course.Level.choices
        ]

        assert result == expected

    def test_each_level_option_contains_only_value_and_label(self):
        result = get_level_options()

        assert all(set(option.keys()) == {"value", "label"} for option in result)

    def test_level_option_values_match_model_choices(self):
        result = get_level_options()

        actual_values = [option["value"] for option in result]
        expected_values = [value for value, _label in Course.Level.choices]

        assert actual_values == expected_values

    def test_level_option_labels_match_model_choices(self):
        result = get_level_options()

        actual_labels = [option["label"] for option in result]
        expected_labels = [label for _value, label in Course.Level.choices]

        assert actual_labels == expected_labels


class TestGetPriceOptions:
    def test_returns_expected_price_options(self):
        result = get_price_options()

        assert result == [
            {
                "value": "free",
                "label": "Free",
            },
            {
                "value": "paid",
                "label": "Paid",
            },
        ]

    def test_price_options_are_ordered_free_then_paid(self):
        result = get_price_options()

        assert [option["value"] for option in result] == [
            "free",
            "paid",
        ]

    def test_each_price_option_contains_only_value_and_label(self):
        result = get_price_options()

        assert all(set(option.keys()) == {"value", "label"} for option in result)


class TestGetDurationOptions:
    def test_returns_expected_duration_options(self):
        result = get_duration_options()

        assert result == [
            {
                "value": "short",
                "label": "0-3 Hours",
            },
            {
                "value": "medium",
                "label": "3-10 Hours",
            },
            {
                "value": "long",
                "label": "10+ Hours",
            },
        ]

    def test_duration_options_are_ordered_short_medium_long(self):
        result = get_duration_options()

        assert [option["value"] for option in result] == [
            "short",
            "medium",
            "long",
        ]

    def test_each_duration_option_contains_only_value_and_label(self):
        result = get_duration_options()

        assert all(set(option.keys()) == {"value", "label"} for option in result)


class TestGetRatingOptions:
    def test_returns_expected_rating_options(self):
        result = get_rating_options()

        assert result == [
            {
                "value": 4.5,
                "label": "4.5 & above",
            },
            {
                "value": 4.0,
                "label": "4.0 & above",
            },
            {
                "value": 3.0,
                "label": "3.0 & above",
            },
        ]

    def test_rating_options_are_ordered_highest_to_lowest(self):
        result = get_rating_options()

        assert [option["value"] for option in result] == [
            4.5,
            4.0,
            3.0,
        ]

    def test_each_rating_option_contains_only_value_and_label(self):
        result = get_rating_options()

        assert all(set(option.keys()) == {"value", "label"} for option in result)

    def test_rating_values_are_numeric(self):
        result = get_rating_options()

        assert all(isinstance(option["value"], float) for option in result)
