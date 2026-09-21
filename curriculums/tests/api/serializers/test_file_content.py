import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from curriculums.api.serializers import FileContentSerializer
from curriculums.models import FileContent


@pytest.fixture
def file_content(db, lesson_content):
    return FileContent.objects.create(
        content=lesson_content,
        file_url="https://example.com/material.pdf",
    )


class TestFileContentSerializer:
    def test_declares_expected_fields(self):
        serializer = FileContentSerializer()

        assert set(serializer.fields) == {"id", "file", "file_url"}

    def test_id_is_optional(self):
        serializer = FileContentSerializer(
            data={
                "file_url": "https://example.com/material.pdf",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert "id" not in serializer.validated_data

    def test_id_is_not_read_only(self):
        serializer = FileContentSerializer(
            data={
                "id": 123,
                "file_url": "https://example.com/material.pdf",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["id"] == 123

    def test_id_accepts_integer(self):
        serializer = FileContentSerializer(
            data={
                "id": 10,
                "file_url": "https://example.com/material.pdf",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["id"] == 10

    def test_id_coerces_numeric_string_to_integer(self):
        serializer = FileContentSerializer(
            data={
                "id": "10",
                "file_url": "https://example.com/material.pdf",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["id"] == 10

    def test_id_rejects_non_numeric_string(self):
        serializer = FileContentSerializer(
            data={
                "id": "invalid",
                "file_url": "https://example.com/material.pdf",
            }
        )

        assert not serializer.is_valid()
        assert "id" in serializer.errors

    def test_id_rejects_decimal_value(self):
        serializer = FileContentSerializer(
            data={
                "id": 10.5,
                "file_url": "https://example.com/material.pdf",
            }
        )

        assert not serializer.is_valid()
        assert "id" in serializer.errors

    def test_file_is_optional(self):
        serializer = FileContentSerializer(
            data={
                "file_url": "https://example.com/material.pdf",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert "file" not in serializer.validated_data

    def test_file_url_is_optional(self):
        uploaded_file = SimpleUploadedFile(
            "material.pdf",
            b"file content",
            content_type="application/pdf",
        )

        serializer = FileContentSerializer(
            data={
                "file": uploaded_file,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert "file" in serializer.validated_data
        assert "file_url" not in serializer.validated_data

    def test_accepts_valid_file_url(self):
        url = "https://example.com/material.pdf"

        serializer = FileContentSerializer(
            data={
                "file_url": url,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["file_url"] == url

    def test_rejects_invalid_file_url(self):
        serializer = FileContentSerializer(
            data={
                "file_url": "not-a-valid-url",
            }
        )

        assert not serializer.is_valid()
        assert "file_url" in serializer.errors

    def test_accepts_empty_file_url(self):
        serializer = FileContentSerializer(
            data={
                "file_url": "",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["file_url"] == ""

    def test_accepts_valid_uploaded_file(self):
        uploaded_file = SimpleUploadedFile(
            "lesson-material.pdf",
            b"PDF content",
            content_type="application/pdf",
        )

        serializer = FileContentSerializer(
            data={
                "file": uploaded_file,
            }
        )

        assert serializer.is_valid(), serializer.errors

        validated_file = serializer.validated_data["file"]

        assert validated_file.name == "lesson-material.pdf"
        assert validated_file.content_type == "application/pdf"
        assert validated_file.size == len(b"PDF content")

    def test_accepts_file_and_file_url_together(self):
        uploaded_file = SimpleUploadedFile(
            "lesson-material.pdf",
            b"PDF content",
            content_type="application/pdf",
        )
        url = "https://example.com/material.pdf"

        serializer = FileContentSerializer(
            data={
                "file": uploaded_file,
                "file_url": url,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["file"].name == "lesson-material.pdf"
        assert serializer.validated_data["file_url"] == url

    def test_serializes_instance(self, file_content):
        serializer = FileContentSerializer(instance=file_content)

        data = serializer.data

        assert set(data) == {"id", "file", "file_url"}
        assert data["id"] == file_content.id
        assert data["file_url"] == "https://example.com/material.pdf"

    def test_serializes_file_field(self, file_content):
        uploaded_file = SimpleUploadedFile(
            "lesson-material.pdf",
            b"PDF content",
            content_type="application/pdf",
        )

        file_content.file.save(
            "lesson-material.pdf",
            uploaded_file,
            save=True,
        )

        serializer = FileContentSerializer(instance=file_content)

        assert serializer.data["file"]
        assert serializer.data["file"].endswith("lesson-material.pdf")

    def test_does_not_expose_content_field(self):
        serializer = FileContentSerializer()

        assert "content" not in serializer.fields

    def test_does_not_expose_display_name(self):
        serializer = FileContentSerializer()

        assert "display_name" not in serializer.fields

    def test_does_not_expose_description(self):
        serializer = FileContentSerializer()

        assert "description" not in serializer.fields

    def test_does_not_expose_is_downloadable(self):
        serializer = FileContentSerializer()

        assert "is_downloadable" not in serializer.fields

    def test_does_not_expose_file_size(self):
        serializer = FileContentSerializer()

        assert "file_size" not in serializer.fields

    def test_partial_update_accepts_file_url(self, file_content):
        new_url = "https://example.com/updated-material.pdf"

        serializer = FileContentSerializer(
            instance=file_content,
            data={"file_url": new_url},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["file_url"] == new_url

    def test_partial_update_accepts_file(self, file_content):
        uploaded_file = SimpleUploadedFile(
            "updated-material.pdf",
            b"updated content",
            content_type="application/pdf",
        )

        serializer = FileContentSerializer(
            instance=file_content,
            data={"file": uploaded_file},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["file"].name == "updated-material.pdf"

    def test_partial_update_accepts_id(self, file_content):
        serializer = FileContentSerializer(
            instance=file_content,
            data={"id": 999},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["id"] == 999

    def test_all_model_fields_are_not_required_by_serializer(self):
        serializer = FileContentSerializer(data={})

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data == {}

    def test_serializer_fields_match_declared_meta_fields(self):
        serializer = FileContentSerializer()

        assert list(serializer.fields) == ["id", "file", "file_url"]
