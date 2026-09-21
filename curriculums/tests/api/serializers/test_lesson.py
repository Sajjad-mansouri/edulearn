import datetime

import pytest

from curriculums.api.serializers import (
    CompletionCriteraSerializer,
    LessonContentSerializer,
    LessonSerializer,
)
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


class TestLessonSerializerFields:
    def test_contains_expected_fields(self):
        serializer = LessonSerializer()

        assert list(serializer.fields) == [
            "id",
            "title",
            "description",
            "duration",
            "content",
            "is_published",
            "is_preview",
            "completion_criteria",
        ]

    def test_id_is_not_required(self):
        serializer = LessonSerializer()

        assert serializer.fields["id"].required is False

    def test_title_is_required(self):
        serializer = LessonSerializer()

        assert serializer.fields["title"].required is True

    def test_description_is_not_required(self):
        serializer = LessonSerializer()

        assert serializer.fields["description"].required is False

    def test_duration_is_not_required(self):
        serializer = LessonSerializer()

        assert serializer.fields["duration"].required is False

    def test_duration_allows_null(self):
        serializer = LessonSerializer()

        assert serializer.fields["duration"].allow_null is True

    def test_content_is_required(self):
        serializer = LessonSerializer()

        assert serializer.fields["content"].required is True

    def test_is_published_is_not_required(self):
        serializer = LessonSerializer()

        assert serializer.fields["is_published"].required is False

    def test_is_preview_is_not_required(self):
        serializer = LessonSerializer()

        assert serializer.fields["is_preview"].required is False

    def test_completion_criteria_is_required(self):
        serializer = LessonSerializer()

        assert serializer.fields["completion_criteria"].required is True

    def test_content_uses_lesson_content_serializer(self):
        serializer = LessonSerializer()

        assert isinstance(
            serializer.fields["content"],
            LessonContentSerializer,
        )

    def test_completion_criteria_uses_completion_criteria_serializer(self):
        serializer = LessonSerializer()

        assert isinstance(
            serializer.fields["completion_criteria"],
            CompletionCriteraSerializer,
        )

    def test_content_is_writable(self):
        serializer = LessonSerializer()

        assert serializer.fields["content"].read_only is False

    def test_completion_criteria_is_writable(self):
        serializer = LessonSerializer()

        assert serializer.fields["completion_criteria"].read_only is False

    def test_does_not_expose_section(self):
        serializer = LessonSerializer()

        assert "section" not in serializer.fields

    def test_does_not_expose_slug(self):
        serializer = LessonSerializer()

        assert "slug" not in serializer.fields

    def test_does_not_expose_order(self):
        serializer = LessonSerializer()

        assert "order" not in serializer.fields


