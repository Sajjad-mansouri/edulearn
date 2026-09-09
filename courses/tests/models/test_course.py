from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.utils import timezone

from courses.models.course import (
    Course,
    CourseFeature,
    LearningOutcome,
    Prerequisite,
    TargetAudience,
)


@pytest.fixture
def learning_outcome(course):
    return LearningOutcome.objects.create(
        course=course,
        description="Understand Django fundamentals.",
    )


@pytest.fixture
def prerequisite(course):
    return Prerequisite.objects.create(
        course=course,
        description="Basic Python knowledge.",
    )


@pytest.fixture
def target_audience(course):
    return TargetAudience.objects.create(
        course=course,
        description="Developers who want to learn Django.",
    )


@pytest.fixture
def course_feature(course):
    return CourseFeature.objects.create(
        course=course,
        icon="book",
        text="Practical examples",
    )


class TestCourseCreation:
    def test_course_can_be_created(self, test_user):
        course = Course.objects.create(
            title="Django Development",
            owner=test_user,
        )

        assert course.pk is not None
        assert course.title == "Django Development"
        assert course.owner == test_user

    def test_str_returns_title(self, course):
        assert str(course) == "Django Development"

    def test_default_values_are_applied(self, test_user):
        course = Course.objects.create(
            title="Django Development",
            owner=test_user,
        )

        assert course.language == Course.LANGUAGE.ENGLISH
        assert course.level == Course.Level.ALL_LEVELS
        assert course.status == Course.Status.DRAFT
        assert course.review_status == Course.ReviewStatus.NOT_SUBMITTED
        assert course.visibility == Course.Visibility.PUBLIC
        assert course.version == "1.0.0"
        assert course.price_type == Course.PriceType.FREE
        assert course.price == Decimal("0.00")
        assert course.price_discount == 0

    def test_created_at_is_set(self, course):
        assert course.created_at is not None

    def test_last_updated_is_set(self, course):
        assert course.last_updated is not None

    def test_last_updated_changes_when_course_is_updated(self, course):
        original_updated = course.last_updated

        course.title = "Advanced Django Development"
        course.save()

        assert course.last_updated > original_updated


class TestCourseSlug:
    def test_slug_is_generated_from_title_when_missing(self, test_user):
        course = Course.objects.create(
            title="Django REST Framework",
            owner=test_user,
        )

        assert course.slug == "django-rest-framework"

    def test_slug_is_generated_only_when_missing(self, test_user):
        course = Course.objects.create(
            title="Django Development",
            slug="custom-course-slug",
            owner=test_user,
        )

        assert course.slug == "custom-course-slug"

    def test_slug_does_not_change_when_title_changes(self, course):
        original_slug = course.slug

        course.title = "Advanced Django Development"
        course.save()

        assert course.slug == original_slug

    def test_slug_must_be_unique(self, test_user):
        Course.objects.create(
            title="First Course",
            slug="same-slug",
            owner=test_user,
        )

        duplicate = Course(
            title="Second Course",
            slug="same-slug",
            owner=test_user,
        )

        with pytest.raises(ValidationError) as exc_info:
            duplicate.save()

        assert "slug" in exc_info.value.message_dict

    def test_database_unique_constraint_exists_for_slug(self, test_user):
        """
        This bypasses Course.save() intentionally so that the test verifies
        the database-level uniqueness constraint independently from the
        model's full_clean() behavior.
        """
        Course.objects.create(
            title="First Course",
            slug="same-slug",
            owner=test_user,
        )

        duplicate = Course(
            title="Second Course",
            slug="same-slug",
            owner=test_user,
        )

        with pytest.raises(IntegrityError):
            Course.objects.bulk_create([duplicate])


class TestCourseSEO:
    def test_seo_title_defaults_to_title(self, test_user):
        course = Course.objects.create(
            title="Django Development",
            owner=test_user,
        )

        assert course.seo_title == "Django Development"

    def test_seo_title_is_truncated_to_60_characters(self, test_user):
        title = "A" * 100

        course = Course.objects.create(
            title=title,
            owner=test_user,
        )

        assert course.seo_title == title[:60]
        assert len(course.seo_title) == 60

    def test_existing_seo_title_is_preserved(self, test_user):
        course = Course.objects.create(
            title="Django Development",
            seo_title="Custom SEO Title",
            owner=test_user,
        )

        assert course.seo_title == "Custom SEO Title"

    def test_seo_description_is_generated_from_description(self, test_user):
        description = "Django is a powerful Python web framework."

        course = Course.objects.create(
            title="Django Development",
            description=description,
            owner=test_user,
        )

        assert course.seo_description == description

    def test_seo_description_is_truncated_to_160_characters(self, test_user):
        description = "A" * 250

        course = Course.objects.create(
            title="Django Development",
            description=description,
            owner=test_user,
        )

        assert course.seo_description == description[:160]
        assert len(course.seo_description) == 160

    def test_existing_seo_description_is_preserved(self, test_user):
        course = Course.objects.create(
            title="Django Development",
            description="Original description",
            seo_description="Custom SEO description",
            owner=test_user,
        )

        assert course.seo_description == "Custom SEO description"

    def test_seo_description_remains_empty_when_description_is_empty(
        self,
        test_user,
    ):
        course = Course.objects.create(
            title="Django Development",
            description="",
            owner=test_user,
        )

        assert course.seo_description == ""


