from datetime import timedelta
from unittest.mock import Mock

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError

from curriculums.models import LessonContent, VideoContent
from curriculums.models.video_content import video_upload_path


@pytest.fixture
def lesson_content(lesson):
    return LessonContent.objects.create(
        lesson=lesson,
        title="Introduction Video",
        content_type=LessonContent.Type.VIDEO,
        order=1,
    )


@pytest.fixture
def video_content(lesson_content):
    return VideoContent.objects.create(
        content=lesson_content,
        source=VideoContent.Source.FILE,
        video_file=SimpleUploadedFile(
            "example.mp4",
            b"fake video content",
            content_type="video/mp4",
        ),
    )


class TestFileUploadPath:
    def test_video_upload_path_uses_owner_course_lesson_content_and_filename(
        self,
        test_user,
        course,
        section,
        lesson,
        lesson_content,
    ):
        instance = Mock()
        instance.content = lesson_content
        instance.content_id = lesson_content.pk

        expected = (
            f"courses/"
            f"{test_user.pk}/"
            f"{course.pk}/"
            f"lesson_contents/"
            f"{lesson_content.pk}/"
            f"videos/"
            f"example.mp4"
        )

        # The actual helper receives an instance whose `content`
        # points to LessonContent.
        result = video_upload_path(instance, "example.mp4")

        assert result == expected

    def test_video_upload_path_preserves_filename(
        self,
        lesson_content,
    ):
        instance = Mock()
        instance.content = lesson_content
        instance.content_id = lesson_content.pk

        result = video_upload_path(instance, "my-video-01.mp4")

        assert result.endswith(
            f"lesson_contents/{lesson_content.pk}/videos/my-video-01.mp4"
        )

    def test_video_upload_path_handles_filename_with_spaces(
        self,
        lesson_content,
    ):
        instance = Mock()
        instance.content = lesson_content
        instance.content_id = lesson_content.pk

        result = video_upload_path(instance, "my lesson video.mp4")

        assert result.endswith(
            f"lesson_contents/{lesson_content.pk}/videos/my lesson video.mp4"
        )


class TestVideoContentCreation:
    def test_creates_video_content_with_uploaded_file(
        self,
        lesson_content,
    ):
        video_file = SimpleUploadedFile(
            "example.mp4",
            b"fake video content",
            content_type="video/mp4",
        )

        video = VideoContent.objects.create(
            content=lesson_content,
            source=VideoContent.Source.FILE,
            video_file=video_file,
        )

        assert video.pk is not None
        assert video.content == lesson_content
        assert video.source == VideoContent.Source.FILE
        assert video.video_file

    def test_source_defaults_to_file(
        self,
        lesson_content,
    ):
        video = VideoContent.objects.create(
            content=lesson_content,
            video_file=SimpleUploadedFile(
                "example.mp4",
                b"fake video content",
                content_type="video/mp4",
            ),
        )

        assert video.source == VideoContent.Source.FILE

    def test_external_url_source_can_be_created_without_file(
        self,
        lesson_content,
    ):
        video = VideoContent.objects.create(
            content=lesson_content,
            source=VideoContent.Source.URL,
            external_url="https://example.com/video",
        )
        assert video.pk is not None
        assert video.source == VideoContent.Source.URL
        assert not video.video_file
        assert video.external_url == "https://example.com/video"

    def test_text_is_optional(
        self,
        lesson_content,
    ):
        video = VideoContent.objects.create(
            content=lesson_content,
            source=VideoContent.Source.URL,
            external_url="https://example.com/video",
        )

        assert video.text == ""

    def test_transcript_is_optional(
        self,
        lesson_content,
    ):
        video = VideoContent.objects.create(
            content=lesson_content,
            source=VideoContent.Source.URL,
            external_url="https://example.com/video",
        )

        assert video.transcript == ""

    def test_duration_is_optional(
        self,
        lesson_content,
    ):
        video = VideoContent.objects.create(
            content=lesson_content,
            source=VideoContent.Source.URL,
            external_url="https://example.com/video",
        )

        assert video.duration is None


