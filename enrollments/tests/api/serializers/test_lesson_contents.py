from django.core.files import File

from curriculums.models import Attachment
from enrollments.api.serializers.lesson_contents import AttachmentSerializer


class TestAttachmentSerializer:
    def test_serializes_expected_fields(self, course, tmp_path):
        file_path = tmp_path / "syllabus.pdf"
        file_path.write_bytes(b"syllabus content")

        attachment = Attachment(
            course=course,
            title="Course Syllabus",
        )

        with file_path.open("rb") as file:
            attachment.file.save(
                "syllabus.pdf",
                File(file),
                save=True,
            )

        data = AttachmentSerializer(instance=attachment).data

        assert set(data) == {"file", "file_size"}

    def test_serializes_uploaded_file_url(self, course, tmp_path):
        file_path = tmp_path / "syllabus.pdf"
        file_path.write_bytes(b"syllabus content")

        attachment = Attachment(
            course=course,
            title="Course Syllabus",
        )

        with file_path.open("rb") as file:
            attachment.file.save(
                "syllabus.pdf",
                File(file),
                save=True,
            )

        data = AttachmentSerializer(instance=attachment).data

        assert data["file"] == attachment.file.url

    def test_serializes_file_size(self, course, tmp_path):
        content = b"syllabus content"

        file_path = tmp_path / "syllabus.pdf"
        file_path.write_bytes(content)

        attachment = Attachment(
            course=course,
            title="Course Syllabus",
        )

        with file_path.open("rb") as file:
            attachment.file.save(
                "syllabus.pdf",
                File(file),
                save=True,
            )

        data = AttachmentSerializer(instance=attachment).data

        assert data["file_size"] == len(content)
        assert data["file_size"] == attachment.file_size

    def test_serializes_null_file_for_external_url_attachment(self, course):
        attachment = Attachment.objects.create(
            course=course,
            title="Documentation",
            file_url="https://example.com/documentation",
        )

        data = AttachmentSerializer(instance=attachment).data

        assert data["file"] is None
        assert data["file_size"] is None

    def test_serializes_lesson_content_attachment(
        self,
        course,
        attachment_lesson_content,
        tmp_path,
    ):
        file_path = tmp_path / "example.zip"
        file_path.write_bytes(b"zip content")

        attachment = Attachment(
            course=course,
            lesson_content=attachment_lesson_content,
            title="Example Files",
        )

        with file_path.open("rb") as file:
            attachment.file.save(
                "example.zip",
                File(file),
                save=True,
            )

        data = AttachmentSerializer(instance=attachment).data

        assert data["file"] == attachment.file.url
        assert data["file_size"] == len(b"zip content")

    def test_does_not_expose_course(self, course):
        attachment = Attachment.objects.create(
            course=course,
            title="Documentation",
            file_url="https://example.com/documentation",
        )

        data = AttachmentSerializer(instance=attachment).data

        assert "course" not in data

    def test_does_not_expose_lesson_content(self, course):
        attachment = Attachment.objects.create(
            course=course,
            title="Documentation",
            file_url="https://example.com/documentation",
        )

        data = AttachmentSerializer(instance=attachment).data

        assert "lesson_content" not in data

    def test_does_not_expose_external_url(self, course):
        attachment = Attachment.objects.create(
            course=course,
            title="Documentation",
            file_url="https://example.com/documentation",
        )

        data = AttachmentSerializer(instance=attachment).data

        assert "file_url" not in data

    def test_does_not_expose_title(self, course):
        attachment = Attachment.objects.create(
            course=course,
            title="Documentation",
            file_url="https://example.com/documentation",
        )

        data = AttachmentSerializer(instance=attachment).data

        assert "title" not in data

    def test_does_not_expose_description(self, course):
        attachment = Attachment.objects.create(
            course=course,
            title="Documentation",
            description="Additional documentation.",
            file_url="https://example.com/documentation",
        )

        data = AttachmentSerializer(instance=attachment).data

        assert "description" not in data

    def test_does_not_expose_is_downloadable(self, course):
        attachment = Attachment.objects.create(
            course=course,
            title="Documentation",
            is_downloadable=True,
            file_url="https://example.com/documentation",
        )

        data = AttachmentSerializer(instance=attachment).data

        assert "is_downloadable" not in data

    def test_file_size_is_read_only(self, course):
        attachment = Attachment.objects.create(
            course=course,
            title="Documentation",
            file_url="https://example.com/documentation",
        )

        serializer = AttachmentSerializer(
            instance=attachment,
            data={
                "file": None,
                "file_size": 999999,
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert "file_size" not in serializer.validated_data

    def test_serializes_multiple_attachments(self, course, tmp_path):
        first_content = b"first attachment"
        second_content = b"second attachment"

        first_path = tmp_path / "first.pdf"
        second_path = tmp_path / "second.zip"

        first_path.write_bytes(first_content)
        second_path.write_bytes(second_content)

        first_attachment = Attachment(
            course=course,
            title="First Attachment",
        )

        with first_path.open("rb") as file:
            first_attachment.file.save(
                "first.pdf",
                File(file),
                save=True,
            )

        second_attachment = Attachment(
            course=course,
            title="Second Attachment",
        )

        with second_path.open("rb") as file:
            second_attachment.file.save(
                "second.zip",
                File(file),
                save=True,
            )

        data = AttachmentSerializer(
            instance=Attachment.objects.filter(
                pk__in=[first_attachment.pk, second_attachment.pk]
            ),
            many=True,
        ).data

        assert len(data) == 2

        serialized_files = {item["file"] for item in data}
        serialized_sizes = {item["file_size"] for item in data}

        assert first_attachment.file.url in serialized_files
        assert second_attachment.file.url in serialized_files
        assert len(first_content) in serialized_sizes
        assert len(second_content) in serialized_sizes
