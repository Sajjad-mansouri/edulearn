import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from curriculums.api.serializers import VideoCaptionSerializer
from curriculums.models import LessonContent, VideoCaption, VideoContent


@pytest.fixture
def lesson_content(db, lesson):
    return LessonContent.objects.create(
        lesson=lesson,
        title="Video Lesson",
        content_type=LessonContent.Type.VIDEO,
        order=1,
    )


@pytest.fixture
def video_content(db, lesson_content):
    return VideoContent.objects.create(
        content=lesson_content,
        source=VideoContent.Source.URL,
        external_url="https://example.com/video.mp4",
    )


@pytest.fixture
def caption_file():
    return SimpleUploadedFile(
        "captions.vtt",
        b"WEBVTT\n\n00:00.000 --> 00:05.000\nHello",
        content_type="text/vtt",
    )


@pytest.fixture
def video_caption(db, video_content, caption_file):
    return VideoCaption.objects.create(
        video=video_content,
        language="en",
        label="English",
        file=caption_file,
        file_format=VideoCaption.Format.VTT,
        is_default=False,
    )


class TestVideoCaptionSerializer:
    def test_declares_expected_fields(self):
        serializer = VideoCaptionSerializer()

        assert set(serializer.fields) == {
            "id",
            "language",
            "label",
            "file",
            "file_format",
            "is_default",
        }

    def test_id_is_optional(self):
        serializer = VideoCaptionSerializer(
            data={
                "language": "en",
                "file": SimpleUploadedFile(
                    "captions.vtt",
                    b"WEBVTT",
                    content_type="text/vtt",
                ),
                "file_format": VideoCaption.Format.VTT,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert "id" not in serializer.validated_data

    def test_id_accepts_integer(self):
        serializer = VideoCaptionSerializer(
            data={
                "id": 10,
                "language": "en",
                "file": SimpleUploadedFile(
                    "captions.vtt",
                    b"WEBVTT",
                    content_type="text/vtt",
                ),
                "file_format": VideoCaption.Format.VTT,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["id"] == 10

    def test_id_coerces_numeric_string_to_integer(self):
        serializer = VideoCaptionSerializer(
            data={
                "id": "10",
                "language": "en",
                "file": SimpleUploadedFile(
                    "captions.vtt",
                    b"WEBVTT",
                    content_type="text/vtt",
                ),
                "file_format": VideoCaption.Format.VTT,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["id"] == 10

    def test_id_rejects_non_numeric_string(self):
        serializer = VideoCaptionSerializer(
            data={
                "id": "invalid",
                "language": "en",
                "file": SimpleUploadedFile(
                    "captions.vtt",
                    b"WEBVTT",
                    content_type="text/vtt",
                ),
                "file_format": VideoCaption.Format.VTT,
            }
        )

        assert not serializer.is_valid()
        assert "id" in serializer.errors

    def test_id_rejects_decimal_value(self):
        serializer = VideoCaptionSerializer(
            data={
                "id": 1.5,
                "language": "en",
                "file": SimpleUploadedFile(
                    "captions.vtt",
                    b"WEBVTT",
                    content_type="text/vtt",
                ),
                "file_format": VideoCaption.Format.VTT,
            }
        )

        assert not serializer.is_valid()
        assert "id" in serializer.errors

    def test_language_is_required(self):
        serializer = VideoCaptionSerializer(
            data={
                "file": SimpleUploadedFile(
                    "captions.vtt",
                    b"WEBVTT",
                    content_type="text/vtt",
                ),
                "file_format": VideoCaption.Format.VTT,
            }
        )

        assert not serializer.is_valid()
        assert "language" in serializer.errors

    def test_accepts_valid_language(self):
        serializer = VideoCaptionSerializer(
            data={
                "language": "en",
                "file": SimpleUploadedFile(
                    "captions.vtt",
                    b"WEBVTT",
                    content_type="text/vtt",
                ),
                "file_format": VideoCaption.Format.VTT,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["language"] == "en"

    def test_language_rejects_value_longer_than_max_length(self):
        serializer = VideoCaptionSerializer(
            data={
                "language": "abcdefghijk",
                "file": SimpleUploadedFile(
                    "captions.vtt",
                    b"WEBVTT",
                    content_type="text/vtt",
                ),
                "file_format": VideoCaption.Format.VTT,
            }
        )

        assert not serializer.is_valid()
        assert "language" in serializer.errors

    def test_label_is_optional(self):
        serializer = VideoCaptionSerializer(
            data={
                "language": "en",
                "file": SimpleUploadedFile(
                    "captions.vtt",
                    b"WEBVTT",
                    content_type="text/vtt",
                ),
                "file_format": VideoCaption.Format.VTT,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert "label" not in serializer.validated_data

    def test_accepts_empty_label(self):
        serializer = VideoCaptionSerializer(
            data={
                "language": "en",
                "label": "",
                "file": SimpleUploadedFile(
                    "captions.vtt",
                    b"WEBVTT",
                    content_type="text/vtt",
                ),
                "file_format": VideoCaption.Format.VTT,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["label"] == ""

    def test_label_rejects_value_longer_than_max_length(self):
        serializer = VideoCaptionSerializer(
            data={
                "language": "en",
                "label": "a" * 51,
                "file": SimpleUploadedFile(
                    "captions.vtt",
                    b"WEBVTT",
                    content_type="text/vtt",
                ),
                "file_format": VideoCaption.Format.VTT,
            }
        )

        assert not serializer.is_valid()
        assert "label" in serializer.errors

    def test_file_is_required(self):
        serializer = VideoCaptionSerializer(
            data={
                "language": "en",
                "file_format": VideoCaption.Format.VTT,
            }
        )

        assert not serializer.is_valid()
        assert "file" in serializer.errors

    def test_accepts_uploaded_file(self):
        uploaded_file = SimpleUploadedFile(
            "captions.vtt",
            b"WEBVTT\n\n00:00.000 --> 00:05.000\nHello",
            content_type="text/vtt",
        )

        serializer = VideoCaptionSerializer(
            data={
                "language": "en",
                "file": uploaded_file,
                "file_format": VideoCaption.Format.VTT,
            }
        )

        assert serializer.is_valid(), serializer.errors

        validated_file = serializer.validated_data["file"]

        assert validated_file.name == "captions.vtt"
        assert validated_file.content_type == "text/vtt"
        assert validated_file.size == len(b"WEBVTT\n\n00:00.000 --> 00:05.000\nHello")

    def test_file_format_is_required(self):
        serializer = VideoCaptionSerializer(
            data={
                "language": "en",
                "file": SimpleUploadedFile(
                    "captions.vtt",
                    b"WEBVTT",
                    content_type="text/vtt",
                ),
            }
        )

        assert not serializer.is_valid()
        assert "file_format" in serializer.errors

    def test_accepts_vtt_file_format(self):
        serializer = VideoCaptionSerializer(
            data={
                "language": "en",
                "file": SimpleUploadedFile(
                    "captions.vtt",
                    b"WEBVTT",
                    content_type="text/vtt",
                ),
                "file_format": VideoCaption.Format.VTT,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["file_format"] == VideoCaption.Format.VTT

    def test_accepts_srt_file_format(self):
        serializer = VideoCaptionSerializer(
            data={
                "language": "en",
                "file": SimpleUploadedFile(
                    "captions.srt",
                    b"1\n00:00:00,000 --> 00:00:05,000\nHello",
                    content_type="text/plain",
                ),
                "file_format": VideoCaption.Format.SRT,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["file_format"] == VideoCaption.Format.SRT

    def test_rejects_invalid_file_format(self):
        serializer = VideoCaptionSerializer(
            data={
                "language": "en",
                "file": SimpleUploadedFile(
                    "captions.txt",
                    b"caption",
                    content_type="text/plain",
                ),
                "file_format": "txt",
            }
        )

        assert not serializer.is_valid()
        assert "file_format" in serializer.errors

    def test_file_format_rejects_value_longer_than_max_length(self):
        serializer = VideoCaptionSerializer(
            data={
                "language": "en",
                "file": SimpleUploadedFile(
                    "captions.vtt",
                    b"WEBVTT",
                    content_type="text/vtt",
                ),
                "file_format": "abcdefghijk",
            }
        )

        assert not serializer.is_valid()
        assert "file_format" in serializer.errors

    def test_is_default_is_optional(self):
        serializer = VideoCaptionSerializer(
            data={
                "language": "en",
                "file": SimpleUploadedFile(
                    "captions.vtt",
                    b"WEBVTT",
                    content_type="text/vtt",
                ),
                "file_format": VideoCaption.Format.VTT,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert "is_default" not in serializer.validated_data

    def test_is_default_accepts_true(self):
        serializer = VideoCaptionSerializer(
            data={
                "language": "en",
                "file": SimpleUploadedFile(
                    "captions.vtt",
                    b"WEBVTT",
                    content_type="text/vtt",
                ),
                "file_format": VideoCaption.Format.VTT,
                "is_default": True,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["is_default"] is True

    def test_is_default_accepts_false(self):
        serializer = VideoCaptionSerializer(
            data={
                "language": "en",
                "file": SimpleUploadedFile(
                    "captions.vtt",
                    b"WEBVTT",
                    content_type="text/vtt",
                ),
                "file_format": VideoCaption.Format.VTT,
                "is_default": False,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["is_default"] is False

    def test_is_default_coerces_boolean_string(self):
        serializer = VideoCaptionSerializer(
            data={
                "language": "en",
                "file": SimpleUploadedFile(
                    "captions.vtt",
                    b"WEBVTT",
                    content_type="text/vtt",
                ),
                "file_format": VideoCaption.Format.VTT,
                "is_default": "true",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["is_default"] is True

    def test_is_default_rejects_invalid_value(self):
        serializer = VideoCaptionSerializer(
            data={
                "language": "en",
                "file": SimpleUploadedFile(
                    "captions.vtt",
                    b"WEBVTT",
                    content_type="text/vtt",
                ),
                "file_format": VideoCaption.Format.VTT,
                "is_default": "not-a-boolean",
            }
        )

        assert not serializer.is_valid()
        assert "is_default" in serializer.errors

    def test_accepts_complete_data(self):
        serializer = VideoCaptionSerializer(
            data={
                "id": 5,
                "language": "en",
                "label": "English",
                "file": SimpleUploadedFile(
                    "english.vtt",
                    b"WEBVTT",
                    content_type="text/vtt",
                ),
                "file_format": VideoCaption.Format.VTT,
                "is_default": True,
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["id"] == 5
        assert serializer.validated_data["language"] == "en"
        assert serializer.validated_data["label"] == "English"
        assert serializer.validated_data["file"].name == "english.vtt"
        assert serializer.validated_data["file_format"] == VideoCaption.Format.VTT
        assert serializer.validated_data["is_default"] is True

    def test_serializes_instance(self, video_caption):
        serializer = VideoCaptionSerializer(instance=video_caption)

        data = serializer.data

        assert set(data) == {
            "id",
            "language",
            "label",
            "file",
            "file_format",
            "is_default",
        }

        assert data["id"] == video_caption.id
        assert data["language"] == "en"
        assert data["label"] == "English"
        assert data["file_format"] == VideoCaption.Format.VTT
        assert data["is_default"] is False

    def test_serializes_uploaded_file(self, video_caption):
        serializer = VideoCaptionSerializer(instance=video_caption)

        file_value = serializer.data["file"]

        assert file_value
        assert file_value.endswith("captions.vtt")

    def test_partial_update_accepts_language(self, video_caption):
        serializer = VideoCaptionSerializer(
            instance=video_caption,
            data={"language": "fa"},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["language"] == "fa"

    def test_partial_update_accepts_label(self, video_caption):
        serializer = VideoCaptionSerializer(
            instance=video_caption,
            data={"label": "Persian"},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["label"] == "Persian"

    def test_partial_update_accepts_file(self, video_caption):
        uploaded_file = SimpleUploadedFile(
            "updated.vtt",
            b"WEBVTT\n\n00:00.000 --> 00:03.000\nUpdated",
            content_type="text/vtt",
        )

        serializer = VideoCaptionSerializer(
            instance=video_caption,
            data={"file": uploaded_file},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["file"].name == "updated.vtt"

    def test_partial_update_accepts_file_format(self, video_caption):
        serializer = VideoCaptionSerializer(
            instance=video_caption,
            data={"file_format": VideoCaption.Format.SRT},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["file_format"] == VideoCaption.Format.SRT

    def test_partial_update_accepts_is_default(self, video_caption):
        serializer = VideoCaptionSerializer(
            instance=video_caption,
            data={"is_default": True},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["is_default"] is True

    def test_partial_update_does_not_require_other_fields(self, video_caption):
        serializer = VideoCaptionSerializer(
            instance=video_caption,
            data={"label": "Updated English"},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data == {
            "label": "Updated English",
        }

    def test_does_not_expose_video_field(self):
        serializer = VideoCaptionSerializer()

        assert "video" not in serializer.fields

    def test_serializer_exposes_only_declared_model_fields(self):
        serializer = VideoCaptionSerializer()

        assert list(serializer.fields) == [
            "id",
            "language",
            "label",
            "file",
            "file_format",
            "is_default",
        ]
