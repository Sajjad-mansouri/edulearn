from pathlib import Path

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError

from courses.models.course import Course
from curriculums.models.attachment import Attachment, attachment_upload_path
from curriculums.models.lesson_content import LessonContent


@pytest.fixture
def lesson_content(lesson):
    return LessonContent.objects.create(
        lesson=lesson,
        title="Lesson Resources",
        content_type=LessonContent.Type.FILE,
        order=1,
    )


@pytest.fixture
def attachment_file(course):
    return Attachment.objects.create(
        course=course,
        file=SimpleUploadedFile(
            "syllabus.pdf",
            b"fake pdf content",
            content_type="application/pdf",
        ),
        title="Syllabus",
        description="Course syllabus.",
    )


@pytest.fixture
def attachment_url(course):
    return Attachment.objects.create(
        course=course,
        file_url="https://example.com/syllabus.pdf",
        title="Online Syllabus",
        description="External syllabus.",
    )


@pytest.fixture
def lesson_attachment(lesson_content, course):
    return Attachment.objects.create(
        course=course,
        lesson_content=lesson_content,
        file=SimpleUploadedFile(
            "lesson-material.zip",
            b"fake zip content",
            content_type="application/zip",
        ),
        title="Lesson Material",
    )


class TestAttachmentUploadPath:
    def test_course_attachment_path(
        self,
        course,
    ):
        attachment = Attachment(
            course=course,
        )

        result = attachment_upload_path(
            attachment,
            "syllabus.pdf",
        )

        expected = f"courses/{course.owner_id}/{course.id}/attachments/syllabus.pdf"

        assert result == expected

    def test_lesson_attachment_path(
        self,
        course,
        lesson_content,
    ):
        attachment = Attachment(
            course=course,
            lesson_content=lesson_content,
        )

        result = attachment_upload_path(
            attachment,
            "lesson-material.zip",
        )

        expected = (
            f"courses/"
            f"{course.owner_id}/"
            f"{course.id}/"
            f"lesson_contents/"
            f"{lesson_content.id}/"
            f"attachments/"
            f"lesson-material.zip"
        )

        assert result == expected

    def test_course_attachment_does_not_include_lesson_content_path(
        self,
        course,
    ):
        attachment = Attachment(
            course=course,
        )

        result = attachment_upload_path(
            attachment,
            "syllabus.pdf",
        )

        assert "lesson_contents" not in result
        assert result.endswith("attachments/syllabus.pdf")

    def test_lesson_attachment_includes_lesson_content_id(
        self,
        course,
        lesson_content,
    ):
        attachment = Attachment(
            course=course,
            lesson_content=lesson_content,
        )

        result = attachment_upload_path(
            attachment,
            "example.zip",
        )

        assert f"lesson_contents/{lesson_content.id}/attachments/" in result

    def test_upload_path_preserves_filename(
        self,
        course,
    ):
        attachment = Attachment(
            course=course,
        )

        result = attachment_upload_path(
            attachment,
            "my course file.pdf",
        )

        assert result.endswith("attachments/my course file.pdf")


class TestAttachmentCreation:
    def test_creates_course_level_attachment(
        self,
        course,
    ):
        attachment = Attachment.objects.create(
            course=course,
            file=SimpleUploadedFile(
                "syllabus.pdf",
                b"pdf content",
                content_type="application/pdf",
            ),
            title="Syllabus",
        )

        assert attachment.pk is not None
        assert attachment.course == course
        assert attachment.lesson_content is None
        assert attachment.file
        assert attachment.title == "Syllabus"

    def test_creates_lesson_level_attachment(
        self,
        course,
        lesson_content,
    ):
        attachment = Attachment.objects.create(
            course=course,
            lesson_content=lesson_content,
            file=SimpleUploadedFile(
                "lesson.zip",
                b"zip content",
                content_type="application/zip",
            ),
            title="Lesson Files",
        )

        assert attachment.pk is not None
        assert attachment.course == course
        assert attachment.lesson_content == lesson_content

    def test_creates_attachment_with_external_url(
        self,
        course,
    ):
        attachment = Attachment.objects.create(
            course=course,
            file_url="https://example.com/resource.pdf",
            title="External Resource",
        )

        assert attachment.pk is not None
        assert attachment.file_url == ("https://example.com/resource.pdf")
        assert not attachment.file

    def test_lesson_content_is_optional(
        self,
        attachment_file,
    ):
        assert attachment_file.lesson_content is None

    def test_title_is_optional(
        self,
        course,
    ):
        attachment = Attachment.objects.create(
            course=course,
            file_url="https://example.com/resource.pdf",
        )

        assert attachment.title == ""

    def test_description_is_optional(
        self,
        course,
    ):
        attachment = Attachment.objects.create(
            course=course,
            file_url="https://example.com/resource.pdf",
        )

        assert attachment.description == ""

    def test_is_downloadable_defaults_to_true(
        self,
        course,
    ):
        attachment = Attachment.objects.create(
            course=course,
            file_url="https://example.com/resource.pdf",
        )

        assert attachment.is_downloadable is True

    def test_file_size_defaults_to_none_for_url_attachment(
        self,
        attachment_url,
    ):
        assert attachment_url.file_size is None


