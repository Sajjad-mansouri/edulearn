from datetime import UTC, datetime
from decimal import Decimal

from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from assessments.models import Assignment, AssignmentSubmissionFile
from curriculums.models import LessonContent
from enrollments.api.serializers.assignment import (
    AssignmentSerializer,
    AssignmentSubmissionFileSerializer,
    AssignmentSubmissionSerializer,
)


class TestAssignmentSerializer:
    @staticmethod
    def make_assignment():
        lesson_content = LessonContent()

        return Assignment(
            content=lesson_content,
            instructions="Submit the completed assignment.",
            passing_score=75,
            max_score=100,
            due_date=datetime(2026, 9, 30, 12, 0, tzinfo=UTC),
            allow_late_submission=True,
            max_attempts=3,
            accepted_file_types="pdf,docx",
            max_file_size_mb=25,
        )

    def test_serializes_expected_fields(self):
        # Arrange
        assignment = self.make_assignment()

        # Act
        data = AssignmentSerializer(instance=assignment).data

        # Assert
        assert set(data) == {
            "id",
            "instructions",
            "passingScore",
            "maxScore",
            "dueDate",
            "allowLateSubmission",
            "maxAttempts",
            "acceptedFileTypes",
            "maxFileSizeMB",
        }

    def test_serializes_field_values_with_api_field_names(self):
        # Arrange
        assignment = self.make_assignment()

        # Act
        data = AssignmentSerializer(instance=assignment).data

        # Assert
        assert data["id"] is None
        assert data["instructions"] == assignment.instructions
        assert data["passingScore"] == assignment.passing_score
        assert data["maxScore"] == assignment.max_score
        assert data["allowLateSubmission"] == assignment.allow_late_submission
        assert data["maxAttempts"] == assignment.max_attempts
        assert data["acceptedFileTypes"] == assignment.accepted_file_types
        assert data["maxFileSizeMB"] == assignment.max_file_size_mb

    def test_serializes_due_date_using_due_date_api_field(self):
        # Arrange
        assignment = self.make_assignment()

        # Act
        data = AssignmentSerializer(instance=assignment).data

        # Assert
        expected_due_date = (
            AssignmentSerializer()
            .fields["dueDate"]
            .to_representation(assignment.due_date)
        )

        assert data["dueDate"] == expected_due_date

    def test_does_not_expose_internal_snake_case_field_names(self):
        # Arrange
        assignment = self.make_assignment()

        # Act
        data = AssignmentSerializer(instance=assignment).data

        # Assert
        assert "passing_score" not in data
        assert "max_score" not in data
        assert "due_date" not in data
        assert "allow_late_submission" not in data
        assert "max_attempts" not in data
        assert "accepted_file_types" not in data
        assert "max_file_size_mb" not in data

    def test_does_not_expose_assignment_content(self):
        # Arrange
        assignment = self.make_assignment()

        # Act
        data = AssignmentSerializer(instance=assignment).data

        # Assert
        assert "content" not in data

    def test_serializes_nullable_due_date_as_null(self):
        # Arrange
        assignment = self.make_assignment()
        assignment.due_date = None

        # Act
        data = AssignmentSerializer(instance=assignment).data

        # Assert
        assert data["dueDate"] is None

    def test_serializes_nullable_scores_as_null(self):
        # Arrange
        assignment = self.make_assignment()
        assignment.passing_score = None
        assignment.max_score = None

        # Act
        data = AssignmentSerializer(instance=assignment).data

        # Assert
        assert data["passingScore"] is None
        assert data["maxScore"] is None

    def test_serializes_default_like_values(self):
        # Arrange
        assignment = Assignment(
            content=LessonContent(),
            instructions="",
            passing_score=70,
            max_score=100,
            due_date=None,
            allow_late_submission=False,
            max_attempts=1,
            accepted_file_types="",
            max_file_size_mb=50,
        )

        # Act
        data = AssignmentSerializer(instance=assignment).data

        # Assert
        assert data["instructions"] == ""
        assert data["passingScore"] == 70
        assert data["maxScore"] == 100
        assert data["dueDate"] is None
        assert data["allowLateSubmission"] is False
        assert data["maxAttempts"] == 1
        assert data["acceptedFileTypes"] == ""
        assert data["maxFileSizeMB"] == 50


