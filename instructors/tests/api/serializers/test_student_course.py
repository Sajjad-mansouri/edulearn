import pytest
from rest_framework import serializers

from courses.models import (
    Category,
    CourseFeature,
    LearningOutcome,
    Prerequisite,
    TargetAudience,
)
from instructors.api.serializers import CourseSerializer


@pytest.mark.django_db
class TestCourseSerializer:
    def test_declared_fields(self):
        serializer = CourseSerializer()

        expected_fields = {
            "id",
            "title",
            "subtitle",
            "short_description",
            "category",
            "level",
            "language",
            "duration",
            "visibility",
            "description",
            "price_type",
            "price",
            "price_discount",
            "thumbnail",
            "promotional_video",
            "course_trailer",
            "version",
            "version_note",
            "seo_title",
            "seo_description",
            "tags",
            "learning_outcomes",
            "prerequisites",
            "target_audiences",
            "features",
            "sections",
            "attachments",
        }

        assert set(serializer.fields) == expected_fields

    def test_category_is_slug_related_field(self):
        serializer = CourseSerializer()

        category = serializer.fields["category"]

        assert isinstance(category, serializers.SlugRelatedField)
        assert category.slug_field == "slug"

    def test_nested_relationships_are_many(self):
        serializer = CourseSerializer()

        assert serializer.fields["tags"].many is True
        assert serializer.fields["learning_outcomes"].many is True
        assert serializer.fields["prerequisites"].many is True
        assert serializer.fields["target_audiences"].many is True
        assert serializer.fields["features"].many is True
        assert serializer.fields["sections"].many is True
        assert serializer.fields["attachments"].many is True

    def test_attachments_are_optional(self):
        serializer = CourseSerializer()

        assert serializer.fields["attachments"].required is False

    def test_nested_course_relationships_are_required(self):
        serializer = CourseSerializer()

        assert serializer.fields["tags"].required is True
        assert serializer.fields["learning_outcomes"].required is True
        assert serializer.fields["prerequisites"].required is True
        assert serializer.fields["target_audiences"].required is True
        assert serializer.fields["features"].required is True
        assert serializer.fields["sections"].required is True

    def test_serializes_simple_course_fields(self, instructor_course):
        serializer = CourseSerializer(instructor_course)

        data = serializer.data

        assert data["id"] == instructor_course.id
        assert data["title"] == instructor_course.title
        assert data["subtitle"] == instructor_course.subtitle
        assert data["short_description"] == instructor_course.short_description
        assert data["language"] == instructor_course.language
        assert data["visibility"] == instructor_course.visibility
        assert data["description"] == instructor_course.description
        assert data["price_type"] == instructor_course.price_type

        if instructor_course.price is None:
            assert data["price"] is None
        else:
            assert data["price"] == format(instructor_course.price, ".2f")

    def test_serializes_category_using_slug(self, instructor_course):
        category = Category.objects.create(
            name="Python",
            slug="python",
        )

        instructor_course.category = category
        instructor_course.save(update_fields=["category"])

        serializer = CourseSerializer(instructor_course)

        assert serializer.data["category"] == category.slug

    def test_serializes_null_category(self, instructor_course):
        instructor_course.category = None
        instructor_course.save(update_fields=["category"])

        serializer = CourseSerializer(instructor_course)

        assert serializer.data["category"] is None

    def test_serializes_empty_nested_relationships(self, instructor_course):
        instructor_course.tags.clear()
        instructor_course.learning_outcomes.all().delete()
        instructor_course.prerequisites.all().delete()
        instructor_course.target_audiences.all().delete()
        instructor_course.features.all().delete()
        instructor_course.sections.all().delete()

        serializer = CourseSerializer(instructor_course)

        data = serializer.data

        assert data["tags"] == []
        assert data["learning_outcomes"] == []
        assert data["prerequisites"] == []
        assert data["target_audiences"] == []
        assert data["features"] == []
        assert data["sections"] == []

    def test_serializes_tags(self, instructor_course):
        serializer = CourseSerializer(instructor_course)

        actual = serializer.data["tags"]

        expected = [
            {
                "id": tag.id,
                "name": tag.name,
            }
            for tag in instructor_course.tags.all()
        ]

        assert actual == expected

    def test_serializes_learning_outcomes(self, instructor_course):
        outcome = LearningOutcome.objects.create(
            course=instructor_course,
            description="Build scalable Django applications.",
        )

        serializer = CourseSerializer(instructor_course)

        assert serializer.data["learning_outcomes"] == [
            {
                "id": outcome.id,
                "description": outcome.description,
            }
        ]

    def test_serializes_prerequisites(self, instructor_course):
        prerequisite = Prerequisite.objects.create(
            course=instructor_course,
            description="Basic Python knowledge.",
        )

        serializer = CourseSerializer(instructor_course)

        assert serializer.data["prerequisites"] == [
            {
                "id": prerequisite.id,
                "description": prerequisite.description,
            }
        ]

    def test_serializes_target_audiences(self, instructor_course):
        target_audience = TargetAudience.objects.create(
            course=instructor_course,
            description="Python developers.",
        )

        serializer = CourseSerializer(instructor_course)

        assert serializer.data["target_audiences"] == [
            {
                "id": target_audience.id,
                "description": target_audience.description,
            }
        ]

    def test_serializes_features(self, instructor_course):
        feature = CourseFeature.objects.create(
            course=instructor_course,
            icon="certificate",
            text="Certificate included",
        )

        serializer = CourseSerializer(instructor_course)

        assert {
            "icon": feature.icon,
            "text": feature.text,
        } in serializer.data["features"]

    def test_serializes_multiple_features(self, instructor_course):
        first = CourseFeature.objects.create(
            course=instructor_course,
            icon="certificate",
            text="Certificate included",
        )
        second = CourseFeature.objects.create(
            course=instructor_course,
            icon="download",
            text="Downloadable resources",
        )

        serializer = CourseSerializer(instructor_course)

        serialized_features = serializer.data["features"]

        assert {
            "icon": first.icon,
            "text": first.text,
        } in serialized_features
        assert {
            "icon": second.icon,
            "text": second.text,
        } in serialized_features

    def test_category_slug_is_accepted_on_deserialization(
        self,
        instructor_course,
    ):
        category = Category.objects.create(
            name="Python",
            slug="python",
        )

        serializer = CourseSerializer(
            instance=instructor_course,
            data={"category": category.slug},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["category"] == category

    def test_invalid_category_slug_is_rejected(self, instructor_course):
        serializer = CourseSerializer(
            instance=instructor_course,
            data={"category": "does-not-exist"},
            partial=True,
        )

        assert not serializer.is_valid()
        assert "category" in serializer.errors

    def test_category_primary_key_is_not_accepted_as_slug(
        self,
        instructor_course,
    ):
        category = Category.objects.create(
            name="Python",
            slug="python",
        )

        serializer = CourseSerializer(
            instance=instructor_course,
            data={"category": category.pk},
            partial=True,
        )

        assert not serializer.is_valid()
        assert "category" in serializer.errors

    def test_category_object_is_not_accepted_instead_of_slug(
        self,
        instructor_course,
    ):
        category = Category.objects.create(
            name="Python",
            slug="python",
        )

        serializer = CourseSerializer(
            instance=instructor_course,
            data={"category": {"id": category.pk}},
            partial=True,
        )

        assert not serializer.is_valid()
        assert "category" in serializer.errors

    def test_partial_update_accepts_category_slug(
        self,
        instructor_course,
    ):
        category = Category.objects.create(
            name="Django",
            slug="django",
        )

        serializer = CourseSerializer(
            instance=instructor_course,
            data={"category": category.slug},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        updated_course = serializer.save()

        assert updated_course.category == category

    def test_partial_update_simple_field(self, instructor_course):
        new_title = "Updated Django Course"

        serializer = CourseSerializer(
            instance=instructor_course,
            data={"title": new_title},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        updated_course = serializer.save()

        assert updated_course.title == new_title

    def test_partial_update_preserves_unspecified_fields(
        self,
        instructor_course,
    ):
        original_subtitle = instructor_course.subtitle
        original_description = instructor_course.description

        serializer = CourseSerializer(
            instance=instructor_course,
            data={"title": "Updated title"},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        updated_course = serializer.save()

        assert updated_course.title == "Updated title"
        assert updated_course.subtitle == original_subtitle
        assert updated_course.description == original_description

    def test_unknown_input_field_is_ignored(self, instructor_course):
        serializer = CourseSerializer(
            instance=instructor_course,
            data={
                "title": "Updated title",
                "unknown_field": "unexpected",
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert "unknown_field" not in serializer.validated_data

    def test_course_id_does_not_change_identity(self, instructor_course):
        original_id = instructor_course.id

        serializer = CourseSerializer(
            instance=instructor_course,
            data={
                "id": original_id + 999999,
                "title": "Updated title",
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        updated_course = serializer.save()

        assert updated_course.pk == original_id

    def test_to_representation_returns_dictionary(self, instructor_course):
        serializer = CourseSerializer(instructor_course)

        assert isinstance(serializer.data, dict)

    def test_all_declared_fields_are_present_in_representation(
        self,
        instructor_course,
    ):
        serializer = CourseSerializer(instructor_course)

        assert set(serializer.data) == set(serializer.fields)

    def test_owner_is_not_exposed(self, instructor_course):
        serializer = CourseSerializer(instructor_course)

        assert "owner" not in serializer.data

    def test_status_is_not_exposed(self, instructor_course):
        serializer = CourseSerializer(instructor_course)

        assert "status" not in serializer.data

    def test_review_status_is_not_exposed(self, instructor_course):
        serializer = CourseSerializer(instructor_course)

        assert "review_status" not in serializer.data

    def test_nested_relationship_counts_match_database(
        self,
        instructor_course,
    ):
        serializer = CourseSerializer(instructor_course)

        data = serializer.data

        assert len(data["tags"]) == instructor_course.tags.count()
        assert (
            len(data["learning_outcomes"])
            == instructor_course.learning_outcomes.count()
        )
        assert len(data["prerequisites"]) == instructor_course.prerequisites.count()
        assert (
            len(data["target_audiences"]) == instructor_course.target_audiences.count()
        )
        assert len(data["features"]) == instructor_course.features.count()
        assert len(data["sections"]) == instructor_course.sections.count()

    def test_repeated_serialization_is_consistent(self, instructor_course):
        first = CourseSerializer(instructor_course).data
        second = CourseSerializer(instructor_course).data

        assert first == second