class TestCourseValidation:
    def test_normal_title_is_valid(self, test_user):
        course = Course(
            title="Django Development",
            owner=test_user,
        )

        course.save()

        assert course.pk is not None
        assert course.slug == "django-development"

    def test_empty_title_is_invalid(self, test_user):
        course = Course(
            title="",
            slug="django-course",
            owner=test_user,
        )

        with pytest.raises(ValidationError) as exc_info:
            course.full_clean()

        assert "title" in exc_info.value.message_dict

    def test_whitespace_only_title_is_invalid(self, test_user):
        course = Course(
            title="   ",
            slug="django-course",
            owner=test_user,
        )

        with pytest.raises(ValidationError) as exc_info:
            course.full_clean()

        assert "title" in exc_info.value.message_dict

    def test_title_max_length_is_enforced(self, test_user):
        course = Course(
            title="A" * 256,
            slug="django-course",
            owner=test_user,
        )

        with pytest.raises(ValidationError) as exc_info:
            course.full_clean()

        assert "title" in exc_info.value.message_dict

    def test_slug_max_length_is_enforced(self, test_user):
        course = Course(
            title="Django Course",
            slug="a" * 281,
            owner=test_user,
        )

        with pytest.raises(ValidationError) as exc_info:
            course.full_clean()

        assert "slug" in exc_info.value.message_dict


class TestCourseChoices:
    @pytest.mark.parametrize(
        "field,value",
        [
            ("language", Course.LANGUAGE.ENGLISH),
            ("language", Course.LANGUAGE.PERSIAN),
            ("level", Course.Level.BEGINNER),
            ("level", Course.Level.INTERMEDIATE),
            ("level", Course.Level.ADVANCED),
            ("level", Course.Level.ALL_LEVELS),
            ("status", Course.Status.DRAFT),
            ("status", Course.Status.PUBLISHED),
            ("status", Course.Status.UPDATED),
            ("status", Course.Status.ARCHIVED),
            ("status", Course.Status.SUBMITTED),
            ("review_status", Course.ReviewStatus.NOT_SUBMITTED),
            ("review_status", Course.ReviewStatus.PENDING),
            ("review_status", Course.ReviewStatus.UNDER_REVIEW),
            ("review_status", Course.ReviewStatus.APPROVED),
            ("review_status", Course.ReviewStatus.CHANGES_REQUESTED),
            ("review_status", Course.ReviewStatus.REJECTED),
            ("visibility", Course.Visibility.PUBLIC),
            ("visibility", Course.Visibility.PRIVATE),
            ("visibility", Course.Visibility.UNLISTED),
            ("price_type", Course.PriceType.PAID),
            ("price_type", Course.PriceType.FREE),
        ],
    )
    def test_valid_choice_value_is_accepted(
        self,
        test_user,
        field,
        value,
    ):
        course = Course(
            title="Django Course",
            slug="django-course",
            owner=test_user,
            **{field: value},
        )

        course.full_clean()

        assert getattr(course, field) == value


