import pytest
from rest_framework import serializers

from assessments.api.serializers import QuestionSerializer, QuizContentSerializer
from assessments.models import QuizContent


class TestQuizContentSerializer:
    def test_serializer_uses_quiz_content_model(self):
        serializer = QuizContentSerializer()

        assert serializer.Meta.model is QuizContent

    def test_serializer_has_expected_fields(self):
        serializer = QuizContentSerializer()

        assert list(serializer.fields.keys()) == [
            "id",
            "instructions",
            "passing_score",
            "time_limit",
            "max_attempts",
            "shuffle_questions",
            "shuffle_choices",
            "show_correct_answers",
            "questions",
        ]

    def test_serializer_does_not_expose_content_field(self):
        serializer = QuizContentSerializer()

        assert "content" not in serializer.fields

    def test_id_field_is_read_only(self):
        serializer = QuizContentSerializer()

        field = serializer.fields["id"]

        assert isinstance(field, serializers.IntegerField)
        assert field.read_only is True
        assert field.required is False

    def test_instructions_field_configuration(self):
        serializer = QuizContentSerializer()

        field = serializer.fields["instructions"]

        assert isinstance(field, serializers.CharField)
        assert field.required is False
        assert field.allow_blank is True
        assert field.allow_null is False
        assert field.read_only is False

    def test_passing_score_field_configuration(self):
        serializer = QuizContentSerializer()

        field = serializer.fields["passing_score"]

        assert isinstance(field, serializers.IntegerField)
        assert field.required is False
        assert field.allow_null is True
        assert field.read_only is False

    def test_time_limit_field_configuration(self):
        serializer = QuizContentSerializer()

        field = serializer.fields["time_limit"]

        assert isinstance(field, serializers.IntegerField)
        assert field.required is False
        assert field.allow_null is True
        assert field.read_only is False

    def test_max_attempts_field_configuration(self):
        serializer = QuizContentSerializer()

        field = serializer.fields["max_attempts"]

        assert isinstance(field, serializers.IntegerField)
        assert field.required is False
        assert field.allow_null is True
        assert field.read_only is False

    @pytest.mark.parametrize(
        "field_name",
        [
            "shuffle_questions",
            "shuffle_choices",
            "show_correct_answers",
        ],
    )
    def test_boolean_fields_configuration(self, field_name):
        serializer = QuizContentSerializer()

        field = serializer.fields[field_name]

        assert isinstance(field, serializers.BooleanField)
        assert field.required is False
        assert field.allow_null is False
        assert field.read_only is False

    def test_questions_field_configuration(self):
        serializer = QuizContentSerializer()

        field = serializer.fields["questions"]

        assert isinstance(field, serializers.ListSerializer)
        assert field.required is True
        assert field.read_only is False
        assert field.allow_empty is True
        assert isinstance(field.child, QuestionSerializer)

    def test_questions_is_required(self):
        serializer = QuizContentSerializer(
            data={
                "instructions": "Answer all questions.",
            }
        )

        assert not serializer.is_valid()
        assert "questions" in serializer.errors

    def test_questions_null_is_rejected(self):
        serializer = QuizContentSerializer(
            data={
                "questions": None,
            }
        )

        assert not serializer.is_valid()
        assert "questions" in serializer.errors

    def test_questions_must_be_a_list(self):
        serializer = QuizContentSerializer(
            data={
                "questions": {
                    "text": "What is Django?",
                },
            }
        )

        assert not serializer.is_valid()
        assert "questions" in serializer.errors

    def test_empty_questions_list_is_valid(self):
        serializer = QuizContentSerializer(
            data={
                "questions": [],
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["questions"] == []

    def test_valid_quiz_content_data_is_accepted(self):
        serializer = QuizContentSerializer(
            data={
                "instructions": "Answer all questions.",
                "passing_score": 70,
                "time_limit": 30,
                "max_attempts": 2,
                "shuffle_questions": True,
                "shuffle_choices": False,
                "show_correct_answers": True,
                "questions": [
                    {
                        "text": "What is Django?",
                    },
                ],
            }
        )

        assert serializer.is_valid(), serializer.errors

        validated_data = serializer.validated_data

        assert validated_data["instructions"] == "Answer all questions."
        assert validated_data["passing_score"] == 70
        assert validated_data["time_limit"] == 30
        assert validated_data["max_attempts"] == 2
        assert validated_data["shuffle_questions"] is True
        assert validated_data["shuffle_choices"] is False
        assert validated_data["show_correct_answers"] is True

        assert len(validated_data["questions"]) == 1
        assert validated_data["questions"][0]["text"] == "What is Django?"

    def test_multiple_questions_are_validated_through_question_serializer(
        self,
    ):
        serializer = QuizContentSerializer(
            data={
                "questions": [
                    {
                        "text": "What is Django?",
                        "points": 2,
                    },
                    {
                        "text": "What is DRF?",
                        "points": 5,
                    },
                ],
            }
        )

        assert serializer.is_valid(), serializer.errors

        questions = serializer.validated_data["questions"]

        assert len(questions) == 2
        assert questions[0]["text"] == "What is Django?"
        assert questions[0]["points"] == 2
        assert questions[1]["text"] == "What is DRF?"
        assert questions[1]["points"] == 5

    def test_invalid_nested_question_is_rejected(self):
        serializer = QuizContentSerializer(
            data={
                "questions": [
                    {
                        "text": "",
                    },
                ],
            }
        )

        assert not serializer.is_valid()
        assert "questions" in serializer.errors

    def test_nested_question_validation_error_is_preserved(self):
        serializer = QuizContentSerializer(
            data={
                "questions": [
                    {
                        "text": "What is Django?",
                        "question_type": "invalid",
                    },
                ],
            }
        )

        assert not serializer.is_valid()
        assert "questions" in serializer.errors

        question_errors = serializer.errors["questions"][0]

        assert "question_type" in question_errors

    def test_nested_question_supports_its_nested_fields(self):
        serializer = QuizContentSerializer(
            data={
                "questions": [
                    {
                        "text": "Is Django a Python framework?",
                        "boolean_answer": {
                            "answer": True,
                        },
                    },
                ],
            }
        )

        assert serializer.is_valid(), serializer.errors

        question = serializer.validated_data["questions"][0]

        assert question["text"] == "Is Django a Python framework?"
        assert question["boolean_answer"]["answer"] is True

    def test_all_quiz_content_fields_and_nested_questions_are_validated(
        self,
    ):
        serializer = QuizContentSerializer(
            data={
                "instructions": "Complete the quiz.",
                "passing_score": 80,
                "time_limit": 45,
                "max_attempts": 3,
                "shuffle_questions": True,
                "shuffle_choices": True,
                "show_correct_answers": False,
                "questions": [
                    {
                        "text": "What is Django?",
                        "question_type": "single_choice",
                        "difficulty": "easy",
                        "points": 5,
                        "explanation": "Django is a Python web framework.",
                        "is_required": True,
                        "estimated_time": "00:05:00",
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
                    },
                    {
                        "text": "Is DRF used with Django?",
                        "question_type": "true_false",
                        "difficulty": "medium",
                        "points": 3,
                        "boolean_answer": {
                            "answer": True,
                        },
                    },
                ],
            }
        )

        assert serializer.is_valid(), serializer.errors

        validated_data = serializer.validated_data

        assert validated_data["instructions"] == "Complete the quiz."
        assert validated_data["passing_score"] == 80
        assert validated_data["time_limit"] == 45
        assert validated_data["max_attempts"] == 3
        assert validated_data["shuffle_questions"] is True
        assert validated_data["shuffle_choices"] is True
        assert validated_data["show_correct_answers"] is False

        questions = validated_data["questions"]

        assert len(questions) == 2

        first_question = questions[0]

        assert first_question["text"] == "What is Django?"
        assert first_question["question_type"] == "single_choice"
        assert first_question["difficulty"] == "easy"
        assert first_question["points"] == 5
        assert first_question["explanation"] == "Django is a Python web framework."
        assert first_question["is_required"] is True

        assert len(first_question["choices"]) == 2
        assert first_question["choices"][0]["text"] == "Django"
        assert first_question["choices"][0]["is_correct"] is True
        assert first_question["choices"][1]["text"] == "Laravel"
        assert first_question["choices"][1]["is_correct"] is False

        second_question = questions[1]

        assert second_question["text"] == "Is DRF used with Django?"
        assert second_question["question_type"] == "true_false"
        assert second_question["difficulty"] == "medium"
        assert second_question["points"] == 3
        assert second_question["boolean_answer"]["answer"] is True

    def test_id_is_read_only_and_ignored_from_input(self):
        serializer = QuizContentSerializer(
            data={
                "id": 999,
                "questions": [
                    {
                        "text": "What is Django?",
                    },
                ],
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert "id" not in serializer.validated_data

    def test_content_is_ignored_from_input(self):
        serializer = QuizContentSerializer(
            data={
                "content": 123,
                "questions": [
                    {
                        "text": "What is Django?",
                    },
                ],
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert "content" not in serializer.validated_data

    def test_partial_update_allows_questions_to_be_omitted(self):
        serializer = QuizContentSerializer(
            data={
                "instructions": "Updated instructions.",
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["instructions"] == ("Updated instructions.")
        assert "questions" not in serializer.validated_data

    def test_partial_update_with_empty_data_is_valid(self):
        serializer = QuizContentSerializer(
            data={},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data == {}
