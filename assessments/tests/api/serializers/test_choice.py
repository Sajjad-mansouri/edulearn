import pytest
from rest_framework import serializers

from assessments.api.serializers import ChoiceSerializer
from assessments.models import Choice


class TestChoiceSerializer:
    def test_serializer_uses_choice_model(self):
        serializer = ChoiceSerializer()

        assert serializer.Meta.model is Choice

    def test_serializer_has_expected_fields(self):
        serializer = ChoiceSerializer()

        assert list(serializer.fields.keys()) == [
            "id",
            "text",
            "is_correct",
        ]

    def test_id_field_configuration(self):
        serializer = ChoiceSerializer()

        field = serializer.fields["id"]

        assert isinstance(field, serializers.IntegerField)
        assert field.read_only is True
        assert field.required is False

    def test_text_field_configuration(self):
        serializer = ChoiceSerializer()

        field = serializer.fields["text"]

        assert isinstance(field, serializers.CharField)
        assert field.required is True
        assert field.allow_blank is False
        assert field.allow_null is False
        assert field.max_length == 500
        assert field.read_only is False

    def test_is_correct_field_configuration(self):
        serializer = ChoiceSerializer()

        field = serializer.fields["is_correct"]

        assert isinstance(field, serializers.BooleanField)
        assert field.required is False
        assert field.allow_null is False
        assert field.read_only is False

    @pytest.mark.parametrize(
        "text",
        [
            "Django",
            "Python",
            "Django REST Framework",
            "A",
            "42",
            "a" * 500,
        ],
    )
    def test_valid_text_values_are_accepted(self, text):
        serializer = ChoiceSerializer(
            data={
                "text": text,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["text"] == text
        assert "is_correct" not in serializer.validated_data

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (123, "123"),
            (12.5, "12.5"),
        ],
    )
    def test_numeric_text_values_are_coerced_to_strings(self, value, expected):
        serializer = ChoiceSerializer(
            data={
                "text": value,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["text"] == expected

    @pytest.mark.parametrize(
        "text",
        [
            "",
            " ",
            "   ",
            "\t",
            "\n",
            "\t \n",
        ],
    )
    def test_blank_text_is_rejected(self, text):
        serializer = ChoiceSerializer(
            data={
                "text": text,
            }
        )

        assert not serializer.is_valid()
        assert "text" in serializer.errors

    def test_null_text_is_rejected(self):
        serializer = ChoiceSerializer(
            data={
                "text": None,
            }
        )

        assert not serializer.is_valid()
        assert "text" in serializer.errors

    @pytest.mark.parametrize(
        "value",
        [
            [],
            {},
            (),
        ],
    )
    def test_container_text_values_are_rejected(self, value):
        serializer = ChoiceSerializer(
            data={
                "text": value,
            }
        )

        assert not serializer.is_valid()
        assert "text" in serializer.errors

    def test_text_with_500_characters_is_accepted(self):
        text = "a" * 500

        serializer = ChoiceSerializer(
            data={
                "text": text,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["text"] == text

    def test_text_with_more_than_500_characters_is_rejected(self):
        text = "a" * 501

        serializer = ChoiceSerializer(
            data={
                "text": text,
            }
        )

        assert not serializer.is_valid()
        assert "text" in serializer.errors

    @pytest.mark.parametrize(
        "value",
        [
            True,
            False,
            "true",
            "false",
            "True",
            "False",
            "TRUE",
            "FALSE",
            "yes",
            "no",
            "Yes",
            "No",
            1,
            0,
        ],
    )
    def test_valid_is_correct_values_are_accepted(self, value):
        serializer = ChoiceSerializer(
            data={
                "text": "Django",
                "is_correct": value,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert isinstance(serializer.validated_data["is_correct"], bool)

    @pytest.mark.parametrize(
        "value",
        [
            None,
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
    def test_invalid_is_correct_values_are_rejected(self, value):
        serializer = ChoiceSerializer(
            data={
                "text": "Django",
                "is_correct": value,
            }
        )

        assert not serializer.is_valid()
        assert "is_correct" in serializer.errors

    def test_is_correct_is_omitted_from_validated_data_when_not_provided(self):
        serializer = ChoiceSerializer(
            data={
                "text": "Django",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert "is_correct" not in serializer.validated_data

    def test_validated_data_contains_only_submitted_serializer_fields(self):
        serializer = ChoiceSerializer(
            data={
                "text": "Django",
                "is_correct": True,
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert set(serializer.validated_data.keys()) == {
            "text",
            "is_correct",
        }

    def test_id_is_read_only_and_ignored_from_input(self):
        serializer = ChoiceSerializer(
            data={
                "id": 999,
                "text": "Django",
                "is_correct": True,
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert "id" not in serializer.validated_data
        assert serializer.validated_data["text"] == "Django"
        assert serializer.validated_data["is_correct"] is True

    def test_question_is_not_a_serializer_field(self):
        serializer = ChoiceSerializer()

        assert "question" not in serializer.fields

    def test_order_is_not_a_serializer_field(self):
        serializer = ChoiceSerializer()

        assert "order" not in serializer.fields

    def test_question_is_ignored_from_input(self):
        serializer = ChoiceSerializer(
            data={
                "text": "Django",
                "question": 123,
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert "question" not in serializer.validated_data

    def test_order_is_ignored_from_input(self):
        serializer = ChoiceSerializer(
            data={
                "text": "Django",
                "order": 10,
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert "order" not in serializer.validated_data

    def test_unknown_fields_are_ignored(self):
        serializer = ChoiceSerializer(
            data={
                "text": "Django",
                "unknown_field": "value",
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert "unknown_field" not in serializer.validated_data
        assert serializer.validated_data["text"] == "Django"

    def test_partial_update_allows_text_to_be_omitted(self):
        choice = Choice(
            text="Django",
            is_correct=False,
            order=1,
        )

        serializer = ChoiceSerializer(
            instance=choice,
            data={
                "is_correct": True,
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["is_correct"] is True

    def test_partial_update_allows_is_correct_to_be_omitted(self):
        choice = Choice(
            text="Django",
            is_correct=False,
            order=1,
        )

        serializer = ChoiceSerializer(
            instance=choice,
            data={
                "text": "Django REST Framework",
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["text"] == "Django REST Framework"
        assert "is_correct" not in serializer.validated_data

    def test_partial_update_with_empty_data_is_valid(self):
        choice = Choice(
            text="Django",
            is_correct=False,
            order=1,
        )

        serializer = ChoiceSerializer(
            instance=choice,
            data={},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data == {}

    def test_text_strips_leading_and_trailing_whitespace(self):
        serializer = ChoiceSerializer(
            data={
                "text": "  Django  ",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["text"] == "Django"

    def test_text_preserves_internal_whitespace(self):
        serializer = ChoiceSerializer(
            data={
                "text": "Django REST Framework",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["text"] == "Django REST Framework"

    @pytest.mark.parametrize(
        "text",
        [
            "Django\nREST Framework",
            "Django\tREST Framework",
            "Django  REST Framework",
        ],
    )
    def test_text_preserves_internal_whitespace_characters(self, text):
        serializer = ChoiceSerializer(
            data={
                "text": text,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["text"] == text

    @pytest.mark.parametrize(
        "text",
        [
            "دجانگو",
            "پایتون",
            "Django — Python",
            "Django & DRF",
            "C++",
            "C#",
            "Python 3.13",
            "What is 2 + 2?",
            "True / False",
        ],
    )
    def test_unicode_and_special_characters_are_accepted(self, text):
        serializer = ChoiceSerializer(
            data={
                "text": text,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["text"] == text

    def test_serialization_contains_expected_fields(self):
        choice = Choice(
            id=10,
            text="Django",
            is_correct=True,
            order=1,
        )

        serializer = ChoiceSerializer(choice)

        assert set(serializer.data.keys()) == {
            "id",
            "text",
            "is_correct",
        }

    def test_serializes_id(self):
        choice = Choice(
            id=10,
            text="Django",
            is_correct=True,
            order=1,
        )

        serializer = ChoiceSerializer(choice)

        assert serializer.data["id"] == 10

    def test_serializes_text(self):
        choice = Choice(
            id=10,
            text="Django REST Framework",
            is_correct=True,
            order=1,
        )

        serializer = ChoiceSerializer(choice)

        assert serializer.data["text"] == "Django REST Framework"

    @pytest.mark.parametrize(
        "is_correct",
        [
            True,
            False,
        ],
    )
    def test_serializes_is_correct(self, is_correct):
        choice = Choice(
            id=10,
            text="Django",
            is_correct=is_correct,
            order=1,
        )

        serializer = ChoiceSerializer(choice)

        assert serializer.data["is_correct"] is is_correct

    def test_serializes_unsaved_choice(self):
        choice = Choice(
            id=None,
            text="Django",
            is_correct=False,
            order=1,
        )

        serializer = ChoiceSerializer(choice)

        assert serializer.data == {
            "id": None,
            "text": "Django",
            "is_correct": False,
        }

    def test_model_default_is_correct_is_false(self):
        choice = Choice(
            text="Django",
            order=1,
        )

        assert choice.is_correct is False

    def test_model_str_returns_text(self):
        choice = Choice(
            text="Django REST Framework",
            order=1,
        )

        assert str(choice) == "Django REST Framework"