class TestCoursePricing:
    def test_paid_course_returns_original_price(self, test_user):
        course = Course.objects.create(
            title="Paid Course",
            owner=test_user,
            price_type=Course.PriceType.PAID,
            price=Decimal("100.00"),
        )

        assert course.original_price == Decimal("100.00")

    def test_paid_course_returns_discounted_price(self, test_user):
        course = Course.objects.create(
            title="Paid Course",
            owner=test_user,
            price_type=Course.PriceType.PAID,
            price=Decimal("100.00"),
            price_discount=20,
        )

        assert course.get_discounted_price == Decimal("80.00")

    def test_paid_course_with_zero_discount_returns_original_price(
        self,
        test_user,
    ):
        course = Course.objects.create(
            title="Paid Course",
            owner=test_user,
            price_type=Course.PriceType.PAID,
            price=Decimal("100.00"),
            price_discount=0,
        )

        assert course.get_discounted_price == Decimal("100.00")

    def test_paid_course_with_100_percent_discount_is_free(
        self,
        test_user,
    ):
        course = Course.objects.create(
            title="Paid Course",
            owner=test_user,
            price_type=Course.PriceType.PAID,
            price=Decimal("100.00"),
            price_discount=100,
        )

        assert course.get_discounted_price == Decimal("0.00")

    def test_free_course_returns_free_for_discounted_price(
        self,
        test_user,
    ):
        course = Course.objects.create(
            title="Free Course",
            owner=test_user,
            price_type=Course.PriceType.FREE,
            price=None,
        )

        assert course.get_discounted_price == "free"

    def test_free_course_returns_free_for_original_price(
        self,
        test_user,
    ):
        course = Course.objects.create(
            title="Free Course",
            owner=test_user,
            price_type=Course.PriceType.FREE,
            price=None,
        )

        assert course.original_price == Course.PriceType.FREE

    def test_free_course_can_have_null_price(self, test_user):
        course = Course.objects.create(
            title="Free Course",
            owner=test_user,
            price_type=Course.PriceType.FREE,
            price=None,
        )

        assert course.price is None

    def test_free_course_can_have_zero_price(self, test_user):
        course = Course.objects.create(
            title="Free Course",
            owner=test_user,
            price_type=Course.PriceType.FREE,
            price=Decimal("0.00"),
        )

        assert course.price == Decimal("0.00")

    def test_price_discount_can_be_zero(self, test_user):
        course = Course.objects.create(
            title="Django Course",
            owner=test_user,
            price_discount=0,
        )

        assert course.price_discount == 0

    def test_price_discount_can_be_100(self, test_user):
        course = Course.objects.create(
            title="Django Course",
            owner=test_user,
            price_discount=100,
        )

        assert course.price_discount == 100

    @pytest.mark.parametrize("discount", [-1, 101])
    def test_price_discount_outside_valid_range_is_rejected(
        self,
        test_user,
        discount,
    ):
        course = Course(
            title="Django Course",
            slug=f"django-course-{discount}",
            owner=test_user,
            price_discount=discount,
        )

        with pytest.raises(ValidationError) as exc_info:
            course.full_clean()

        assert "price_discount" in exc_info.value.message_dict


class TestCourseRelationships:
    def test_course_belongs_to_owner(self, test_user):
        course = Course.objects.create(
            title="Django Course",
            owner=test_user,
        )

        assert course.owner == test_user
        assert course in test_user.owned_courses.all()

    def test_course_can_belong_to_category(
        self,
        test_user,
        category,
    ):
        course = Course.objects.create(
            title="Django Course",
            owner=test_user,
            category=category,
        )

        assert course.category == category
        assert course in category.courses.all()

    def test_category_is_optional(self, test_user):
        course = Course.objects.create(
            title="Django Course",
            owner=test_user,
            category=None,
        )

        assert course.category is None

    def test_deleting_owner_deletes_courses(
        self,
        test_user,
    ):
        course = Course.objects.create(
            title="Django Course",
            owner=test_user,
        )

        course_id = course.pk

        test_user.delete()

        assert not Course.objects.filter(pk=course_id).exists()

    def test_deleting_category_is_protected(
        self,
        test_user,
        category,
    ):
        Course.objects.create(
            title="Django Course",
            owner=test_user,
            category=category,
        )

        with pytest.raises(ProtectedError):
            category.delete()


class TestCourseOptionalFields:
    def test_optional_fields_can_be_empty(self, test_user):
        course = Course.objects.create(
            title="Django Course",
            owner=test_user,
            subtitle="",
            description="",
            promotional_video="",
            short_description="",
            course_trailer="",
            version_note="",
            seo_title="",
            seo_description="",
            seo_keywords="",
        )

        assert course.subtitle == ""
        assert course.description == ""
        assert course.promotional_video == ""
        assert course.short_description == ""
        assert course.course_trailer == ""
        assert course.version_note == ""
        assert course.seo_keywords == ""

    def test_duration_can_be_null(self, test_user):
        course = Course.objects.create(
            title="Django Course",
            owner=test_user,
            duration=None,
        )

        assert course.duration is None

    def test_duration_can_be_stored(self, test_user):
        duration = timedelta(hours=3, minutes=30)

        course = Course.objects.create(
            title="Django Course",
            owner=test_user,
            duration=duration,
        )

        assert course.duration == duration

    def test_published_at_can_be_null(self, test_user):
        course = Course.objects.create(
            title="Django Course",
            owner=test_user,
            published_at=None,
        )

        assert course.published_at is None

    def test_published_at_can_be_stored(self, test_user):
        published_at = timezone.now()

        course = Course.objects.create(
            title="Django Course",
            owner=test_user,
            published_at=published_at,
        )

        assert course.published_at == published_at


