from rest_framework import serializers

from assessments.models import Choice, Question, QuizContent


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ["id", "text"]


class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True)

    class Meta:
        model = Question
        fields = ["id", "text", "question_type", "explanation", "choices"]


class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True)

    class Meta:
        model = QuizContent
        fields = ["passing_score", "questions"]


class QuizSubmission(serializers.Serializer):
    questionType = serializers.ChoiceField(
        choices=["single_choice", "short_answer", "true_false", "multiple_choice"]
    )
    boolValue = serializers.BooleanField(required=False)
    textAnswer = serializers.CharField(required=False)
    questionId = serializers.IntegerField(required=False)
    selectedValues = serializers.ListField(
        child=serializers.IntegerField(), allow_empty=True, required=False
    )
