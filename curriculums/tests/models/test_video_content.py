import datetime

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from curriculums.models import VideoCaption, VideoContent
from curriculums.tests.factories import (
    LessonContentFactory,
    VideoCaptionFactory,
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
            video_file=file_field(
                "video.mp4",
                b"video-content",
            ),
            duration=datetime.timedelta(minutes=10),
            transcript="Video transcript",
        )

        assert video.content == content
        assert video.source == VideoContent.Source.FILE
        assert video.video_file.name.endswith("video.mp4")
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

    def test_requires_video_file_for_file_source(self, content):
        """Uploaded file source requires a video file."""
        video = VideoContent(
            content=content,
            source=VideoContent.Source.FILE,
        )

        with pytest.raises(ValidationError) as exc:
            video.clean()

        assert "video_file" in exc.value.message_dict

    def test_requires_external_url_for_url_source(self, content):
        """External URL source requires a URL."""
        video = VideoContent(
            content=content,
            source=VideoContent.Source.URL,
        )

        with pytest.raises(ValidationError) as exc:
            video.clean()

        assert "external_url" in exc.value.message_dict

    def test_video_file_passes_validation(self, content):
        """A valid uploaded video passes validation."""
        video = VideoContent(
            content=content,
            source=VideoContent.Source.FILE,
            video_file=file_field(
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


@pytest.mark.django_db
class TestVideoCaptionModel:
    """Tests for the VideoCaption model."""

    @pytest.fixture
    def video(self):
        return VideoContentFactory()

    def test_create_video_caption(self, video):
        """A video caption can be created."""
        caption = VideoCaptionFactory(
            video=video,
            language="en",
            label="English",
            file_format=VideoCaption.Format.VTT,
            is_default=True,
        )

        assert caption.video == video
        assert caption.language == "en"
        assert caption.label == "English"
        assert caption.file_format == VideoCaption.Format.VTT
        assert caption.is_default is True
        assert caption.file

    def test_label_is_optional(self, video):
        """Label may be blank."""
        caption = VideoCaptionFactory(
            video=video,
            label="",
        )

        assert caption.label == ""

    def test_is_default_defaults_to_false(self, video):
        """is_default defaults to False."""
        caption = VideoCaptionFactory(
            video=video,
        )

        assert caption.is_default is False

    def test_video_can_have_multiple_caption_languages(self, video):
        """A video can have captions in different languages."""
        english = VideoCaptionFactory(
            video=video,
            language="en",
        )

        persian = VideoCaptionFactory(
            video=video,
            language="fa",
        )

        assert set(video.captions.all()) == {
            english,
            persian,
        }

    def test_same_language_can_be_used_for_different_videos(self):
        """Different videos may use the same language."""
        video1 = VideoContentFactory()
        video2 = VideoContentFactory()

        caption1 = VideoCaptionFactory(
            video=video1,
            language="en",
        )

        caption2 = VideoCaptionFactory(
            video=video2,
            language="en",
        )

        assert caption1.language == caption2.language == "en"

    def test_same_video_cannot_have_duplicate_language(self, video):
        """A video cannot have two captions with the same language."""
        VideoCaptionFactory(
            video=video,
            language="en",
        )

        with pytest.raises(IntegrityError):
            VideoCaptionFactory(
                video=video,
                language="en",
            )

    def test_only_one_default_caption_is_allowed_per_video(self, video):
        """A video can have only one default caption."""
        VideoCaptionFactory(
            video=video,
            language="en",
            is_default=True,
        )

        with pytest.raises(IntegrityError):
            VideoCaptionFactory(
                video=video,
                language="fa",
                is_default=True,
            )

    def test_multiple_non_default_captions_are_allowed(self, video):
        """Multiple non-default captions are allowed."""
        english = VideoCaptionFactory(
            video=video,
            language="en",
            is_default=False,
        )

        persian = VideoCaptionFactory(
            video=video,
            language="fa",
            is_default=False,
        )

        assert english.is_default is False
        assert persian.is_default is False

    def test_default_caption_on_different_videos_is_allowed(self):
        """Each video may have its own default caption."""
        video1 = VideoContentFactory()
        video2 = VideoContentFactory()

        caption1 = VideoCaptionFactory(
            video=video1,
            language="en",
            is_default=True,
        )

        caption2 = VideoCaptionFactory(
            video=video2,
            language="en",
            is_default=True,
        )

        assert caption1.is_default is True
        assert caption2.is_default is True

    def test_deleting_video_deletes_captions(self):
        """Deleting a video cascades to its captions."""
        video = VideoContentFactory()

        caption = VideoCaptionFactory(
            video=video,
        )

        video.delete()

        assert not VideoCaption.objects.filter(
            pk=caption.pk,
        ).exists()

    def test_related_name_returns_video_captions(self, video):
        """Captions are accessible via the related name."""
        caption1 = VideoCaptionFactory(
            video=video,
            language="en",
        )

        caption2 = VideoCaptionFactory(
            video=video,
            language="fa",
        )

        assert set(video.captions.all()) == {
            caption1,
            caption2,
        }

    def test_file_is_uploaded_to_expected_location(self):
        """Caption files are stored in the expected upload directory."""
        caption = VideoCaptionFactory()

        assert caption.file.name.startswith("courses/captions/")

    def test_string_representation(self):
        """String representation contains video and language."""
        caption = VideoCaptionFactory(
            language="en",
        )

        assert str(caption) == f"{caption.video} (en)"
