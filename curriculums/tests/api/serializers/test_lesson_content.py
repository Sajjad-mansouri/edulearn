from types import SimpleNamespace

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.serializers import ListSerializer

from curriculums.api.serializers import (
    ArticleContenttSerializer,
    AssignmentSerializer,
    AttachmentSerializer,
    FileContentSerializer,
    LessonContentSerializer,
    QuizContentSerializer,
    VideoContentSerializer,
)
from curriculums.models import Attachment, LessonContent


@pytest.fixture
def lesson_content(db, lesson):
    return LessonContent.objects.create(
        lesson=lesson,
        title="Lesson Content",
        content_type=LessonContent.Type.VIDEO,
        order=1,
    )


class TestLessonContentSerializerFields:
    def test_contains_expected_fields(self):
        serializer = LessonContentSerializer()

        assert list(serializer.fields) == [
            "id",
            "content_type",
            "video",
            "file",
            "article",
            "attachments",
            "quiz",
            "assignment",
        ]

    def test_id_is_not_required(self):
        serializer = LessonContentSerializer()

        assert serializer.fields["id"].required is False

    def test_content_type_is_required(self):
        serializer = LessonContentSerializer()

        assert serializer.fields["content_type"].required is True

    @pytest.mark.parametrize(
        "field_name",
        [
            "video",
            "file",
            "article",
            "attachments",
            "quiz",
            "assignment",
        ],
    )
    def test_nested_content_fields_are_not_required(self, field_name):
        serializer = LessonContentSerializer()

        assert serializer.fields[field_name].required is False

    def test_attachments_is_a_many_serializer(self):
        serializer = LessonContentSerializer()
        field = serializer.fields["attachments"]

        assert isinstance(field, ListSerializer)
        assert isinstance(field.child, AttachmentSerializer)

    def test_video_uses_video_content_serializer(self):
        serializer = LessonContentSerializer()

        assert isinstance(serializer.fields["video"], VideoContentSerializer)

    def test_file_uses_file_content_serializer(self):
        serializer = LessonContentSerializer()

        assert isinstance(serializer.fields["file"], FileContentSerializer)

    def test_article_uses_article_content_serializer(self):
        serializer = LessonContentSerializer()

        assert isinstance(serializer.fields["article"], ArticleContenttSerializer)

    def test_quiz_uses_quiz_content_serializer(self):
        serializer = LessonContentSerializer()

        assert isinstance(serializer.fields["quiz"], QuizContentSerializer)

    def test_assignment_uses_assignment_serializer(self):
        serializer = LessonContentSerializer()

        assert isinstance(serializer.fields["assignment"], AssignmentSerializer)

    def test_attachment_child_serializer_is_not_required(self):
        serializer = LessonContentSerializer()

        assert serializer.fields["attachments"].required is False

    def test_does_not_expose_lesson_field(self):
        serializer = LessonContentSerializer()

        assert "lesson" not in serializer.fields

    def test_does_not_expose_title_field(self):
        serializer = LessonContentSerializer()

        assert "title" not in serializer.fields

    def test_does_not_expose_order_field(self):
        serializer = LessonContentSerializer()

        assert "order" not in serializer.fields

    def test_does_not_expose_is_main_content_field(self):
        serializer = LessonContentSerializer()

        assert "is_main_content" not in serializer.fields