class TestAttachmentSourceValidation:
    def test_file_source_is_valid(
        self,
        course,
    ):
        attachment = Attachment(
            course=course,
            file=SimpleUploadedFile(
                "document.pdf",
                b"pdf content",
                content_type="application/pdf",
            ),
        )

        attachment.full_clean()

    def test_url_source_is_valid(
        self,
        course,
    ):
        attachment = Attachment(
            course=course,
            file_url="https://example.com/document.pdf",
        )

        attachment.full_clean()

    def test_file_and_url_together_are_invalid(
        self,
        course,
    ):
        attachment = Attachment(
            course=course,
            file=SimpleUploadedFile(
                "document.pdf",
                b"pdf content",
                content_type="application/pdf",
            ),
            file_url="https://example.com/document.pdf",
        )

        with pytest.raises(ValidationError) as exc_info:
            attachment.full_clean()

        assert "__all__" in exc_info.value.message_dict

    def test_neither_file_nor_url_is_invalid(
        self,
        course,
    ):
        attachment = Attachment(
            course=course,
        )

        with pytest.raises(ValidationError) as exc_info:
            attachment.full_clean()

        assert "__all__" in exc_info.value.message_dict

    def test_empty_file_with_valid_url_is_valid(
        self,
        course,
    ):
        attachment = Attachment(
            course=course,
            file_url="https://example.com/document.pdf",
        )

        attachment.full_clean()

        assert not attachment.file

    def test_file_without_url_is_valid(
        self,
        course,
    ):
        attachment = Attachment(
            course=course,
            file=SimpleUploadedFile(
                "document.pdf",
                b"pdf content",
                content_type="application/pdf",
            ),
        )

        attachment.full_clean()

        assert attachment.file_url == ""


class TestAttachmentCourseValidation:
    def test_lesson_content_must_belong_to_selected_course(
        self,
        course,
        lesson_content,
    ):
        other_user = type(course.owner).objects.create_user(
            username="other_test_user",
            email="other_test_user@example.com",
            password="test-password",
        )

        other_course = Course.objects.create(
            title="Other Course",
            owner=other_user,
        )

        attachment = Attachment(
            course=other_course,
            lesson_content=lesson_content,
            file_url="https://example.com/resource.pdf",
        )

        with pytest.raises(ValidationError) as exc_info:
            attachment.full_clean()

        assert exc_info.value.message_dict == {
            "lesson_content": ["Lesson content must belong to the selected course."]
        }

    def test_lesson_content_from_same_course_is_valid(
        self,
        course,
        lesson_content,
    ):
        attachment = Attachment(
            course=course,
            lesson_content=lesson_content,
            file_url="https://example.com/resource.pdf",
        )

        attachment.full_clean()

    def test_course_level_attachment_does_not_require_lesson_content(
        self,
        course,
    ):
        attachment = Attachment(
            course=course,
            file_url="https://example.com/resource.pdf",
        )

        attachment.full_clean()


class TestAttachmentFileSize:
    def test_save_sets_file_size(
        self,
        course,
    ):
        file_data = b"course attachment content"

        attachment = Attachment(
            course=course,
            file=SimpleUploadedFile(
                "document.txt",
                file_data,
                content_type="text/plain",
            ),
        )

        attachment.save()

        assert attachment.file_size == len(file_data)

    def test_save_persists_file_size(
        self,
        attachment_file,
    ):
        expected_size = attachment_file.file.size

        attachment_file.refresh_from_db()

        assert attachment_file.file_size == expected_size

    def test_save_updates_file_size_when_file_changes(
        self,
        attachment_file,
    ):
        first_size = attachment_file.file_size

        new_data = b"a significantly different file"

        attachment_file.file = SimpleUploadedFile(
            "new-document.txt",
            new_data,
            content_type="text/plain",
        )

        attachment_file.save()
        attachment_file.refresh_from_db()

        assert attachment_file.file_size != first_size
        assert attachment_file.file_size == len(new_data)

    def test_url_attachment_does_not_have_file_size(
        self,
        attachment_url,
    ):
        assert attachment_url.file_size is None


class TestAttachmentFilename:
    def test_filename_returns_uploaded_filename(
        self,
        attachment_file,
    ):
        assert attachment_file.filename == "syllabus.pdf"

    def test_filename_returns_only_basename(
        self,
        attachment_file,
    ):
        expected_filename = Path(attachment_file.file.name).name

        assert attachment_file.filename == expected_filename

    def test_filename_returns_empty_string_without_file(
        self,
        attachment_url,
    ):
        assert attachment_url.filename == ""

    def test_filename_is_based_on_current_file(
        self,
        attachment_file,
    ):
        attachment_file.file = SimpleUploadedFile(
            "updated-document.pdf",
            b"updated content",
            content_type="application/pdf",
        )
        attachment_file.save()

        assert attachment_file.filename == ("updated-document.pdf")


