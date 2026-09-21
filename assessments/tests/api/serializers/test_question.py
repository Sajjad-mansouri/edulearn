import datetime

import pytest
from rest_framework import serializers

from assessments.api.serializers import (
    AcceptedAnswerSerializer,
    BooleanAnswerSerializer,
    ChoiceSerializer,
    QuestionSerializer,
)
from assessments.models import Question


class TestQuestionSerializer:
    def test_serializer_uses_question_model(self):
        serializer = QuestionSerializer()

        assert serializer.Meta.model is Question

    def test_serializer_has_expected_fields(self):
        serializer = QuestionSerializer()

        assert list(serializer.fields.keys()) == [
            "id",
            "text",
            "question_type",
            "difficulty",
            "points",
            "explanation",
            "is_required",
            "estimated_time",
            "boolean_answer",
            "accepted_answers",
            "choices",
        ]

    def test_serializer_does_not_expose_internal_fields(self):
        serializer = QuestionSerializer()

        assert "quiz" not in serializer.fields
        assert "order" not in serializer.fields

    def test_id_field_is_read_only(self):
        serializer = QuestionSerializer()

        field = serializer.fields["id"]

        assert isinstance(field, serializers.IntegerField)
        assert field.read_only is True
        assert field.required is False

    def test_text_field_configuration(self):
        serializer = QuestionSerializer()

        field = serializer.fields["text"]

        assert isinstance(field, serializers.CharField)
        assert field.required is True
        assert field.allow_blank is False
        assert field.allow_null is False
        assert field.read_only is False

    def test_question_type_field_configuration(self):
        serializer = QuestionSerializer()

        field = serializer.fields["question_type"]

        assert isinstance(field, serializers.ChoiceField)
        assert field.required is False
        assert field.allow_null is False
        assert field.read_only is False

    def test_difficulty_field_configuration(self):
        serializer = QuestionSerializer()

        field = serializer.fields["difficulty"]

        assert isinstance(field, serializers.ChoiceField)
        assert field.required is False
        assert field.allow_null is False
        assert field.read_only is False

    def test_points_field_configuration(self):
        serializer = QuestionSerializer()

        field = serializer.fields["points"]

        assert isinstance(field, serializers.IntegerField)
        assert field.required is False
        assert field.allow_null is False
        assert field.read_only is False

    def test_explanation_field_configuration(self):
        serializer = QuestionSerializer()

        field = serializer.fields["explanation"]

        assert isinstance(field, serializers.CharField)
        assert field.required is False
        assert field.allow_blank is True
        assert field.allow_null is False
        assert field.read_only is False

    def test_is_required_field_configuration(self):
        serializer = QuestionSerializer()

        field = serializer.fields["is_required"]

        assert isinstance(field, serializers.BooleanField)
        assert field.required is False
        assert field.allow_null is False
        assert field.read_only is False

    def test_estimated_time_field_configuration(self):
        serializer = QuestionSerializer()

        field = serializer.fields["estimated_time"]

        assert isinstance(field, serializers.DurationField)
        assert field.required is False
        assert field.allow_null is True
        assert field.read_only is False

    def test_boolean_answer_field_configuration(self):
        serializer = QuestionSerializer()

        field = serializer.fields["boolean_answer"]

        assert isinstance(field, BooleanAnswerSerializer)
        assert field.required is False
        assert field.read_only is False

    def test_accepted_answers_field_configuration(self):
        serializer = QuestionSerializer()

        field = serializer.fields["accepted_answers"]

        assert isinstance(field, serializers.ListSerializer)
        assert field.required is False
        assert field.read_only is False
        assert isinstance(field.child, AcceptedAnswerSerializer)

    def test_choices_field_configuration(self):
        serializer = QuestionSerializer()

        field = serializer.fields["choices"]

        assert isinstance(field, serializers.ListSerializer)
        assert field.required is False
        assert field.read_only is False
        assert isinstance(field.child, ChoiceSerializer)

    def test_text_is_required(self):
        serializer = QuestionSerializer(data={})

        assert not serializer.is_valid()
        assert "text" in serializer.errors

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
        serializer = QuestionSerializer(
            data={
                "text": text,
            }
        )

        assert not serializer.is_valid()
        assert "text" in serializer.errors

    def test_null_text_is_rejected(self):
        serializer = QuestionSerializer(
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
    def test_invalid_text_containers_are_rejected(self, value):
        serializer = QuestionSerializer(
            data={
                "text": value,
            }
        )

        assert not serializer.is_valid()
        assert "text" in serializer.errors

    def test_text_strips_surrounding_whitespace(self):
        serializer = QuestionSerializer(
            data={
                "text": "  What is Django?  ",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["text"] == "What is Django?"

    @pytest.mark.parametrize(
        "question_type",
        [
            Question.Type.SINGLE_CHOICE,
            Question.Type.MULTIPLE_CHOICE,
            Question.Type.TRUE_FALSE,
            Question.Type.SHORT_ANSWER,
        ],
    )
    def test_valid_question_types_are_accepted(self, question_type):
        serializer = QuestionSerializer(
            data={
                "text": "What is Django?",
                "question_type": question_type,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["question_type"] == question_type

    @pytest.mark.parametrize(
        "question_type",
        [
            "",
            "invalid",
            "multiple",
            "single",
            "true_false_question",
        ],
    )
    def test_invalid_question_types_are_rejected(self, question_type):
        serializer = QuestionSerializer(
            data={
                "text": "What is Django?",
                "question_type": question_type,
            }
        )

        assert not serializer.is_valid()
        assert "question_type" in serializer.errors

    @pytest.mark.parametrize(
        "difficulty",
        [
            Question.Difficulty.EASY,
            Question.Difficulty.MEDIUM,
            Question.Difficulty.HARD,
        ],
    )
    def test_valid_difficulties_are_accepted(self, difficulty):
        serializer = QuestionSerializer(
            data={
                "text": "What is Django?",
                "difficulty": difficulty,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["difficulty"] == difficulty

    @pytest.mark.parametrize(
        "difficulty",
        [
            "",
            "invalid",
            "beginner",
            "advanced",
            "very_hard",
        ],
    )
    def test_invalid_difficulties_are_rejected(self, difficulty):
        serializer = QuestionSerializer(
            data={
                "text": "What is Django?",
                "difficulty": difficulty,
            }
        )

        assert not serializer.is_valid()
        assert "difficulty" in serializer.errors

    @pytest.mark.parametrize(
        "points",
        [
            0,
            1,
            2,
            10,
            100,
        ],
    )
    def test_valid_points_are_accepted(self, points):
        serializer = QuestionSerializer(
            data={
                "text": "What is Django?",
                "points": points,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["points"] == points

    @pytest.mark.parametrize(
        "points",
        [
            -1,
            -10,
        ],
    )
    def test_negative_points_are_rejected(self, points):
        serializer = QuestionSerializer(
            data={
                "text": "What is Django?",
                "points": points,
            }
        )

        assert not serializer.is_valid()
        assert "points" in serializer.errors

    @pytest.mark.parametrize(
        "value",
        [
            True,
            False,
        ],
    )
    def test_is_required_accepts_boolean_values(self, value):
        serializer = QuestionSerializer(
            data={
                "text": "What is Django?",
                "is_required": value,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["is_required"] is value

    @pytest.mark.parametrize(
        "value",
        [
            None,
            "invalid",
            "maybe",
            2,
            -1,
            [],
            {},
        ],
    )
    def test_invalid_is_required_values_are_rejected(self, value):
        serializer = QuestionSerializer(
            data={
                "text": "What is Django?",
                "is_required": value,
            }
        )

        assert not serializer.is_valid()
        assert "is_required" in serializer.errors

    @pytest.mark.parametrize(
        "explanation",
        [
            "",
            "Django is a Python web framework.",
            "A" * 1000,
            "توضیح فارسی",
        ],
    )
    def test_valid_explanations_are_accepted(self, explanation):
        serializer = QuestionSerializer(
            data={
                "text": "What is Django?",
                "explanation": explanation,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["explanation"] == explanation

    def test_estimated_time_accepts_duration_string(self):
        serializer = QuestionSerializer(
            data={
                "text": "What is Django?",
                "estimated_time": "00:05:00",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["estimated_time"] == (
            datetime.timedelta(minutes=5)
        )

    def test_estimated_time_accepts_duration_object(self):
        estimated_time = datetime.timedelta(minutes=5)

        serializer = QuestionSerializer(
            data={
                "text": "What is Django?",
                "estimated_time": estimated_time,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["estimated_time"] == estimated_time

    def test_estimated_time_can_be_null(self):
        serializer = QuestionSerializer(
            data={
                "text": "What is Django?",
                "estimated_time": None,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["estimated_time"] is None

    def test_nested_boolean_answer_is_validated(self):
        serializer = QuestionSerializer(
            data={
                "text": "Is Django a Python framework?",
                "boolean_answer": {
                    "answer": True,
                },
            }
        )

        assert serializer.is_valid(), serializer.errors

        boolean_answer = serializer.validated_data["boolean_answer"]

        assert boolean_answer["answer"] is True

    def test_nested_boolean_answer_accepts_false(self):
        serializer = QuestionSerializer(
            data={
                "text": "Is Django a Python framework?",
                "boolean_answer": {
                    "answer": False,
                },
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["boolean_answer"]["answer"] is False

    def test_invalid_nested_boolean_answer_is_rejected(self):
        serializer = QuestionSerializer(
            data={
                "text": "Is Django a Python framework?",
                "boolean_answer": {
                    "answer": "invalid",
                },
            }
        )

        assert not serializer.is_valid()
        assert "boolean_answer" in serializer.errors

    def test_nested_accepted_answers_are_validated(self):
        serializer = QuestionSerializer(
            data={
                "text": "What language is Django written in?",
                "accepted_answers": [
                    {
                        "answer": "Python",
                    },
                    {
                        "answer": "python",
                    },
                ],
            }
        )

        assert serializer.is_valid(), serializer.errors

        accepted_answers = serializer.validated_data["accepted_answers"]

        assert len(accepted_answers) == 2
        assert accepted_answers[0]["answer"] == "Python"
        assert accepted_answers[1]["answer"] == "python"

    def test_invalid_nested_accepted_answer_is_rejected(self):
        serializer = QuestionSerializer(
            data={
                "text": "What language is Django written in?",
                "accepted_answers": [
                    {
                        "answer": "",
                    },
                ],
            }
        )

        assert not serializer.is_valid()
        assert "accepted_answers" in serializer.errors

    def test_nested_choices_are_validated(self):
        serializer = QuestionSerializer(
            data={
                "text": "Which framework is written in Python?",
                "choices": [
                    {
                        "text": "Django",
                        "is_correct": True,
                    },
                    {
                        "text": "Laravel",
                        "is_correct": False,
                    },
                ],
            }
        )

        assert serializer.is_valid(), serializer.errors

        choices = serializer.validated_data["choices"]

        assert len(choices) == 2
        assert choices[0]["text"] == "Django"
        assert choices[0]["is_correct"] is True
        assert choices[1]["text"] == "Laravel"
        assert choices[1]["is_correct"] is False

    def test_invalid_nested_choice_is_rejected(self):
        serializer = QuestionSerializer(
            data={
                "text": "Which framework is written in Python?",
                "choices": [
                    {
                        "text": "",
                        "is_correct": True,
                    },
                ],
            }
        )

        assert not serializer.is_valid()
        assert "choices" in serializer.errors

    def test_nested_choice_can_omit_is_correct(self):
        serializer = QuestionSerializer(
            data={
                "text": "Which framework is written in Python?",
                "choices": [
                    {
                        "text": "Django",
                    },
                ],
            }
        )

        assert serializer.is_valid(), serializer.errors

        choice = serializer.validated_data["choices"][0]

        assert choice["text"] == "Django"
        assert "is_correct" not in choice

    def test_all_nested_fields_can_be_submitted_together(self):
        serializer = QuestionSerializer(
            data={
                "text": "Assessment question",
                "question_type": Question.Type.SINGLE_CHOICE,
                "difficulty": Question.Difficulty.MEDIUM,
                "points": 5,
                "explanation": "Explanation.",
                "is_required": True,
                "estimated_time": "00:10:00",
                "boolean_answer": {
                    "answer": True,
                },
                "accepted_answers": [
                    {
                        "answer": "Python",
                    },
                ],
                "choices": [
                    {
                        "text": "Django",
                        "is_correct": True,
                    },
                    {
                        "text": "Laravel",
                        "is_correct": False,
                    },
                ],
            }
        )

        assert serializer.is_valid(), serializer.errors

        validated_data = serializer.validated_data

        assert validated_data["text"] == "Assessment question"
        assert validated_data["question_type"] == Question.Type.SINGLE_CHOICE
        assert validated_data["difficulty"] == Question.Difficulty.MEDIUM
        assert validated_data["points"] == 5
        assert validated_data["explanation"] == "Explanation."
        assert validated_data["is_required"] is True
        assert validated_data["estimated_time"] == (datetime.timedelta(minutes=10))

        assert validated_data["boolean_answer"]["answer"] is True

        assert len(validated_data["accepted_answers"]) == 1
        assert validated_data["accepted_answers"][0]["answer"] == "Python"

        assert len(validated_data["choices"]) == 2
        assert validated_data["choices"][0]["text"] == "Django"
        assert validated_data["choices"][0]["is_correct"] is True
        assert validated_data["choices"][1]["text"] == "Laravel"
        assert validated_data["choices"][1]["is_correct"] is False

    def test_id_is_read_only_and_ignored_from_input(self):
        serializer = QuestionSerializer(
            data={
                "id": 999,
                "text": "What is Django?",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert "id" not in serializer.validated_data

    def test_quiz_is_ignored_from_input(self):
        serializer = QuestionSerializer(
            data={
                "text": "What is Django?",
                "quiz": 123,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert "quiz" not in serializer.validated_data

    def test_order_is_ignored_from_input(self):
        serializer = QuestionSerializer(
            data={
                "text": "What is Django?",
                "order": 10,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert "order" not in serializer.validated_data

    def test_partial_update_allows_required_fields_to_be_omitted(self):
        question = Question(
            text="Original question",
            question_type=Question.Type.SINGLE_CHOICE,
            difficulty=Question.Difficulty.MEDIUM,
            points=1,
            is_required=True,
            order=1,
        )

        serializer = QuestionSerializer(
            instance=question,
            data={
                "points": 5,
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["points"] == 5
        assert "text" not in serializer.validated_data

    def test_partial_update_with_empty_data_is_valid(self):
        question = Question(
            text="Original question",
            question_type=Question.Type.SINGLE_CHOICE,
            difficulty=Question.Difficulty.MEDIUM,
            points=1,
            is_required=True,
            order=1,
        )

        serializer = QuestionSerializer(
            instance=question,
            data={},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data == {}