class TestCourseTags:
    def test_course_can_be_created_without_tags(self, test_user):
        course = Course.objects.create(
            title="Django Course",
            owner=test_user,
        )

        assert course.tags.count() == 0


class TestCourseSaveBehavior:
    def test_save_runs_model_validation(self, test_user):
        course = Course(
            title="",
            owner=test_user,
        )

        with pytest.raises(ValidationError):
            course.save()

    def test_save_generates_slug_before_validation(self, test_user):
        course = Course(
            title="Django REST Framework",
            owner=test_user,
        )

        course.save()

        assert course.slug == "django-rest-framework"

    def test_save_generates_seo_title_before_persisting(
        self,
        test_user,
    ):
        course = Course(
            title="Django REST Framework",
            owner=test_user,
        )

        course.save()

        assert course.seo_title == "Django REST Framework"

    def test_save_generates_seo_description_before_persisting(
        self,
        test_user,
    ):
        course = Course(
            title="Django REST Framework",
            description="Learn Django REST Framework from the beginning.",
            owner=test_user,
        )

        course.save()

        assert (
            course.seo_description == "Learn Django REST Framework from the beginning."
        )


# LearningOutcome tests


class TestLearningOutcomeCreation:
    def test_learning_outcome_can_be_created(self, course):
        outcome = LearningOutcome.objects.create(
            course=course,
            description="Understand Django fundamentals.",
        )

        assert outcome.pk is not None
        assert outcome.course == course
        assert outcome.description == "Understand Django fundamentals."
        assert outcome.order == 1

    def test_learning_outcome_is_available_through_course_relation(
        self,
        course,
        learning_outcome,
    ):
        assert course.learning_outcomes.get(pk=learning_outcome.pk) == (
            learning_outcome
        )

    def test_learning_outcome_string_representation(
        self,
        course,
        learning_outcome,
    ):
        assert str(learning_outcome) == (f"{course.title} - {learning_outcome.order}")

    def test_multiple_learning_outcomes_receive_global_sequential_orders(
        self,
        course,
    ):
        first = LearningOutcome.objects.create(
            course=course,
            description="First outcome",
        )
        second = LearningOutcome.objects.create(
            course=course,
            description="Second outcome",
        )
        third = LearningOutcome.objects.create(
            course=course,
            description="Third outcome",
        )

        assert first.order == 1
        assert second.order == 2
        assert third.order == 3

    def test_learning_outcome_order_is_global_across_courses(
        self,
        test_user,
        category,
    ):
        first_course = Course.objects.create(
            title="First Course",
            owner=test_user,
            category=category,
        )
        second_course = Course.objects.create(
            title="Second Course",
            owner=test_user,
            category=category,
        )

        first = LearningOutcome.objects.create(
            course=first_course,
            description="First course outcome",
        )
        second = LearningOutcome.objects.create(
            course=second_course,
            description="Second course outcome",
        )

        assert first.order == 1
        assert second.order == 2

    def test_explicit_order_is_overwritten_on_creation(
        self,
        course,
    ):
        outcome = LearningOutcome.objects.create(
            course=course,
            order=999,
            description="Learning outcome",
        )

        assert outcome.order == 1


class TestLearningOutcomeValidation:
    def test_description_is_required(self, course):
        outcome = LearningOutcome(
            course=course,
            description="",
        )

        with pytest.raises(ValidationError) as exc_info:
            outcome.full_clean()

        assert "description" in exc_info.value.message_dict

    def test_description_max_length_is_enforced(self, course):
        outcome = LearningOutcome(
            course=course,
            description="A" * 501,
        )

        # SequentialField has no value until pre_save(), so save first.
        outcome.save()

        with pytest.raises(ValidationError) as exc_info:
            outcome.full_clean()

        assert "description" in exc_info.value.message_dict

    def test_description_at_max_length_is_valid(self, course):
        outcome = LearningOutcome.objects.create(
            course=course,
            description="A" * 500,
        )

        outcome.full_clean()

        assert len(outcome.description) == 500

    def test_course_is_required(self, test_user):
        outcome = LearningOutcome(
            course=None,
            description="Learning outcome",
        )

        with pytest.raises(ValidationError) as exc_info:
            outcome.full_clean()

        assert "course" in exc_info.value.message_dict


