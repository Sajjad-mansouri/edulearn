import pytest
from rest_framework import serializers

from assessments.api.serializers import BooleanAnswerSerializer
from assessments.models import BooleanAnswer


class TestBooleanAnswerSerializer:
    def test_serializer_uses_boolean_answer_model(self):
        # Arrange
        serializer = BooleanAnswerSerializer()

        # Act
        model = serializer.Meta.model

        # Assert
        assert model is BooleanAnswer

    def test_serializer_exposes_expected_fields(self):
        # Arrange
        serializer = BooleanAnswerSerializer()

        # Act
        fields = serializer.fields

        # Assert
        assert set(fields.keys()) == {"id", "answer"}

    def test_serializer_field_order_is_preserved(self):
        # Arrange
        serializer = BooleanAnswerSerializer()

        # Act
        field_names = list(serializer.fields.keys())

        # Assert
        assert field_names == ["id", "answer"]

    def test_id_field_is_integer_field(self):
        # Arrange
        serializer = BooleanAnswerSerializer()

        # Act
        field = serializer.fields["id"]

        # Assert
        assert isinstance(field, serializers.IntegerField)

    def test_id_field_is_read_only(self):
        # Arrange
        serializer = BooleanAnswerSerializer()

        # Act
        field = serializer.fields["id"]

        # Assert
        assert field.read_only is True

    def test_answer_field_is_boolean_field(self):
        # Arrange
        serializer = BooleanAnswerSerializer()

        # Act
        field = serializer.fields["answer"]

        # Assert
        assert isinstance(field, serializers.BooleanField)

    def test_answer_field_is_writable(self):
        # Arrange
        serializer = BooleanAnswerSerializer()

        # Act
        field = serializer.fields["answer"]

        # Assert
        assert field.read_only is False

    def test_answer_field_is_not_required(self):
        # Arrange
        serializer = BooleanAnswerSerializer()

        # Act
        field = serializer.fields["answer"]

        # Assert
        assert field.required is False

    @pytest.mark.parametrize("answer", [True, False])
    def test_serializes_answer_value(self, answer):
        # Arrange
        boolean_answer = BooleanAnswer(answer=answer)
        serializer = BooleanAnswerSerializer(boolean_answer)

        # Act
        data = serializer.data

        # Assert
        assert data["answer"] is answer

    def test_serializes_unsaved_instance(self):
        # Arrange
        boolean_answer = BooleanAnswer(answer=True)
        serializer = BooleanAnswerSerializer(boolean_answer)

        # Act
        data = serializer.data

        # Assert
        assert data == {
            "id": None,
            "answer": True,
        }

    def test_serializes_instance_with_id(self):
        # Arrange
        boolean_answer = BooleanAnswer(
            id=42,
            answer=True,
        )
        serializer = BooleanAnswerSerializer(boolean_answer)

        # Act
        data = serializer.data

        # Assert
        assert data == {
            "id": 42,
            "answer": True,
        }

    def test_question_is_not_exposed(self):
        # Arrange
        boolean_answer = BooleanAnswer(
            id=1,
            answer=True,
        )
        serializer = BooleanAnswerSerializer(boolean_answer)

        # Act
        data = serializer.data

        # Assert
        assert "question" not in data

    def test_serializer_has_no_unexpected_output_fields(self):
        # Arrange
        boolean_answer = BooleanAnswer(
            id=1,
            answer=True,
        )
        serializer = BooleanAnswerSerializer(boolean_answer)

        # Act
        data = serializer.data

        # Assert
        assert set(data.keys()) == {"id", "answer"}

    def test_serialized_answer_is_boolean(self):
        # Arrange
        boolean_answer = BooleanAnswer(
            id=1,
            answer=True,
        )
        serializer = BooleanAnswerSerializer(boolean_answer)

        # Act
        data = serializer.data

        # Assert
        assert data["answer"] is True
        assert isinstance(data["answer"], bool)

    @pytest.mark.parametrize(
        ("raw_value", "expected"),
        [
            (True, True),
            (False, False),
            ("true", True),
            ("false", False),
            ("True", True),
            ("False", False),
            ("TRUE", True),
            ("FALSE", False),
            ("yes", True),
            ("no", False),
            ("Yes", True),
            ("No", False),
            (1, True),
            (0, False),
        ],
    )
    def test_valid_boolean_values_are_normalized(
        self,
        raw_value,
        expected,
    ):
        # Arrange
        serializer = BooleanAnswerSerializer(
            data={"answer": raw_value},
        )

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid is True
        assert serializer.errors == {}
        assert serializer.validated_data["answer"] is expected

    @pytest.mark.parametrize(
        "invalid_value",
        [
            "invalid",
            "maybe",
            "true_value",
            "false_value",
            [],
            {},
            2,
            -1,
            2.5,
        ],
    )
    def test_invalid_boolean_values_are_rejected(self, invalid_value):
        # Arrange
        serializer = BooleanAnswerSerializer(
            data={"answer": invalid_value},
        )

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid is False
        assert "answer" in serializer.errors

    def test_empty_data_is_valid_for_creation(self):
        # Arrange
        serializer = BooleanAnswerSerializer(data={})

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid is True
        assert serializer.errors == {}
        assert serializer.validated_data == {}

    def test_answer_can_be_omitted_from_partial_update(self):
        # Arrange
        boolean_answer = BooleanAnswer(
            id=1,
            answer=True,
        )

        serializer = BooleanAnswerSerializer(
            instance=boolean_answer,
            data={},
            partial=True,
        )

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid is True
        assert serializer.errors == {}
        assert serializer.validated_data == {}

    @pytest.mark.parametrize("answer", [True, False])
    def test_partial_update_accepts_boolean_answer(self, answer):
        # Arrange
        boolean_answer = BooleanAnswer(
            id=1,
            answer=not answer,
        )

        serializer = BooleanAnswerSerializer(
            instance=boolean_answer,
            data={"answer": answer},
            partial=True,
        )

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid is True
        assert serializer.errors == {}
        assert serializer.validated_data["answer"] is answer

    def test_id_is_not_in_validated_data(self):
        # Arrange
        serializer = BooleanAnswerSerializer(
            data={
                "id": 999,
                "answer": True,
            },
        )

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid is True
        assert "id" not in serializer.validated_data
        assert serializer.validated_data["answer"] is True

    def test_id_cannot_be_updated_through_input(self):
        # Arrange
        boolean_answer = BooleanAnswer(
            id=10,
            answer=False,
        )

        serializer = BooleanAnswerSerializer(
            instance=boolean_answer,
            data={
                "id": 999,
                "answer": True,
            },
        )

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid is True
        assert "id" not in serializer.validated_data
        assert serializer.validated_data["answer"] is True
        assert boolean_answer.pk == 10

    def test_validated_data_contains_only_answer(self):
        # Arrange
        serializer = BooleanAnswerSerializer(
            data={
                "answer": True,
            },
        )

        # Act
        assert serializer.is_valid() is True

        # Assert
        assert set(serializer.validated_data.keys()) == {"answer"}

    def test_unknown_input_fields_are_ignored(self):
        # Arrange
        serializer = BooleanAnswerSerializer(
            data={
                "answer": True,
                "question": 123,
                "unexpected": "value",
            },
        )

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid is True
        assert serializer.validated_data == {"answer": True}

    @pytest.mark.parametrize(
        ("answer", "expected"),
        [
            (True, True),
            (False, False),
        ],
    )
    def test_update_validated_data_preserves_boolean_type(
        self,
        answer,
        expected,
    ):
        # Arrange
        serializer = BooleanAnswerSerializer(
            data={"answer": answer},
        )

        # Act
        assert serializer.is_valid() is True

        # Assert
        assert serializer.validated_data["answer"] is expected

    def test_model_string_representation_is_not_serializer_representation(self):
        # Arrange
        true_answer = BooleanAnswer(answer=True)
        false_answer = BooleanAnswer(answer=False)

        true_serializer = BooleanAnswerSerializer(true_answer)
        false_serializer = BooleanAnswerSerializer(false_answer)

        # Act
        true_model_string = str(true_answer)
        false_model_string = str(false_answer)

        # Assert
        assert true_model_string == "True"
        assert false_model_string == "False"

        assert true_serializer.data["answer"] is True
        assert false_serializer.data["answer"] is False