class TestVideoContentValidation:
    def test_file_source_requires_video_file(
        self,
        lesson_content,
    ):
        video = VideoContent(
            content=lesson_content,
            source=VideoContent.Source.FILE,
        )

        with pytest.raises(ValidationError) as exc_info:
            video.full_clean()

        assert exc_info.value.message_dict == {
            "video_file": ["An video file is required."]
        }

    def test_file_source_is_valid_with_video_file(
        self,
        lesson_content,
    ):
        video = VideoContent(
            content=lesson_content,
            source=VideoContent.Source.FILE,
            video_file=SimpleUploadedFile(
                "example.mp4",
                b"fake video content",
                content_type="video/mp4",
            ),
        )

        video.full_clean()

    def test_url_source_requires_external_url(
        self,
        lesson_content,
    ):
        video = VideoContent(
            content=lesson_content,
            source=VideoContent.Source.URL,
        )

        with pytest.raises(ValidationError) as exc_info:
            video.full_clean()

        assert exc_info.value.message_dict == {
            "external_url": ["A video URL is required."]
        }

    def test_url_source_is_valid_with_external_url(
        self,
        lesson_content,
    ):
        video = VideoContent(
            content=lesson_content,
            source=VideoContent.Source.URL,
            external_url="https://example.com/video.mp4",
        )

        video.full_clean()

    def test_non_file_source_does_not_require_video_file(
        self,
        lesson_content,
    ):
        video = VideoContent(
            content=lesson_content,
            source=VideoContent.Source.URL,
            external_url="https://example.com/video.mp4",
        )

        video.full_clean()

        assert not video.video_file

    def test_file_source_does_not_require_external_url(
        self,
        lesson_content,
    ):
        video = VideoContent(
            content=lesson_content,
            source=VideoContent.Source.FILE,
            video_file=SimpleUploadedFile(
                "example.mp4",
                b"fake video content",
                content_type="video/mp4",
            ),
        )

        video.full_clean()

        assert video.external_url == ""


class TestVideoContentRelations:
    def test_content_has_reverse_video_relation(
        self,
        lesson_content,
        video_content,
    ):
        assert lesson_content.video == video_content

    def test_content_is_required(
        self,
        db,
    ):
        video = VideoContent(
            source=VideoContent.Source.URL,
            external_url="https://example.com/video",
        )

        with pytest.raises(ValidationError):
            video.full_clean()

    def test_content_is_one_to_one(
        self,
        lesson_content,
        video_content,
    ):
        duplicate = VideoContent(
            content=lesson_content,
            source=VideoContent.Source.URL,
            external_url="https://example.com/video",
        )

        with pytest.raises(ValidationError):
            duplicate.full_clean()

    def test_content_is_unique_at_database_level(
        self,
        lesson_content,
        video_content,
    ):
        duplicate = VideoContent(
            content=lesson_content,
            source=VideoContent.Source.URL,
            external_url="https://example.com/video",
        )

        with pytest.raises(IntegrityError):
            duplicate.save(force_insert=True)


class TestVideoContentDeletion:
    def test_deleting_lesson_content_deletes_video_content(
        self,
        lesson_content,
        video_content,
    ):
        video_id = video_content.pk

        lesson_content.delete()

        assert not VideoContent.objects.filter(pk=video_id).exists()


class TestVideoContentStringRepresentation:
    def test_str_returns_content_title(
        self,
        lesson_content,
        video_content,
    ):
        assert str(video_content) == lesson_content.title


class TestVideoContentFields:
    @pytest.mark.parametrize(
        "source",
        [
            VideoContent.Source.FILE,
            VideoContent.Source.URL,
        ],
    )
    def test_valid_source_choices(
        self,
        lesson_content,
        source,
    ):
        video = VideoContent(
            content=lesson_content,
            source=source,
            video_file=(
                SimpleUploadedFile(
                    "example.mp4",
                    b"fake video content",
                    content_type="video/mp4",
                )
                if source == VideoContent.Source.FILE
                else None
            ),
            external_url=(
                "https://example.com/video" if source == VideoContent.Source.URL else ""
            ),
        )

        video.full_clean()

    def test_invalid_source_is_rejected_by_model_validation(
        self,
        lesson_content,
    ):
        video = VideoContent(
            content=lesson_content,
            source="invalid",
            external_url="https://example.com/video",
        )

        with pytest.raises(ValidationError) as exc_info:
            video.full_clean()

        assert "source" in exc_info.value.message_dict

    @pytest.mark.parametrize(
        "duration",
        [
            timedelta(seconds=0),
            timedelta(seconds=30),
            timedelta(minutes=10),
            timedelta(hours=2),
        ],
    )
    def test_valid_duration_values(
        self,
        lesson_content,
        duration,
    ):
        video = VideoContent(
            content=lesson_content,
            source=VideoContent.Source.URL,
            external_url="https://example.com/video",
            duration=duration,
        )

        video.full_clean()

        assert video.duration == duration

    def test_video_file_can_be_empty(
        self,
        lesson_content,
    ):
        video = VideoContent(
            content=lesson_content,
            source=VideoContent.Source.URL,
            external_url="https://example.com/video",
            video_file=None,
        )

        video.full_clean()

        assert not video.video_file
