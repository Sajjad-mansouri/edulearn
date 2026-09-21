# curriculums/tests/api/serializers/test_section.py

import datetime

import pytest
from rest_framework.serializers import ListSerializer

from curriculums.api.serializers import LessonSerializer, SectionSerializer
from curriculums.models import LessonCompletionCriteria, LessonContent


@pytest.fixture
def lesson_content(db, lesson):
    return LessonContent.objects.create(
        lesson=lesson,
        title="Lesson Content",
        content_type=LessonContent.Type.VIDEO,
        order=1,
    )


@pytest.fixture
def completion_criteria(db, lesson):
    return LessonCompletionCriteria.objects.create(
        lesson=lesson,
        criteria_type=LessonCompletionCriteria.CriteriaType.MANUAL,
    )


@pytest.fixture
def section_with_lesson_graph(
    section,
    lesson_content,
    completion_criteria,
):
    return section


class TestSectionSerializerFields:
    def test_contains_expected_fields(self):
        serializer = SectionSerializer()

        assert list(serializer.fields) == [
            "id",
            "title",
            "description",
            "duration",
            "lessons",
        ]

    def test_id_is_not_required(self):
        serializer = SectionSerializer()

        assert serializer.fields["id"].required is False

    def test_title_is_required(self):
        serializer = SectionSerializer()

        assert serializer.fields["title"].required is True

    def test_description_is_not_required(self):
        serializer = SectionSerializer()

        assert serializer.fields["description"].required is False

    def test_duration_is_not_required(self):
        serializer = SectionSerializer()

        assert serializer.fields["duration"].required is False

    def test_duration_allows_null(self):
        serializer = SectionSerializer()

        assert serializer.fields["duration"].allow_null is True

    def test_lessons_is_required(self):
        serializer = SectionSerializer()

        assert serializer.fields["lessons"].required is True

    def test_lessons_is_many_serializer(self):
        serializer = SectionSerializer()

        assert isinstance(
            serializer.fields["lessons"],
            ListSerializer,
        )

    def test_lessons_uses_lesson_serializer_as_child(self):
        serializer = SectionSerializer()

        assert isinstance(
            serializer.fields["lessons"].child,
            LessonSerializer,
        )

    def test_lessons_is_writable(self):
        serializer = SectionSerializer()

        assert serializer.fields["lessons"].read_only is False

    def test_does_not_expose_course(self):
        serializer = SectionSerializer()

        assert "course" not in serializer.fields

    def test_does_not_expose_order(self):
        serializer = SectionSerializer()

        assert "order" not in serializer.fields

    def test_does_not_expose_is_published(self):
        serializer = SectionSerializer()

        assert "is_published" not in serializer.fields


