import datetime

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from curriculums.models import VideoContent
from curriculums.tests.factories import (
    LessonContentFactory,
    VideoContentFactory,
)
from utils.test.files import file_field


@pytest.mark.django_db
class TestVideoContentModel:
    """Tests for the VideoContent model."""

    @pytest.fixture
    def content(self):
        return LessonContentFactory()

    def test_create_uploaded_video(self, content):
        """A video content using an uploaded file can be created."""
        video = VideoContent.objects.create(
            content=content,
            source=VideoContent.Source.FILE,
            uploaded_video=file_field(
                "video.mp4",
                b"video-content",
            ),
            captions=file_field(
                "captions.vtt",
                b"WEBVTT",
            ),
            duration=datetime.timedelta(minutes=10),
            transcript="Video transcript",
        )

        assert video.content == content
        assert video.source == VideoContent.Source.FILE
        assert video.uploaded_video.name.endswith("video.mp4")
        assert video.captions.name.endswith("captions.vtt")
        assert video.duration == datetime.timedelta(minutes=10)
        assert video.transcript == "Video transcript"

    def test_create_external_video(self, content):
        """A video content using an external URL can be created."""
        video = VideoContent.objects.create(
            content=content,
            source=VideoContent.Source.URL,
            external_url="https://www.youtube.com/watch?v=abcdefghijk",
        )

        assert video.source == VideoContent.Source.URL
        assert video.external_url == "https://www.youtube.com/watch?v=abcdefghijk"

    def test_string_representation(self):
        """The string representation should return the lesson content title."""
        video = VideoContentFactory()

        assert str(video) == video.content.title

    def test_duration_is_optional(self, content):
        """Duration is optional."""
        video = VideoContent.objects.create(
            content=content,
            source=VideoContent.Source.URL,
            external_url="https://example.com/video",
        )

        assert video.duration is None

    def test_transcript_is_optional(self, content):
        """Transcript is optional."""
        video = VideoContent.objects.create(
            content=content,
            source=VideoContent.Source.URL,
            external_url="https://example.com/video",
        )

        assert video.transcript == ""

    def test_captions_are_optional(self, content):
        """Captions are optional."""
        video = VideoContent.objects.create(
            content=content,
            source=VideoContent.Source.URL,
            external_url="https://example.com/video",
        )

        assert not video.captions

    def test_requires_uploaded_video_for_file_source(self, content):
        """Uploaded file source requires a video file."""
        video = VideoContent(
            content=content,
            source=VideoContent.Source.FILE,
        )

        with pytest.raises(ValidationError) as exc:
            video.clean()

        assert "uploaded_video" in exc.value.message_dict

    def test_requires_external_url_for_url_source(self, content):
        """External URL source requires a URL."""
        video = VideoContent(
            content=content,
            source=VideoContent.Source.URL,
        )

        with pytest.raises(ValidationError) as exc:
            video.clean()

        assert "external_url" in exc.value.message_dict

    def test_uploaded_video_passes_validation(self, content):
        """A valid uploaded video passes validation."""
        video = VideoContent(
            content=content,
            source=VideoContent.Source.FILE,
            uploaded_video=file_field(
                "video.mp4",
                b"video-content",
            ),
        )

        video.clean()

    def test_external_video_passes_validation(self, content):
        """A valid external video passes validation."""
        video = VideoContent(
            content=content,
            source=VideoContent.Source.URL,
            external_url="https://vimeo.com/123456",
        )

        video.clean()

    def test_content_can_have_only_one_video(self, content):
        """Each lesson content can have only one video."""
        VideoContentFactory(content=content)

        with pytest.raises(IntegrityError):
            VideoContentFactory(content=content)
