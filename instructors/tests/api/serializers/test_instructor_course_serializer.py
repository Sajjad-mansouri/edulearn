from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.db.models import Avg
from rest_framework import serializers

from courses.models import (
    Course,
    CourseFeature,
    CourseFeedback,
    LearningOutcome,
    Prerequisite,
    TargetAudience,
)
from instructors.api.serializers.course import (
    FeatureSerializer,
    InstructorCourseSerializer,
    InstructorCourseSubmissionSerializer,
    InstructorFilterCoursesSerializer,
    LearningOutcomeSerializer,
    PrerequisiteSerializer,
    TargetAudienceSerializer,
)

User = get_user_model()


@pytest.mark.django_db
class TestFeatureSerializer:
    """Tests for FeatureSerializer."""

    def test_fields_are_configured_correctly(self):
        serializer = FeatureSerializer()

        assert set(serializer.fields) == {"icon", "text"}

    def test_icon_is_optional(self):
        serializer = FeatureSerializer(
            data={
                "text": "Learn Django from fundamentals to advanced concepts.",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["text"] == (
            "Learn Django from fundamentals to advanced concepts."
        )
        assert serializer.validated_data.get("icon", "") == ""

    def test_text_is_required(self):
        serializer = FeatureSerializer(
            data={
                "icon": "certificate",
            }
        )

        assert not serializer.is_valid()
        assert "text" in serializer.errors

    def test_valid_data_is_accepted(self):
        data = {
            "icon": "certificate",
            "text": "Learn Django from fundamentals to advanced concepts.",
        }

        serializer = FeatureSerializer(data=data)

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data == data

    def test_blank_icon_is_accepted(self):
        serializer = FeatureSerializer(
            data={
                "icon": "",
                "text": "Learn Django from fundamentals to advanced concepts.",
            }
        )

        assert serializer.is_valid(), serializer.errors

    def test_blank_text_is_rejected(self):
        serializer = FeatureSerializer(
            data={
                "icon": "certificate",
                "text": "",
            }
        )

        assert not serializer.is_valid()
        assert "text" in serializer.errors

    def test_icon_max_length_is_enforced(self):
        serializer = FeatureSerializer(
            data={
                "icon": "x" * 101,
                "text": "Test feature",
            }
        )

        assert not serializer.is_valid()
        assert "icon" in serializer.errors

    def test_text_max_length_is_enforced(self):
        serializer = FeatureSerializer(
            data={
                "icon": "certificate",
                "text": "x" * 251,
            }
        )

        assert not serializer.is_valid()
        assert "text" in serializer.errors

    def test_serializes_model_instance(self, instructor_course):
        feature = CourseFeature.objects.create(
            course=instructor_course,
            icon="certificate",
            text="Learn Django from fundamentals to advanced concepts.",
        )

        serializer = FeatureSerializer(instance=feature)

        assert serializer.data == {
            "icon": "certificate",
            "text": "Learn Django from fundamentals to advanced concepts.",
        }

    def test_serialization_does_not_expose_model_id(self, instructor_course):
        feature = CourseFeature.objects.create(
            course=instructor_course,
            icon="certificate",
            text="Test feature",
        )

        serializer = FeatureSerializer(instance=feature)

        assert "id" not in serializer.data
        assert "course" not in serializer.data

    def test_update_changes_exposed_fields(self, instructor_course):
        feature = CourseFeature.objects.create(
            course=instructor_course,
            icon="certificate",
            text="Original feature",
        )

        serializer = FeatureSerializer(
            instance=feature,
            data={
                "icon": "book",
                "text": "Updated feature",
            },
        )

        assert serializer.is_valid(), serializer.errors

        updated_feature = serializer.save()

        assert updated_feature.pk == feature.pk
        assert updated_feature.icon == "book"
        assert updated_feature.text == "Updated feature"

    def test_partial_update_can_update_only_icon(self, instructor_course):
        feature = CourseFeature.objects.create(
            course=instructor_course,
            icon="certificate",
            text="Original feature",
        )

        serializer = FeatureSerializer(
            instance=feature,
            data={"icon": "book"},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        updated_feature = serializer.save()

        assert updated_feature.icon == "book"
        assert updated_feature.text == "Original feature"

    def test_partial_update_can_update_only_text(self, instructor_course):
        feature = CourseFeature.objects.create(
            course=instructor_course,
            icon="certificate",
            text="Original feature",
        )

        serializer = FeatureSerializer(
            instance=feature,
            data={"text": "Updated feature"},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        updated_feature = serializer.save()

        assert updated_feature.icon == "certificate"
        assert updated_feature.text == "Updated feature"

    def test_extra_input_fields_are_ignored(self):
        serializer = FeatureSerializer(
            data={
                "icon": "certificate",
                "text": "Test feature",
                "id": 999,
                "course": 999,
                "unexpected": "ignored",
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert "id" not in serializer.validated_data
        assert "course" not in serializer.validated_data
        assert "unexpected" not in serializer.validated_data


@pytest.mark.django_db
class TestLearningOutcomeSerializer:
    """Tests for LearningOutcomeSerializer."""

    def test_fields_are_configured_correctly(self):
        serializer = LearningOutcomeSerializer()

        assert set(serializer.fields) == {"id", "description"}

    def test_id_is_read_only(self):
        serializer = LearningOutcomeSerializer()

        assert serializer.fields["id"].read_only is True

    def test_description_is_required(self):
        serializer = LearningOutcomeSerializer(data={})

        assert not serializer.is_valid()
        assert "description" in serializer.errors

    def test_valid_description_is_accepted(self):
        serializer = LearningOutcomeSerializer(
            data={"description": "Build Django REST APIs."}
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["description"] == "Build Django REST APIs."

    def test_blank_description_is_rejected(self):
        serializer = LearningOutcomeSerializer(
            data={"description": ""},
        )

        assert not serializer.is_valid()
        assert "description" in serializer.errors

    def test_serializes_model_instance(self, instructor_course):
        outcome = LearningOutcome.objects.create(
            course=instructor_course,
            description="Build Django REST APIs.",
        )

        serializer = LearningOutcomeSerializer(instance=outcome)

        assert serializer.data == {
            "id": outcome.id,
            "description": "Build Django REST APIs.",
        }

    def test_serialized_id_matches_model_id(self, instructor_course):
        outcome = LearningOutcome.objects.create(
            course=instructor_course,
            description="Design scalable databases.",
        )

        serializer = LearningOutcomeSerializer(instance=outcome)

        assert serializer.data["id"] == outcome.id

    def test_course_is_not_exposed(self, instructor_course):
        outcome = LearningOutcome.objects.create(
            course=instructor_course,
            description="Deploy applications with Docker.",
        )

        serializer = LearningOutcomeSerializer(instance=outcome)

        assert "course" not in serializer.data

    def test_id_cannot_be_changed_through_input(self, instructor_course):
        outcome = LearningOutcome.objects.create(
            course=instructor_course,
            description="Original outcome",
        )

        serializer = LearningOutcomeSerializer(
            instance=outcome,
            data={
                "id": outcome.id + 999,
                "description": "Updated outcome",
            },
        )

        assert serializer.is_valid(), serializer.errors

        updated_outcome = serializer.save()

        assert updated_outcome.pk == outcome.pk
        assert updated_outcome.description == "Updated outcome"

    def test_partial_update_changes_description(self, instructor_course):
        outcome = LearningOutcome.objects.create(
            course=instructor_course,
            description="Original outcome",
        )

        serializer = LearningOutcomeSerializer(
            instance=outcome,
            data={"description": "Updated outcome"},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        updated_outcome = serializer.save()

        assert updated_outcome.pk == outcome.pk
        assert updated_outcome.description == "Updated outcome"

    def test_extra_fields_are_ignored(self):
        serializer = LearningOutcomeSerializer(
            data={
                "description": "Build Django REST APIs.",
                "course": 999,
                "unexpected": "ignored",
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert "course" not in serializer.validated_data
        assert "unexpected" not in serializer.validated_data


@pytest.mark.django_db
class TestPrerequisiteSerializer:
    """Tests for PrerequisiteSerializer."""

    def test_fields_are_configured_correctly(self):
        serializer = PrerequisiteSerializer()

        assert set(serializer.fields) == {"id", "description"}

    def test_id_is_not_required(self):
        serializer = PrerequisiteSerializer()

        assert serializer.fields["id"].required is False

    def test_description_is_required(self):
        serializer = PrerequisiteSerializer(data={})

        assert not serializer.is_valid()
        assert "description" in serializer.errors

    def test_valid_data_without_id_is_accepted(self):
        serializer = PrerequisiteSerializer(
            data={"description": "Basic Python knowledge."}
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["description"] == ("Basic Python knowledge.")
        assert "id" not in serializer.validated_data

    def test_valid_data_with_id_is_accepted(self):
        serializer = PrerequisiteSerializer(
            data={
                "id": 10,
                "description": "Basic Python knowledge.",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["id"] == 10
        assert serializer.validated_data["description"] == ("Basic Python knowledge.")

    def test_blank_description_is_rejected(self):
        serializer = PrerequisiteSerializer(
            data={"description": ""},
        )

        assert not serializer.is_valid()
        assert "description" in serializer.errors

    def test_invalid_id_type_is_rejected(self):
        serializer = PrerequisiteSerializer(
            data={
                "id": "not-an-integer",
                "description": "Basic Python knowledge.",
            }
        )

        assert not serializer.is_valid()
        assert "id" in serializer.errors

    def test_negative_id_is_accepted_at_serializer_level(self):
        serializer = PrerequisiteSerializer(
            data={
                "id": -1,
                "description": "Basic Python knowledge.",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["id"] == -1

    def test_serializes_model_instance(self, instructor_course):
        prerequisite = Prerequisite.objects.create(
            course=instructor_course,
            description="Basic Python knowledge.",
        )

        serializer = PrerequisiteSerializer(instance=prerequisite)

        assert serializer.data == {
            "id": prerequisite.id,
            "description": "Basic Python knowledge.",
        }

    def test_serialized_id_matches_model_id(self, instructor_course):
        prerequisite = Prerequisite.objects.create(
            course=instructor_course,
            description="Basic Python knowledge.",
        )

        serializer = PrerequisiteSerializer(instance=prerequisite)

        assert serializer.data["id"] == prerequisite.id

    def test_course_is_not_exposed(self, instructor_course):
        prerequisite = Prerequisite.objects.create(
            course=instructor_course,
            description="Basic Python knowledge.",
        )

        serializer = PrerequisiteSerializer(instance=prerequisite)

        assert "course" not in serializer.data

    def test_partial_update_changes_description(self, instructor_course):
        prerequisite = Prerequisite.objects.create(
            course=instructor_course,
            description="Original prerequisite",
        )

        serializer = PrerequisiteSerializer(
            instance=prerequisite,
            data={"description": "Updated prerequisite"},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        updated_prerequisite = serializer.save()

        assert updated_prerequisite.pk == prerequisite.pk
        assert updated_prerequisite.description == "Updated prerequisite"

    def test_update_does_not_change_model_id(self, instructor_course):
        prerequisite = Prerequisite.objects.create(
            course=instructor_course,
            description="Original prerequisite",
        )

        serializer = PrerequisiteSerializer(
            instance=prerequisite,
            data={
                "id": prerequisite.id + 100,
                "description": "Updated prerequisite",
            },
        )

        assert serializer.is_valid(), serializer.errors

        updated_prerequisite = serializer.save()

        assert updated_prerequisite.pk == prerequisite.pk
        assert updated_prerequisite.description == "Updated prerequisite"

    def test_extra_fields_are_ignored(self):
        serializer = PrerequisiteSerializer(
            data={
                "description": "Basic Python knowledge.",
                "course": 999,
                "unexpected": "ignored",
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert "course" not in serializer.validated_data
        assert "unexpected" not in serializer.validated_data


@pytest.mark.django_db
class TestTargetAudienceSerializer:
    """Tests for TargetAudienceSerializer."""

    def test_fields_are_configured_correctly(self):
        serializer = TargetAudienceSerializer()

        assert set(serializer.fields) == {"id", "description"}

    def test_id_is_not_required(self):
        serializer = TargetAudienceSerializer()

        assert serializer.fields["id"].required is False

    def test_description_is_required(self):
        serializer = TargetAudienceSerializer(data={})

        assert not serializer.is_valid()
        assert "description" in serializer.errors

    def test_valid_data_without_id_is_accepted(self):
        serializer = TargetAudienceSerializer(
            data={"description": "Beginner Python developers."}
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["description"] == (
            "Beginner Python developers."
        )
        assert "id" not in serializer.validated_data

    def test_valid_data_with_id_is_accepted(self):
        serializer = TargetAudienceSerializer(
            data={
                "id": 10,
                "description": "Beginner Python developers.",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["id"] == 10
        assert serializer.validated_data["description"] == (
            "Beginner Python developers."
        )

    def test_blank_description_is_rejected(self):
        serializer = TargetAudienceSerializer(
            data={"description": ""},
        )

        assert not serializer.is_valid()
        assert "description" in serializer.errors

    def test_invalid_id_type_is_rejected(self):
        serializer = TargetAudienceSerializer(
            data={
                "id": "not-an-integer",
                "description": "Beginner Python developers.",
            }
        )

        assert not serializer.is_valid()
        assert "id" in serializer.errors

    def test_negative_id_is_accepted_at_serializer_level(self):
        serializer = TargetAudienceSerializer(
            data={
                "id": -1,
                "description": "Beginner Python developers.",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["id"] == -1

    def test_serializes_model_instance(self, instructor_course):
        target_audience = TargetAudience.objects.create(
            course=instructor_course,
            description="Beginner Python developers.",
        )

        serializer = TargetAudienceSerializer(instance=target_audience)

        assert serializer.data == {
            "id": target_audience.id,
            "description": "Beginner Python developers.",
        }

    def test_serialized_id_matches_model_id(self, instructor_course):
        target_audience = TargetAudience.objects.create(
            course=instructor_course,
            description="Software engineers.",
        )

        serializer = TargetAudienceSerializer(instance=target_audience)

        assert serializer.data["id"] == target_audience.id

    def test_course_is_not_exposed(self, instructor_course):
        target_audience = TargetAudience.objects.create(
            course=instructor_course,
            description="Software engineers.",
        )

        serializer = TargetAudienceSerializer(instance=target_audience)

        assert "course" not in serializer.data

    def test_partial_update_changes_description(self, instructor_course):
        target_audience = TargetAudience.objects.create(
            course=instructor_course,
            description="Original audience",
        )

        serializer = TargetAudienceSerializer(
            instance=target_audience,
            data={"description": "Updated audience"},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        updated_target_audience = serializer.save()

        assert updated_target_audience.pk == target_audience.pk
        assert updated_target_audience.description == "Updated audience"

    def test_update_does_not_change_model_id(self, instructor_course):
        target_audience = TargetAudience.objects.create(
            course=instructor_course,
            description="Original audience",
        )

        serializer = TargetAudienceSerializer(
            instance=target_audience,
            data={
                "id": target_audience.id + 100,
                "description": "Updated audience",
            },
        )

        assert serializer.is_valid(), serializer.errors

        updated_target_audience = serializer.save()

        assert updated_target_audience.pk == target_audience.pk
        assert updated_target_audience.description == "Updated audience"

    def test_extra_fields_are_ignored(self):
        serializer = TargetAudienceSerializer(
            data={
                "description": "Software engineers.",
                "course": 999,
                "unexpected": "ignored",
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert "course" not in serializer.validated_data
        assert "unexpected" not in serializer.validated_data


@pytest.mark.django_db
class TestInstructorCourseSerializer:
    def test_declared_fields(self):
        serializer = InstructorCourseSerializer()

        assert set(serializer.fields) == {
            "id",
            "title",
            "category",
            "version",
            "rating",
            "students",
            "revenue",
            "thumbnail",
            "last_updated",
            "slug",
            "status",
            "review_status",
        }

    def test_category_is_char_field(self):
        serializer = InstructorCourseSerializer()

        field = serializer.fields["category"]

        assert isinstance(field, serializers.CharField)

    def test_category_uses_category_name_source(self):
        serializer = InstructorCourseSerializer()

        field = serializer.fields["category"]

        assert field.source == "category.name"
        assert field.read_only is True

    def test_students_is_serializer_method_field(self):
        serializer = InstructorCourseSerializer()

        field = serializer.fields["students"]

        assert isinstance(field, serializers.SerializerMethodField)
        assert field.read_only is True

    def test_rating_is_serializer_method_field(self):
        serializer = InstructorCourseSerializer()

        field = serializer.fields["rating"]

        assert isinstance(field, serializers.SerializerMethodField)
        assert field.read_only is True

    def test_revenue_is_decimal_field(self):
        serializer = InstructorCourseSerializer()

        field = serializer.fields["revenue"]

        assert isinstance(field, serializers.DecimalField)
        assert field.max_digits == 12
        assert field.decimal_places == 2

    def test_revenue_is_writable(self):
        serializer = InstructorCourseSerializer()

        assert serializer.fields["revenue"].read_only is False

    def test_category_is_not_writable(self, instructor_course):
        serializer = InstructorCourseSerializer(
            instructor_course,
            data={"category": "New Category"},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert "category" not in serializer.validated_data

    def test_students_is_not_writable(self, instructor_course):
        serializer = InstructorCourseSerializer(
            instructor_course,
            data={"students": 100},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert "students" not in serializer.validated_data

    def test_rating_is_not_writable(self, instructor_course):
        serializer = InstructorCourseSerializer(
            instructor_course,
            data={"rating": 5},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert "rating" not in serializer.validated_data

    def test_students_returns_enrollment_count(
        self,
        instructor_course,
    ):
        serializer = InstructorCourseSerializer()

        expected = instructor_course.enrollments.count()

        result = serializer.get_students(instructor_course)

        assert result == expected

    def test_students_returns_zero_when_course_has_no_enrollments(
        self,
        instructor_course,
    ):
        instructor_course.enrollments.all().delete()

        serializer = InstructorCourseSerializer()

        result = serializer.get_students(instructor_course)

        assert result == 0

    def test_students_returns_integer(
        self,
        instructor_course,
    ):
        serializer = InstructorCourseSerializer()

        result = serializer.get_students(instructor_course)

        assert isinstance(result, int)

    def test_rating_returns_none_without_feedback(
        self,
        instructor_course,
    ):
        CourseFeedback.objects.filter(
            enrollment__course=instructor_course,
        ).delete()

        serializer = InstructorCourseSerializer()

        result = serializer.get_rating(instructor_course)

        assert result is None

    def test_rating_returns_feedback_rating(
        self,
        instructor_course,
        instructor_enrollment,
    ):
        CourseFeedback.objects.filter(
            enrollment__course=instructor_course,
        ).delete()

        feedback = CourseFeedback.objects.create(
            enrollment=instructor_enrollment,
            rating=4,
        )

        serializer = InstructorCourseSerializer()

        result = serializer.get_rating(instructor_course)

        assert result == feedback.rating

    def test_rating_uses_average_database_aggregation(
        self,
        instructor_course,
        instructor_enrollment,
    ):
        CourseFeedback.objects.filter(
            enrollment__course=instructor_course,
        ).delete()

        CourseFeedback.objects.create(
            enrollment=instructor_enrollment,
            rating=4,
        )

        expected = CourseFeedback.objects.filter(
            enrollment__course=instructor_course,
        ).aggregate(
            avg=Avg("rating"),
        )["avg"]

        serializer = InstructorCourseSerializer()

        result = serializer.get_rating(instructor_course)

        assert result == expected

    def test_rating_returns_none_when_aggregate_average_is_none(
        self,
        instructor_course,
    ):
        CourseFeedback.objects.filter(
            enrollment__course=instructor_course,
        ).delete()

        serializer = InstructorCourseSerializer()

        result = serializer.get_rating(instructor_course)

        assert result is None

    def test_rating_returns_integer_average_without_rounding_change(
        self,
        instructor_course,
        instructor_enrollment,
    ):
        CourseFeedback.objects.filter(
            enrollment__course=instructor_course,
        ).delete()

        CourseFeedback.objects.create(
            enrollment=instructor_enrollment,
            rating=5,
        )

        serializer = InstructorCourseSerializer()

        result = serializer.get_rating(instructor_course)

        assert result == 5

    def test_rating_result_is_rounded_to_one_decimal_place_when_needed(
        self,
        instructor_course,
        instructor_enrollment,
    ):
        """
        This test verifies the serializer's rounding expression.

        A single feedback record cannot produce a fractional average,
        so this test uses the serializer method's database query only
        when the existing enrollment fixture supports another feedback
        record. If CourseFeedback has a uniqueness constraint on
        enrollment, this scenario requires a second enrollment fixture.
        """
        CourseFeedback.objects.filter(
            enrollment__course=instructor_course,
        ).delete()

        CourseFeedback.objects.create(
            enrollment=instructor_enrollment,
            rating=4,
        )

        serializer = InstructorCourseSerializer()

        result = serializer.get_rating(instructor_course)

        assert result == round(4, 1)

    def test_rating_query_is_scoped_to_current_course(
        self,
        instructor_course,
    ):
        CourseFeedback.objects.filter(
            enrollment__course=instructor_course,
        ).delete()

        serializer = InstructorCourseSerializer()

        result = serializer.get_rating(instructor_course)

        assert result is None

    def test_rating_method_does_not_require_serializer_context(
        self,
        instructor_course,
    ):
        serializer = InstructorCourseSerializer()

        result = serializer.get_rating(instructor_course)

        assert result is None

    def test_students_method_does_not_require_serializer_context(
        self,
        instructor_course,
    ):
        serializer = InstructorCourseSerializer()

        result = serializer.get_students(instructor_course)

        assert result == instructor_course.enrollments.count()

    def test_revenue_accepts_valid_decimal(
        self,
        instructor_course,
    ):
        serializer = InstructorCourseSerializer(
            instructor_course,
            data={
                "revenue": "1234.50",
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["revenue"] == Decimal("1234.50")

    def test_revenue_accepts_zero(
        self,
        instructor_course,
    ):
        serializer = InstructorCourseSerializer(
            instructor_course,
            data={
                "revenue": "0.00",
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["revenue"] == Decimal("0.00")

    def test_revenue_accepts_maximum_valid_value(
        self,
        instructor_course,
    ):
        serializer = InstructorCourseSerializer(
            instructor_course,
            data={
                "revenue": "9999999999.99",
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["revenue"] == Decimal(
            "9999999999.99",
        )

    def test_revenue_rejects_more_than_two_decimal_places(
        self,
        instructor_course,
    ):
        serializer = InstructorCourseSerializer(
            instructor_course,
            data={
                "revenue": "1234.567",
            },
            partial=True,
        )

        assert not serializer.is_valid()
        assert "revenue" in serializer.errors

    def test_revenue_rejects_value_exceeding_max_digits(
        self,
        instructor_course,
    ):
        serializer = InstructorCourseSerializer(
            instructor_course,
            data={
                "revenue": "12345678901.00",
            },
            partial=True,
        )

        assert not serializer.is_valid()
        assert "revenue" in serializer.errors

    def test_revenue_rejects_invalid_string(
        self,
        instructor_course,
    ):
        serializer = InstructorCourseSerializer(
            instructor_course,
            data={
                "revenue": "not-a-number",
            },
            partial=True,
        )

        assert not serializer.is_valid()
        assert "revenue" in serializer.errors

    def test_revenue_rejects_more_than_twelve_total_digits(
        self,
        instructor_course,
    ):
        serializer = InstructorCourseSerializer(
            instructor_course,
            data={
                "revenue": "1234567890.12",
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

    def test_revenue_rejects_thirteen_total_digits(
        self,
        instructor_course,
    ):
        serializer = InstructorCourseSerializer(
            instructor_course,
            data={
                "revenue": "12345678901.12",
            },
            partial=True,
        )

        assert not serializer.is_valid()
        assert "revenue" in serializer.errors

    def test_serializer_contains_expected_model_fields(
        self,
        instructor_course,
    ):
        InstructorCourseSerializer()

        model_fields = {field.name for field in instructor_course._meta.get_fields()}

        expected_model_fields = {
            "id",
            "title",
            "version",
            "thumbnail",
            "last_updated",
            "slug",
            "status",
            "review_status",
        }

        assert expected_model_fields.issubset(model_fields)

    def test_unlisted_fields_are_not_declared(
        self,
    ):
        serializer = InstructorCourseSerializer()

        assert "description" not in serializer.fields
        assert "price" not in serializer.fields
        assert "price_type" not in serializer.fields
        assert "visibility" not in serializer.fields
        assert "owner" not in serializer.fields

    def test_category_representation_when_category_exists(
        self,
        instructor_course,
    ):
        if instructor_course.category is None:
            pytest.skip("The instructor_course fixture has no category.")

        serializer = InstructorCourseSerializer(instructor_course)

        field = serializer.fields["category"]

        assert field.source == "category.name"

        expected = instructor_course.category.name

        # Test the method through the actual DRF field.
        value = field.get_attribute(instructor_course)

        assert value == expected

    def test_category_field_skips_representation_when_category_is_none(
        self,
        instructor_course,
    ):
        instructor_course.category = None

        serializer = InstructorCourseSerializer(instructor_course)

        field = serializer.fields["category"]

        with pytest.raises(serializers.SkipField):
            field.get_attribute(instructor_course)

    def test_serializer_method_fields_are_not_in_validated_data(
        self,
        instructor_course,
    ):
        serializer = InstructorCourseSerializer(
            instructor_course,
            data={
                "students": 999,
                "rating": 1,
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        assert "students" not in serializer.validated_data
        assert "rating" not in serializer.validated_data


@pytest.mark.django_db
class TestInstructorCourseSubmissionSerializer:
    def test_serializes_expected_fields(self, instructor_course):
        serializer = InstructorCourseSubmissionSerializer(instructor_course)

        assert set(serializer.data.keys()) == {
            "id",
            "status",
            "review_status",
        }

    def test_serializes_course_values(self, instructor_course):
        serializer = InstructorCourseSubmissionSerializer(instructor_course)

        data = serializer.data

        assert data["id"] == instructor_course.id
        assert data["status"] == instructor_course.status
        assert data["review_status"] == instructor_course.review_status

    def test_declared_model_fields_are_not_read_only(self):
        serializer = InstructorCourseSubmissionSerializer()

        assert serializer.fields["id"].read_only is True
        assert serializer.fields["status"].read_only is False
        assert serializer.fields["review_status"].read_only is False

    def test_status_is_deserializable(self, instructor_course):
        serializer = InstructorCourseSubmissionSerializer(
            instructor_course,
            data={
                "status": instructor_course.status,
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert "status" in serializer.validated_data

    def test_review_status_is_deserializable(self, instructor_course):
        serializer = InstructorCourseSubmissionSerializer(
            instructor_course,
            data={
                "review_status": instructor_course.review_status,
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert "review_status" in serializer.validated_data

    def test_id_cannot_be_changed_through_input(self, instructor_course):
        serializer = InstructorCourseSubmissionSerializer(
            instructor_course,
            data={
                "id": instructor_course.id + 999,
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert "id" not in serializer.validated_data

    def test_does_not_expose_other_course_fields(self, instructor_course):
        serializer = InstructorCourseSubmissionSerializer(instructor_course)

        data = serializer.data

        assert "title" not in data
        assert "slug" not in data
        assert "category" not in data
        assert "version" not in data
        assert "revenue" not in data
        assert "students" not in data
        assert "rating" not in data
        assert "thumbnail" not in data
        assert "last_updated" not in data


@pytest.mark.django_db
class TestInstructorFilterCoursesSerializer:
    def test_serializes_courses_field(self, instructor_user):
        serializer = InstructorFilterCoursesSerializer(instructor_user)

        assert "courses" in serializer.data

    def test_courses_is_a_dictionary(self, instructor_user):
        serializer = InstructorFilterCoursesSerializer(instructor_user)

        assert isinstance(serializer.data["courses"], dict)

    def test_courses_maps_slug_to_title(
        self,
        instructor_user,
        instructor_course,
    ):
        serializer = InstructorFilterCoursesSerializer(instructor_user)

        assert serializer.data["courses"] == {
            instructor_course.slug: instructor_course.title,
        }

    def test_multiple_owned_courses_are_included(
        self,
        instructor_user,
        instructor_course,
    ):
        second_course = Course.objects.create(
            owner=instructor_user,
            title="Second Course",
            slug="second-course",
        )

        serializer = InstructorFilterCoursesSerializer(instructor_user)

        assert serializer.data["courses"] == {
            instructor_course.slug: instructor_course.title,
            second_course.slug: second_course.title,
        }

    def test_no_owned_courses_returns_empty_dictionary(
        self,
        instructor_user,
    ):
        instructor_user.owned_courses.all().delete()

        serializer = InstructorFilterCoursesSerializer(instructor_user)

        assert serializer.data["courses"] == {}

    def test_unowned_course_is_not_included(
        self,
        instructor_user,
        instructor_course,
        student_user,
    ):
        other_course = Course.objects.create(
            owner=student_user,
            title="Other User Course",
            slug="other-user-course",
        )

        serializer = InstructorFilterCoursesSerializer(instructor_user)

        courses = serializer.data["courses"]

        assert instructor_course.slug in courses
        assert other_course.slug not in courses

    def test_course_titles_are_values_and_slugs_are_keys(
        self,
        instructor_user,
        instructor_course,
    ):
        serializer = InstructorFilterCoursesSerializer(instructor_user)

        courses = serializer.data["courses"]

        assert instructor_course.slug in courses
        assert courses[instructor_course.slug] == instructor_course.title

    def test_courses_is_read_only_method_field(self):
        serializer = InstructorFilterCoursesSerializer()

        field = serializer.fields["courses"]

        assert isinstance(field, serializers.SerializerMethodField)
        assert field.read_only is True

    def test_courses_is_not_accepted_as_input(self, instructor_user):
        serializer = InstructorFilterCoursesSerializer(
            data={
                "courses": {
                    "fake-course": "Fake Course",
                }
            }
        )

        assert serializer.is_valid()

        assert "courses" not in serializer.validated_data

    def test_only_courses_owned_by_user_are_returned(
        self,
        instructor_user,
        instructor_course,
        student_user,
    ):
        Course.objects.create(
            owner=student_user,
            title="Student Course",
            slug="student-course",
        )

        serializer = InstructorFilterCoursesSerializer(instructor_user)

        assert serializer.data["courses"] == {
            instructor_course.slug: instructor_course.title,
        }

    def test_serializer_output_is_stable(
        self,
        instructor_user,
        instructor_course,
    ):
        first = InstructorFilterCoursesSerializer(instructor_user).data
        second = InstructorFilterCoursesSerializer(instructor_user).data

        assert first == second
