import pytest
from rest_framework import serializers

from assessments.api.serializers import AcceptedAnswerSerializer
from assessments.models import AcceptedAnswer


class TestAcceptedAnswerSerializer:
    def test_serializer_uses_accepted_answer_model(self):
        # Arrange
        serializer = AcceptedAnswerSerializer()

        # Act
        model = serializer.Meta.model

        # Assert
        assert model is AcceptedAnswer

    def test_serializer_exposes_expected_fields(self):
        # Arrange
        serializer = AcceptedAnswerSerializer()

        # Act
        fields = serializer.fields

        # Assert
        assert set(fields.keys()) == {"id", "answer"}

    def test_serializer_field_order_is_preserved(self):
        # Arrange
        serializer = AcceptedAnswerSerializer()

        # Act
        field_names = list(serializer.fields.keys())

        # Assert
        assert field_names == ["id", "answer"]

    def test_id_field_is_integer_field(self):
        # Arrange
        serializer = AcceptedAnswerSerializer()

        # Act
        field = serializer.fields["id"]

        # Assert
        assert isinstance(field, serializers.IntegerField)

    def test_id_field_is_read_only(self):
        # Arrange
        serializer = AcceptedAnswerSerializer()

        # Act
        field = serializer.fields["id"]

        # Assert
        assert field.read_only is True

    def test_id_field_is_not_required(self):
        # Arrange
        serializer = AcceptedAnswerSerializer()

        # Act
        field = serializer.fields["id"]

        # Assert
        assert field.required is False

    def test_answer_field_is_char_field(self):
        # Arrange
        serializer = AcceptedAnswerSerializer()

        # Act
        field = serializer.fields["answer"]

        # Assert
        assert isinstance(field, serializers.CharField)

    def test_answer_field_is_writable(self):
        # Arrange
        serializer = AcceptedAnswerSerializer()

        # Act
        field = serializer.fields["answer"]

        # Assert
        assert field.read_only is False

    def test_answer_field_is_required(self):
        # Arrange
        serializer = AcceptedAnswerSerializer()

        # Act
        field = serializer.fields["answer"]

        # Assert
        assert field.required is True

    def test_answer_field_does_not_allow_blank(self):
        # Arrange
        serializer = AcceptedAnswerSerializer()

        # Act
        field = serializer.fields["answer"]

        # Assert
        assert field.allow_blank is False

    def test_answer_field_does_not_allow_null(self):
        # Arrange
        serializer = AcceptedAnswerSerializer()

        # Act
        field = serializer.fields["answer"]

        # Assert
        assert field.allow_null is False

    def test_answer_field_has_max_length_255(self):
        # Arrange
        serializer = AcceptedAnswerSerializer()

        # Act
        field = serializer.fields["answer"]

        # Assert
        assert field.max_length == 255

    def test_serializes_answer(self):
        # Arrange
        accepted_answer = AcceptedAnswer(
            id=1,
            answer="Django",
        )
        serializer = AcceptedAnswerSerializer(accepted_answer)

        # Act
        data = serializer.data

        # Assert
        assert data == {
            "id": 1,
            "answer": "Django",
        }

    def test_serializes_unsaved_instance(self):
        # Arrange
        accepted_answer = AcceptedAnswer(
            answer="Django",
        )
        serializer = AcceptedAnswerSerializer(accepted_answer)

        # Act
        data = serializer.data

        # Assert
        assert data == {
            "id": None,
            "answer": "Django",
        }

    def test_serializes_instance_id(self):
        # Arrange
        accepted_answer = AcceptedAnswer(
            id=42,
            answer="Django",
        )
        serializer = AcceptedAnswerSerializer(accepted_answer)

        # Act
        data = serializer.data

        # Assert
        assert data["id"] == 42
        assert isinstance(data["id"], int)

    def test_serializes_answer_as_string(self):
        # Arrange
        accepted_answer = AcceptedAnswer(
            id=1,
            answer="Django",
        )
        serializer = AcceptedAnswerSerializer(accepted_answer)

        # Act
        data = serializer.data

        # Assert
        assert data["answer"] == "Django"
        assert isinstance(data["answer"], str)

    @pytest.mark.parametrize(
        "answer",
        [
            "Django",
            "Python",
            "True",
            "False",
            "42",
            "a",
            "Django REST Framework",
            "Python 3.13",
            "a" * 255,
        ],
    )
    def test_valid_answer_values_are_accepted(self, answer):
        # Arrange
        serializer = AcceptedAnswerSerializer(
            data={"answer": answer},
        )

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid is True
        assert serializer.errors == {}
        assert serializer.validated_data["answer"] == answer

    def test_answer_is_required(self):
        # Arrange
        serializer = AcceptedAnswerSerializer(data={})

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid is False
        assert "answer" in serializer.errors

    def test_blank_answer_is_rejected(self):
        # Arrange
        serializer = AcceptedAnswerSerializer(
            data={"answer": ""},
        )

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid is False
        assert "answer" in serializer.errors

    def test_null_answer_is_rejected(self):
        # Arrange
        serializer = AcceptedAnswerSerializer(
            data={"answer": None},
        )

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid is False
        assert "answer" in serializer.errors

    @pytest.mark.parametrize(
        "answer",
        [
            True,
            False,
            [],
            {},
        ],
    )
    def test_invalid_answer_types_are_rejected(self, answer):
        # Arrange
        serializer = AcceptedAnswerSerializer(
            data={"answer": answer},
        )

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid is False
        assert "answer" in serializer.errors

    def test_answer_with_255_characters_is_valid(self):
        # Arrange
        answer = "a" * 255
        serializer = AcceptedAnswerSerializer(
            data={"answer": answer},
        )

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid is True
        assert serializer.validated_data["answer"] == answer

    def test_answer_with_256_characters_is_rejected(self):
        # Arrange
        answer = "a" * 256
        serializer = AcceptedAnswerSerializer(
            data={"answer": answer},
        )

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid is False
        assert "answer" in serializer.errors

    @pytest.mark.parametrize(
        ("answer", "expected"),
        [
            (" Django ", "Django"),
            ("  Django  ", "Django"),
            ("\tDjango\t", "Django"),
            ("\nDjango\n", "Django"),
            (" Django REST Framework ", "Django REST Framework"),
        ],
    )
    def test_answer_strips_leading_and_trailing_whitespace(
        self,
        answer,
        expected,
    ):
        # Arrange
        serializer = AcceptedAnswerSerializer(
            data={"answer": answer},
        )

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid is True
        assert serializer.validated_data["answer"] == expected

    @pytest.mark.parametrize(
        "answer",
        [
            "Django REST Framework",
            "Django  REST  Framework",
            "Django\tREST",
            "Django\nREST",
            "Python 3.13",
        ],
    )
    def test_internal_whitespace_is_preserved(self, answer):
        # Arrange
        serializer = AcceptedAnswerSerializer(
            data={"answer": answer},
        )

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid is True
        assert serializer.validated_data["answer"] == answer

    def test_whitespace_only_answer_is_rejected(self):
        # Arrange
        serializer = AcceptedAnswerSerializer(
            data={"answer": "   "},
        )

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid is False
        assert "answer" in serializer.errors

    def test_tab_only_answer_is_rejected(self):
        # Arrange
        serializer = AcceptedAnswerSerializer(
            data={"answer": "\t\t"},
        )

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid is False
        assert "answer" in serializer.errors

    def test_newline_only_answer_is_rejected(self):
        # Arrange
        serializer = AcceptedAnswerSerializer(
            data={"answer": "\n\n"},
        )

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid is False
        assert "answer" in serializer.errors

    def test_id_is_not_in_validated_data(self):
        # Arrange
        serializer = AcceptedAnswerSerializer(
            data={
                "id": 999,
                "answer": "Django",
            },
        )

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid is True
        assert "id" not in serializer.validated_data
        assert serializer.validated_data["answer"] == "Django"

    def test_id_cannot_be_changed_through_input(self):
        # Arrange
        accepted_answer = AcceptedAnswer(
            id=10,
            answer="Django",
        )

        serializer = AcceptedAnswerSerializer(
            instance=accepted_answer,
            data={
                "id": 999,
                "answer": "Python",
            },
        )

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid is True
        assert "id" not in serializer.validated_data
        assert serializer.validated_data["answer"] == "Python"
        assert accepted_answer.pk == 10

    def test_validated_data_contains_only_answer(self):
        # Arrange
        serializer = AcceptedAnswerSerializer(
            data={
                "answer": "Django",
            },
        )

        # Act
        assert serializer.is_valid() is True

        # Assert
        assert set(serializer.validated_data.keys()) == {"answer"}

    def test_question_is_not_exposed(self):
        # Arrange
        accepted_answer = AcceptedAnswer(
            id=1,
            answer="Django",
        )
        serializer = AcceptedAnswerSerializer(accepted_answer)

        # Act
        data = serializer.data

        # Assert
        assert "question" not in data

    def test_question_is_not_a_serializer_field(self):
        # Arrange
        serializer = AcceptedAnswerSerializer()

        # Act
        fields = serializer.fields

        # Assert
        assert "question" not in fields

    def test_unknown_input_fields_are_ignored(self):
        # Arrange
        serializer = AcceptedAnswerSerializer(
            data={
                "answer": "Django",
                "question": 123,
                "unexpected": "value",
            },
        )

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid is True
        assert serializer.validated_data == {
            "answer": "Django",
        }

    def test_partial_update_allows_answer_to_be_omitted(self):
        # Arrange
        accepted_answer = AcceptedAnswer(
            id=1,
            answer="Django",
        )

        serializer = AcceptedAnswerSerializer(
            instance=accepted_answer,
            data={},
            partial=True,
        )

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid is True
        assert serializer.errors == {}
        assert serializer.validated_data == {}

    @pytest.mark.parametrize(
        "answer",
        [
            "Python",
            "Django",
            "Flask",
            "FastAPI",
        ],
    )
    def test_partial_update_accepts_answer(self, answer):
        # Arrange
        accepted_answer = AcceptedAnswer(
            id=1,
            answer="Django",
        )

        serializer = AcceptedAnswerSerializer(
            instance=accepted_answer,
            data={"answer": answer},
            partial=True,
        )

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid is True
        assert serializer.errors == {}
        assert serializer.validated_data["answer"] == answer

    def test_partial_update_without_answer_has_empty_validated_data(self):
        # Arrange
        accepted_answer = AcceptedAnswer(
            id=1,
            answer="Django",
        )

        serializer = AcceptedAnswerSerializer(
            instance=accepted_answer,
            data={},
            partial=True,
        )

        # Act
        assert serializer.is_valid() is True

        # Assert
        assert serializer.validated_data == {}

    def test_serializer_has_no_unexpected_output_fields(self):
        # Arrange
        accepted_answer = AcceptedAnswer(
            id=1,
            answer="Django",
        )
        serializer = AcceptedAnswerSerializer(accepted_answer)

        # Act
        data = serializer.data

        # Assert
        assert set(data.keys()) == {"id", "answer"}

    def test_model_string_representation_returns_answer(self):
        # Arrange
        accepted_answer = AcceptedAnswer(
            answer="Django",
        )

        # Act
        result = str(accepted_answer)

        # Assert
        assert result == "Django"

    @pytest.mark.parametrize(
        "answer",
        [
            "Django",
            "Python",
            "True",
            "False",
            "123",
            "Yes",
            "No",
        ],
    )
    def test_model_string_representation_matches_answer(self, answer):
        # Arrange
        accepted_answer = AcceptedAnswer(answer=answer)

        # Act
        result = str(accepted_answer)

        # Assert
        assert result == answer

    def test_unicode_answer_is_accepted(self):
        # Arrange
        answer = "پایتون"
        serializer = AcceptedAnswerSerializer(
            data={"answer": answer},
        )

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid is True
        assert serializer.validated_data["answer"] == answer

    def test_special_characters_are_accepted(self):
        # Arrange
        answer = "Python/Django @ 2026 #1"
        serializer = AcceptedAnswerSerializer(
            data={"answer": answer},
        )

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid is True
        assert serializer.validated_data["answer"] == answer

    def test_unicode_answer_respects_max_length(self):
        # Arrange
        answer = "پ" * 255
        serializer = AcceptedAnswerSerializer(
            data={"answer": answer},
        )

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid is True
        assert serializer.validated_data["answer"] == answer

    def test_unicode_answer_over_max_length_is_rejected(self):
        # Arrange
        answer = "پ" * 256
        serializer = AcceptedAnswerSerializer(
            data={"answer": answer},
        )

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid is False
        assert "answer" in serializer.errors
