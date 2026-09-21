import datetime

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from curriculums.api.serializers import VideoCaptionSerializer, VideoContentSerializer
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
def video_file():
    return SimpleUploadedFile(
        "lesson-video.mp4",
        b"video content",
        content_type="video/mp4",
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


class TestVideoContentSerializer:
    def test_declares_expected_fields(self):
        serializer = VideoContentSerializer()

        assert set(serializer.fields) == {
            "id",
            "source",
            "video_file",
            "external_url",
            "duration",
            "transcript",
            "text",
            "captions",
        }

    def test_fields_are_in_expected_order(self):
        serializer = VideoContentSerializer()

        assert list(serializer.fields) == [
            "id",
            "source",
            "video_file",
            "external_url",
            "duration",
            "transcript",
            "text",
            "captions",
        ]

    def test_id_is_optional(self):
        serializer = VideoContentSerializer(
            data={
                "source": VideoContent.Source.URL,
                "external_url": "https://example.com/video.mp4",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert "id" not in serializer.validated_data

    def test_id_accepts_integer(self):
        serializer = VideoContentSerializer(
            data={
                "id": 10,
                "source": VideoContent.Source.URL,
                "external_url": "https://example.com/video.mp4",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["id"] == 10

    def test_id_coerces_numeric_string_to_integer(self):
        serializer = VideoContentSerializer(
            data={
                "id": "10",
                "source": VideoContent.Source.URL,
                "external_url": "https://example.com/video.mp4",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["id"] == 10

    def test_id_rejects_non_numeric_string(self):
        serializer = VideoContentSerializer(
            data={
                "id": "invalid",
                "source": VideoContent.Source.URL,
                "external_url": "https://example.com/video.mp4",
            }
        )

        assert not serializer.is_valid()
        assert "id" in serializer.errors

    def test_id_rejects_decimal_value(self):
        serializer = VideoContentSerializer(
            data={
                "id": 1.5,
                "source": VideoContent.Source.URL,
                "external_url": "https://example.com/video.mp4",
            }
        )

        assert not serializer.is_valid()
        assert "id" in serializer.errors

    def test_source_is_optional(self):
        serializer = VideoContentSerializer(
            data={
                "external_url": "https://example.com/video.mp4",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert "source" not in serializer.validated_data

    def test_accepts_file_source(self):
        serializer = VideoContentSerializer(
            data={
                "source": VideoContent.Source.FILE,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["source"] == VideoContent.Source.FILE

    def test_accepts_url_source(self):
        serializer = VideoContentSerializer(
            data={
                "source": VideoContent.Source.URL,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["source"] == VideoContent.Source.URL

    def test_rejects_invalid_source(self):
        serializer = VideoContentSerializer(
            data={
                "source": "invalid",
            }
        )

        assert not serializer.is_valid()
        assert "source" in serializer.errors

    def test_video_file_is_optional(self):
        serializer = VideoContentSerializer(
            data={
                "source": VideoContent.Source.URL,
                "external_url": "https://example.com/video.mp4",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert "video_file" not in serializer.validated_data

    def test_accepts_uploaded_video_file(self, video_file):
        serializer = VideoContentSerializer(
            data={
                "video_file": video_file,
            }
        )

        assert serializer.is_valid(), serializer.errors

        validated_file = serializer.validated_data["video_file"]

        assert validated_file.name == "lesson-video.mp4"
        assert validated_file.content_type == "video/mp4"
        assert validated_file.size == len(b"video content")

    def test_external_url_is_optional(self):
        serializer = VideoContentSerializer(
            data={
                "source": VideoContent.Source.FILE,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert "external_url" not in serializer.validated_data

    def test_accepts_valid_external_url(self):
        url = "https://example.com/video.mp4"

        serializer = VideoContentSerializer(
            data={
                "external_url": url,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["external_url"] == url

    def test_rejects_invalid_external_url(self):
        serializer = VideoContentSerializer(
            data={
                "external_url": "not-a-valid-url",
            }
        )

        assert not serializer.is_valid()
        assert "external_url" in serializer.errors

    def test_accepts_empty_external_url(self):
        serializer = VideoContentSerializer(
            data={
                "external_url": "",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["external_url"] == ""

    def test_duration_is_optional(self):
        serializer = VideoContentSerializer(
            data={
                "source": VideoContent.Source.URL,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert "duration" not in serializer.validated_data

    def test_accepts_duration_string(self):
        serializer = VideoContentSerializer(
            data={
                "duration": "01:30:00",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["duration"] == datetime.timedelta(
            hours=1,
            minutes=30,
        )

    def test_accepts_zero_duration(self):
        serializer = VideoContentSerializer(
            data={
                "duration": "00:00:00",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["duration"] == datetime.timedelta(0)

    def test_rejects_invalid_duration(self):
        serializer = VideoContentSerializer(
            data={
                "duration": "not-a-duration",
            }
        )

        assert not serializer.is_valid()
        assert "duration" in serializer.errors

    def test_accepts_duration_with_seconds(self):
        serializer = VideoContentSerializer(
            data={
                "duration": "00:05:30",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["duration"] == datetime.timedelta(
            minutes=5,
            seconds=30,
        )

    def test_transcript_is_optional(self):
        serializer = VideoContentSerializer(
            data={
                "source": VideoContent.Source.URL,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert "transcript" not in serializer.validated_data

    def test_accepts_transcript(self):
        transcript = "This is the complete video transcript."

        serializer = VideoContentSerializer(
            data={
                "transcript": transcript,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["transcript"] == transcript

    def test_accepts_empty_transcript(self):
        serializer = VideoContentSerializer(
            data={
                "transcript": "",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["transcript"] == ""

    def test_text_is_optional(self):
        serializer = VideoContentSerializer(
            data={
                "source": VideoContent.Source.URL,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert "text" not in serializer.validated_data

    def test_accepts_text(self):
        text = "Additional information about this video."

        serializer = VideoContentSerializer(
            data={
                "text": text,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["text"] == text

    def test_accepts_empty_text(self):
        serializer = VideoContentSerializer(
            data={
                "text": "",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["text"] == ""

    def test_captions_is_optional(self):
        serializer = VideoContentSerializer(
            data={
                "source": VideoContent.Source.URL,
                "external_url": "https://example.com/video.mp4",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert "captions" not in serializer.validated_data

    def test_accepts_empty_captions_list(self):
        serializer = VideoContentSerializer(
            data={
                "captions": [],
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["captions"] == []

    def test_accepts_single_nested_caption(self):
        serializer = VideoContentSerializer(
            data={
                "captions": [
                    {
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
                ],
            }
        )

        assert serializer.is_valid(), serializer.errors

        captions = serializer.validated_data["captions"]

        assert len(captions) == 1
        assert captions[0]["language"] == "en"
        assert captions[0]["label"] == "English"
        assert captions[0]["file"].name == "english.vtt"
        assert captions[0]["file_format"] == VideoCaption.Format.VTT
        assert captions[0]["is_default"] is True

    def test_accepts_multiple_nested_captions(self):
        serializer = VideoContentSerializer(
            data={
                "captions": [
                    {
                        "language": "en",
                        "label": "English",
                        "file": SimpleUploadedFile(
                            "english.vtt",
                            b"WEBVTT",
                            content_type="text/vtt",
                        ),
                        "file_format": VideoCaption.Format.VTT,
                        "is_default": True,
                    },
                    {
                        "language": "fa",
                        "label": "Persian",
                        "file": SimpleUploadedFile(
                            "persian.srt",
                            b"1\n00:00:00,000 --> 00:00:05,000\nHello",
                            content_type="text/plain",
                        ),
                        "file_format": VideoCaption.Format.SRT,
                        "is_default": False,
                    },
                ],
            }
        )

        assert serializer.is_valid(), serializer.errors

        captions = serializer.validated_data["captions"]

        assert len(captions) == 2
        assert captions[0]["language"] == "en"
        assert captions[1]["language"] == "fa"
        assert captions[0]["file_format"] == VideoCaption.Format.VTT
        assert captions[1]["file_format"] == VideoCaption.Format.SRT

    def test_nested_caption_requires_language(self):
        serializer = VideoContentSerializer(
            data={
                "captions": [
                    {
                        "label": "English",
                        "file": SimpleUploadedFile(
                            "english.vtt",
                            b"WEBVTT",
                            content_type="text/vtt",
                        ),
                        "file_format": VideoCaption.Format.VTT,
                    }
                ],
            }
        )

        assert not serializer.is_valid()
        assert "captions" in serializer.errors
        assert "language" in serializer.errors["captions"][0]

    def test_nested_caption_requires_file(self):
        serializer = VideoContentSerializer(
            data={
                "captions": [
                    {
                        "language": "en",
                        "label": "English",
                        "file_format": VideoCaption.Format.VTT,
                    }
                ],
            }
        )

        assert not serializer.is_valid()
        assert "captions" in serializer.errors
        assert "file" in serializer.errors["captions"][0]

    def test_nested_caption_requires_file_format(self):
        serializer = VideoContentSerializer(
            data={
                "captions": [
                    {
                        "language": "en",
                        "file": SimpleUploadedFile(
                            "english.vtt",
                            b"WEBVTT",
                            content_type="text/vtt",
                        ),
                    }
                ],
            }
        )

        assert not serializer.is_valid()
        assert "captions" in serializer.errors
        assert "file_format" in serializer.errors["captions"][0]

    def test_nested_caption_rejects_invalid_file_format(self):
        serializer = VideoContentSerializer(
            data={
                "captions": [
                    {
                        "language": "en",
                        "file": SimpleUploadedFile(
                            "english.txt",
                            b"caption",
                            content_type="text/plain",
                        ),
                        "file_format": "txt",
                    }
                ],
            }
        )

        assert not serializer.is_valid()
        assert "captions" in serializer.errors
        assert "file_format" in serializer.errors["captions"][0]

    def test_nested_caption_rejects_invalid_language_length(self):
        serializer = VideoContentSerializer(
            data={
                "captions": [
                    {
                        "language": "abcdefghijk",
                        "file": SimpleUploadedFile(
                            "caption.vtt",
                            b"WEBVTT",
                            content_type="text/vtt",
                        ),
                        "file_format": VideoCaption.Format.VTT,
                    }
                ],
            }
        )

        assert not serializer.is_valid()
        assert "captions" in serializer.errors
        assert "language" in serializer.errors["captions"][0]

    def test_nested_captions_use_many_serializer(self):
        serializer = VideoContentSerializer()

        captions_field = serializer.fields["captions"]

        assert captions_field.many is True
        assert isinstance(captions_field.child, VideoCaptionSerializer)

    def test_nested_captions_are_not_required(self):
        serializer = VideoContentSerializer()

        assert serializer.fields["captions"].required is False

    def test_accepts_complete_data(self):
        serializer = VideoContentSerializer(
            data={
                "id": 5,
                "source": VideoContent.Source.FILE,
                "video_file": SimpleUploadedFile(
                    "lesson.mp4",
                    b"video content",
                    content_type="video/mp4",
                ),
                "external_url": "",
                "duration": "00:12:30",
                "transcript": "Complete transcript.",
                "text": "Additional video text.",
                "captions": [
                    {
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
                ],
            }
        )

        assert serializer.is_valid(), serializer.errors

        validated_data = serializer.validated_data

        assert validated_data["id"] == 5
        assert validated_data["source"] == VideoContent.Source.FILE
        assert validated_data["video_file"].name == "lesson.mp4"
        assert validated_data["external_url"] == ""
        assert validated_data["duration"] == datetime.timedelta(
            minutes=12,
            seconds=30,
        )
        assert validated_data["transcript"] == "Complete transcript."
        assert validated_data["text"] == "Additional video text."
        assert len(validated_data["captions"]) == 1

    def test_serializes_instance_without_captions(self, video_content):
        serializer = VideoContentSerializer(instance=video_content)

        data = serializer.data

        assert set(data) == {
            "id",
            "source",
            "video_file",
            "external_url",
            "duration",
            "transcript",
            "text",
            "captions",
        }

        assert data["id"] == video_content.id
        assert data["source"] == VideoContent.Source.URL
        assert data["external_url"] == "https://example.com/video.mp4"
        assert data["video_file"] is None
        assert data["duration"] is None
        assert data["transcript"] == ""
        assert data["text"] == ""
        assert data["captions"] == []

    def test_serializes_instance_with_captions(
        self,
        video_content,
        video_caption,
    ):
        serializer = VideoContentSerializer(instance=video_content)

        data = serializer.data

        assert len(data["captions"]) == 1

        caption = data["captions"][0]

        assert caption["id"] == video_caption.id
        assert caption["language"] == "en"
        assert caption["label"] == "English"
        assert caption["file_format"] == VideoCaption.Format.VTT
        assert caption["is_default"] is False
        assert caption["file"].endswith("captions.vtt")

    def test_serializes_duration(self, video_content):
        video_content.duration = datetime.timedelta(
            minutes=5,
            seconds=30,
        )
        video_content.save(update_fields=["duration"])

        serializer = VideoContentSerializer(instance=video_content)

        assert serializer.data["duration"] == "00:05:30"

    def test_serializes_uploaded_video_file(
        self,
        video_content,
        video_file,
    ):
        video_content.video_file.save(
            "lesson-video.mp4",
            video_file,
            save=True,
        )

        serializer = VideoContentSerializer(instance=video_content)

        file_value = serializer.data["video_file"]

        assert file_value
        assert file_value.endswith("lesson-video.mp4")

    def test_partial_update_accepts_source(self, video_content):
        serializer = VideoContentSerializer(
            instance=video_content,
            data={"source": VideoContent.Source.FILE},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["source"] == VideoContent.Source.FILE

    def test_partial_update_accepts_external_url(self, video_content):
        url = "https://example.com/updated-video.mp4"

        serializer = VideoContentSerializer(
            instance=video_content,
            data={"external_url": url},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["external_url"] == url

    def test_partial_update_accepts_video_file(
        self,
        video_content,
        video_file,
    ):
        serializer = VideoContentSerializer(
            instance=video_content,
            data={"video_file": video_file},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["video_file"].name == "lesson-video.mp4"

    def test_partial_update_accepts_duration(self, video_content):
        serializer = VideoContentSerializer(
            instance=video_content,
            data={"duration": "00:10:00"},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["duration"] == datetime.timedelta(
            minutes=10,
        )

    def test_partial_update_accepts_transcript(self, video_content):
        serializer = VideoContentSerializer(
            instance=video_content,
            data={"transcript": "Updated transcript."},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["transcript"] == "Updated transcript."

    def test_partial_update_accepts_text(self, video_content):
        serializer = VideoContentSerializer(
            instance=video_content,
            data={"text": "Updated text."},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["text"] == "Updated text."

    def test_partial_update_accepts_captions(
        self,
        video_content,
    ):
        serializer = VideoContentSerializer(
            instance=video_content,
            data={
                "captions": [
                    {
                        "language": "fa",
                        "label": "Persian",
                        "file": SimpleUploadedFile(
                            "persian.vtt",
                            b"WEBVTT",
                            content_type="text/vtt",
                        ),
                        "file_format": VideoCaption.Format.VTT,
                        "is_default": True,
                    }
                ]
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        captions = serializer.validated_data["captions"]

        assert len(captions) == 1
        assert captions[0]["language"] == "fa"
        assert captions[0]["label"] == "Persian"

    def test_partial_update_accepts_id(self, video_content):
        serializer = VideoContentSerializer(
            instance=video_content,
            data={"id": 999},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["id"] == 999

    def test_partial_update_does_not_require_other_fields(
        self,
        video_content,
    ):
        serializer = VideoContentSerializer(
            instance=video_content,
            data={"text": "Updated text."},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data == {
            "text": "Updated text.",
        }

    def test_does_not_expose_content_field(self):
        serializer = VideoContentSerializer()

        assert "content" not in serializer.fields

    def test_does_not_expose_source_model_validation(self):
        serializer = VideoContentSerializer()

        assert "content" not in serializer.fields

    def test_does_not_expose_model_internal_fields(self):
        serializer = VideoContentSerializer()

        assert "pk" not in serializer.fields
