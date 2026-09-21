from unittest.mock import Mock

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.exceptions import ErrorDetail

from curriculums.api.serializers import AttachmentSerializer
from curriculums.models.attachment import Attachment


@pytest.mark.django_db
class TestAttachmentSerializer:
    def test_declares_expected_fields(self):
        serializer = AttachmentSerializer()

        assert set(serializer.fields) == {
            "id",
            "file",
            "file_url",
        }

    def test_id_is_optional(self):
        serializer = AttachmentSerializer()

        assert serializer.fields["id"].required is False

    def test_id_is_not_read_only(self):
        serializer = AttachmentSerializer()

        assert serializer.fields["id"].read_only is False

    def test_file_is_not_required(self):
        serializer = AttachmentSerializer()

        assert serializer.fields["file"].required is False

    def test_file_url_is_not_required(self):
        serializer = AttachmentSerializer()

        assert serializer.fields["file_url"].required is False

    def test_id_uses_integer_field(self):
        serializer = AttachmentSerializer()

        assert serializer.fields["id"].__class__.__name__ == "IntegerField"

    def test_file_uses_file_field(self):
        serializer = AttachmentSerializer()

        assert serializer.fields["file"].__class__.__name__ == "FileField"

    def test_file_url_uses_url_field(self):
        serializer = AttachmentSerializer()

        assert serializer.fields["file_url"].__class__.__name__ == "URLField"

    def test_accepts_external_url_without_file(self):
        data = {
            "file_url": "https://example.com/resources/syllabus.pdf",
        }

        serializer = AttachmentSerializer(data=data)

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["file_url"] == (
            "https://example.com/resources/syllabus.pdf"
        )

    def test_accepts_file_without_external_url(self):
        uploaded_file = SimpleUploadedFile(
            "syllabus.pdf",
            b"course syllabus",
            content_type="application/pdf",
        )

        serializer = AttachmentSerializer(
            data={"file": uploaded_file},
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["file"].name == "syllabus.pdf"
        assert serializer.validated_data["file"].size == len(b"course syllabus")

    def test_accepts_id_when_provided(self):
        serializer = AttachmentSerializer(
            data={
                "id": 15,
                "file_url": "https://example.com/file.pdf",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["id"] == 15

    def test_accepts_string_integer_id(self):
        serializer = AttachmentSerializer(
            data={
                "id": "15",
                "file_url": "https://example.com/file.pdf",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["id"] == 15

    def test_rejects_non_integer_id(self):
        serializer = AttachmentSerializer(
            data={
                "id": "not-an-integer",
                "file_url": "https://example.com/file.pdf",
            }
        )

        assert serializer.is_valid() is False

        assert "id" in serializer.errors

    def test_rejects_decimal_id(self):
        serializer = AttachmentSerializer(
            data={
                "id": "15.5",
                "file_url": "https://example.com/file.pdf",
            }
        )

        assert serializer.is_valid() is False

        assert "id" in serializer.errors

    def test_accepts_valid_http_url(self):
        url = "http://example.com/files/example.pdf"

        serializer = AttachmentSerializer(
            data={"file_url": url},
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["file_url"] == url

    def test_accepts_valid_https_url(self):
        url = "https://example.com/files/example.pdf"

        serializer = AttachmentSerializer(
            data={"file_url": url},
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["file_url"] == url

    def test_rejects_invalid_url(self):
        serializer = AttachmentSerializer(
            data={
                "file_url": "not-a-valid-url",
            }
        )

        assert serializer.is_valid() is False

        assert "file_url" in serializer.errors

    def test_accepts_blank_file_url(self):
        serializer = AttachmentSerializer(
            data={
                "file_url": "",
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["file_url"] == ""

    def test_rejects_url_longer_than_model_max_length(self):
        long_url = "https://example.com/" + ("a" * 2048)

        serializer = AttachmentSerializer(
            data={
                "file_url": long_url,
            }
        )

        assert serializer.is_valid() is False

        assert "file_url" in serializer.errors

    def test_file_name_is_preserved(self):
        uploaded_file = SimpleUploadedFile(
            "example.zip",
            b"zip-content",
            content_type="application/zip",
        )

        serializer = AttachmentSerializer(
            data={"file": uploaded_file},
        )

        assert serializer.is_valid(), serializer.errors

        file_value = serializer.validated_data["file"]

        assert file_value.name == "example.zip"

    def test_file_content_is_preserved(self):
        content = b"example file content"

        uploaded_file = SimpleUploadedFile(
            "example.txt",
            content,
            content_type="text/plain",
        )

        serializer = AttachmentSerializer(
            data={"file": uploaded_file},
        )

        assert serializer.is_valid(), serializer.errors

        file_value = serializer.validated_data["file"]

        assert file_value.read() == content

    def test_file_size_is_preserved(self):
        content = b"123456789"

        uploaded_file = SimpleUploadedFile(
            "example.txt",
            content,
            content_type="text/plain",
        )

        serializer = AttachmentSerializer(
            data={"file": uploaded_file},
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["file"].size == len(content)

    def test_accepts_file_and_file_url_together_at_serializer_level(
        self,
    ):
        uploaded_file = SimpleUploadedFile(
            "example.pdf",
            b"pdf-content",
            content_type="application/pdf",
        )

        serializer = AttachmentSerializer(
            data={
                "file": uploaded_file,
                "file_url": "https://example.com/example.pdf",
            }
        )

        # Attachment's model constraint requires exactly one source,
        # but ModelSerializer validation does not execute that model
        # CheckConstraint. This test documents serializer behavior.
        assert serializer.is_valid(), serializer.errors

        assert "file" in serializer.validated_data
        assert "file_url" in serializer.validated_data

    def test_accepts_empty_input_at_serializer_level(self):
        serializer = AttachmentSerializer(data={})

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data == {}

    def test_partial_update_allows_empty_data(self):
        attachment = Mock(spec=Attachment)

        serializer = AttachmentSerializer(
            instance=attachment,
            data={},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data == {}

    def test_partial_update_can_update_only_file_url(self):
        attachment = Mock(spec=Attachment)

        serializer = AttachmentSerializer(
            instance=attachment,
            data={
                "file_url": "https://example.com/new-file.pdf",
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["file_url"] == (
            "https://example.com/new-file.pdf"
        )

    def test_partial_update_can_update_only_file(self):
        attachment = Mock(spec=Attachment)

        uploaded_file = SimpleUploadedFile(
            "new-file.pdf",
            b"new-content",
            content_type="application/pdf",
        )

        serializer = AttachmentSerializer(
            instance=attachment,
            data={"file": uploaded_file},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["file"].name == "new-file.pdf"

    def test_partial_update_can_update_id(self):
        attachment = Mock(spec=Attachment)

        serializer = AttachmentSerializer(
            instance=attachment,
            data={"id": 25},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["id"] == 25

    def test_serializes_attachment_id(self):
        attachment = Mock(spec=Attachment)
        attachment.id = 10
        attachment.file = None
        attachment.file_url = "https://example.com/file.pdf"

        serializer = AttachmentSerializer(attachment)

        assert serializer.data["id"] == 10

    def test_serializes_external_file_url(self):
        url = "https://example.com/resources/file.pdf"

        attachment = Mock(spec=Attachment)
        attachment.id = 10
        attachment.file = None
        attachment.file_url = url

        serializer = AttachmentSerializer(attachment)

        assert serializer.data["file_url"] == url

    def test_serializes_file_field_when_file_exists(
        self,
        settings,
    ):
        settings.MEDIA_URL = "/media/"

        attachment = Mock(spec=Attachment)
        attachment.id = 10
        attachment.file = Mock()
        attachment.file.url = "/media/attachments/example.pdf"
        attachment.file_url = ""

        serializer = AttachmentSerializer(attachment)

        assert serializer.data["file"] == ("/media/attachments/example.pdf")

    def test_serializes_null_file_as_null(self):
        attachment = Mock(spec=Attachment)
        attachment.id = 10
        attachment.file = None
        attachment.file_url = "https://example.com/file.pdf"

        serializer = AttachmentSerializer(attachment)

        assert serializer.data["file"] is None

    def test_serializes_all_declared_fields(self):
        attachment = Mock(spec=Attachment)
        attachment.id = 10
        attachment.file = None
        attachment.file_url = "https://example.com/file.pdf"

        serializer = AttachmentSerializer(attachment)

        assert set(serializer.data) == {
            "id",
            "file",
            "file_url",
        }

    def test_ignores_model_fields_not_declared_in_serializer(self):
        attachment = Mock(spec=Attachment)
        attachment.id = 10
        attachment.file = None
        attachment.file_url = "https://example.com/file.pdf"
        attachment.title = "Syllabus"
        attachment.description = "Course syllabus"
        attachment.is_downloadable = True
        attachment.file_size = 1234

        serializer = AttachmentSerializer(attachment)

        assert "title" not in serializer.data
        assert "description" not in serializer.data
        assert "is_downloadable" not in serializer.data
        assert "file_size" not in serializer.data

    def test_invalid_file_url_error_is_for_file_url_field(self):
        serializer = AttachmentSerializer(
            data={"file_url": "invalid-url"},
        )

        assert serializer.is_valid() is False

        assert "file_url" in serializer.errors
        assert isinstance(
            serializer.errors["file_url"][0],
            ErrorDetail,
        )

    def test_id_is_not_required_when_serializing_existing_instance(
        self,
    ):
        attachment = Mock(spec=Attachment)
        attachment.id = None
        attachment.file = None
        attachment.file_url = "https://example.com/file.pdf"

        serializer = AttachmentSerializer(attachment)

        assert serializer.data["id"] is None

    def test_serializer_does_not_require_course(self):
        serializer = AttachmentSerializer(
            data={
                "file_url": "https://example.com/file.pdf",
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert "course" not in serializer.fields

    def test_serializer_does_not_require_lesson_content(self):
        serializer = AttachmentSerializer(
            data={
                "file_url": "https://example.com/file.pdf",
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert "lesson_content" not in serializer.fields
