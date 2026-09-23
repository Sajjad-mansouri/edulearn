import pytest

from courses.api.serializers.course import CourseMetadataSerializer
from courses.models import Course

pytestmark = pytest.mark.django_db


class TestCourseMetadataSerializer:
    @pytest.fixture
    def serializer(self, course):
        return CourseMetadataSerializer(course)

    def test_serializes_expected_fields(self, serializer):
        assert set(serializer.data.keys()) == {
            "levels",
            "languages",
        }

    def test_serializes_all_course_levels(self, serializer):
        expected = [
            {
                "label": level.label,
                "value": level.value,
            }
            for level in Course.Level
        ]

        assert serializer.data["levels"] == expected

    def test_serializes_all_course_languages(self, serializer):
        expected = [
            {
                "label": language.label,
                "value": language.value,
            }
            for language in Course.LANGUAGE
        ]

        assert serializer.data["languages"] == expected

    def test_level_metadata_contains_only_label_and_value(
        self,
        serializer,
    ):
        for level in serializer.data["levels"]:
            assert set(level.keys()) == {
                "label",
                "value",
            }

    def test_language_metadata_contains_only_label_and_value(
        self,
        serializer,
    ):
        for language in serializer.data["languages"]:
            assert set(language.keys()) == {
                "label",
                "value",
            }

    def test_level_values_match_course_level_choices(
        self,
        serializer,
    ):
        actual_values = [level["value"] for level in serializer.data["levels"]]

        expected_values = [level.value for level in Course.Level]

        assert actual_values == expected_values

    def test_language_values_match_course_language_choices(
        self,
        serializer,
    ):
        actual_values = [language["value"] for language in serializer.data["languages"]]

        expected_values = [language.value for language in Course.LANGUAGE]

        assert actual_values == expected_values

    def test_level_labels_match_course_level_choices(
        self,
        serializer,
    ):
        actual_labels = [level["label"] for level in serializer.data["levels"]]

        expected_labels = [level.label for level in Course.Level]

        assert actual_labels == expected_labels

    def test_language_labels_match_course_language_choices(
        self,
        serializer,
    ):
        actual_labels = [language["label"] for language in serializer.data["languages"]]

        expected_labels = [language.label for language in Course.LANGUAGE]

        assert actual_labels == expected_labels

    def test_serializer_does_not_depend_on_course_instance_values(
        self,
        course,
    ):
        first_serializer = CourseMetadataSerializer(course)

        course.title = "Completely Different Course"
        course.level = Course.Level.ADVANCED
        course.language = "different"

        second_serializer = CourseMetadataSerializer(course)

        assert first_serializer.data["levels"] == second_serializer.data["levels"]
        assert first_serializer.data["languages"] == second_serializer.data["languages"]
