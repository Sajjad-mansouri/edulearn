from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from django.utils import timezone
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from assessments.models import AssignmentSubmission
from instructors.api.serializers.assignments import (
    AssignmentSubmissionSerializer,
    GradeSerializer,
    InstructorAssignmentSerializer,
)


class TestInstructorAssignmentSerializer:
    def test_serializer_configuration_requires_fields_or_exclude(self):
        """
        DRF validates ModelSerializer Meta configuration when its fields
        are evaluated, not when the serializer instance is constructed.
        """
        serializer = InstructorAssignmentSerializer()

        with pytest.raises(AssertionError):
            _ = serializer.fields


class TestAssignmentSubmissionSerializer:
    @pytest.fixture
    def api_request(self):
        factory = APIRequestFactory()

        return Request(
            factory.get(
                "/api/instructors/assignments/submissions/",
                HTTP_HOST="testserver",
            )
        )

    @pytest.fixture
    def submission(self):
        user = SimpleNamespace(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
        )
        user.get_full_name = Mock(return_value="John Doe")

        profile = Mock()
        profile.get_avatar.return_value = "/media/avatars/john.jpg"
        user.profile = profile

        course = SimpleNamespace(
            title="Django REST Framework",
            slug="django-rest-framework",
        )

        enrollment = SimpleNamespace(
            user=user,
            course=course,
        )

        lesson = SimpleNamespace(
            title="Assignment: Serializers",
        )

        section = SimpleNamespace(
            course=course,
        )

        lesson.section = section

        content = SimpleNamespace(
            title="Assignment: Serializers",
            lesson=lesson,
        )

        assignment = SimpleNamespace(
            content=content,
            instructions="Implement a DRF serializer.",
            max_score=100,
        )

        submission = SimpleNamespace(
            id=123,
            assignment=assignment,
            enrollment=enrollment,
            status=AssignmentSubmission.Status.SUBMITTED,
            submitted_at=timezone.make_aware(datetime(2026, 9, 10, 10, 0, 0)),
            graded_at=timezone.make_aware(datetime(2026, 9, 10, 11, 0, 0)),
            score=Decimal("85.00"),
            attempt_number=1,
            feedback="Good work.",
            submission_text="My submission.",
        )

        submission.get_letter_grade = Mock(return_value="B")

        files_manager = Mock()
        files_manager.all.return_value = []
        submission.files = files_manager

        return submission

    @pytest.fixture
    def serializer(self, api_request, submission):
        return AssignmentSubmissionSerializer(
            instance=submission,
            context={"request": api_request},
        )

    def test_declares_expected_fields(self):
        serializer = AssignmentSubmissionSerializer()

        assert set(serializer.fields) == {
            "id",
            "student_name",
            "student_email",
            "student_avatar",
            "assignment_name",
            "assignment_desc",
            "course_name",
            "course_slug",
            "status",
            "submitted_at",
            "graded_at",
            "score",
            "letter_grade",
            "attempt_number",
            "feedback",
            "submission_text",
            "files",
        }

    def test_all_computed_fields_are_serializer_method_fields(self):
        serializer = AssignmentSubmissionSerializer()

        expected_method_fields = {
            "student_name",
            "student_email",
            "student_avatar",
            "assignment_name",
            "assignment_desc",
            "course_name",
            "course_slug",
            "letter_grade",
            "files",
        }

        for field_name in expected_method_fields:
            assert isinstance(
                serializer.fields[field_name],
                serializers.SerializerMethodField,
            )

    def test_student_name_uses_user_get_full_name(
        self,
        serializer,
        submission,
    ):
        result = serializer.get_student_name(submission)

        assert result == "John Doe"
        submission.enrollment.user.get_full_name.assert_called_once_with()

    def test_student_email_returns_user_email(
        self,
        serializer,
        submission,
    ):
        result = serializer.get_student_email(submission)

        assert result == "john@example.com"

    def test_student_avatar_uses_profile_avatar(
        self,
        serializer,
        submission,
        api_request,
    ):
        avatar = "/media/avatars/john.jpg"

        submission.enrollment.user.profile.get_avatar.return_value = avatar

        result = serializer.get_student_avatar(submission)

        assert result == api_request.build_absolute_uri(avatar)

        submission.enrollment.user.profile.get_avatar.assert_called_once_with()

    def test_student_avatar_builds_absolute_url(
        self,
        serializer,
        submission,
        api_request,
    ):
        avatar = "/media/avatars/student.png"

        submission.enrollment.user.profile.get_avatar.return_value = avatar

        result = serializer.get_student_avatar(submission)

        assert result.startswith("http://testserver/")
        assert result == api_request.build_absolute_uri(avatar)

    def test_assignment_name_comes_from_lesson_title(
        self,
        serializer,
        submission,
    ):
        result = serializer.get_assignment_name(submission)

        assert result == "Assignment: Serializers"

    def test_assignment_description_comes_from_instructions(
        self,
        serializer,
        submission,
    ):
        result = serializer.get_assignment_desc(submission)

        assert result == "Implement a DRF serializer."

    def test_course_name_comes_from_enrollment_course(
        self,
        serializer,
        submission,
    ):
        result = serializer.get_course_name(submission)

        assert result == "Django REST Framework"

    def test_course_slug_comes_from_enrollment_course(
        self,
        serializer,
        submission,
    ):
        result = serializer.get_course_slug(submission)

        assert result == "django-rest-framework"

    def test_letter_grade_delegates_to_model_method(
        self,
        serializer,
        submission,
    ):
        submission.get_letter_grade.return_value = "B"

        result = serializer.get_letter_grade(submission)

        assert result == "B"
        submission.get_letter_grade.assert_called_once_with()

    @pytest.mark.parametrize(
        "letter_grade",
        ["A", "B", "C", "D", ""],
    )
    def test_letter_grade_returns_model_result(
        self,
        serializer,
        submission,
        letter_grade,
    ):
        submission.get_letter_grade.return_value = letter_grade

        assert serializer.get_letter_grade(submission) == letter_grade

    def test_get_files_returns_empty_list_without_files(
        self,
        serializer,
        submission,
    ):
        submission.files.all.return_value = []

        result = serializer.get_files(submission)

        assert result == []
        submission.files.all.assert_called_once_with()

    def test_get_files_serializes_file_metadata(
        self,
        serializer,
        submission,
        api_request,
    ):
        uploaded_at = timezone.make_aware(datetime(2026, 9, 10, 12, 30, 0))

        file_field = Mock()
        file_field.name = "courses/1/submissions/solution.pdf"
        file_field.url = "/media/courses/1/submissions/solution.pdf"
        file_field.size = len(b"assignment content")

        submission_file = SimpleNamespace(
            id=10,
            file=file_field,
            uploaded_at=uploaded_at,
        )

        submission.files.all.return_value = [submission_file]

        result = serializer.get_files(submission)

        assert len(result) == 1

        serialized_file = result[0]

        assert serialized_file["id"] == 10
        assert serialized_file["name"] == "solution.pdf"
        assert serialized_file["size"] == len(b"assignment content")
        assert serialized_file["uploaded_at"] == uploaded_at
        assert serialized_file["path"] == api_request.build_absolute_uri(file_field.url)

    def test_get_files_extracts_basename_from_nested_path(
        self,
        serializer,
        submission,
        api_request,
    ):
        uploaded_at = timezone.make_aware(datetime(2026, 9, 10, 12, 30, 0))

        file_field = Mock()
        file_field.name = (
            "courses/1/2/lesson_contents/3/"
            "assignment_submission/user_4/final-answer.pdf"
        )
        file_field.url = (
            "/media/courses/1/2/lesson_contents/3/"
            "assignment_submission/user_4/final-answer.pdf"
        )
        file_field.size = 1234

        submission_file = SimpleNamespace(
            id=20,
            file=file_field,
            uploaded_at=uploaded_at,
        )

        submission.files.all.return_value = [submission_file]

        result = serializer.get_files(submission)

        assert result == [
            {
                "id": 20,
                "name": "final-answer.pdf",
                "path": api_request.build_absolute_uri(file_field.url),
                "size": 1234,
                "uploaded_at": uploaded_at,
            }
        ]

    def test_get_files_preserves_uploaded_at_value(
        self,
        serializer,
        submission,
    ):
        uploaded_at = timezone.make_aware(datetime(2026, 9, 12, 14, 45, 30))

        file_field = Mock()
        file_field.name = "submissions/answer.pdf"
        file_field.url = "/media/submissions/answer.pdf"
        file_field.size = 500

        submission_file = SimpleNamespace(
            id=5,
            file=file_field,
            uploaded_at=uploaded_at,
        )

        submission.files.all.return_value = [submission_file]

        result = serializer.get_files(submission)

        assert result[0]["uploaded_at"] == uploaded_at

    def test_get_files_serializes_multiple_files(
        self,
        serializer,
        submission,
        api_request,
    ):
        first_file = Mock()
        first_file.id = 1
        first_file.file.name = "submissions/first.pdf"
        first_file.file.url = "/media/submissions/first.pdf"
        first_file.file.size = 100
        first_file.uploaded_at = timezone.make_aware(datetime(2026, 9, 10, 10, 0, 0))

        second_file = Mock()
        second_file.id = 2
        second_file.file.name = "submissions/second.zip"
        second_file.file.url = "/media/submissions/second.zip"
        second_file.file.size = 200
        second_file.uploaded_at = timezone.make_aware(datetime(2026, 9, 10, 11, 0, 0))

        submission.files.all.return_value = [
            first_file,
            second_file,
        ]

        result = serializer.get_files(submission)

        assert result == [
            {
                "id": 1,
                "name": "first.pdf",
                "path": api_request.build_absolute_uri("/media/submissions/first.pdf"),
                "size": 100,
                "uploaded_at": first_file.uploaded_at,
            },
            {
                "id": 2,
                "name": "second.zip",
                "path": api_request.build_absolute_uri("/media/submissions/second.zip"),
                "size": 200,
                "uploaded_at": second_file.uploaded_at,
            },
        ]

    def test_serializes_complete_submission(
        self,
        serializer,
    ):
        data = serializer.data

        assert data["id"] == 123
        assert data["student_name"] == "John Doe"
        assert data["student_email"] == "john@example.com"
        assert data["assignment_name"] == "Assignment: Serializers"
        assert data["assignment_desc"] == ("Implement a DRF serializer.")
        assert data["course_name"] == "Django REST Framework"
        assert data["course_slug"] == "django-rest-framework"
        assert data["status"] == AssignmentSubmission.Status.SUBMITTED

        assert data["submitted_at"] == ("2026-09-10T10:00:00+03:30")
        assert data["graded_at"] == ("2026-09-10T11:00:00+03:30")

        assert data["score"] == "85.00"
        assert data["letter_grade"] == "B"
        assert data["attempt_number"] == 1
        assert data["feedback"] == "Good work."
        assert data["submission_text"] == "My submission."
        assert data["files"] == []

    def test_serializes_null_score(
        self,
        serializer,
        submission,
    ):
        submission.score = None
        submission.get_letter_grade.return_value = ""

        data = serializer.data

        assert data["score"] is None
        assert data["letter_grade"] == ""

    def test_serializes_null_submitted_at(
        self,
        serializer,
        submission,
    ):
        submission.submitted_at = None

        data = serializer.data

        assert data["submitted_at"] is None

    def test_serializes_null_graded_at(
        self,
        serializer,
        submission,
    ):
        submission.graded_at = None

        data = serializer.data

        assert data["graded_at"] is None

    def test_serializes_empty_feedback(
        self,
        serializer,
        submission,
    ):
        submission.feedback = ""

        data = serializer.data

        assert data["feedback"] == ""

    def test_serializes_empty_submission_text(
        self,
        serializer,
        submission,
    ):
        submission.submission_text = ""

        data = serializer.data

        assert data["submission_text"] == ""

    def test_serializes_attempt_number(
        self,
        serializer,
        submission,
    ):
        submission.attempt_number = 3

        data = serializer.data

        assert data["attempt_number"] == 3

    @pytest.mark.parametrize(
        "status",
        [
            AssignmentSubmission.Status.DRAFT,
            AssignmentSubmission.Status.SUBMITTED,
            AssignmentSubmission.Status.GRADED,
            AssignmentSubmission.Status.RETURNED,
            AssignmentSubmission.Status.LATE,
        ],
    )
    def test_serializes_submission_status(
        self,
        serializer,
        submission,
        status,
    ):
        submission.status = status

        data = serializer.data

        assert data["status"] == status