class TestLearningOutcomeSequence:
    def test_sequence_continues_after_existing_outcomes(
        self,
        course,
    ):
        first = LearningOutcome.objects.create(
            course=course,
            description="First outcome",
        )
        second = LearningOutcome.objects.create(
            course=course,
            description="Second outcome",
        )

        third = LearningOutcome.objects.create(
            course=course,
            description="Third outcome",
        )

        assert first.order == 1
        assert second.order == 2
        assert third.order == 3

    def test_sequence_uses_maximum_existing_order(
        self,
        course,
    ):
        first = LearningOutcome.objects.create(
            course=course,
            description="First outcome",
        )
        second = LearningOutcome.objects.create(
            course=course,
            description="Second outcome",
        )

        LearningOutcome.objects.filter(pk=first.pk).update(order=100)

        third = LearningOutcome.objects.create(
            course=course,
            description="Third outcome",
        )

        assert second.order == 2
        assert third.order == 101

    def test_order_does_not_change_when_existing_instance_is_saved(
        self,
        learning_outcome,
    ):
        original_order = learning_outcome.order

        learning_outcome.description = "Updated description"
        learning_outcome.save()

        learning_outcome.refresh_from_db()

        assert learning_outcome.order == original_order

    def test_sequence_is_independent_from_other_sequential_models(
        self,
        course,
    ):
        outcome = LearningOutcome.objects.create(
            course=course,
            description="Learning outcome",
        )
        prerequisite = Prerequisite.objects.create(
            course=course,
            description="Prerequisite",
        )
        audience = TargetAudience.objects.create(
            course=course,
            description="Target audience",
        )

        assert outcome.order == 1
        assert prerequisite.order == 1
        assert audience.order == 1


class TestLearningOutcomeOrdering:
    def test_outcomes_are_ordered_by_course_then_order(
        self,
        test_user,
        category,
    ):
        first_course = Course.objects.create(
            title="First Course",
            owner=test_user,
            category=category,
        )
        second_course = Course.objects.create(
            title="Second Course",
            owner=test_user,
            category=category,
        )

        first = LearningOutcome.objects.create(
            course=first_course,
            description="First course outcome",
        )
        second = LearningOutcome.objects.create(
            course=first_course,
            description="Second course outcome",
        )
        third = LearningOutcome.objects.create(
            course=second_course,
            description="Second course first outcome",
        )

        outcomes = list(LearningOutcome.objects.all())

        assert outcomes == [first, second, third]

    def test_outcomes_are_ordered_by_order_within_course(
        self,
        course,
    ):
        first = LearningOutcome.objects.create(
            course=course,
            description="First outcome",
        )
        second = LearningOutcome.objects.create(
            course=course,
            description="Second outcome",
        )
        third = LearningOutcome.objects.create(
            course=course,
            description="Third outcome",
        )

        outcomes = list(LearningOutcome.objects.filter(course=course))

        assert outcomes == [first, second, third]


class TestLearningOutcomeConstraints:
    def test_duplicate_order_is_rejected_by_model_validation(
        self,
        course,
    ):
        first = LearningOutcome.objects.create(
            course=course,
            description="First outcome",
        )

        duplicate = LearningOutcome(
            course=course,
            order=first.order,
            description="Duplicate outcome",
        )

        with pytest.raises(ValidationError) as exc_info:
            duplicate.full_clean()

        assert "__all__" in exc_info.value.message_dict

    def test_database_rejects_duplicate_order_for_same_course(
        self,
        course,
    ):
        first = LearningOutcome.objects.create(
            course=course,
            description="First outcome",
        )

        second = LearningOutcome.objects.create(
            course=course,
            description="Second outcome",
        )

        # Directly modify the database value.
        # This bypasses LearningOutcome.save() and SequentialField.pre_save().
        with pytest.raises(IntegrityError):
            LearningOutcome.objects.filter(
                pk=second.pk,
            ).update(
                order=first.order,
            )

    def test_same_order_can_exist_for_different_courses(
        self,
        test_user,
        category,
    ):
        first_course = Course.objects.create(
            title="First Course",
            owner=test_user,
            category=category,
        )
        second_course = Course.objects.create(
            title="Second Course",
            owner=test_user,
            category=category,
        )

        first = LearningOutcome.objects.create(
            course=first_course,
            description="First outcome",
        )

        second = LearningOutcome.objects.create(
            course=second_course,
            description="Second outcome",
        )

        # Force the same order intentionally.
        LearningOutcome.objects.filter(pk=second.pk).update(
            order=first.order,
        )

        second.refresh_from_db()

        assert first.order == second.order
        assert first.course_id != second.course_id


class TestLearningOutcomeDeletion:
    def test_deleting_course_deletes_learning_outcomes(
        self,
        course,
        learning_outcome,
    ):
        outcome_id = learning_outcome.pk

        course.delete()

        assert not LearningOutcome.objects.filter(pk=outcome_id).exists()


