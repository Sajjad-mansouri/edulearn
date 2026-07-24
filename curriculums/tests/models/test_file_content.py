import pytest
from django.db import IntegrityError

from curriculums.models import FileContent
from curriculums.tests.factories import (
    FileContentFactory,
    LessonContentFactory,
)
from utils.test.files import file_field


@pytest.mark.django_db
class TestFileContentModel:
    """Tests for the FileContent model."""

    @pytest.fixture
    def content(self):
        return LessonContentFactory()

    def test_create_file_content(self, content):
        """A file content can be created."""
        uploaded_file = file_field(
            "python-cheatsheet.pdf",
            b"pdf-content",
            content_type="application/pdf",
        )

        file_content = FileContent.objects.create(
            content=content,
            file=uploaded_file,
            display_name="Python Cheat Sheet",
            description="Useful Python reference.",
            is_downloadable=False,
        )

        assert file_content.content == content
        assert file_content.file.name.endswith("python-cheatsheet.pdf")
        assert file_content.display_name == "Python Cheat Sheet"
        assert file_content.description == "Useful Python reference."
        assert file_content.is_downloadable is False
        assert file_content.file_size == len(b"pdf-content")

    def test_string_representation_uses_display_name(self):
        """The string representation should use the display name when provided."""
        file_content = FileContentFactory(
            display_name="Lecture Slides",
        )

        assert str(file_content) == "Lecture Slides"

    def test_string_representation_falls_back_to_content_title(self):
        """The string representation falls back to the lesson content title."""
        content = LessonContentFactory(
            title="Week 1 Resources",
        )

        file_content = FileContentFactory(
            content=content,
            display_name="",
        )

        assert str(file_content) == "Week 1 Resources"

    def test_description_is_optional(self, content):
        """A file content can be created without a description."""
        file_content = FileContent.objects.create(
            content=content,
            file=file_field("notes.pdf"),
        )

        assert file_content.description == ""

    def test_display_name_is_optional(self, content):
        """A file content can be created without a display name."""
        file_content = FileContent.objects.create(
            content=content,
            file=file_field("notes.pdf"),
        )

        assert file_content.display_name == ""

    def test_is_downloadable_defaults_to_true(self, content):
        """Files are downloadable by default."""
        file_content = FileContent.objects.create(
            content=content,
            file=file_field("notes.pdf"),
        )

        assert file_content.is_downloadable is True

    def test_file_size_is_populated_on_save(self, content):
        """Saving the model stores the uploaded file size."""
        data = b"1234567890"

        file_content = FileContent.objects.create(
            content=content,
            file=file_field(
                "notes.pdf",
                data,
            ),
        )

        assert file_content.file_size == len(data)

    def test_content_can_have_only_one_file(self, content):
        """Each lesson content can have only one file."""
        FileContentFactory(content=content)

        with pytest.raises(IntegrityError):
            FileContentFactory(content=content)

    def test_deleting_content_deletes_file_content(self):
        """Deleting lesson content cascades to file content."""
        content = LessonContentFactory()

        file_content = FileContentFactory(
            content=content,
        )

        content.delete()

        assert not FileContent.objects.filter(
            pk=file_content.pk,
        ).exists()
