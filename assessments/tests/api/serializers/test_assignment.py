import datetime

import pytest
from django.utils import timezone
from rest_framework import serializers

from assessments.api.serializers import AssignmentSerializer
from assessments.models import Assignment


class TestAssignmentSerializer:
    def test_serializer_uses_assignment_model(self):
        serializer = AssignmentSerializer()

        assert serializer.Meta.model is Assignment

    def test_serializer_has_expected_fields(self):
        serializer = AssignmentSerializer()

        assert list(serializer.fields.keys()) == [
            "id",
            "instructions",
            "passing_score",
            "max_score",
            "due_date",
            "allow_late_submission",
            "max_attempts",
            "accepted_file_types",
            "max_file_size_mb",
        ]

    def test_serializer_does_not_expose_content_field(self):
        serializer = AssignmentSerializer()

        assert "content" not in serializer.fields

    def test_id_field_is_read_only(self):
        serializer = AssignmentSerializer()

        field = serializer.fields["id"]

        assert isinstance(field, serializers.IntegerField)
        assert field.read_only is True
        assert field.required is False

    def test_instructions_field_configuration(self):
        serializer = AssignmentSerializer()

        field = serializer.fields["instructions"]

        assert isinstance(field, serializers.CharField)
        assert field.required is False
        assert field.allow_blank is True
        assert field.allow_null is False
        assert field.read_only is False

    def test_passing_score_field_configuration(self):
        serializer = AssignmentSerializer()

        field = serializer.fields["passing_score"]

        assert isinstance(field, serializers.IntegerField)
        assert field.required is False
        assert field.allow_null is True
        assert field.read_only is False

    def test_max_score_field_configuration(self):
        serializer = AssignmentSerializer()

        field = serializer.fields["max_score"]

        assert isinstance(field, serializers.IntegerField)
        assert field.required is False
        assert field.allow_null is True
        assert field.read_only is False

    def test_due_date_field_configuration(self):
        serializer = AssignmentSerializer()

        field = serializer.fields["due_date"]

        assert isinstance(field, serializers.DateTimeField)
        assert field.required is False
        assert field.allow_null is True
        assert field.read_only is False

    def test_allow_late_submission_field_configuration(self):
        serializer = AssignmentSerializer()

        field = serializer.fields["allow_late_submission"]

        assert isinstance(field, serializers.BooleanField)
        assert field.required is False
        assert field.allow_null is False
        assert field.read_only is False

    def test_max_attempts_field_configuration(self):
        serializer = AssignmentSerializer()

        field = serializer.fields["max_attempts"]

        assert isinstance(field, serializers.IntegerField)
        assert field.required is False
        assert field.allow_null is False
        assert field.read_only is False

    def test_accepted_file_types_field_configuration(self):
        serializer = AssignmentSerializer()

        field = serializer.fields["accepted_file_types"]

        assert isinstance(field, serializers.CharField)
        assert field.required is False
        assert field.allow_blank is True
        assert field.allow_null is False
        assert field.read_only is False
        assert field.max_length == 255

    def test_max_file_size_mb_field_configuration(self):
        serializer = AssignmentSerializer()

        field = serializer.fields["max_file_size_mb"]

        assert isinstance(field, serializers.IntegerField)
        assert field.required is False
        assert field.allow_null is False
        assert field.read_only is False

    def test_empty_data_is_valid_because_all_fields_are_optional(self):
        serializer = AssignmentSerializer(data={})

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data == {}

    @pytest.mark.parametrize(
        "instructions",
        [
            "",
            "Complete the assignment.",
            "Submit a PDF document containing your solution.",
            "توضیحات تکلیف",
        ],
    )
    def test_valid_instructions_are_accepted(self, instructions):
        serializer = AssignmentSerializer(
            data={
                "instructions": instructions,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["instructions"] == instructions

    def test_instructions_strips_surrounding_whitespace(self):
        serializer = AssignmentSerializer(
            data={
                "instructions": "  Complete the assignment.  ",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["instructions"] == ("Complete the assignment.")

    @pytest.mark.parametrize(
        "passing_score",
        [
            0,
            1,
            70,
            99,
            100,
        ],
    )
    def test_valid_passing_scores_are_accepted(self, passing_score):
        serializer = AssignmentSerializer(
            data={
                "passing_score": passing_score,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["passing_score"] == passing_score

    def test_passing_score_can_be_null(self):
        serializer = AssignmentSerializer(
            data={
                "passing_score": None,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["passing_score"] is None

    @pytest.mark.parametrize(
        "passing_score",
        [
            -1,
            -10,
        ],
    )
    def test_negative_passing_score_is_rejected(self, passing_score):
        serializer = AssignmentSerializer(
            data={
                "passing_score": passing_score,
            }
        )

        assert not serializer.is_valid()
        assert "passing_score" in serializer.errors

    @pytest.mark.parametrize(
        "max_score",
        [
            0,
            1,
            50,
            100,
        ],
    )
    def test_valid_max_scores_are_accepted(self, max_score):
        serializer = AssignmentSerializer(
            data={
                "max_score": max_score,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["max_score"] == max_score

    def test_max_score_can_be_null(self):
        serializer = AssignmentSerializer(
            data={
                "max_score": None,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["max_score"] is None

    @pytest.mark.parametrize(
        "max_score",
        [
            -1,
            -10,
        ],
    )
    def test_negative_max_score_is_rejected(self, max_score):
        serializer = AssignmentSerializer(
            data={
                "max_score": max_score,
            }
        )

        assert not serializer.is_valid()
        assert "max_score" in serializer.errors

    def test_due_date_accepts_datetime(self):
        due_date = timezone.now() + datetime.timedelta(days=7)

        serializer = AssignmentSerializer(
            data={
                "due_date": due_date,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["due_date"] == due_date

    def test_due_date_accepts_iso_datetime_string(self):
        serializer = AssignmentSerializer(
            data={
                "due_date": "2030-06-15T12:30:00Z",
            }
        )

        assert serializer.is_valid(), serializer.errors

        expected = datetime.datetime(
            2030,
            6,
            15,
            12,
            30,
            tzinfo=datetime.UTC,
        )

        assert serializer.validated_data["due_date"] == expected

    def test_due_date_can_be_null(self):
        serializer = AssignmentSerializer(
            data={
                "due_date": None,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["due_date"] is None

    def test_invalid_due_date_is_rejected(self):
        serializer = AssignmentSerializer(
            data={
                "due_date": "not-a-date",
            }
        )

        assert not serializer.is_valid()
        assert "due_date" in serializer.errors

    @pytest.mark.parametrize(
        "allow_late_submission",
        [
            True,
            False,
        ],
    )
    def test_allow_late_submission_accepts_boolean_values(
        self,
        allow_late_submission,
    ):
        serializer = AssignmentSerializer(
            data={
                "allow_late_submission": allow_late_submission,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert (
            serializer.validated_data["allow_late_submission"] is allow_late_submission
        )

    @pytest.mark.parametrize(
        "max_attempts",
        [
            0,
            1,
            2,
            10,
            100,
        ],
    )
    def test_valid_max_attempts_are_accepted(self, max_attempts):
        serializer = AssignmentSerializer(
            data={
                "max_attempts": max_attempts,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["max_attempts"] == max_attempts

    @pytest.mark.parametrize(
        "max_attempts",
        [
            -1,
            -10,
        ],
    )
    def test_negative_max_attempts_are_rejected(self, max_attempts):
        serializer = AssignmentSerializer(
            data={
                "max_attempts": max_attempts,
            }
        )

        assert not serializer.is_valid()
        assert "max_attempts" in serializer.errors

    @pytest.mark.parametrize(
        "accepted_file_types",
        [
            "",
            "pdf",
            "pdf,docx",
            "pdf,docx,zip",
            "PDF,DOCX,ZIP",
        ],
    )
    def test_valid_accepted_file_types_are_accepted(
        self,
        accepted_file_types,
    ):
        serializer = AssignmentSerializer(
            data={
                "accepted_file_types": accepted_file_types,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["accepted_file_types"] == accepted_file_types

    def test_accepted_file_types_rejects_values_longer_than_255_characters(
        self,
    ):
        accepted_file_types = "a" * 256

        serializer = AssignmentSerializer(
            data={
                "accepted_file_types": accepted_file_types,
            }
        )

        assert not serializer.is_valid()
        assert "accepted_file_types" in serializer.errors

    @pytest.mark.parametrize(
        "max_file_size_mb",
        [
            1,
            10,
            50,
            100,
            1000,
        ],
    )
    def test_valid_max_file_size_mb_is_accepted(self, max_file_size_mb):
        serializer = AssignmentSerializer(
            data={
                "max_file_size_mb": max_file_size_mb,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["max_file_size_mb"] == max_file_size_mb

    def test_zero_max_file_size_mb_is_accepted_by_serializer(self):
        serializer = AssignmentSerializer(
            data={
                "max_file_size_mb": 0,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["max_file_size_mb"] == 0

    @pytest.mark.parametrize(
        "max_file_size_mb",
        [
            -1,
            -10,
        ],
    )
    def test_negative_max_file_size_mb_is_rejected(
        self,
        max_file_size_mb,
    ):
        serializer = AssignmentSerializer(
            data={
                "max_file_size_mb": max_file_size_mb,
            }
        )

        assert not serializer.is_valid()
        assert "max_file_size_mb" in serializer.errors

    def test_all_assignment_fields_are_validated_together(self):
        due_date = timezone.now() + datetime.timedelta(days=7)

        serializer = AssignmentSerializer(
            data={
                "instructions": "Submit your completed project.",
                "passing_score": 70,
                "max_score": 100,
                "due_date": due_date,
                "allow_late_submission": True,
                "max_attempts": 3,
                "accepted_file_types": "pdf,docx,zip",
                "max_file_size_mb": 50,
            }
        )

        assert serializer.is_valid(), serializer.errors

        validated_data = serializer.validated_data

        assert validated_data["instructions"] == "Submit your completed project."
        assert validated_data["passing_score"] == 70
        assert validated_data["max_score"] == 100
        assert validated_data["due_date"] == due_date
        assert validated_data["allow_late_submission"] is True
        assert validated_data["max_attempts"] == 3
        assert validated_data["accepted_file_types"] == "pdf,docx,zip"
        assert validated_data["max_file_size_mb"] == 50

    def test_id_is_read_only_and_ignored_from_input(self):
        serializer = AssignmentSerializer(
            data={
                "id": 999,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert "id" not in serializer.validated_data

    def test_content_is_ignored_from_input(self):
        serializer = AssignmentSerializer(
            data={
                "content": 123,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert "content" not in serializer.validated_data

    def test_unknown_fields_are_ignored(self):
        serializer = AssignmentSerializer(
            data={
                "unknown_field": "value",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert "unknown_field" not in serializer.validated_data

    def test_partial_update_allows_fields_to_be_omitted(self):
        assignment = Assignment(
            instructions="Original instructions.",
            passing_score=70,
            max_score=100,
            allow_late_submission=False,
            max_attempts=1,
            accepted_file_types="pdf",
            max_file_size_mb=50,
        )

        serializer = AssignmentSerializer(
            instance=assignment,
            data={
                "passing_score": 80,
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["passing_score"] == 80
        assert "instructions" not in serializer.validated_data
        assert "max_score" not in serializer.validated_data
        assert "due_date" not in serializer.validated_data
        assert "allow_late_submission" not in serializer.validated_data
        assert "max_attempts" not in serializer.validated_data
        assert "accepted_file_types" not in serializer.validated_data
        assert "max_file_size_mb" not in serializer.validated_data

    def test_partial_update_with_empty_data_is_valid(self):
        assignment = Assignment(
            instructions="Original instructions.",
            passing_score=70,
            max_score=100,
            allow_late_submission=False,
            max_attempts=1,
            accepted_file_types="pdf",
            max_file_size_mb=50,
        )

        serializer = AssignmentSerializer(
            instance=assignment,
            data={},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data == {}
