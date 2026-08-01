from rest_framework import serializers

from assessments.models import (
    AcceptedAnswer,
    Assignment,
    BooleanAnswer,
    Choice,
    Question,
    QuizContent,
)


class BooleanAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = BooleanAnswer
        fields = ["answer"]


class AcceptedAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcceptedAnswer
        fields = ["answer"]


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ["text", "is_correct"]


class QuestionSerializer(serializers.ModelSerializer):
    boolean_answer = BooleanAnswerSerializer(required=False)
    accepted_answers = AcceptedAnswerSerializer(required=False, many=True)
    options = ChoiceSerializer(required=False, many=True)

    class Meta:
        model = Question
        fields = [
            "text",
            "question_type",
            "difficulty",
            "points",
            "explanation",
            "is_required",
            "estimated_time",
            "boolean_answer",
            "accepted_answers",
            "options",
        ]


class QuizContentSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True)

    class Meta:
        model = QuizContent
        fields = [
            "instructions",
            "passing_score",
            "time_limit",
            "max_attempts",
            "shuffle_questions",
            "shuffle_choices",
            "show_correct_answers",
            "questions",
        ]


class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = [
            "instructions",
            "max_score",
            "due_date",
            "allow_late_submission",
            "max_attempts",
            "accepted_file_types",
            "max_file_size_mb",
        ]