# Prerequisite
class TestPrerequisiteCreation:
    def test_prerequisite_can_be_created(self, course):
        prerequisite = Prerequisite.objects.create(
            course=course,
            description="Basic Python knowledge.",
        )

        assert prerequisite.pk is not None
        assert prerequisite.course == course
        assert prerequisite.description == "Basic Python knowledge."
        assert prerequisite.order == 1

    def test_prerequisite_is_available_through_course_relation(
        self,
        course,
        prerequisite,
    ):
        assert course.prerequisites.get(pk=prerequisite.pk) == prerequisite

    def test_prerequisite_string_representation(
        self,
        course,
        prerequisite,
    ):
        assert str(prerequisite) == (f"{course.title} - {prerequisite.order}")

    def test_multiple_prerequisites_receive_sequential_orders(
        self,
        course,
    ):
        first = Prerequisite.objects.create(
            course=course,
            description="First prerequisite",
        )
        second = Prerequisite.objects.create(
            course=course,
            description="Second prerequisite",
        )
        third = Prerequisite.objects.create(
            course=course,
            description="Third prerequisite",
        )

        assert first.order == 1
        assert second.order == 2
        assert third.order == 3

    def test_prerequisite_order_is_global_across_courses(
        self,
        test_user,
        category,
    ):
        first_course = Course.objects.create(
            title="First Course",
            owner=test_user,
            category=category,
        )
        second_course = Course.objects.create(
            title="Second Course",
            owner=test_user,
            category=category,
        )

        first = Prerequisite.objects.create(
            course=first_course,
            description="First prerequisite",
        )
        second = Prerequisite.objects.create(
            course=second_course,
            description="Second prerequisite",
        )

        assert first.order == 1
        assert second.order == 2

    def test_explicit_order_is_overwritten_on_creation(
        self,
        course,
    ):
        prerequisite = Prerequisite.objects.create(
            course=course,
            order=999,
            description="Prerequisite",
        )

        assert prerequisite.order == 1


class TestPrerequisiteValidation:
    def test_description_is_required(self, course):
        prerequisite = Prerequisite(
            course=course,
            description="",
        )

        with pytest.raises(ValidationError) as exc_info:
            prerequisite.full_clean()

        assert "description" in exc_info.value.message_dict

    def test_description_max_length_is_enforced(self, course):
        prerequisite = Prerequisite(
            course=course,
            description="A" * 501,
        )

        prerequisite.save()

        with pytest.raises(ValidationError) as exc_info:
            prerequisite.full_clean()

        assert "description" in exc_info.value.message_dict

    def test_description_at_max_length_is_valid(self, course):
        prerequisite = Prerequisite.objects.create(
            course=course,
            description="A" * 500,
        )

        prerequisite.full_clean()

        assert len(prerequisite.description) == 500

    def test_course_is_required(self):
        prerequisite = Prerequisite(
            course=None,
            description="Basic Python knowledge.",
        )

        with pytest.raises(ValidationError) as exc_info:
            prerequisite.full_clean()

        assert "course" in exc_info.value.message_dict


class TestPrerequisiteSequence:
    def test_order_does_not_change_when_existing_instance_is_saved(
        self,
        prerequisite,
    ):
        original_order = prerequisite.order

        prerequisite.description = "Updated prerequisite"
        prerequisite.save()

        prerequisite.refresh_from_db()

        assert prerequisite.order == original_order


class TestPrerequisiteOrdering:
    def test_prerequisites_are_ordered_by_course_then_order(
        self,
        test_user,
        category,
    ):
        first_course = Course.objects.create(
            title="First Course",
            owner=test_user,
            category=category,
        )
        second_course = Course.objects.create(
            title="Second Course",
            owner=test_user,
            category=category,
        )

        first = Prerequisite.objects.create(
            course=first_course,
            description="First prerequisite",
        )
        second = Prerequisite.objects.create(
            course=first_course,
            description="Second prerequisite",
        )
        third = Prerequisite.objects.create(
            course=second_course,
            description="Other prerequisite",
        )

        prerequisites = list(Prerequisite.objects.all())

        assert prerequisites == [first, second, third]

    def test_prerequisites_are_ordered_by_order_within_course(
        self,
        course,
    ):
        first = Prerequisite.objects.create(
            course=course,
            description="First prerequisite",
        )
        second = Prerequisite.objects.create(
            course=course,
            description="Second prerequisite",
        )
        third = Prerequisite.objects.create(
            course=course,
            description="Third prerequisite",
        )

        prerequisites = list(Prerequisite.objects.filter(course=course))

        assert prerequisites == [first, second, third]