class TestAttachmentStringRepresentation:
    def test_str_returns_title(
        self,
        attachment_file,
    ):
        assert str(attachment_file) == "Syllabus"

    def test_str_uses_updated_title(
        self,
        attachment_file,
    ):
        attachment_file.title = "Updated Syllabus"
        attachment_file.save()

        assert str(attachment_file) == "Updated Syllabus"


class TestAttachmentRelations:
    def test_course_has_reverse_attachments_relation(
        self,
        course,
        attachment_file,
    ):
        assert list(course.attachments.all()) == [attachment_file]

    def test_lesson_content_has_reverse_attachments_relation(
        self,
        lesson_content,
        lesson_attachment,
    ):
        assert list(lesson_content.attachments.all()) == [lesson_attachment]

    def test_lesson_content_can_have_multiple_attachments(
        self,
        course,
        lesson_content,
    ):
        first = Attachment.objects.create(
            course=course,
            lesson_content=lesson_content,
            file_url="https://example.com/one.pdf",
            title="First",
        )

        second = Attachment.objects.create(
            course=course,
            lesson_content=lesson_content,
            file_url="https://example.com/two.pdf",
            title="Second",
        )

        assert lesson_content.attachments.count() == 2
        assert set(lesson_content.attachments.all()) == {first, second}


class TestAttachmentDeletion:
    def test_deleting_course_deletes_attachments(
        self,
        course,
        attachment_file,
        attachment_url,
    ):
        file_id = attachment_file.pk
        url_id = attachment_url.pk

        course.delete()

        assert not Attachment.objects.filter(pk=file_id).exists()

        assert not Attachment.objects.filter(pk=url_id).exists()

    def test_deleting_lesson_content_deletes_lesson_attachments(
        self,
        lesson_content,
        lesson_attachment,
    ):
        attachment_id = lesson_attachment.pk

        lesson_content.delete()

        assert not Attachment.objects.filter(pk=attachment_id).exists()


class TestAttachmentOrdering:
    def test_attachments_are_ordered_by_title_then_created_at(
        self,
        course,
    ):
        second = Attachment.objects.create(
            course=course,
            file_url="https://example.com/second.pdf",
            title="Zebra",
        )

        first = Attachment.objects.create(
            course=course,
            file_url="https://example.com/first.pdf",
            title="Alpha",
        )

        assert list(Attachment.objects.filter(course=course)) == [first, second]


class TestAttachmentDefaults:
    def test_is_downloadable_can_be_false(
        self,
        course,
    ):
        attachment = Attachment.objects.create(
            course=course,
            file_url="https://example.com/resource.pdf",
            is_downloadable=False,
        )

        assert attachment.is_downloadable is False

    def test_title_maximum_length_is_valid(
        self,
        course,
    ):
        attachment = Attachment(
            course=course,
            file_url="https://example.com/resource.pdf",
            title="a" * 255,
        )

        attachment.full_clean()

    def test_title_longer_than_maximum_is_invalid(
        self,
        course,
    ):
        attachment = Attachment(
            course=course,
            file_url="https://example.com/resource.pdf",
            title="a" * 256,
        )

        with pytest.raises(ValidationError) as exc_info:
            attachment.full_clean()

        assert "title" in exc_info.value.message_dict


class TestAttachmentTimestamps:
    def test_created_at_is_set(
        self,
        attachment_file,
    ):
        assert attachment_file.created_at is not None

    def test_updated_at_is_set(
        self,
        attachment_file,
    ):
        assert attachment_file.updated_at is not None

    def test_updated_at_changes_on_save(
        self,
        attachment_file,
    ):
        original_updated_at = attachment_file.updated_at

        attachment_file.title = "Updated"
        attachment_file.save()

        attachment_file.refresh_from_db()

        assert attachment_file.updated_at >= original_updated_at

    def test_created_at_does_not_change_on_update(
        self,
        attachment_file,
    ):
        original_created_at = attachment_file.created_at

        attachment_file.title = "Updated"
        attachment_file.save()

        attachment_file.refresh_from_db()

        assert attachment_file.created_at == original_created_at


class TestAttachmentDatabaseConstraint:
    def test_exactly_one_source_constraint_exists(self):
        constraint_names = {
            constraint.name for constraint in Attachment._meta.constraints
        }

        assert "attachment_exactly_one_source" in constraint_names

    def test_database_rejects_attachment_without_source(
        self,
        course,
    ):
        attachment = Attachment(
            course=course,
            title="Invalid Attachment",
        )

        with pytest.raises(IntegrityError):
            Attachment.objects.bulk_create([attachment])

    def test_database_rejects_attachment_with_both_sources(
        self,
        course,
    ):
        attachment = Attachment(
            course=course,
            file=SimpleUploadedFile(
                "document.pdf",
                b"pdf content",
                content_type="application/pdf",
            ),
            file_url="https://example.com/document.pdf",
        )

        with pytest.raises(IntegrityError):
            Attachment.objects.bulk_create([attachment])
