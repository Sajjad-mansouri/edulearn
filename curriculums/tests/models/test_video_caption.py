import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError

from curriculums.models.lesson_content import LessonContent
from curriculums.models.video_content import (
    VideoCaption,
    VideoContent,
    caption_upload_path,
)


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


@pytest.fixture
def caption(video_content):
    return VideoCaption.objects.create(
        video=video_content,
        language="en",
        label="English",
        file=SimpleUploadedFile(
            "english.vtt",
            b"WEBVTT\n\n00:00.000 --> 00:02.000\nHello",
            content_type="text/vtt",
        ),
        file_format=VideoCaption.Format.VTT,
    )


class TestCaptionUploadPath:
    def test_caption_upload_path_uses_expected_directory_structure(
        self,
        video_content,
    ):
        caption = VideoCaption(
            video=video_content,
        )

        result = caption_upload_path(caption, "english.vtt")

        expected = (
            f"courses/"
            f"{video_content.content.lesson.section.course.owner_id}/"
            f"{video_content.content.lesson.section.course.id}/"
            f"lesson_contents/"
            f"{video_content.content_id}/"
            f"captions/"
            f"english.vtt"
        )

        assert result == expected


class TestVideoCaptionCreation:
    def test_creates_caption(
        self,
        video_content,
    ):
        caption = VideoCaption.objects.create(
            video=video_content,
            language="en",
            label="English",
            file=SimpleUploadedFile(
                "english.vtt",
                b"WEBVTT",
                content_type="text/vtt",
            ),
            file_format=VideoCaption.Format.VTT,
        )

        assert caption.pk is not None
        assert caption.video == video_content
        assert caption.language == "en"
        assert caption.label == "English"
        assert caption.file_format == VideoCaption.Format.VTT
        assert caption.file

    def test_label_defaults_to_empty_string(
        self,
        video_content,
    ):
        caption = VideoCaption.objects.create(
            video=video_content,
            language="en",
            file=SimpleUploadedFile(
                "english.vtt",
                b"WEBVTT",
                content_type="text/vtt",
            ),
            file_format=VideoCaption.Format.VTT,
        )

        assert caption.label == ""

    def test_is_default_defaults_to_false(
        self,
        video_content,
    ):
        caption = VideoCaption.objects.create(
            video=video_content,
            language="en",
            file=SimpleUploadedFile(
                "english.vtt",
                b"WEBVTT",
                content_type="text/vtt",
            ),
            file_format=VideoCaption.Format.VTT,
        )

        assert caption.is_default is False


class TestVideoCaptionStringRepresentation:
    def test_str_returns_video_and_language(
        self,
        video_content,
        caption,
    ):
        assert str(caption) == f"{video_content} (en)"

    def test_str_uses_language_exactly(
        self,
        video_content,
    ):
        caption = VideoCaption(
            video=video_content,
            language="fa",
        )

        assert str(caption) == f"{video_content} (fa)"