class TestSectionSerializerValidation:
    def test_rejects_empty_payload(self):
        serializer = SectionSerializer(data={})

        assert not serializer.is_valid()

        assert "title" in serializer.errors
        assert "lessons" in serializer.errors

    def test_accepts_minimal_valid_payload(self):
        serializer = SectionSerializer(
            data={
                "title": "Introduction",
                "lessons": [
                    {
                        "title": "Getting Started",
                        "content": {
                            "content_type": LessonContent.Type.VIDEO,
                        },
                        "completion_criteria": {
                            "criteria_type": (
                                LessonCompletionCriteria.CriteriaType.MANUAL
                            ),
                        },
                    },
                ],
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["title"] == "Introduction"
        assert len(serializer.validated_data["lessons"]) == 1

    def test_accepts_id_as_integer(self):
        serializer = SectionSerializer(
            data={
                "id": 10,
                "title": "Introduction",
                "lessons": [
                    {
                        "title": "Getting Started",
                        "content": {
                            "content_type": LessonContent.Type.VIDEO,
                        },
                        "completion_criteria": {
                            "criteria_type": (
                                LessonCompletionCriteria.CriteriaType.MANUAL
                            ),
                        },
                    },
                ],
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["id"] == 10

    def test_coerces_id_from_string(self):
        serializer = SectionSerializer(
            data={
                "id": "25",
                "title": "Introduction",
                "lessons": [
                    {
                        "title": "Getting Started",
                        "content": {
                            "content_type": LessonContent.Type.VIDEO,
                        },
                        "completion_criteria": {
                            "criteria_type": (
                                LessonCompletionCriteria.CriteriaType.MANUAL
                            ),
                        },
                    },
                ],
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["id"] == 25

    @pytest.mark.parametrize(
        "id_value",
        [
            "not-an-integer",
            1.5,
            True,
        ],
    )
    def test_rejects_invalid_id(self, id_value):
        serializer = SectionSerializer(
            data={
                "id": id_value,
                "title": "Introduction",
                "lessons": [],
            }
        )

        assert not serializer.is_valid()
        assert "id" in serializer.errors

    def test_rejects_missing_title(self):
        serializer = SectionSerializer(
            data={
                "lessons": [],
            }
        )

        assert not serializer.is_valid()
        assert "title" in serializer.errors

    def test_rejects_empty_title(self):
        serializer = SectionSerializer(
            data={
                "title": "",
                "lessons": [],
            }
        )

        assert not serializer.is_valid()
        assert "title" in serializer.errors

    def test_accepts_description(self):
        serializer = SectionSerializer(
            data={
                "title": "Introduction",
                "description": "Fundamental concepts.",
                "lessons": [],
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["description"] == ("Fundamental concepts.")

    def test_accepts_empty_description(self):
        serializer = SectionSerializer(
            data={
                "title": "Introduction",
                "description": "",
                "lessons": [],
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["description"] == ""

    def test_description_is_optional(self):
        serializer = SectionSerializer(
            data={
                "title": "Introduction",
                "lessons": [],
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert "description" not in serializer.validated_data

    def test_rejects_null_description(self):
        serializer = SectionSerializer(
            data={
                "title": "Introduction",
                "description": None,
                "lessons": [],
            }
        )

        assert not serializer.is_valid()
        assert "description" in serializer.errors

    def test_accepts_null_duration(self):
        serializer = SectionSerializer(
            data={
                "title": "Introduction",
                "duration": None,
                "lessons": [],
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["duration"] is None

    def test_duration_is_optional(self):
        serializer = SectionSerializer(
            data={
                "title": "Introduction",
                "lessons": [],
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert "duration" not in serializer.validated_data

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (
                "01:30:00",
                datetime.timedelta(hours=1, minutes=30),
            ),
            (
                "00:45:30",
                datetime.timedelta(minutes=45, seconds=30),
            ),
            (
                "00:00:00",
                datetime.timedelta(0),
            ),
        ],
    )
    def test_accepts_valid_duration(self, value, expected):
        serializer = SectionSerializer(
            data={
                "title": "Introduction",
                "duration": value,
                "lessons": [],
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["duration"] == expected

    def test_rejects_invalid_duration(self):
        serializer = SectionSerializer(
            data={
                "title": "Introduction",
                "duration": "not-a-duration",
                "lessons": [],
            }
        )

        assert not serializer.is_valid()
        assert "duration" in serializer.errors


class TestSectionSerializerLessons:
    def test_rejects_missing_lessons(self):
        serializer = SectionSerializer(
            data={
                "title": "Introduction",
            }
        )

        assert not serializer.is_valid()
        assert "lessons" in serializer.errors

    def test_accepts_empty_lessons_list(self):
        serializer = SectionSerializer(
            data={
                "title": "Introduction",
                "lessons": [],
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["lessons"] == []

    def test_accepts_multiple_lessons(self):
        serializer = SectionSerializer(
            data={
                "title": "Introduction",
                "lessons": [
                    {
                        "title": "Lesson One",
                        "content": {
                            "content_type": LessonContent.Type.VIDEO,
                        },
                        "completion_criteria": {
                            "criteria_type": (
                                LessonCompletionCriteria.CriteriaType.MANUAL
                            ),
                        },
                    },
                    {
                        "title": "Lesson Two",
                        "content": {
                            "content_type": LessonContent.Type.ARTICLE,
                        },
                        "completion_criteria": {
                            "criteria_type": (
                                LessonCompletionCriteria.CriteriaType.READ_ARTICLE
                            ),
                        },
                    },
                ],
            }
        )

        assert serializer.is_valid(), serializer.errors

        lessons = serializer.validated_data["lessons"]

        assert len(lessons) == 2
        assert lessons[0]["title"] == "Lesson One"
        assert lessons[1]["title"] == "Lesson Two"

    def test_rejects_invalid_lessons_value(self):
        serializer = SectionSerializer(
            data={
                "title": "Introduction",
                "lessons": "not-a-list",
            }
        )

        assert not serializer.is_valid()
        assert "lessons" in serializer.errors

    def test_rejects_null_lessons(self):
        serializer = SectionSerializer(
            data={
                "title": "Introduction",
                "lessons": None,
            }
        )

        assert not serializer.is_valid()
        assert "lessons" in serializer.errors

    def test_rejects_invalid_nested_lesson(self):
        serializer = SectionSerializer(
            data={
                "title": "Introduction",
                "lessons": [
                    {
                        "title": "Invalid Lesson",
                        "content": {
                            "content_type": "invalid_type",
                        },
                        "completion_criteria": {
                            "criteria_type": (
                                LessonCompletionCriteria.CriteriaType.MANUAL
                            ),
                        },
                    },
                ],
            }
        )

        assert not serializer.is_valid()
        assert "lessons" in serializer.errors

    def test_rejects_lesson_missing_required_fields(self):
        serializer = SectionSerializer(
            data={
                "title": "Introduction",
                "lessons": [
                    {},
                ],
            }
        )

        assert not serializer.is_valid()
        assert "lessons" in serializer.errors

    def test_preserves_nested_lesson_data(self):
        serializer = SectionSerializer(
            data={
                "title": "Introduction",
                "lessons": [
                    {
                        "title": "Getting Started",
                        "description": "First lesson.",
                        "duration": "00:30:00",
                        "is_published": True,
                        "is_preview": True,
                        "content": {
                            "content_type": LessonContent.Type.VIDEO,
                        },
                        "completion_criteria": {
                            "criteria_type": (
                                LessonCompletionCriteria.CriteriaType.WATCH_VIDEO
                            ),
                            "video_watch_percentage": 80,
                        },
                    },
                ],
            }
        )

        assert serializer.is_valid(), serializer.errors

        lesson_data = serializer.validated_data["lessons"][0]

        assert lesson_data["title"] == "Getting Started"
        assert lesson_data["description"] == "First lesson."
        assert lesson_data["duration"] == datetime.timedelta(minutes=30)
        assert lesson_data["is_published"] is True
        assert lesson_data["is_preview"] is True

        assert lesson_data["content"]["content_type"] == (LessonContent.Type.VIDEO)

        assert lesson_data["completion_criteria"]["criteria_type"] == (
            LessonCompletionCriteria.CriteriaType.WATCH_VIDEO
        )

        assert lesson_data["completion_criteria"]["video_watch_percentage"] == 80


class TestSectionSerializerSerialization:
    def test_serializes_expected_fields(
        self,
        section_with_lesson_graph,
    ):
        serializer = SectionSerializer(
            instance=section_with_lesson_graph,
        )

        assert set(serializer.data) == {
            "id",
            "title",
            "description",
            "duration",
            "lessons",
        }

    def test_serializes_section_fields(
        self,
        section_with_lesson_graph,
    ):
        serializer = SectionSerializer(
            instance=section_with_lesson_graph,
        )

        data = serializer.data

        assert data["id"] == section_with_lesson_graph.id
        assert data["title"] == section_with_lesson_graph.title
        assert data["description"] == section_with_lesson_graph.description

    def test_serializes_null_duration(
        self,
        section_with_lesson_graph,
    ):
        section_with_lesson_graph.duration = None

        serializer = SectionSerializer(
            instance=section_with_lesson_graph,
        )

        assert serializer.data["duration"] is None

    def test_serializes_duration(
        self,
        section_with_lesson_graph,
    ):
        section_with_lesson_graph.duration = datetime.timedelta(
            hours=1,
            minutes=30,
            seconds=15,
        )

        serializer = SectionSerializer(
            instance=section_with_lesson_graph,
        )

        assert serializer.data["duration"] == "01:30:15"

    def test_serializes_related_lessons(
        self,
        section_with_lesson_graph,
    ):
        serializer = SectionSerializer(
            instance=section_with_lesson_graph,
        )

        lessons = serializer.data["lessons"]

        assert len(lessons) == 1
        assert lessons[0]["id"] == section_with_lesson_graph.lessons.first().id
        assert lessons[0]["title"] == section_with_lesson_graph.lessons.first().title

    def test_serializes_nested_lesson_fields(
        self,
        section_with_lesson_graph,
    ):
        serializer = SectionSerializer(
            instance=section_with_lesson_graph,
        )

        lesson_data = serializer.data["lessons"][0]

        assert "id" in lesson_data
        assert "title" in lesson_data
        assert "description" in lesson_data
        assert "duration" in lesson_data
        assert "content" in lesson_data
        assert "is_published" in lesson_data
        assert "is_preview" in lesson_data
        assert "completion_criteria" in lesson_data

    def test_serializes_empty_lessons_relation(
        self,
        course,
    ):
        empty_section = course.sections.create(
            title="Empty Section",
        )

        serializer = SectionSerializer(
            instance=empty_section,
        )

        assert serializer.data["lessons"] == []

    def test_serializes_multiple_lessons(
        self,
        section,
        lesson,
        lesson_content,
        completion_criteria,
    ):
        second_lesson = section.lessons.create(
            title="Second Lesson",
            slug="second-lesson",
            order=2,
        )

        LessonContent.objects.create(
            lesson=second_lesson,
            title="Second Content",
            content_type=LessonContent.Type.ARTICLE,
            order=1,
        )

        LessonCompletionCriteria.objects.create(
            lesson=second_lesson,
            criteria_type=(LessonCompletionCriteria.CriteriaType.READ_ARTICLE),
        )

        serializer = SectionSerializer(instance=section)

        lessons = serializer.data["lessons"]

        assert len(lessons) == 2
        assert lessons[0]["id"] == lesson.id
        assert lessons[1]["id"] == second_lesson.id


class TestSectionSerializerPartialUpdates:
    def test_partial_update_accepts_empty_data(self, section):
        serializer = SectionSerializer(
            instance=section,
            data={},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data == {}

    def test_partial_update_accepts_title(self, section):
        serializer = SectionSerializer(
            instance=section,
            data={
                "title": "Updated Section",
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["title"] == "Updated Section"

    def test_partial_update_accepts_description(self, section):
        serializer = SectionSerializer(
            instance=section,
            data={
                "description": "Updated description.",
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["description"] == ("Updated description.")

    def test_partial_update_accepts_empty_description(self, section):
        serializer = SectionSerializer(
            instance=section,
            data={
                "description": "",
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["description"] == ""

    def test_partial_update_rejects_null_description(self, section):
        serializer = SectionSerializer(
            instance=section,
            data={
                "description": None,
            },
            partial=True,
        )

        assert not serializer.is_valid()
        assert "description" in serializer.errors

    def test_partial_update_accepts_duration(self, section):
        serializer = SectionSerializer(
            instance=section,
            data={
                "duration": "00:45:00",
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["duration"] == (datetime.timedelta(minutes=45))

    def test_partial_update_accepts_null_duration(self, section):
        serializer = SectionSerializer(
            instance=section,
            data={
                "duration": None,
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["duration"] is None

    def test_partial_update_accepts_lessons(self, section):
        serializer = SectionSerializer(
            instance=section,
            data={
                "lessons": [
                    {
                        "title": "Updated Lesson",
                        "content": {
                            "content_type": LessonContent.Type.ARTICLE,
                        },
                        "completion_criteria": {
                            "criteria_type": (
                                LessonCompletionCriteria.CriteriaType.READ_ARTICLE
                            ),
                        },
                    },
                ],
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        lessons = serializer.validated_data["lessons"]

        assert len(lessons) == 1
        assert lessons[0]["title"] == "Updated Lesson"

    def test_partial_update_does_not_require_title(self, section):
        serializer = SectionSerializer(
            instance=section,
            data={
                "description": "Updated description.",
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert "title" not in serializer.validated_data

    def test_partial_update_does_not_require_lessons(self, section):
        serializer = SectionSerializer(
            instance=section,
            data={
                "description": "Updated description.",
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert "lessons" not in serializer.validated_data


class TestSectionSerializerNestedComposition:
    def test_lessons_is_a_list_serializer(self):
        serializer = SectionSerializer()

        field = serializer.fields["lessons"]

        assert isinstance(field, ListSerializer)

    def test_lessons_child_is_lesson_serializer(self):
        serializer = SectionSerializer()

        field = serializer.fields["lessons"]

        assert isinstance(field.child, LessonSerializer)

    def test_lessons_is_not_read_only(self):
        serializer = SectionSerializer()

        assert serializer.fields["lessons"].read_only is False

    def test_lessons_is_required(self):
        serializer = SectionSerializer()

        assert serializer.fields["lessons"].required is True
