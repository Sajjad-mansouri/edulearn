from datetime import timedelta
from decimal import Decimal

import pytest
from django.conf import settings
from django.utils import timezone

from courses.api.serializers.course import CourseSerializer
from courses.models.category import Category
from courses.models.course import Course

pytestmark = pytest.mark.django_db


class TestCourseSerializer:
    @pytest.fixture
    def serializer_context(self):
        return {
            "best_sellers": set(),
            "now": timezone.now(),
        }

    @pytest.fixture
    def prepared_course(self, course, serializer_context):
        course.duration = timedelta(hours=2.5)
        course.published_at = serializer_context["now"]
        course.save(
            update_fields=[
                "duration",
                "published_at",
            ]
        )
        return course

    @pytest.fixture
    def serialized_course(
        self,
        prepared_course,
        serializer_context,
    ):
        prepared_course.rating = 4.5
        prepared_course.rating_count = 12
        prepared_course.students = 150

        return CourseSerializer(
            prepared_course,
            context=serializer_context,
        )

    def test_serializes_expected_fields(self, serialized_course):
        assert set(serialized_course.data.keys()) == {
            "id",
            "title",
            "instructor",
            "category",
            "subcategory",
            "rating",
            "rating_count",
            "students",
            "level",
            "duration",
            "price",
            "original_price",
            "language",
            "badge",
            "thumbnail",
            "slug",
        }

    def test_serializes_course_id(
        self,
        serialized_course,
        course,
    ):
        assert serialized_course.data["id"] == course.id

    def test_serializes_title(
        self,
        serialized_course,
        course,
    ):
        assert serialized_course.data["title"] == course.title

    def test_serializes_slug(
        self,
        serialized_course,
        course,
    ):
        assert serialized_course.data["slug"] == course.slug

    def test_serializes_level(
        self,
        serialized_course,
        course,
    ):
        assert serialized_course.data["level"] == course.level

    def test_serializes_language(
        self,
        serialized_course,
        course,
    ):
        assert serialized_course.data["language"] == course.language

    def test_serializes_thumbnail(
        self,
        serialized_course,
        course,
    ):
        expected = course.thumbnail.url if course.thumbnail else None

        assert serialized_course.data["thumbnail"] == expected

    def test_instructor_returns_owner_full_name(
        self,
        prepared_course,
    ):
        prepared_course.owner.first_name = "John"
        prepared_course.owner.last_name = "Doe"
        prepared_course.owner.save(
            update_fields=[
                "first_name",
                "last_name",
            ]
        )

        serializer = CourseSerializer(
            prepared_course,
            context={
                "best_sellers": set(),
                "now": timezone.now(),
            },
        )

        assert serializer.data["instructor"] == "John Doe"

    def test_instructor_returns_empty_string_when_owner_has_no_name(
        self,
        prepared_course,
    ):
        prepared_course.owner.first_name = ""
        prepared_course.owner.last_name = ""
        prepared_course.owner.save(
            update_fields=[
                "first_name",
                "last_name",
            ]
        )

        serializer = CourseSerializer(
            prepared_course,
            context={
                "best_sellers": set(),
                "now": timezone.now(),
            },
        )

        assert serializer.data["instructor"] == ""

    def test_category_returns_category_name_for_root_category(
        self,
        serialized_course,
        category,
    ):
        assert category.parent is None
        assert serialized_course.data["category"] == category.name

    def test_subcategory_returns_empty_string_for_root_category(
        self,
        serialized_course,
        category,
    ):
        assert category.parent is None
        assert serialized_course.data["subcategory"] == ""

    def test_category_returns_parent_name_for_subcategory(
        self,
        test_user,
        category,
        serializer_context,
    ):
        subcategory = Category.objects.create(
            name="Django",
            slug="django",
            parent=category,
        )

        course = Course.objects.create(
            title="Django Development",
            owner=test_user,
            category=subcategory,
            duration=timedelta(hours=2),
            published_at=serializer_context["now"],
        )

        serializer = CourseSerializer(
            course,
            context=serializer_context,
        )

        assert serializer.data["category"] == category.name

    def test_subcategory_returns_category_name_for_subcategory(
        self,
        test_user,
        category,
        serializer_context,
    ):
        subcategory = Category.objects.create(
            name="Django",
            slug="django",
            parent=category,
        )

        course = Course.objects.create(
            title="Django Development",
            owner=test_user,
            category=subcategory,
            duration=timedelta(hours=2),
            published_at=serializer_context["now"],
        )

        serializer = CourseSerializer(
            course,
            context=serializer_context,
        )

        assert serializer.data["subcategory"] == subcategory.name

    def test_duration_is_formatted_in_hours(
        self,
        prepared_course,
        serializer_context,
    ):
        prepared_course.duration = timedelta(hours=2.5)

        serializer = CourseSerializer(
            prepared_course,
            context=serializer_context,
        )

        assert serializer.data["duration"] == "2.5h"

    def test_duration_formats_whole_hours(
        self,
        prepared_course,
        serializer_context,
    ):
        prepared_course.duration = timedelta(hours=5)

        serializer = CourseSerializer(
            prepared_course,
            context=serializer_context,
        )

        assert serializer.data["duration"] == "5.0h"

    def test_duration_formats_fractional_hours(
        self,
        prepared_course,
        serializer_context,
    ):
        prepared_course.duration = timedelta(
            hours=1,
            minutes=30,
        )

        serializer = CourseSerializer(
            prepared_course,
            context=serializer_context,
        )

        assert serializer.data["duration"] == "1.5h"

    def test_rating_is_read_only(
        self,
        prepared_course,
        serializer_context,
    ):
        serializer = CourseSerializer(
            prepared_course,
            data={
                "rating": 1.0,
            },
            partial=True,
            context=serializer_context,
        )

        assert serializer.is_valid(), serializer.errors
        assert "rating" not in serializer.validated_data

    def test_rating_count_is_read_only(
        self,
        prepared_course,
        serializer_context,
    ):
        serializer = CourseSerializer(
            prepared_course,
            data={
                "rating_count": 999,
            },
            partial=True,
            context=serializer_context,
        )

        assert serializer.is_valid(), serializer.errors
        assert "rating_count" not in serializer.validated_data

    def test_students_is_read_only(
        self,
        prepared_course,
        serializer_context,
    ):
        serializer = CourseSerializer(
            prepared_course,
            data={
                "students": 999,
            },
            partial=True,
            context=serializer_context,
        )

        assert serializer.is_valid(), serializer.errors
        assert "students" not in serializer.validated_data

    def test_rating_uses_annotated_value(
        self,
        prepared_course,
        serializer_context,
    ):
        prepared_course.rating = 4.25

        serializer = CourseSerializer(
            prepared_course,
            context=serializer_context,
        )

        assert serializer.data["rating"] == 4.25

    def test_rating_count_uses_annotated_value(
        self,
        prepared_course,
        serializer_context,
    ):
        prepared_course.rating_count = 17

        serializer = CourseSerializer(
            prepared_course,
            context=serializer_context,
        )

        assert serializer.data["rating_count"] == 17

    def test_students_uses_annotated_value(
        self,
        prepared_course,
        serializer_context,
    ):
        prepared_course.students = 42

        serializer = CourseSerializer(
            prepared_course,
            context=serializer_context,
        )

        assert serializer.data["students"] == 42

    def test_price_returns_discounted_price(
        self,
        prepared_course,
        serializer_context,
        mocker,
    ):
        mocker.patch.object(
            type(prepared_course),
            "get_discounted_price",
            new_callable=mocker.PropertyMock,
            return_value=Decimal("79.99"),
        )

        serializer = CourseSerializer(
            prepared_course,
            context=serializer_context,
        )

        assert serializer.data["price"] == Decimal("79.99")

    def test_original_price_returns_model_property(
        self,
        prepared_course,
        serializer_context,
    ):
        serializer = CourseSerializer(
            prepared_course,
            context=serializer_context,
        )

        assert serializer.data["original_price"] == prepared_course.original_price

    def test_badge_is_bestseller_when_course_is_in_best_sellers(
        self,
        prepared_course,
        serializer_context,
    ):
        serializer_context["best_sellers"] = {
            prepared_course.id,
        }

        serializer = CourseSerializer(
            prepared_course,
            context=serializer_context,
        )

        assert serializer.data["badge"] == "bestseller"

    def test_bestseller_badge_takes_precedence_over_new_badge(
        self,
        prepared_course,
        serializer_context,
    ):
        prepared_course.published_at = serializer_context["now"] - timedelta(
            days=settings.NEW_COUSRE_RANGE,
        )

        serializer_context["best_sellers"] = {
            prepared_course.id,
        }

        serializer = CourseSerializer(
            prepared_course,
            context=serializer_context,
        )

        assert serializer.data["badge"] == "bestseller"

    def test_badge_is_new_for_recently_published_course(
        self,
        prepared_course,
        serializer_context,
    ):
        prepared_course.published_at = serializer_context["now"] - timedelta(
            days=settings.NEW_COUSRE_RANGE - 1,
        )

        serializer = CourseSerializer(
            prepared_course,
            context=serializer_context,
        )

        assert serializer.data["badge"] == "new"

    def test_badge_is_new_at_exact_new_course_boundary(
        self,
        prepared_course,
        serializer_context,
    ):
        prepared_course.published_at = serializer_context["now"] - timedelta(
            days=settings.NEW_COUSRE_RANGE,
        )

        serializer = CourseSerializer(
            prepared_course,
            context=serializer_context,
        )

        assert serializer.data["badge"] == "new"

    def test_badge_is_empty_for_old_course(
        self,
        prepared_course,
        serializer_context,
    ):
        prepared_course.published_at = serializer_context["now"] - timedelta(
            days=settings.NEW_COUSRE_RANGE + 1,
        )

        serializer = CourseSerializer(
            prepared_course,
            context=serializer_context,
        )

        assert serializer.data["badge"] == ""

    def test_badge_is_empty_when_course_is_not_new_and_not_bestseller(
        self,
        prepared_course,
        serializer_context,
    ):
        prepared_course.published_at = serializer_context["now"] - timedelta(
            days=settings.NEW_COUSRE_RANGE + 1,
        )

        serializer_context["best_sellers"] = set()

        serializer = CourseSerializer(
            prepared_course,
            context=serializer_context,
        )

        assert serializer.data["badge"] == ""

    def test_badge_requires_best_sellers_context(
        self,
        prepared_course,
        serializer_context,
    ):
        serializer = CourseSerializer(
            prepared_course,
            context={
                "now": serializer_context["now"],
            },
        )

        with pytest.raises(KeyError):
            serializer.data  # noqa: B018

    def test_badge_requires_now_context(
        self,
        prepared_course,
    ):
        serializer = CourseSerializer(
            prepared_course,
            context={
                "best_sellers": set(),
            },
        )

        with pytest.raises(KeyError):
            serializer.data  # noqa: B018

    def test_serializer_does_not_modify_course(
        self,
        prepared_course,
        serializer_context,
    ):
        original_title = prepared_course.title
        original_slug = prepared_course.slug
        original_category_id = prepared_course.category_id

        CourseSerializer(
            prepared_course,
            context=serializer_context,
        )

        prepared_course.refresh_from_db()

        assert prepared_course.title == original_title
        assert prepared_course.slug == original_slug
        assert prepared_course.category_id == original_category_id