class TestVideoCaptionValidation:
    @pytest.mark.parametrize(
        "file_format",
        [
            VideoCaption.Format.VTT,
            VideoCaption.Format.SRT,
        ],
    )
    def test_valid_file_formats(
        self,
        video_content,
        file_format,
    ):
        caption = VideoCaption(
            video=video_content,
            language="en",
            file=SimpleUploadedFile(
                "caption.vtt",
                b"caption content",
                content_type="text/plain",
            ),
            file_format=file_format,
        )

        caption.full_clean()

    def test_invalid_file_format_is_rejected(
        self,
        video_content,
    ):
        caption = VideoCaption(
            video=video_content,
            language="en",
            file=SimpleUploadedFile(
                "caption.txt",
                b"caption content",
                content_type="text/plain",
            ),
            file_format="invalid",
        )

        with pytest.raises(ValidationError) as exc_info:
            caption.full_clean()

        assert "file_format" in exc_info.value.message_dict

    def test_language_is_required(
        self,
        video_content,
    ):
        caption = VideoCaption(
            video=video_content,
            language="",
            file=SimpleUploadedFile(
                "caption.vtt",
                b"WEBVTT",
                content_type="text/vtt",
            ),
            file_format=VideoCaption.Format.VTT,
        )

        with pytest.raises(ValidationError) as exc_info:
            caption.full_clean()

        assert "language" in exc_info.value.message_dict

    def test_file_is_required(
        self,
        video_content,
    ):
        caption = VideoCaption(
            video=video_content,
            language="en",
            file_format=VideoCaption.Format.VTT,
        )

        with pytest.raises(ValidationError) as exc_info:
            caption.full_clean()

        assert "file" in exc_info.value.message_dict

    def test_language_max_length_is_10(
        self,
        video_content,
    ):
        caption = VideoCaption(
            video=video_content,
            language="abcdefghij",
            file=SimpleUploadedFile(
                "caption.vtt",
                b"WEBVTT",
                content_type="text/plain",
            ),
            file_format=VideoCaption.Format.VTT,
        )

        caption.full_clean()

    def test_language_longer_than_10_is_rejected(
        self,
        video_content,
    ):
        caption = VideoCaption(
            video=video_content,
            language="abcdefghijk",
            file=SimpleUploadedFile(
                "caption.vtt",
                b"WEBVTT",
                content_type="text/plain",
            ),
            file_format=VideoCaption.Format.VTT,
        )

        with pytest.raises(ValidationError) as exc_info:
            caption.full_clean()

        assert "language" in exc_info.value.message_dict

    def test_label_max_length_is_50(
        self,
        video_content,
    ):
        caption = VideoCaption(
            video=video_content,
            language="en",
            label="a" * 50,
            file=SimpleUploadedFile(
                "caption.vtt",
                b"WEBVTT",
                content_type="text/plain",
            ),
            file_format=VideoCaption.Format.VTT,
        )

        caption.full_clean()

    def test_label_longer_than_50_is_rejected(
        self,
        video_content,
    ):
        caption = VideoCaption(
            video=video_content,
            language="en",
            label="a" * 51,
            file=SimpleUploadedFile(
                "caption.vtt",
                b"WEBVTT",
                content_type="text/plain",
            ),
            file_format=VideoCaption.Format.VTT,
        )

        with pytest.raises(ValidationError) as exc_info:
            caption.full_clean()

        assert "label" in exc_info.value.message_dict


class TestVideoCaptionRelations:
    def test_video_has_reverse_captions_relation(
        self,
        video_content,
        caption,
    ):
        assert list(video_content.captions.all()) == [caption]

    def test_multiple_languages_are_allowed_for_same_video(
        self,
        video_content,
        caption,
    ):
        second_caption = VideoCaption.objects.create(
            video=video_content,
            language="fa",
            label="Persian",
            file=SimpleUploadedFile(
                "persian.vtt",
                b"WEBVTT",
                content_type="text/vtt",
            ),
            file_format=VideoCaption.Format.VTT,
        )

        assert video_content.captions.count() == 2
        assert {caption.language, second_caption.language} == {"en", "fa"}

    def test_same_language_is_not_allowed_twice_for_same_video(
        self,
        video_content,
        caption,
    ):
        duplicate = VideoCaption(
            video=video_content,
            language="en",
            label="Another English",
            file=SimpleUploadedFile(
                "english-2.vtt",
                b"WEBVTT",
                content_type="text/vtt",
            ),
            file_format=VideoCaption.Format.VTT,
        )

        with pytest.raises(ValidationError) as exc_info:
            duplicate.full_clean()

        assert "__all__" in exc_info.value.message_dict

    def test_same_language_is_enforced_at_database_level(
        self,
        video_content,
        caption,
    ):
        duplicate = VideoCaption(
            video=video_content,
            language="en",
            label="Another English",
            file=SimpleUploadedFile(
                "english-2.vtt",
                b"WEBVTT",
                content_type="text/vtt",
            ),
            file_format=VideoCaption.Format.VTT,
        )

        with pytest.raises(IntegrityError):
            duplicate.save(force_insert=True)


