import pytest
from django.db import IntegrityError

from assessments.models import Question
from assessments.tests.factories import (
    QuestionFactory,
    QuizContentFactory,
)


@pytest.mark.django_db
class TestQuestionModel:
    """Tests for the Question model."""

    @pytest.fixture
    def quiz(self):
        return QuizContentFactory()

    def test_create_question(self, quiz):
        """A question can be created."""
        question = Question.objects.create(
            quiz=quiz,
            text="What is Python?",
            question_type=Question.Type.SINGLE_CHOICE,
            difficulty=Question.Difficulty.HARD,
            order=1,
            points=5,
            explanation="Python is a programming language.",
            is_required=False,
            estimated_time=90,
        )

        assert question.quiz == quiz
        assert question.text == "What is Python?"
        assert question.question_type == Question.Type.SINGLE_CHOICE
        assert question.difficulty == Question.Difficulty.HARD
        assert question.order == 1
        assert question.points == 5
        assert question.explanation == "Python is a programming language."
        assert question.is_required is False
        assert question.estimated_time == 90

    def test_string_representation(self):
        """The string representation should return the question text."""
        question = QuestionFactory(
            text="What is Django?",
        )

        assert str(question) == "What is Django?"

    def test_question_type_defaults_to_single_choice(self, quiz):
        """Question type defaults to single choice."""
        question = Question.objects.create(
            quiz=quiz,
            text="Question",
            order=1,
        )

        assert question.question_type == Question.Type.SINGLE_CHOICE

    def test_difficulty_defaults_to_medium(self, quiz):
        """Difficulty defaults to medium."""
        question = Question.objects.create(
            quiz=quiz,
            text="Question",
            order=1,
        )

        assert question.difficulty == Question.Difficulty.MEDIUM

    def test_points_default_to_one(self, quiz):
        """Points default to one."""
        question = Question.objects.create(
            quiz=quiz,
            text="Question",
            order=1,
        )

        assert question.points == 1

    def test_explanation_is_optional(self, quiz):
        """Explanation is optional."""
        question = Question.objects.create(
            quiz=quiz,
            text="Question",
            order=1,
        )

        assert question.explanation == ""

    def test_is_required_defaults_to_true(self, quiz):
        """Questions are required by default."""
        question = Question.objects.create(
            quiz=quiz,
            text="Question",
            order=1,
        )

        assert question.is_required is True

    def test_estimated_time_is_optional(self, quiz):
        """Estimated time is optional."""
        question = Question.objects.create(
            quiz=quiz,
            text="Question",
            order=1,
        )

        assert question.estimated_time is None

    def test_quiz_can_have_multiple_questions(self, quiz):
        """A quiz can contain multiple questions."""
        question1 = QuestionFactory(
            quiz=quiz,
            order=1,
        )

        question2 = QuestionFactory(
            quiz=quiz,
            order=2,
        )

        assert set(quiz.questions.all()) == {
            question1,
            question2,
        }

    def test_same_order_can_be_used_in_different_quizzes(self):
        """Different quizzes may reuse the same question order."""
        quiz1 = QuizContentFactory()
        quiz2 = QuizContentFactory()

        question1 = QuestionFactory(
            quiz=quiz1,
            order=1,
        )

        question2 = QuestionFactory(
            quiz=quiz2,
            order=1,
        )

        assert question1.order == question2.order == 1

    def test_order_must_be_unique_per_quiz(self, quiz):
        """A quiz cannot contain two questions with the same order."""
        QuestionFactory(
            quiz=quiz,
            order=1,
        )

        with pytest.raises(IntegrityError):
            QuestionFactory(
                quiz=quiz,
                order=1,
            )

    def test_questions_are_ordered_by_order(self, quiz):
        """Questions are returned in ascending order."""
        QuestionFactory(
            quiz=quiz,
            order=3,
        )
        QuestionFactory(
            quiz=quiz,
            order=1,
        )
        QuestionFactory(
            quiz=quiz,
            order=2,
        )

        orders = list(
            quiz.questions.values_list(
                "order",
                flat=True,
            )
        )

        assert orders == [1, 2, 3]

    def test_deleting_quiz_deletes_questions(self):
        """Deleting a quiz cascades to its questions."""
        quiz = QuizContentFactory()

        question = QuestionFactory(
            quiz=quiz,
        )

        quiz.delete()

        assert not Question.objects.filter(
            pk=question.pk,
        ).exists()