class TestAssignmentSubmissionFileSerializer:
    @staticmethod
    def make_submission_file():
        uploaded_file = SimpleUploadedFile(
            name="assignment.pdf",
            content=b"assignment content",
            content_type="application/pdf",
        )

        return AssignmentSubmissionFile(
            file=uploaded_file,
            size=12345,
            original_filename="my-assignment.pdf",
        )

    def test_serializes_expected_fields(self):
        # Arrange
        submission_file = self.make_submission_file()

        # Act
        data = AssignmentSubmissionFileSerializer(instance=submission_file).data

        # Assert
        assert set(data) == {"file", "name", "size"}

    def test_serializes_file_as_file_url(self):
        # Arrange
        submission_file = self.make_submission_file()

        # Act
        data = AssignmentSubmissionFileSerializer(instance=submission_file).data

        # Assert
        assert data["file"] == submission_file.file.url

    def test_name_is_serialized_from_file_name_property(self):
        # Arrange
        submission_file = self.make_submission_file()

        # Act
        data = AssignmentSubmissionFileSerializer(instance=submission_file).data

        # Assert
        assert data["name"] == "assignment.pdf"

    def test_name_contains_only_filename_not_storage_path(self):
        # Arrange
        submission_file = self.make_submission_file()
        submission_file.file.name = (
            "courses/10/25/lesson_contents/40/"
            "assignment_submission/user_7/assignment.pdf"
        )

        # Act
        data = AssignmentSubmissionFileSerializer(instance=submission_file).data

        # Assert
        assert data["name"] == "assignment.pdf"

    def test_original_filename_is_not_used_for_name(self):
        # Arrange
        submission_file = self.make_submission_file()
        submission_file.original_filename = "original-document.pdf"
        submission_file.file.name = "stored-document.pdf"

        # Act
        data = AssignmentSubmissionFileSerializer(instance=submission_file).data

        # Assert
        assert data["name"] == "stored-document.pdf"

    def test_serializes_size(self):
        # Arrange
        submission_file = self.make_submission_file()
        submission_file.size = 54321

        # Act
        data = AssignmentSubmissionFileSerializer(instance=submission_file).data

        # Assert
        assert data["size"] == 54321

    def test_serializes_null_size(self):
        # Arrange
        submission_file = self.make_submission_file()
        submission_file.size = None

        # Act
        data = AssignmentSubmissionFileSerializer(instance=submission_file).data

        # Assert
        assert data["size"] is None

    def test_size_is_read_only(self):
        # Arrange
        uploaded_file = SimpleUploadedFile(
            name="assignment.pdf",
            content=b"assignment content",
            content_type="application/pdf",
        )

        serializer = AssignmentSubmissionFileSerializer(
            data={
                "file": uploaded_file,
                "size": 99999,
            }
        )

        # Act
        assert serializer.is_valid(), serializer.errors

        # Assert
        assert "size" not in serializer.validated_data

    def test_name_is_read_only(self):
        # Arrange
        uploaded_file = SimpleUploadedFile(
            name="assignment.pdf",
            content=b"assignment content",
            content_type="application/pdf",
        )

        serializer = AssignmentSubmissionFileSerializer(
            data={
                "file": uploaded_file,
                "name": "fake-name.pdf",
            }
        )

        # Act
        assert serializer.is_valid(), serializer.errors

        # Assert
        assert "name" not in serializer.validated_data

    def test_file_is_writable(self):
        # Arrange
        uploaded_file = SimpleUploadedFile(
            name="assignment.pdf",
            content=b"assignment content",
            content_type="application/pdf",
        )

        serializer = AssignmentSubmissionFileSerializer(data={"file": uploaded_file})

        # Act
        assert serializer.is_valid(), serializer.errors

        # Assert
        assert serializer.validated_data["file"].name == "assignment.pdf"

    def test_does_not_expose_original_filename(self):
        # Arrange
        submission_file = self.make_submission_file()

        # Act
        data = AssignmentSubmissionFileSerializer(instance=submission_file).data

        # Assert
        assert "original_filename" not in data

    def test_does_not_expose_submission(self):
        # Arrange
        submission_file = self.make_submission_file()

        # Act
        data = AssignmentSubmissionFileSerializer(instance=submission_file).data

        # Assert
        assert "submission" not in data