class TestPrerequisiteDeletion:
    def test_deleting_course_deletes_prerequisites(
        self,
        course,
        prerequisite,
    ):
        prerequisite_id = prerequisite.pk

        course.delete()

        assert not Prerequisite.objects.filter(pk=prerequisite_id).exists()


# TargetAudience
class TestTargetAudienceCreation:
    def test_target_audience_can_be_created(self, course):
        audience = TargetAudience.objects.create(
            course=course,
            description="Developers who want to learn Django.",
        )

        assert audience.pk is not None
        assert audience.course == course
        assert audience.description == "Developers who want to learn Django."
        assert audience.order == 1

    def test_target_audience_is_available_through_course_relation(
        self,
        course,
        target_audience,
    ):
        assert course.target_audiences.get(pk=target_audience.pk) == target_audience

    def test_target_audience_string_representation(
        self,
        course,
        target_audience,
    ):
        assert str(target_audience) == (f"{course.title} - {target_audience.order}")

    def test_multiple_target_audiences_receive_sequential_orders(
        self,
        course,
    ):
        first = TargetAudience.objects.create(
            course=course,
            description="First audience",
        )
        second = TargetAudience.objects.create(
            course=course,
            description="Second audience",
        )
        third = TargetAudience.objects.create(
            course=course,
            description="Third audience",
        )

        assert first.order == 1
        assert second.order == 2
        assert third.order == 3

    def test_target_audience_order_is_global_across_courses(
        self,
        test_user,
        category,
    ):
        first_course = Course.objects.create(
            title="First Course",
            owner=test_user,
            category=category,
        )
        second_course = Course.objects.create(
            title="Second Course",
            owner=test_user,
            category=category,
        )

        first = TargetAudience.objects.create(
            course=first_course,
            description="First audience",
        )
        second = TargetAudience.objects.create(
            course=second_course,
            description="Second audience",
        )

        assert first.order == 1
        assert second.order == 2

    def test_explicit_order_is_overwritten_on_creation(
        self,
        course,
    ):
        audience = TargetAudience.objects.create(
            course=course,
            order=999,
            description="Target audience",
        )

        assert audience.order == 1


class TestTargetAudienceValidation:
    def test_description_is_required(self, course):
        audience = TargetAudience(
            course=course,
            description="",
        )

        with pytest.raises(ValidationError) as exc_info:
            audience.full_clean()

        assert "description" in exc_info.value.message_dict

    def test_description_max_length_is_enforced(self, course):
        audience = TargetAudience(
            course=course,
            description="A" * 501,
        )

        audience.save()

        with pytest.raises(ValidationError) as exc_info:
            audience.full_clean()

        assert "description" in exc_info.value.message_dict

    def test_description_at_max_length_is_valid(self, course):
        audience = TargetAudience.objects.create(
            course=course,
            description="A" * 500,
        )

        audience.full_clean()

        assert len(audience.description) == 500

    def test_course_is_required(self):
        audience = TargetAudience(
            course=None,
            description="Target audience",
        )

        with pytest.raises(ValidationError) as exc_info:
            audience.full_clean()

        assert "course" in exc_info.value.message_dict


class TestTargetAudienceSequence:
    def test_order_does_not_change_when_existing_instance_is_saved(
        self,
        target_audience,
    ):
        original_order = target_audience.order

        target_audience.description = "Updated audience"
        target_audience.save()

        target_audience.refresh_from_db()

        assert target_audience.order == original_order


class TestTargetAudienceOrdering:
    def test_target_audiences_are_ordered_by_course_then_order(
        self,
        test_user,
        category,
    ):
        first_course = Course.objects.create(
            title="First Course",
            owner=test_user,
            category=category,
        )
        second_course = Course.objects.create(
            title="Second Course",
            owner=test_user,
            category=category,
        )

        first = TargetAudience.objects.create(
            course=first_course,
            description="First course audience",
        )
        second = TargetAudience.objects.create(
            course=first_course,
            description="Second course audience",
        )
        third = TargetAudience.objects.create(
            course=second_course,
            description="Other course audience",
        )

        audiences = list(TargetAudience.objects.all())

        assert audiences == [first, second, third]

    def test_target_audiences_are_ordered_by_order_within_course(
        self,
        course,
    ):
        first = TargetAudience.objects.create(
            course=course,
            description="First audience",
        )
        second = TargetAudience.objects.create(
            course=course,
            description="Second audience",
        )
        third = TargetAudience.objects.create(
            course=course,
            description="Third audience",
        )

        audiences = list(TargetAudience.objects.filter(course=course))

        assert audiences == [first, second, third]


