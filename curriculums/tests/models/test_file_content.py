import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError

from curriculums.models.file_content import FileContent, file_upload_path
from curriculums.models.lesson_content import LessonContent


@pytest.fixture
def lesson_content(lesson):
    return LessonContent.objects.create(
        lesson=lesson,
        title="Downloadable Resources",
        content_type=LessonContent.Type.FILE,
        order=1,
    )


@pytest.fixture
def file_content(lesson_content):
    return FileContent.objects.create(
        content=lesson_content,
        file=SimpleUploadedFile(
            "document.pdf",
            b"fake pdf content",
            content_type="application/pdf",
        ),
        display_name="Course Document",
        description="Course reference document.",
    )


class TestFileUploadPath:
    def test_file_upload_path_returns_expected_path(
        self,
        lesson_content,
    ):
        file_content = FileContent(
            content=lesson_content,
        )

        result = file_upload_path(
            file_content,
            "document.pdf",
        )

        expected = (
            f"courses/"
            f"{lesson_content.lesson.section.course.owner_id}/"
            f"{lesson_content.lesson.section.course.id}/"
            f"lesson_contents/"
            f"{lesson_content.id}/"
            f"file/"
            f"document.pdf"
        )

        assert result == expected

    def test_file_upload_path_preserves_filename(
        self,
        lesson_content,
    ):
        file_content = FileContent(
            content=lesson_content,
        )

        result = file_upload_path(
            file_content,
            "my-document.pdf",
        )

        assert result.endswith(
            f"lesson_contents/{lesson_content.id}/file/my-document.pdf"
        )

    def test_file_upload_path_handles_filename_with_spaces(
        self,
        lesson_content,
    ):
        file_content = FileContent(
            content=lesson_content,
        )

        result = file_upload_path(
            file_content,
            "course document.pdf",
        )

        assert result.endswith(
            f"lesson_contents/{lesson_content.id}/file/course document.pdf"
        )

    def test_file_upload_path_uses_correct_owner(
        self,
        test_user,
        lesson_content,
    ):
        file_content = FileContent(
            content=lesson_content,
        )

        result = file_upload_path(
            file_content,
            "document.pdf",
        )

        assert result.startswith(f"courses/{test_user.pk}/")

    def test_file_upload_path_uses_lesson_content_id(
        self,
        lesson_content,
    ):
        file_content = FileContent(
            content=lesson_content,
        )

        result = file_upload_path(
            file_content,
            "document.pdf",
        )

        assert f"lesson_contents/{lesson_content.pk}/" in result


class TestFileContentCreation:
    def test_creates_file_content(
        self,
        lesson_content,
    ):
        uploaded_file = SimpleUploadedFile(
            "document.pdf",
            b"fake pdf content",
            content_type="application/pdf",
        )

        file_content = FileContent.objects.create(
            content=lesson_content,
            file=uploaded_file,
        )

        assert file_content.pk is not None
        assert file_content.content == lesson_content
        assert file_content.file
        assert file_content.file.name

    def test_creates_file_content_without_file(
        self,
        lesson_content,
    ):
        file_content = FileContent.objects.create(
            content=lesson_content,
        )

        assert file_content.pk is not None
        assert not file_content.file

    def test_file_url_is_optional(
        self,
        lesson_content,
    ):
        file_content = FileContent.objects.create(
            content=lesson_content,
        )

        assert file_content.file_url == ""

    def test_display_name_is_optional(
        self,
        lesson_content,
    ):
        file_content = FileContent.objects.create(
            content=lesson_content,
        )

        assert file_content.display_name == ""

    def test_description_is_optional(
        self,
        lesson_content,
    ):
        file_content = FileContent.objects.create(
            content=lesson_content,
        )

        assert file_content.description == ""

    def test_is_downloadable_defaults_to_true(
        self,
        lesson_content,
    ):
        file_content = FileContent.objects.create(
            content=lesson_content,
        )

        assert file_content.is_downloadable is True

    def test_file_size_defaults_to_none(
        self,
        lesson_content,
    ):
        file_content = FileContent.objects.create(
            content=lesson_content,
        )

        assert file_content.file_size is None


