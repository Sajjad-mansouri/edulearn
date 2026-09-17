import pytest

from courses.api.serializers.course import CourseFeatureSerializer
from courses.models.course import CourseFeature

pytestmark = pytest.mark.django_db


class TestCourseFeatureSerializer:
    @pytest.fixture
    def course_feature(self, course):
        return CourseFeature.objects.create(
            course=course,
            icon="certificate",
            text="Learn Django from fundamentals to advanced concepts.",
        )

    @pytest.fixture
    def serializer(self, course_feature):
        return CourseFeatureSerializer(course_feature)

    def test_serializes_expected_fields(self, serializer):
        assert set(serializer.data.keys()) == {
            "icon",
            "text",
        }

    def test_serializes_icon(self, serializer, course_feature):
        assert serializer.data["icon"] == course_feature.icon

    def test_serializes_text(self, serializer, course_feature):
        assert serializer.data["text"] == course_feature.text

    def test_serializes_exact_values(self, serializer):
        assert serializer.data == {
            "icon": "certificate",
            "text": "Learn Django from fundamentals to advanced concepts.",
        }

    def test_icon_is_writable(self, course_feature):
        serializer = CourseFeatureSerializer(
            course_feature,
            data={"icon": "video"},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["icon"] == "video"

    def test_text_is_writable(self, course_feature):
        serializer = CourseFeatureSerializer(
            course_feature,
            data={"text": "Updated feature description."},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["text"] == "Updated feature description."

    def test_updates_icon_and_text(self, course_feature):
        serializer = CourseFeatureSerializer(
            course_feature,
            data={
                "icon": "code",
                "text": "Practice Django through real projects.",
            },
        )

        assert serializer.is_valid(), serializer.errors

        updated_feature = serializer.save()

        assert updated_feature.icon == "code"
        assert updated_feature.text == "Practice Django through real projects."

    def test_serializes_multiple_features(self, course):
        first_feature = CourseFeature.objects.create(
            course=course,
            icon="video",
            text="Watch high-quality video lessons.",
        )
        second_feature = CourseFeature.objects.create(
            course=course,
            icon="project",
            text="Build practical projects.",
        )

        serializer = CourseFeatureSerializer(
            [first_feature, second_feature],
            many=True,
        )

        assert serializer.data == [
            {
                "icon": "video",
                "text": "Watch high-quality video lessons.",
            },
            {
                "icon": "project",
                "text": "Build practical projects.",
            },
        ]

    def test_serializer_does_not_expose_course_field(
        self,
        serializer,
    ):
        assert "course" not in serializer.data

    def test_serializer_does_not_modify_instance(
        self,
        course_feature,
        serializer,
    ):
        original_icon = course_feature.icon
        original_text = course_feature.text

        course_feature.refresh_from_db()

        assert course_feature.icon == original_icon
        assert course_feature.text == original_text