class TestTargetAudienceDeletion:
    def test_deleting_course_deletes_target_audiences(
        self,
        course,
        target_audience,
    ):
        audience_id = target_audience.pk

        course.delete()

        assert not TargetAudience.objects.filter(pk=audience_id).exists()


# CourseFeature


class TestCourseFeatureCreation:
    def test_course_feature_can_be_created(
        self,
        course,
    ):
        feature = CourseFeature.objects.create(
            course=course,
            icon="book",
            text="Practical examples",
        )

        assert feature.pk is not None
        assert feature.course == course
        assert feature.icon == "book"
        assert feature.text == "Practical examples"

    def test_course_feature_is_available_through_course_relation(
        self,
        course,
        course_feature,
    ):
        assert course.features.get(pk=course_feature.pk) == course_feature

    def test_string_representation(
        self,
        course,
        course_feature,
    ):
        assert str(course_feature) == (f"{course.title} : {course_feature.text}")


class TestCourseFeatureFields:
    def test_icon_is_optional(
        self,
        course,
    ):
        feature = CourseFeature.objects.create(
            course=course,
            text="Practical examples",
        )

        assert feature.icon == ""

    def test_icon_can_be_empty_string(
        self,
        course,
    ):
        feature = CourseFeature.objects.create(
            course=course,
            icon="",
            text="Practical examples",
        )

        assert feature.icon == ""

    def test_icon_max_length_is_valid(
        self,
        course,
    ):
        feature = CourseFeature(
            course=course,
            icon="A" * 100,
            text="Practical examples",
        )

        feature.full_clean()

    def test_icon_over_max_length_is_invalid(
        self,
        course,
    ):
        feature = CourseFeature(
            course=course,
            icon="A" * 101,
            text="Practical examples",
        )

        with pytest.raises(ValidationError) as exc_info:
            feature.full_clean()

        assert "icon" in exc_info.value.message_dict

    def test_text_is_required(
        self,
        course,
    ):
        feature = CourseFeature(
            course=course,
            text="",
        )

        with pytest.raises(ValidationError) as exc_info:
            feature.full_clean()

        assert "text" in exc_info.value.message_dict

    def test_text_max_length_is_valid(
        self,
        course,
    ):
        feature = CourseFeature(
            course=course,
            text="A" * 250,
        )

        feature.full_clean()

    def test_text_over_max_length_is_invalid(
        self,
        course,
    ):
        feature = CourseFeature(
            course=course,
            text="A" * 251,
        )

        with pytest.raises(ValidationError) as exc_info:
            feature.full_clean()

        assert "text" in exc_info.value.message_dict

    def test_course_is_required(self):
        feature = CourseFeature(
            course=None,
            text="Practical examples",
        )

        with pytest.raises(ValidationError) as exc_info:
            feature.full_clean()

        assert "course" in exc_info.value.message_dict


class TestCourseFeatureTimestamps:
    def test_created_at_is_set(
        self,
        course_feature,
    ):
        assert course_feature.created_at is not None

    def test_updated_at_is_set(
        self,
        course_feature,
    ):
        assert course_feature.updated_at is not None

    def test_updated_at_changes_when_feature_is_updated(
        self,
        course_feature,
    ):
        original_updated_at = course_feature.updated_at

        course_feature.text = "Updated feature"
        course_feature.save()

        course_feature.refresh_from_db()

        assert course_feature.updated_at > original_updated_at

    def test_created_at_does_not_change_when_feature_is_updated(
        self,
        course_feature,
    ):
        original_created_at = course_feature.created_at

        course_feature.text = "Updated feature"
        course_feature.save()

        course_feature.refresh_from_db()

        assert course_feature.created_at == original_created_at


class TestCourseFeatureOrdering:
    def test_features_are_ordered_by_newest_first(
        self,
        course,
    ):
        first = CourseFeature.objects.create(
            course=course,
            text="First feature",
        )
        second = CourseFeature.objects.create(
            course=course,
            text="Second feature",
        )
        third = CourseFeature.objects.create(
            course=course,
            text="Third feature",
        )

        now = timezone.now()

        CourseFeature.objects.filter(pk=first.pk).update(
            created_at=now - timedelta(minutes=3)
        )
        CourseFeature.objects.filter(pk=second.pk).update(
            created_at=now - timedelta(minutes=2)
        )
        CourseFeature.objects.filter(pk=third.pk).update(
            created_at=now - timedelta(minutes=1)
        )

        features = list(CourseFeature.objects.filter(course=course))

        assert features == [third, second, first]


class TestCourseFeatureDeletion:
    def test_deleting_course_deletes_features(
        self,
        course,
        course_feature,
    ):
        feature_id = course_feature.pk

        course.delete()

        assert not CourseFeature.objects.filter(pk=feature_id).exists()