class TestLessonSerializerValidation:
    def test_rejects_empty_payload(self):
        serializer = LessonSerializer(data={})

        assert not serializer.is_valid()

        assert "title" in serializer.errors
        assert "content" in serializer.errors
        assert "completion_criteria" in serializer.errors

    def test_accepts_minimal_valid_payload(self):
        data = {
            "title": "Advanced Django",
            "content": {
                "content_type": LessonContent.Type.VIDEO,
            },
            "completion_criteria": {
                "criteria_type": (LessonCompletionCriteria.CriteriaType.MANUAL),
            },
        }

        serializer = LessonSerializer(data=data)

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["title"] == "Advanced Django"
        assert serializer.validated_data["content"]["content_type"] == (
            LessonContent.Type.VIDEO
        )
        assert (
            serializer.validated_data["completion_criteria"]["criteria_type"]
            == LessonCompletionCriteria.CriteriaType.MANUAL
        )

    def test_accepts_id_as_integer(self):
        data = {
            "id": 10,
            "title": "Django Lesson",
            "content": {
                "content_type": LessonContent.Type.VIDEO,
            },
            "completion_criteria": {
                "criteria_type": (LessonCompletionCriteria.CriteriaType.MANUAL),
            },
        }

        serializer = LessonSerializer(data=data)

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["id"] == 10

    def test_coerces_id_from_string(self):
        data = {
            "id": "25",
            "title": "Django Lesson",
            "content": {
                "content_type": LessonContent.Type.VIDEO,
            },
            "completion_criteria": {
                "criteria_type": (LessonCompletionCriteria.CriteriaType.MANUAL),
            },
        }

        serializer = LessonSerializer(data=data)

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
        serializer = LessonSerializer(
            data={
                "id": id_value,
                "title": "Django Lesson",
                "content": {
                    "content_type": LessonContent.Type.VIDEO,
                },
                "completion_criteria": {
                    "criteria_type": (LessonCompletionCriteria.CriteriaType.MANUAL),
                },
            }
        )

        assert not serializer.is_valid()
        assert "id" in serializer.errors

    def test_rejects_missing_title(self):
        serializer = LessonSerializer(
            data={
                "content": {
                    "content_type": LessonContent.Type.VIDEO,
                },
                "completion_criteria": {
                    "criteria_type": (LessonCompletionCriteria.CriteriaType.MANUAL),
                },
            }
        )

        assert not serializer.is_valid()
        assert "title" in serializer.errors

    def test_rejects_empty_title(self):
        serializer = LessonSerializer(
            data={
                "title": "",
                "content": {
                    "content_type": LessonContent.Type.VIDEO,
                },
                "completion_criteria": {
                    "criteria_type": (LessonCompletionCriteria.CriteriaType.MANUAL),
                },
            }
        )

        assert not serializer.is_valid()
        assert "title" in serializer.errors

    def test_accepts_description(self):
        serializer = LessonSerializer(
            data={
                "title": "Django ORM",
                "description": "Learn advanced ORM queries.",
                "content": {
                    "content_type": LessonContent.Type.ARTICLE,
                },
                "completion_criteria": {
                    "criteria_type": (
                        LessonCompletionCriteria.CriteriaType.READ_ARTICLE
                    ),
                },
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["description"] == (
            "Learn advanced ORM queries."
        )

    def test_accepts_empty_description(self):
        serializer = LessonSerializer(
            data={
                "title": "Django ORM",
                "description": "",
                "content": {
                    "content_type": LessonContent.Type.ARTICLE,
                },
                "completion_criteria": {
                    "criteria_type": (
                        LessonCompletionCriteria.CriteriaType.READ_ARTICLE
                    ),
                },
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["description"] == ""

    def test_description_is_optional(self):
        serializer = LessonSerializer(
            data={
                "title": "Django ORM",
                "content": {
                    "content_type": LessonContent.Type.ARTICLE,
                },
                "completion_criteria": {
                    "criteria_type": (
                        LessonCompletionCriteria.CriteriaType.READ_ARTICLE
                    ),
                },
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert "description" not in serializer.validated_data

    def test_accepts_null_duration(self):
        serializer = LessonSerializer(
            data={
                "title": "Django ORM",
                "duration": None,
                "content": {
                    "content_type": LessonContent.Type.ARTICLE,
                },
                "completion_criteria": {
                    "criteria_type": (
                        LessonCompletionCriteria.CriteriaType.READ_ARTICLE
                    ),
                },
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["duration"] is None

    def test_duration_is_optional(self):
        serializer = LessonSerializer(
            data={
                "title": "Django ORM",
                "content": {
                    "content_type": LessonContent.Type.ARTICLE,
                },
                "completion_criteria": {
                    "criteria_type": (
                        LessonCompletionCriteria.CriteriaType.READ_ARTICLE
                    ),
                },
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
        serializer = LessonSerializer(
            data={
                "title": "Django ORM",
                "duration": value,
                "content": {
                    "content_type": LessonContent.Type.ARTICLE,
                },
                "completion_criteria": {
                    "criteria_type": (
                        LessonCompletionCriteria.CriteriaType.READ_ARTICLE
                    ),
                },
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["duration"] == expected

    def test_rejects_invalid_duration(self):
        serializer = LessonSerializer(
            data={
                "title": "Django ORM",
                "duration": "not-a-duration",
                "content": {
                    "content_type": LessonContent.Type.ARTICLE,
                },
                "completion_criteria": {
                    "criteria_type": (
                        LessonCompletionCriteria.CriteriaType.READ_ARTICLE
                    ),
                },
            }
        )

        assert not serializer.is_valid()
        assert "duration" in serializer.errors

    @pytest.mark.parametrize(
        "is_published",
        [True, False],
    )
    def test_accepts_is_published(self, is_published):
        serializer = LessonSerializer(
            data={
                "title": "Django Lesson",
                "content": {
                    "content_type": LessonContent.Type.VIDEO,
                },
                "completion_criteria": {
                    "criteria_type": (LessonCompletionCriteria.CriteriaType.MANUAL),
                },
                "is_published": is_published,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["is_published"] is is_published

    def test_is_published_is_optional(self):
        serializer = LessonSerializer(
            data={
                "title": "Django Lesson",
                "content": {
                    "content_type": LessonContent.Type.VIDEO,
                },
                "completion_criteria": {
                    "criteria_type": (LessonCompletionCriteria.CriteriaType.MANUAL),
                },
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert "is_published" not in serializer.validated_data

    @pytest.mark.parametrize(
        "is_preview",
        [True, False],
    )
    def test_accepts_is_preview(self, is_preview):
        serializer = LessonSerializer(
            data={
                "title": "Django Lesson",
                "content": {
                    "content_type": LessonContent.Type.VIDEO,
                },
                "completion_criteria": {
                    "criteria_type": (LessonCompletionCriteria.CriteriaType.MANUAL),
                },
                "is_preview": is_preview,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["is_preview"] is is_preview

    def test_is_preview_is_optional(self):
        serializer = LessonSerializer(
            data={
                "title": "Django Lesson",
                "content": {
                    "content_type": LessonContent.Type.VIDEO,
                },
                "completion_criteria": {
                    "criteria_type": (LessonCompletionCriteria.CriteriaType.MANUAL),
                },
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert "is_preview" not in serializer.validated_data


class TestLessonSerializerNestedValidation:
    def test_requires_content(self):
        serializer = LessonSerializer(
            data={
                "title": "Django ORM",
                "completion_criteria": {
                    "criteria_type": (LessonCompletionCriteria.CriteriaType.MANUAL),
                },
            }
        )

        assert not serializer.is_valid()
        assert "content" in serializer.errors

    def test_requires_completion_criteria(self):
        serializer = LessonSerializer(
            data={
                "title": "Django ORM",
                "content": {
                    "content_type": LessonContent.Type.VIDEO,
                },
            }
        )

        assert not serializer.is_valid()
        assert "completion_criteria" in serializer.errors

    def test_rejects_invalid_nested_content(self):
        serializer = LessonSerializer(
            data={
                "title": "Django Lesson",
                "content": {
                    "content_type": "invalid_type",
                },
                "completion_criteria": {
                    "criteria_type": (LessonCompletionCriteria.CriteriaType.MANUAL),
                },
            }
        )

        assert not serializer.is_valid()
        assert "content" in serializer.errors

    def test_rejects_invalid_nested_completion_criteria(self):
        serializer = LessonSerializer(
            data={
                "title": "Django Lesson",
                "content": {
                    "content_type": LessonContent.Type.VIDEO,
                },
                "completion_criteria": {
                    "criteria_type": "invalid_type",
                },
            }
        )

        assert not serializer.is_valid()
        assert "completion_criteria" in serializer.errors

    def test_accepts_nested_video_content(self):
        serializer = LessonSerializer(
            data={
                "title": "Video Lesson",
                "content": {
                    "content_type": LessonContent.Type.VIDEO,
                    "video": {
                        "source": "url",
                        "external_url": "https://example.com/video.mp4",
                    },
                },
                "completion_criteria": {
                    "criteria_type": (
                        LessonCompletionCriteria.CriteriaType.WATCH_VIDEO
                    ),
                    "video_watch_percentage": 80,
                },
            }
        )

        assert serializer.is_valid(), serializer.errors

        content = serializer.validated_data["content"]

        assert content["content_type"] == LessonContent.Type.VIDEO
        assert content["video"]["source"] == "url"
        assert content["video"]["external_url"] == "https://example.com/video.mp4"

    def test_accepts_nested_article_content(self):
        serializer = LessonSerializer(
            data={
                "title": "Article Lesson",
                "content": {
                    "content_type": LessonContent.Type.ARTICLE,
                    "article": {
                        "body": "Article content",
                        "estimated_read_time": 10,
                    },
                },
                "completion_criteria": {
                    "criteria_type": (
                        LessonCompletionCriteria.CriteriaType.READ_ARTICLE
                    ),
                },
            }
        )

        assert serializer.is_valid(), serializer.errors

        article = serializer.validated_data["content"]["article"]

        assert article["body"] == "Article content"
        assert article["estimated_read_time"] == 10

    def test_accepts_nested_file_content(self):
        serializer = LessonSerializer(
            data={
                "title": "File Lesson",
                "content": {
                    "content_type": LessonContent.Type.FILE,
                    "file": {
                        "file_url": "https://example.com/file.pdf",
                    },
                },
                "completion_criteria": {
                    "criteria_type": (LessonCompletionCriteria.CriteriaType.MANUAL),
                },
            }
        )

        assert serializer.is_valid(), serializer.errors

        file_data = serializer.validated_data["content"]["file"]

        assert file_data["file_url"] == "https://example.com/file.pdf"

    def test_accepts_nested_quiz_content(self):
        serializer = LessonSerializer(
            data={
                "title": "Quiz Lesson",
                "content": {
                    "content_type": LessonContent.Type.QUIZ,
                    "quiz": {
                        "instructions": "Answer all questions.",
                        "passing_score": 70,
                        "questions": [],
                    },
                },
                "completion_criteria": {
                    "criteria_type": (LessonCompletionCriteria.CriteriaType.PASS_QUIZ),
                    "quiz_passing_score": 70,
                },
            }
        )

        assert serializer.is_valid(), serializer.errors

        quiz = serializer.validated_data["content"]["quiz"]

        assert quiz["instructions"] == "Answer all questions."
        assert quiz["passing_score"] == 70
        assert quiz["questions"] == []

    def test_accepts_nested_assignment_content(self):
        serializer = LessonSerializer(
            data={
                "title": "Assignment Lesson",
                "content": {
                    "content_type": LessonContent.Type.ASSIGNMENT,
                    "assignment": {
                        "instructions": "Complete the assignment.",
                        "passing_score": 70,
                        "max_score": 100,
                    },
                },
                "completion_criteria": {
                    "criteria_type": (
                        LessonCompletionCriteria.CriteriaType.SUBMIT_ASSIGNMENT
                    ),
                },
            }
        )

        assert serializer.is_valid(), serializer.errors

        assignment = serializer.validated_data["content"]["assignment"]

        assert assignment["instructions"] == "Complete the assignment."
        assert assignment["passing_score"] == 70
        assert assignment["max_score"] == 100

    def test_accepts_video_completion_criteria(self):
        serializer = LessonSerializer(
            data={
                "title": "Video Lesson",
                "content": {
                    "content_type": LessonContent.Type.VIDEO,
                },
                "completion_criteria": {
                    "criteria_type": (
                        LessonCompletionCriteria.CriteriaType.WATCH_VIDEO
                    ),
                    "video_watch_percentage": 80,
                },
            }
        )

        assert serializer.is_valid(), serializer.errors

        criteria = serializer.validated_data["completion_criteria"]

        assert criteria["criteria_type"] == (
            LessonCompletionCriteria.CriteriaType.WATCH_VIDEO
        )
        assert criteria["video_watch_percentage"] == 80

    def test_accepts_quiz_completion_criteria(self):
        serializer = LessonSerializer(
            data={
                "title": "Quiz Lesson",
                "content": {
                    "content_type": LessonContent.Type.QUIZ,
                },
                "completion_criteria": {
                    "criteria_type": (LessonCompletionCriteria.CriteriaType.PASS_QUIZ),
                    "quiz_passing_score": 75,
                },
            }
        )

        assert serializer.is_valid(), serializer.errors

        criteria = serializer.validated_data["completion_criteria"]

        assert criteria["criteria_type"] == (
            LessonCompletionCriteria.CriteriaType.PASS_QUIZ
        )
        assert criteria["quiz_passing_score"] == 75

    def test_preserves_all_nested_validated_data(self):
        serializer = LessonSerializer(
            data={
                "title": "Complete Lesson",
                "description": "A complete lesson.",
                "duration": "01:15:30",
                "content": {
                    "content_type": LessonContent.Type.VIDEO,
                    "video": {
                        "source": "url",
                        "external_url": "https://example.com/video.mp4",
                    },
                },
                "is_published": True,
                "is_preview": True,
                "completion_criteria": {
                    "criteria_type": (
                        LessonCompletionCriteria.CriteriaType.WATCH_VIDEO
                    ),
                    "video_watch_percentage": 90,
                },
            }
        )

        assert serializer.is_valid(), serializer.errors

        validated_data = serializer.validated_data

        assert validated_data["title"] == "Complete Lesson"
        assert validated_data["description"] == "A complete lesson."
        assert validated_data["duration"] == datetime.timedelta(
            hours=1,
            minutes=15,
            seconds=30,
        )
        assert validated_data["is_published"] is True
        assert validated_data["is_preview"] is True

        assert validated_data["content"]["content_type"] == (LessonContent.Type.VIDEO)
        assert validated_data["content"]["video"]["source"] == "url"

        assert validated_data["completion_criteria"]["criteria_type"] == (
            LessonCompletionCriteria.CriteriaType.WATCH_VIDEO
        )


class TestLessonSerializerSerialization:
    def test_serializes_expected_top_level_fields(
        self,
        lesson,
        lesson_content,
        completion_criteria,
    ):
        serializer = LessonSerializer(instance=lesson)

        assert set(serializer.data) == {
            "id",
            "title",
            "description",
            "duration",
            "content",
            "is_published",
            "is_preview",
            "completion_criteria",
        }

    def test_serializes_lesson_fields(
        self,
        lesson,
        lesson_content,
        completion_criteria,
    ):
        serializer = LessonSerializer(instance=lesson)

        data = serializer.data

        assert data["id"] == lesson.id
        assert data["title"] == lesson.title
        assert data["description"] == lesson.description
        assert data["is_published"] == lesson.is_published
        assert data["is_preview"] == lesson.is_preview

    def test_serializes_null_duration(
        self,
        lesson,
        lesson_content,
        completion_criteria,
    ):
        lesson.duration = None

        serializer = LessonSerializer(instance=lesson)

        assert serializer.data["duration"] is None

    def test_serializes_duration(
        self,
        lesson,
        lesson_content,
        completion_criteria,
    ):
        lesson.duration = datetime.timedelta(
            hours=1,
            minutes=30,
            seconds=15,
        )

        serializer = LessonSerializer(instance=lesson)

        assert serializer.data["duration"] == "01:30:15"

    def test_serializes_boolean_fields(
        self,
        lesson,
        lesson_content,
        completion_criteria,
    ):
        lesson.is_published = True
        lesson.is_preview = True

        serializer = LessonSerializer(instance=lesson)

        assert serializer.data["is_published"] is True
        assert serializer.data["is_preview"] is True

    def test_serializes_nested_content(
        self,
        lesson,
        lesson_content,
        completion_criteria,
    ):
        serializer = LessonSerializer(instance=lesson)

        content = serializer.data["content"]

        assert content["id"] == lesson_content.id
        assert content["content_type"] == lesson_content.content_type

    def test_serializes_nested_completion_criteria(
        self,
        lesson,
        lesson_content,
        completion_criteria,
    ):
        serializer = LessonSerializer(instance=lesson)

        criteria = serializer.data["completion_criteria"]

        assert criteria["criteria_type"] == completion_criteria.criteria_type
        assert criteria["quiz_passing_score"] is None
        assert criteria["video_watch_percentage"] is None

    def test_serializes_video_completion_criteria(
        self,
        lesson,
        lesson_content,
        completion_criteria,
    ):
        completion_criteria.criteria_type = (
            LessonCompletionCriteria.CriteriaType.WATCH_VIDEO
        )
        completion_criteria.video_watch_percentage = 85
        completion_criteria.save()

        serializer = LessonSerializer(instance=lesson)

        criteria = serializer.data["completion_criteria"]

        assert criteria["criteria_type"] == (
            LessonCompletionCriteria.CriteriaType.WATCH_VIDEO
        )
        assert criteria["video_watch_percentage"] == 85
        assert criteria["quiz_passing_score"] is None

    def test_serializes_quiz_completion_criteria(
        self,
        lesson,
        lesson_content,
        completion_criteria,
    ):
        completion_criteria.criteria_type = (
            LessonCompletionCriteria.CriteriaType.PASS_QUIZ
        )
        completion_criteria.quiz_passing_score = 75
        completion_criteria.video_watch_percentage = None
        completion_criteria.save()

        serializer = LessonSerializer(instance=lesson)

        criteria = serializer.data["completion_criteria"]

        assert criteria["criteria_type"] == (
            LessonCompletionCriteria.CriteriaType.PASS_QUIZ
        )
        assert criteria["quiz_passing_score"] == 75
        assert criteria["video_watch_percentage"] is None


class TestLessonSerializerPartialUpdates:
    def test_partial_update_accepts_empty_data(self, lesson):
        serializer = LessonSerializer(
            instance=lesson,
            data={},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data == {}

    def test_partial_update_accepts_title(self, lesson):
        serializer = LessonSerializer(
            instance=lesson,
            data={"title": "Updated Lesson"},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["title"] == "Updated Lesson"

    def test_partial_update_accepts_description(self, lesson):
        serializer = LessonSerializer(
            instance=lesson,
            data={"description": "Updated description"},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["description"] == ("Updated description")

    def test_partial_update_accepts_null_description(self, lesson):
        serializer = LessonSerializer(
            instance=lesson,
            data={"description": None},
            partial=True,
        )

        assert not serializer.is_valid()
        assert "description" in serializer.errors

    def test_partial_update_accepts_duration(self, lesson):
        serializer = LessonSerializer(
            instance=lesson,
            data={"duration": "00:45:00"},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["duration"] == (datetime.timedelta(minutes=45))

    def test_partial_update_accepts_null_duration(self, lesson):
        serializer = LessonSerializer(
            instance=lesson,
            data={"duration": None},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["duration"] is None

    @pytest.mark.parametrize(
        "field_name",
        [
            "is_published",
            "is_preview",
        ],
    )
    def test_partial_update_accepts_boolean_fields(
        self,
        lesson,
        field_name,
    ):
        serializer = LessonSerializer(
            instance=lesson,
            data={field_name: True},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data[field_name] is True

    def test_partial_update_accepts_nested_content(self, lesson):
        serializer = LessonSerializer(
            instance=lesson,
            data={
                "content": {
                    "content_type": LessonContent.Type.ARTICLE,
                },
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["content"]["content_type"] == (
            LessonContent.Type.ARTICLE
        )

    def test_partial_update_accepts_nested_completion_criteria(
        self,
        lesson,
    ):
        serializer = LessonSerializer(
            instance=lesson,
            data={
                "completion_criteria": {
                    "criteria_type": (
                        LessonCompletionCriteria.CriteriaType.READ_ARTICLE
                    ),
                },
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        assert (
            serializer.validated_data["completion_criteria"]["criteria_type"]
            == LessonCompletionCriteria.CriteriaType.READ_ARTICLE
        )

    def test_partial_update_does_not_require_content(
        self,
        lesson,
    ):
        serializer = LessonSerializer(
            instance=lesson,
            data={"title": "Updated"},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert "content" not in serializer.validated_data

    def test_partial_update_does_not_require_completion_criteria(
        self,
        lesson,
    ):
        serializer = LessonSerializer(
            instance=lesson,
            data={"title": "Updated"},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert "completion_criteria" not in serializer.validated_data


class TestLessonSerializerNestedComposition:
    def test_content_is_single_nested_serializer(self):
        serializer = LessonSerializer()

        assert isinstance(
            serializer.fields["content"],
            LessonContentSerializer,
        )

    def test_completion_criteria_is_single_nested_serializer(self):
        serializer = LessonSerializer()

        assert isinstance(
            serializer.fields["completion_criteria"],
            CompletionCriteraSerializer,
        )

    def test_content_is_not_read_only(self):
        serializer = LessonSerializer()

        assert serializer.fields["content"].read_only is False

    def test_completion_criteria_is_not_read_only(self):
        serializer = LessonSerializer()

        assert serializer.fields["completion_criteria"].read_only is False

    def test_content_is_required(self):
        serializer = LessonSerializer()

        assert serializer.fields["content"].required is True

    def test_completion_criteria_is_required(self):
        serializer = LessonSerializer()

        assert serializer.fields["completion_criteria"].required is True