class TestAssignmentSubmissionSerializer:
    def test_serializes_expected_fields(
        self,
        assignment_submission,
    ):
        # Arrange

        # Act
        data = AssignmentSubmissionSerializer(instance=assignment_submission).data

        # Assert
        assert set(data) == {
            "attemptNumber",
            "status",
            "submissionText",
            "files",
            "score",
            "feedback",
            "submittedAt",
            "gradedAt",
        }

    def test_serializes_submission_fields(
        self,
        assignment_submission,
    ):
        # Arrange
        assignment_submission.attempt_number = 2
        assignment_submission.status = assignment_submission.Status.SUBMITTED
        assignment_submission.submission_text = "My assignment submission."
        assignment_submission.score = Decimal("85.50")
        assignment_submission.feedback = "Good work."

        submitted_at = timezone.now()
        graded_at = timezone.now()

        assignment_submission.submitted_at = submitted_at
        assignment_submission.graded_at = graded_at
        assignment_submission.save()

        # Act
        data = AssignmentSubmissionSerializer(instance=assignment_submission).data

        # Assert
        assert data["attemptNumber"] == 2
        assert data["status"] == assignment_submission.Status.GRADED
        assert data["submissionText"] == "My assignment submission."
        assert data["score"] == "85.50"
        assert data["feedback"] == "Good work."

    def test_serializes_submitted_at(
        self,
        assignment_submission,
    ):
        # Arrange
        submitted_at = timezone.now()

        assignment_submission.submitted_at = submitted_at
        assignment_submission.save()

        # Act
        data = AssignmentSubmissionSerializer(instance=assignment_submission).data

        # Assert
        expected = (
            AssignmentSubmissionSerializer()
            .fields["submittedAt"]
            .to_representation(submitted_at)
        )

        assert data["submittedAt"] == expected

    def test_serializes_graded_at(
        self,
        assignment_submission,
    ):
        # Arrange
        graded_at = timezone.now()

        assignment_submission.graded_at = graded_at
        assignment_submission.save()

        # Act
        data = AssignmentSubmissionSerializer(instance=assignment_submission).data

        # Assert
        expected = (
            AssignmentSubmissionSerializer()
            .fields["gradedAt"]
            .to_representation(graded_at)
        )

        assert data["gradedAt"] == expected

    def test_serializes_empty_files(
        self,
        assignment_submission,
    ):
        # Arrange

        # Act
        data = AssignmentSubmissionSerializer(instance=assignment_submission).data

        # Assert
        assert data["files"] == []

    def test_serializes_nested_file(
        self,
        assignment_submission,
        tmp_path,
    ):
        # Arrange
        file_path = tmp_path / "assignment.pdf"
        file_path.write_bytes(b"assignment content")

        with file_path.open("rb") as file:
            submission_file = AssignmentSubmissionFile(
                submission=assignment_submission,
                original_filename="assignment.pdf",
            )
            submission_file.file.save(
                "assignment.pdf",
                File(file),
                save=True,
            )

        # Act
        data = AssignmentSubmissionSerializer(instance=assignment_submission).data

        # Assert
        assert len(data["files"]) == 1

        serialized_file = data["files"][0]

        assert serialized_file["file"] == submission_file.file.url
        assert serialized_file["name"] == "assignment.pdf"
        assert serialized_file["size"] == len(b"assignment content")

    def test_serializes_multiple_nested_files(
        self,
        assignment_submission,
        tmp_path,
    ):
        # Arrange
        first_path = tmp_path / "assignment.pdf"
        first_path.write_bytes(b"pdf content")

        second_path = tmp_path / "source.zip"
        second_path.write_bytes(b"zip content")

        with first_path.open("rb") as file:
            first_submission_file = AssignmentSubmissionFile(
                submission=assignment_submission,
                original_filename="assignment.pdf",
            )
            first_submission_file.file.save(
                "assignment.pdf",
                File(file),
                save=True,
            )

        with second_path.open("rb") as file:
            second_submission_file = AssignmentSubmissionFile(
                submission=assignment_submission,
                original_filename="source.zip",
            )
            second_submission_file.file.save(
                "source.zip",
                File(file),
                save=True,
            )

        # Act
        data = AssignmentSubmissionSerializer(instance=assignment_submission).data

        # Assert
        assert len(data["files"]) == 2

        first_serialized = data["files"][0]
        second_serialized = data["files"][1]

        assert first_serialized["file"] == first_submission_file.file.url
        assert first_serialized["name"] == "assignment.pdf"
        assert first_serialized["size"] == len(b"pdf content")

        assert second_serialized["file"] == second_submission_file.file.url
        assert second_serialized["name"] == "source.zip"
        assert second_serialized["size"] == len(b"zip content")

    def test_does_not_expose_internal_field_names(
        self,
        assignment_submission,
    ):
        # Arrange

        # Act
        data = AssignmentSubmissionSerializer(instance=assignment_submission).data

        # Assert
        assert "attempt_number" not in data
        assert "submission_text" not in data
        assert "submitted_at" not in data
        assert "graded_at" not in data

    def test_does_not_expose_assignment(
        self,
        assignment_submission,
    ):
        # Arrange

        # Act
        data = AssignmentSubmissionSerializer(instance=assignment_submission).data

        # Assert
        assert "assignment" not in data

    def test_does_not_expose_enrollment(
        self,
        assignment_submission,
    ):
        # Arrange

        # Act
        data = AssignmentSubmissionSerializer(instance=assignment_submission).data

        # Assert
        assert "enrollment" not in data

    def test_serializes_nullable_score(
        self,
        assignment_submission,
    ):
        # Arrange
        assignment_submission.score = None
        assignment_submission.save()

        # Act
        data = AssignmentSubmissionSerializer(instance=assignment_submission).data

        # Assert
        assert data["score"] is None

    def test_serializes_nullable_submitted_at(
        self,
        assignment_submission,
    ):
        # Arrange
        assignment_submission.submitted_at = None
        assignment_submission.save()

        # Act
        data = AssignmentSubmissionSerializer(instance=assignment_submission).data

        # Assert
        assert data["submittedAt"] is None

    def test_serializes_nullable_graded_at(
        self,
        assignment_submission,
    ):
        # Arrange
        assignment_submission.graded_at = None
        assignment_submission.save()

        # Act
        data = AssignmentSubmissionSerializer(instance=assignment_submission).data

        # Assert
        assert data["gradedAt"] is None