class TestFileContentFileSize:
    def test_save_sets_file_size_from_uploaded_file(
        self,
        lesson_content,
    ):
        file_data = b"some file content"

        uploaded_file = SimpleUploadedFile(
            "document.txt",
            file_data,
            content_type="text/plain",
        )

        file_content = FileContent(
            content=lesson_content,
            file=uploaded_file,
        )

        file_content.save()

        assert file_content.file_size == len(file_data)

    def test_save_updates_file_size_when_file_changes(
        self,
        file_content,
    ):
        first_size = file_content.file_size

        new_data = b"this is a much longer file"

        file_content.file = SimpleUploadedFile(
            "new-document.txt",
            new_data,
            content_type="text/plain",
        )

        file_content.save()
        file_content.refresh_from_db()

        assert first_size != file_content.file_size
        assert file_content.file_size == len(new_data)

    def test_save_without_file_does_not_set_file_size(
        self,
        lesson_content,
    ):
        file_content = FileContent(
            content=lesson_content,
        )

        file_content.save()

        assert file_content.file_size is None

    def test_file_size_is_persisted(
        self,
        file_content,
    ):
        expected_size = file_content.file.size

        file_content.refresh_from_db()

        assert file_content.file_size == expected_size


class TestFileContentStringRepresentation:
    def test_str_returns_display_name_when_available(
        self,
        file_content,
    ):
        assert str(file_content) == "Course Document"

    def test_str_falls_back_to_content_title(
        self,
        lesson_content,
    ):
        file_content = FileContent(
            content=lesson_content,
            display_name="",
        )

        assert str(file_content) == lesson_content.title

    def test_str_uses_updated_display_name(
        self,
        file_content,
    ):
        file_content.display_name = "Updated Document"

        assert str(file_content) == "Updated Document"


class TestFileContentValidation:
    def test_content_is_required(
        self,
        db,
    ):
        file_content = FileContent()

        with pytest.raises(ValidationError) as exc_info:
            file_content.full_clean()

        assert "content" in exc_info.value.message_dict

    def test_valid_file_url(
        self,
        lesson_content,
    ):
        file_content = FileContent(
            content=lesson_content,
            file_url="https://example.com/document.pdf",
        )

        file_content.full_clean()

    def test_invalid_file_url_is_rejected(
        self,
        lesson_content,
    ):
        file_content = FileContent(
            content=lesson_content,
            file_url="not-a-url",
        )

        with pytest.raises(ValidationError) as exc_info:
            file_content.full_clean()

        assert "file_url" in exc_info.value.message_dict

    def test_display_name_accepts_maximum_length(
        self,
        lesson_content,
    ):
        file_content = FileContent(
            content=lesson_content,
            display_name="a" * 255,
        )

        file_content.full_clean()

    def test_display_name_longer_than_maximum_is_rejected(
        self,
        lesson_content,
    ):
        file_content = FileContent(
            content=lesson_content,
            display_name="a" * 256,
        )

        with pytest.raises(ValidationError) as exc_info:
            file_content.full_clean()

        assert "display_name" in exc_info.value.message_dict


class TestFileContentRelations:
    def test_lesson_content_has_reverse_file_relation(
        self,
        lesson_content,
        file_content,
    ):
        assert lesson_content.file == file_content

    def test_only_one_file_content_is_allowed_per_lesson_content(
        self,
        lesson_content,
        file_content,
    ):
        duplicate = FileContent(
            content=lesson_content,
        )

        with pytest.raises(ValidationError) as exc_info:
            duplicate.full_clean()

        assert "content" in exc_info.value.message_dict

    def test_one_to_one_constraint_is_enforced_at_database_level(
        self,
        lesson_content,
        file_content,
    ):
        duplicate = FileContent(
            content=lesson_content,
        )

        with pytest.raises(IntegrityError):
            duplicate.save(force_insert=True)


class TestFileContentDeletion:
    def test_deleting_lesson_content_deletes_file_content(
        self,
        lesson_content,
        file_content,
    ):
        file_content_id = file_content.pk

        lesson_content.delete()

        assert not FileContent.objects.filter(pk=file_content_id).exists()


class TestFileContentUpdate:
    def test_display_name_can_be_updated(
        self,
        file_content,
    ):
        file_content.display_name = "Updated Document"
        file_content.save()

        file_content.refresh_from_db()

        assert file_content.display_name == "Updated Document"

    def test_description_can_be_updated(
        self,
        file_content,
    ):
        file_content.description = "Updated description."
        file_content.save()

        file_content.refresh_from_db()

        assert file_content.description == "Updated description."

    def test_is_downloadable_can_be_disabled(
        self,
        file_content,
    ):
        file_content.is_downloadable = False
        file_content.save()

        file_content.refresh_from_db()

        assert file_content.is_downloadable is False

    def test_file_url_can_be_updated(
        self,
        file_content,
    ):
        file_content.file_url = "https://example.com/new-file.pdf"
        file_content.save()

        file_content.refresh_from_db()

        assert file_content.file_url == ("https://example.com/new-file.pdf")
