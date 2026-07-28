import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError

from curriculums.models import Attachment
from curriculums.tests.factories import (
    AttachmentFactory,
    CourseFactory,
    LessonContentFactory,
    LessonFactory,
    SectionFactory,
)


@pytest.mark.django_db
class TestAttachmentModel:
    """Tests for the Attachment model."""

    @pytest.fixture
    def course(self):
        return CourseFactory()

    @pytest.fixture
    def lesson_content(self, course):
        return LessonContentFactory(
            lesson__section__course=course,
        )

    def test_create_course_attachment(self, course):
        """A course-level attachment can be created."""
        attachment = AttachmentFactory(
            course=course,
            lesson_content=None,
        )

        assert attachment.course == course
        assert attachment.lesson_content is None

    def test_create_lesson_attachment(self, course, lesson_content):
        """A lesson attachment can be created."""
        attachment = AttachmentFactory(
            course=course,
            lesson_content=lesson_content,
        )

        assert attachment.course == course
        assert attachment.lesson_content == lesson_content

    def test_string_representation(self):
        """String representation returns the title."""
        attachment = AttachmentFactory(
            title="Course Slides",
        )

        assert str(attachment) == "Course Slides"

    def test_filename_property_returns_filename(self):
        """Filename property returns the file name only."""
        attachment = AttachmentFactory()

        assert attachment.filename == "attachment.pdf"

    def test_filename_returns_empty_string_when_file_missing(self, course):
        """Filename property returns empty string for URL attachments."""
        attachment = AttachmentFactory(
            course=course,
            file=None,
            file_url="https://example.com/file.pdf",
        )

        assert attachment.filename == ""

    def test_description_defaults_to_empty(self):
        """Description is optional."""
        attachment = AttachmentFactory()

        assert attachment.description == ""

    def test_is_downloadable_defaults_true(self):
        """Downloadable defaults to True."""
        attachment = AttachmentFactory()

        assert attachment.is_downloadable is True

    def test_file_size_saved(self):
        """File size is automatically populated."""
        uploaded = SimpleUploadedFile(
            "example.pdf",
            b"123456789",
            content_type="application/pdf",
        )

        attachment = AttachmentFactory(
            file=uploaded,
        )

        attachment.refresh_from_db()

        assert attachment.file_size == 9

    def test_lesson_content_must_belong_to_course(self):
        course1 = CourseFactory()
        course2 = CourseFactory()

        section = SectionFactory(course=course2)
        lesson = LessonFactory(section=section)
        lesson_content = LessonContentFactory(lesson=lesson)

        attachment = AttachmentFactory.build(
            course=course1,
            lesson_content=lesson_content,
        )

        with pytest.raises(ValidationError) as exc:
            attachment.full_clean()

        assert "lesson_content" in exc.value.message_dict

    def test_course_can_have_multiple_attachments(self, course):
        """A course may have multiple attachments."""
        attachment1 = AttachmentFactory(course=course)
        attachment2 = AttachmentFactory(course=course)

        assert set(course.attachments.all()) == {
            attachment1,
            attachment2,
        }

    def test_lesson_content_can_have_multiple_attachments(
        self,
        course,
        lesson_content,
    ):
        """A lesson content may have multiple attachments."""
        attachment1 = AttachmentFactory(
            course=course,
            lesson_content=lesson_content,
        )

        attachment2 = AttachmentFactory(
            course=course,
            lesson_content=lesson_content,
        )

        assert set(lesson_content.attachments.all()) == {
            attachment1,
            attachment2,
        }

    def test_deleting_course_deletes_attachments(self, course):
        """Deleting a course cascades to attachments."""
        attachment = AttachmentFactory(course=course)

        course.delete()

        assert not Attachment.objects.filter(
            pk=attachment.pk,
        ).exists()

    def test_deleting_lesson_content_deletes_attachment(
        self,
        course,
        lesson_content,
    ):
        """Deleting lesson content cascades to attachments."""
        attachment = AttachmentFactory(
            course=course,
            lesson_content=lesson_content,
        )

        lesson_content.delete()

        assert not Attachment.objects.filter(
            pk=attachment.pk,
        ).exists()

    def test_file_or_url_is_required(self, course):
        """Either file or URL must be provided."""
        attachment = AttachmentFactory.build(
            course=course,
            file=None,
            file_url="",
        )

        with pytest.raises(
            (ValidationError, IntegrityError),
        ):
            attachment.save()

    def test_file_and_url_cannot_both_exist(self, course):
        """File and URL cannot both be provided."""
        uploaded = SimpleUploadedFile(
            "example.pdf",
            b"content",
            content_type="application/pdf",
        )

        attachment = AttachmentFactory.build(
            course=course,
            file=uploaded,
            file_url="https://example.com/file.pdf",
        )

        with pytest.raises(
            (ValidationError, IntegrityError),
        ):
            attachment.save()

    def test_course_attachment_upload_path(self, course):
        """Course attachment upload path is correct."""
        attachment = AttachmentFactory.build(
            course=course,
            lesson_content=None,
        )

        path = attachment.file.field.upload_to(
            attachment,
            "slides.pdf",
        )

        expected = f"courses/{course.owner_id}/{course.id}/attachments/slides.pdf"

        assert path == expected

    def test_lesson_attachment_upload_path(
        self,
        course,
        lesson_content,
    ):
        """Lesson attachment upload path is correct."""
        attachment = AttachmentFactory.build(
            course=course,
            lesson_content=lesson_content,
        )

        path = attachment.file.field.upload_to(
            attachment,
            "notes.pdf",
        )

        expected = (
            f"courses/"
            f"{course.owner_id}/"
            f"{course.id}/"
            f"lesson_contents/"
            f"{lesson_content.id}/"
            f"attachments/"
            f"notes.pdf"
        )

        assert path == expected