class TestVideoCaptionDefaultConstraint:
    def test_one_default_caption_is_allowed(
        self,
        video_content,
    ):
        caption = VideoCaption.objects.create(
            video=video_content,
            language="en",
            file=SimpleUploadedFile(
                "english.vtt",
                b"WEBVTT",
                content_type="text/vtt",
            ),
            file_format=VideoCaption.Format.VTT,
            is_default=True,
        )

        assert caption.is_default is True

    def test_second_default_caption_is_not_allowed_for_same_video(
        self,
        video_content,
    ):
        VideoCaption.objects.create(
            video=video_content,
            language="en",
            file=SimpleUploadedFile(
                "english.vtt",
                b"WEBVTT",
                content_type="text/vtt",
            ),
            file_format=VideoCaption.Format.VTT,
            is_default=True,
        )

        second_default = VideoCaption(
            video=video_content,
            language="fa",
            file=SimpleUploadedFile(
                "persian.vtt",
                b"WEBVTT",
                content_type="text/vtt",
            ),
            file_format=VideoCaption.Format.VTT,
            is_default=True,
        )

        with pytest.raises(ValidationError) as exc_info:
            second_default.full_clean()

        assert "__all__" in exc_info.value.message_dict

    def test_second_default_caption_is_enforced_at_database_level(
        self,
        video_content,
    ):
        VideoCaption.objects.create(
            video=video_content,
            language="en",
            file=SimpleUploadedFile(
                "english.vtt",
                b"WEBVTT",
                content_type="text/vtt",
            ),
            file_format=VideoCaption.Format.VTT,
            is_default=True,
        )

        second_default = VideoCaption(
            video=video_content,
            language="fa",
            file=SimpleUploadedFile(
                "persian.vtt",
                b"WEBVTT",
                content_type="text/vtt",
            ),
            file_format=VideoCaption.Format.VTT,
            is_default=True,
        )

        with pytest.raises(IntegrityError):
            second_default.save(force_insert=True)

    def test_multiple_non_default_captions_are_allowed(
        self,
        video_content,
    ):
        first = VideoCaption.objects.create(
            video=video_content,
            language="en",
            file=SimpleUploadedFile(
                "english.vtt",
                b"WEBVTT",
                content_type="text/plain",
            ),
            file_format=VideoCaption.Format.VTT,
            is_default=False,
        )

        second = VideoCaption.objects.create(
            video=video_content,
            language="fa",
            file=SimpleUploadedFile(
                "persian.vtt",
                b"WEBVTT",
                content_type="text/plain",
            ),
            file_format=VideoCaption.Format.VTT,
            is_default=False,
        )

        assert first.is_default is False
        assert second.is_default is False


class TestVideoCaptionDeletion:
    def test_deleting_video_deletes_captions(
        self,
        video_content,
        caption,
    ):
        caption_id = caption.pk

        video_content.delete()

        assert not VideoCaption.objects.filter(pk=caption_id).exists()

    def test_deleting_video_removes_all_captions(
        self,
        video_content,
    ):
        VideoCaption.objects.create(
            video=video_content,
            language="en",
            file=SimpleUploadedFile(
                "english.vtt",
                b"WEBVTT",
                content_type="text/plain",
            ),
            file_format=VideoCaption.Format.VTT,
        )

        VideoCaption.objects.create(
            video=video_content,
            language="fa",
            file=SimpleUploadedFile(
                "persian.vtt",
                b"WEBVTT",
                content_type="text/plain",
            ),
            file_format=VideoCaption.Format.VTT,
        )

        video_content.delete()

        assert VideoCaption.objects.count() == 0


class TestVideoCaptionUpdate:
    def test_caption_can_be_updated(
        self,
        caption,
    ):
        caption.language = "fa"
        caption.label = "Persian"
        caption.file_format = VideoCaption.Format.SRT
        caption.is_default = True
        caption.save()

        caption.refresh_from_db()

        assert caption.language == "fa"
        assert caption.label == "Persian"
        assert caption.file_format == VideoCaption.Format.SRT
        assert caption.is_default is True