class TestLessonContentSerializerValidation:
    @pytest.mark.parametrize(
        "content_type",
        [
            LessonContent.Type.VIDEO,
            LessonContent.Type.ARTICLE,
            LessonContent.Type.FILE,
            LessonContent.Type.QUIZ,
            LessonContent.Type.ASSIGNMENT,
            LessonContent.Type.LIVE_SESSION,
            LessonContent.Type.CODING_EXERCISE,
        ],
    )
    def test_accepts_valid_content_type(self, content_type):
        serializer = LessonContentSerializer(data={"content_type": content_type})

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["content_type"] == content_type

    def test_rejects_invalid_content_type(self):
        serializer = LessonContentSerializer(data={"content_type": "invalid_type"})

        assert not serializer.is_valid()
        assert "content_type" in serializer.errors

    def test_requires_content_type(self):
        serializer = LessonContentSerializer(data={})

        assert not serializer.is_valid()
        assert "content_type" in serializer.errors

    @pytest.mark.parametrize(
        "content_type",
        [
            "",
            None,
        ],
    )
    def test_rejects_empty_content_type(self, content_type):
        serializer = LessonContentSerializer(data={"content_type": content_type})

        assert not serializer.is_valid()
        assert "content_type" in serializer.errors

    @pytest.mark.parametrize(
        "id_value",
        [
            1,
            10,
            "25",
        ],
    )
    def test_accepts_valid_id(self, id_value):
        serializer = LessonContentSerializer(
            data={
                "id": id_value,
                "content_type": LessonContent.Type.VIDEO,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["id"] == int(id_value)

    def test_id_is_optional(self):
        serializer = LessonContentSerializer(
            data={"content_type": LessonContent.Type.VIDEO}
        )

        assert serializer.is_valid(), serializer.errors
        assert "id" not in serializer.validated_data

    @pytest.mark.parametrize(
        "id_value",
        [
            "not-an-integer",
            1.5,
            True,
        ],
    )
    def test_rejects_invalid_id(self, id_value):
        serializer = LessonContentSerializer(
            data={
                "id": id_value,
                "content_type": LessonContent.Type.VIDEO,
            }
        )

        assert not serializer.is_valid()
        assert "id" in serializer.errors

    def test_accepts_video_without_nested_content(self):
        serializer = LessonContentSerializer(
            data={"content_type": LessonContent.Type.VIDEO}
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["content_type"] == (LessonContent.Type.VIDEO)

    def test_accepts_article_without_nested_content(self):
        serializer = LessonContentSerializer(
            data={"content_type": LessonContent.Type.ARTICLE}
        )

        assert serializer.is_valid(), serializer.errors

    def test_accepts_file_without_nested_content(self):
        serializer = LessonContentSerializer(
            data={"content_type": LessonContent.Type.FILE}
        )

        assert serializer.is_valid(), serializer.errors

    def test_accepts_quiz_without_nested_content(self):
        serializer = LessonContentSerializer(
            data={"content_type": LessonContent.Type.QUIZ}
        )

        assert serializer.is_valid(), serializer.errors

    def test_accepts_assignment_without_nested_content(self):
        serializer = LessonContentSerializer(
            data={"content_type": LessonContent.Type.ASSIGNMENT}
        )

        assert serializer.is_valid(), serializer.errors

    def test_accepts_live_session_without_nested_content(self):
        serializer = LessonContentSerializer(
            data={"content_type": LessonContent.Type.LIVE_SESSION}
        )

        assert serializer.is_valid(), serializer.errors

    def test_accepts_coding_exercise_without_nested_content(self):
        serializer = LessonContentSerializer(
            data={"content_type": LessonContent.Type.CODING_EXERCISE}
        )

        assert serializer.is_valid(), serializer.errors


class TestLessonContentSerializerNestedValidation:
    def test_accepts_empty_attachments_list(self):
        serializer = LessonContentSerializer(
            data={
                "content_type": LessonContent.Type.VIDEO,
                "attachments": [],
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["attachments"] == []

    def test_accepts_multiple_attachment_payloads(self):
        data = {
            "content_type": LessonContent.Type.VIDEO,
            "attachments": [
                {
                    "file_url": "https://example.com/one.pdf",
                },
                {
                    "file_url": "https://example.com/two.pdf",
                },
            ],
        }

        serializer = LessonContentSerializer(data=data)

        assert serializer.is_valid(), serializer.errors

        attachments = serializer.validated_data["attachments"]

        assert len(attachments) == 2
        assert attachments[0]["file_url"] == "https://example.com/one.pdf"
        assert attachments[1]["file_url"] == "https://example.com/two.pdf"

    def test_rejects_invalid_nested_attachment(self):
        serializer = LessonContentSerializer(
            data={
                "content_type": LessonContent.Type.VIDEO,
                "attachments": [
                    {
                        "file_url": "not-a-url",
                    }
                ],
            }
        )

        assert not serializer.is_valid()
        assert "attachments" in serializer.errors

    def test_accepts_valid_nested_article(self):
        serializer = LessonContentSerializer(
            data={
                "content_type": LessonContent.Type.ARTICLE,
                "article": {
                    "body": "Article body",
                    "estimated_read_time": 5,
                },
            }
        )

        assert serializer.is_valid(), serializer.errors

        article = serializer.validated_data["article"]

        assert article["body"] == "Article body"
        assert article["estimated_read_time"] == 5

    def test_accepts_valid_nested_file(self):
        serializer = LessonContentSerializer(
            data={
                "content_type": LessonContent.Type.FILE,
                "file": {
                    "file_url": "https://example.com/document.pdf",
                },
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert (
            serializer.validated_data["file"]["file_url"]
            == "https://example.com/document.pdf"
        )

    def test_accepts_valid_nested_video(self):
        serializer = LessonContentSerializer(
            data={
                "content_type": LessonContent.Type.VIDEO,
                "video": {
                    "source": "url",
                    "external_url": "https://example.com/video.mp4",
                },
            }
        )

        assert serializer.is_valid(), serializer.errors

        video = serializer.validated_data["video"]

        assert video["source"] == "url"
        assert video["external_url"] == "https://example.com/video.mp4"

    def test_accepts_valid_nested_assignment(self):
        serializer = LessonContentSerializer(
            data={
                "content_type": LessonContent.Type.ASSIGNMENT,
                "assignment": {
                    "instructions": "Complete the assignment.",
                    "passing_score": 70,
                    "max_score": 100,
                    "allow_late_submission": True,
                    "max_attempts": 3,
                },
            }
        )

        assert serializer.is_valid(), serializer.errors

        assignment = serializer.validated_data["assignment"]

        assert assignment["instructions"] == "Complete the assignment."
        assert assignment["passing_score"] == 70
        assert assignment["max_score"] == 100
        assert assignment["allow_late_submission"] is True
        assert assignment["max_attempts"] == 3

    def test_accepts_valid_nested_quiz(self):
        serializer = LessonContentSerializer(
            data={
                "content_type": LessonContent.Type.QUIZ,
                "quiz": {
                    "instructions": "Answer all questions.",
                    "passing_score": 70,
                    "time_limit": 30,
                    "max_attempts": 2,
                    "shuffle_questions": True,
                    "shuffle_choices": False,
                    "show_correct_answers": True,
                    "questions": [],
                },
            }
        )

        assert serializer.is_valid(), serializer.errors

        quiz = serializer.validated_data["quiz"]

        assert quiz["instructions"] == "Answer all questions."
        assert quiz["passing_score"] == 70
        assert quiz["time_limit"] == 30
        assert quiz["max_attempts"] == 2
        assert quiz["shuffle_questions"] is True
        assert quiz["shuffle_choices"] is False
        assert quiz["show_correct_answers"] is True
        assert quiz["questions"] == []

    def test_validates_nested_serializer_fields(self):
        serializer = LessonContentSerializer(
            data={
                "content_type": LessonContent.Type.VIDEO,
                "video": {
                    "source": "invalid-source",
                    "external_url": "https://example.com/video.mp4",
                },
            }
        )

        assert not serializer.is_valid()
        assert "video" in serializer.errors

    @pytest.mark.parametrize(
        "field_name",
        [
            "video",
            "file",
            "article",
            "quiz",
            "assignment",
        ],
    )
    def test_nested_fields_are_optional(self, field_name):
        serializer = LessonContentSerializer(
            data={"content_type": LessonContent.Type.VIDEO}
        )

        assert serializer.is_valid(), serializer.errors
        assert field_name not in serializer.validated_data


class TestLessonContentSerializerValidatedData:
    def test_returns_expected_top_level_validated_data(self):
        serializer = LessonContentSerializer(
            data={
                "id": "10",
                "content_type": LessonContent.Type.VIDEO,
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data == {
            "id": 10,
            "content_type": LessonContent.Type.VIDEO,
        }

    def test_preserves_nested_validated_data(self):
        serializer = LessonContentSerializer(
            data={
                "content_type": LessonContent.Type.ARTICLE,
                "article": {
                    "body": "  Article body  ",
                    "estimated_read_time": 10,
                },
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["article"]["body"] == "Article body"
        assert serializer.validated_data["article"]["estimated_read_time"] == 10

    def test_preserves_multiple_nested_sections(self):
        serializer = LessonContentSerializer(
            data={
                "content_type": LessonContent.Type.VIDEO,
                "video": {
                    "source": "url",
                    "external_url": "https://example.com/video.mp4",
                },
                "attachments": [
                    {
                        "file_url": "https://example.com/slides.pdf",
                    }
                ],
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert "video" in serializer.validated_data
        assert "attachments" in serializer.validated_data

        assert (
            serializer.validated_data["video"]["external_url"]
            == "https://example.com/video.mp4"
        )

        assert (
            serializer.validated_data["attachments"][0]["file_url"]
            == "https://example.com/slides.pdf"
        )


class TestLessonContentSerializerSerialization:
    def test_serializes_lesson_content_without_nested_objects(
        self,
        lesson_content,
    ):
        serializer = LessonContentSerializer(instance=lesson_content)

        data = serializer.data

        assert data["id"] == lesson_content.id
        assert data["content_type"] == lesson_content.content_type

    def test_serializes_id_as_integer(self, lesson_content):
        serializer = LessonContentSerializer(instance=lesson_content)

        assert isinstance(serializer.data["id"], int)

    def test_serializes_content_type_value(self, lesson_content):
        lesson_content.content_type = LessonContent.Type.ARTICLE
        lesson_content.save(update_fields=["content_type"])

        serializer = LessonContentSerializer(instance=lesson_content)

        assert serializer.data["content_type"] == LessonContent.Type.ARTICLE

    def test_serializes_nested_fields_as_absent_or_empty_when_relations_do_not_exist(
        self,
        lesson_content,
    ):
        serializer = LessonContentSerializer(instance=lesson_content)

        data = serializer.data

        assert data["id"] == lesson_content.id
        assert data["content_type"] == lesson_content.content_type

        assert data["attachments"] == []

        assert data["video"] is None
        assert data["file"] is None
        assert data["article"] is None
        assert data["quiz"] is None
        assert data["assignment"] is None

    def test_serializes_attachments_from_related_objects(
        self,
        lesson_content,
    ):
        attachment = Attachment.objects.create(
            course=lesson_content.lesson.section.course,
            lesson_content=lesson_content,
            file=SimpleUploadedFile(
                "material.pdf",
                b"pdf content",
                content_type="application/pdf",
            ),
        )

        serializer = LessonContentSerializer(instance=lesson_content)

        assert serializer.data["attachments"] == [
            {
                "id": attachment.id,
                "file": attachment.file.url,
                "file_url": "",
            }
        ]

    def test_serializes_nested_article(self, lesson_content):
        article = SimpleNamespace(
            id=1,
            body="Article body",
            estimated_read_time=10,
        )

        instance = SimpleNamespace(
            id=lesson_content.id,
            content_type=LessonContent.Type.ARTICLE,
            article=article,
            video=None,
            file=None,
            quiz=None,
            assignment=None,
            attachments=[],
        )

        serializer = LessonContentSerializer(instance=instance)

        assert serializer.data["article"] == {
            "id": 1,
            "body": "Article body",
            "estimated_read_time": 10,
        }

    def test_serializes_nested_file(self, lesson_content):
        file_content = SimpleNamespace(
            id=1,
            file=None,
            file_url="https://example.com/document.pdf",
        )

        instance = SimpleNamespace(
            id=lesson_content.id,
            content_type=LessonContent.Type.FILE,
            article=None,
            video=None,
            file=file_content,
            quiz=None,
            assignment=None,
            attachments=[],
        )

        serializer = LessonContentSerializer(instance=instance)

        assert serializer.data["file"] == {
            "id": 1,
            "file": None,
            "file_url": "https://example.com/document.pdf",
        }

    def test_serializes_nested_video(self, lesson_content):
        video = SimpleNamespace(
            id=1,
            source="url",
            video_file=None,
            external_url="https://example.com/video.mp4",
            duration=None,
            transcript="",
            text="",
            captions=[],
        )

        instance = SimpleNamespace(
            id=lesson_content.id,
            content_type=LessonContent.Type.VIDEO,
            article=None,
            video=video,
            file=None,
            quiz=None,
            assignment=None,
            attachments=[],
        )

        serializer = LessonContentSerializer(instance=instance)

        assert serializer.data["video"]["id"] == 1
        assert serializer.data["video"]["source"] == "url"
        assert (
            serializer.data["video"]["external_url"] == "https://example.com/video.mp4"
        )

    def test_serializes_nested_assignment(self, lesson_content):
        assignment = SimpleNamespace(
            id=1,
            instructions="Complete the assignment.",
            passing_score=70,
            max_score=100,
            due_date=None,
            allow_late_submission=True,
            max_attempts=3,
            accepted_file_types="pdf",
            max_file_size_mb=10,
        )

        instance = SimpleNamespace(
            id=lesson_content.id,
            content_type=LessonContent.Type.ASSIGNMENT,
            article=None,
            video=None,
            file=None,
            quiz=None,
            assignment=assignment,
            attachments=[],
        )

        serializer = LessonContentSerializer(instance=instance)

        assert serializer.data["assignment"] == {
            "id": 1,
            "instructions": "Complete the assignment.",
            "passing_score": 70,
            "max_score": 100,
            "due_date": None,
            "allow_late_submission": True,
            "max_attempts": 3,
            "accepted_file_types": "pdf",
            "max_file_size_mb": 10,
        }

    def test_serializes_nested_quiz(self, lesson_content):
        quiz = SimpleNamespace(
            id=1,
            instructions="Answer all questions.",
            passing_score=70,
            time_limit=30,
            max_attempts=2,
            shuffle_questions=True,
            shuffle_choices=False,
            show_correct_answers=True,
            questions=[],
        )

        instance = SimpleNamespace(
            id=lesson_content.id,
            content_type=LessonContent.Type.QUIZ,
            article=None,
            video=None,
            file=None,
            quiz=quiz,
            assignment=None,
            attachments=[],
        )

        serializer = LessonContentSerializer(instance=instance)

        assert serializer.data["quiz"]["id"] == 1
        assert serializer.data["quiz"]["passing_score"] == 70
        assert serializer.data["quiz"]["questions"] == []


class TestLessonContentSerializerPartialUpdates:
    @pytest.mark.parametrize(
        "data",
        [
            {"content_type": LessonContent.Type.ARTICLE},
            {"content_type": LessonContent.Type.FILE},
            {"content_type": LessonContent.Type.VIDEO},
            {"content_type": LessonContent.Type.QUIZ},
            {"content_type": LessonContent.Type.ASSIGNMENT},
        ],
    )
    def test_partial_update_accepts_content_type_only(
        self,
        lesson_content,
        data,
    ):
        serializer = LessonContentSerializer(
            instance=lesson_content,
            data=data,
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["content_type"] == data["content_type"]

    def test_partial_update_does_not_require_content_type(
        self,
        lesson_content,
    ):
        serializer = LessonContentSerializer(
            instance=lesson_content,
            data={},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data == {}

    def test_partial_update_accepts_nested_article(
        self,
        lesson_content,
    ):
        serializer = LessonContentSerializer(
            instance=lesson_content,
            data={
                "article": {
                    "body": "Updated article",
                    "estimated_read_time": 15,
                }
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["article"]["body"] == ("Updated article")
        assert serializer.validated_data["article"]["estimated_read_time"] == 15

    def test_partial_update_accepts_empty_attachments(
        self,
        lesson_content,
    ):
        serializer = LessonContentSerializer(
            instance=lesson_content,
            data={"attachments": []},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["attachments"] == []


class TestLessonContentSerializerNestedStructure:
    def test_nested_serializers_are_not_many(self):
        serializer = LessonContentSerializer()

        assert not isinstance(
            serializer.fields["video"],
            ListSerializer,
        )
        assert not isinstance(
            serializer.fields["file"],
            ListSerializer,
        )
        assert not isinstance(
            serializer.fields["article"],
            ListSerializer,
        )
        assert not isinstance(
            serializer.fields["quiz"],
            ListSerializer,
        )
        assert not isinstance(
            serializer.fields["assignment"],
            ListSerializer,
        )

    def test_only_attachments_is_many(self):
        serializer = LessonContentSerializer()

        many_fields = [
            field_name
            for field_name, field in serializer.fields.items()
            if getattr(field, "many", False)
        ]

        assert many_fields == ["attachments"]

    def test_nested_serializers_are_not_read_only(self):
        serializer = LessonContentSerializer()

        assert serializer.fields["video"].read_only is False
        assert serializer.fields["file"].read_only is False
        assert serializer.fields["article"].read_only is False
        assert serializer.fields["quiz"].read_only is False
        assert serializer.fields["assignment"].read_only is False
        assert serializer.fields["attachments"].read_only is False