class TestGradeSerializer:
    def test_declares_only_expected_fields(self):
        serializer = GradeSerializer()

        assert set(serializer.fields) == {
            "score",
            "feedback",
        }

    def test_score_is_decimal_field(self):
        serializer = GradeSerializer()

        assert isinstance(
            serializer.fields["score"],
            serializers.DecimalField,
        )

    def test_feedback_is_char_field(self):
        serializer = GradeSerializer()

        assert isinstance(
            serializer.fields["feedback"],
            serializers.CharField,
        )

    def test_score_allows_null(self):
        serializer = GradeSerializer()

        assert serializer.fields["score"].allow_null is True

    def test_score_is_not_required(self):
        serializer = GradeSerializer()

        assert serializer.fields["score"].required is False

    def test_feedback_is_not_required(self):
        serializer = GradeSerializer()

        assert serializer.fields["feedback"].required is False

    def test_serializes_score_and_feedback(self):
        submission = SimpleNamespace(
            score=Decimal("85.50"),
            feedback="Good work.",
        )

        serializer = GradeSerializer(instance=submission)

        assert serializer.data == {
            "score": "85.50",
            "feedback": "Good work.",
        }

    def test_serializes_null_score(self):
        submission = SimpleNamespace(
            score=None,
            feedback="Not graded yet.",
        )

        serializer = GradeSerializer(instance=submission)

        assert serializer.data == {
            "score": None,
            "feedback": "Not graded yet.",
        }

    def test_serializes_empty_feedback(self):
        submission = SimpleNamespace(
            score=Decimal("75.00"),
            feedback="",
        )

        serializer = GradeSerializer(instance=submission)

        assert serializer.data == {
            "score": "75.00",
            "feedback": "",
        }

    def test_deserializes_valid_grade(self):
        serializer = GradeSerializer(
            data={
                "score": "85.50",
                "feedback": "Good work.",
            }
        )

        assert serializer.is_valid()

        assert serializer.validated_data == {
            "score": Decimal("85.50"),
            "feedback": "Good work.",
        }

    def test_accepts_missing_score(self):
        serializer = GradeSerializer(
            data={
                "feedback": "Good work.",
            }
        )

        assert serializer.is_valid()

        assert serializer.validated_data == {
            "feedback": "Good work.",
        }

    def test_accepts_missing_feedback(self):
        serializer = GradeSerializer(
            data={
                "score": "85.00",
            }
        )

        assert serializer.is_valid()

        assert serializer.validated_data == {
            "score": Decimal("85.00"),
        }

    def test_accepts_null_score(self):
        serializer = GradeSerializer(
            data={
                "score": None,
                "feedback": "Not graded yet.",
            }
        )

        assert serializer.is_valid()

        assert serializer.validated_data["score"] is None

    def test_accepts_empty_feedback(self):
        serializer = GradeSerializer(
            data={
                "score": "85.00",
                "feedback": "",
            }
        )

        assert serializer.is_valid()

        assert serializer.validated_data["feedback"] == ""

    @pytest.mark.parametrize(
        "score",
        [
            "0",
            "0.00",
            "1.25",
            "50.50",
            "85.75",
            "9999.99",
        ],
    )
    def test_accepts_values_supported_by_decimal_field(
        self,
        score,
    ):
        serializer = GradeSerializer(
            data={
                "score": score,
                "feedback": "Feedback",
            }
        )

        assert serializer.is_valid()

    def test_rejects_score_exceeding_max_digits(self):
        serializer = GradeSerializer(
            data={
                "score": "1234567.89",
                "feedback": "Feedback",
            }
        )

        assert not serializer.is_valid()
        assert "score" in serializer.errors

    def test_rejects_score_with_too_many_decimal_places(self):
        serializer = GradeSerializer(
            data={
                "score": "85.123",
                "feedback": "Feedback",
            }
        )

        assert not serializer.is_valid()
        assert "score" in serializer.errors

    def test_rejects_non_numeric_score(self):
        serializer = GradeSerializer(
            data={
                "score": "not-a-number",
                "feedback": "Feedback",
            }
        )

        assert not serializer.is_valid()
        assert "score" in serializer.errors

    def test_accepts_negative_score_at_serializer_level(self):
        """
        AssignmentSubmission.clean() is responsible for rejecting
        negative scores. The DecimalField itself does not define a
        minimum-value validator.
        """
        serializer = GradeSerializer(
            data={
                "score": "-1.00",
                "feedback": "Feedback",
            }
        )

        assert serializer.is_valid()
        assert serializer.validated_data["score"] == Decimal("-1.00")
