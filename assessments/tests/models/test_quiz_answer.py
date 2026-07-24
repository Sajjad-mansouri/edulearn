import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from assessments.models import QuizAnswer
from assessments.tests.factories import (
    ChoiceFactory,
    QuestionFactory,
    QuizAnswerFactory,
    QuizAttemptFactory,
)


@pytest.mark.django_db
class TestQuizAnswerModel:
    """Tests for the QuizAnswer model."""

    @pytest.fixture
    def attempt(self):
        return QuizAttemptFactory()

    @pytest.fixture
    def question(self, attempt):
        return QuestionFactory(
            quiz=attempt.quiz,
        )

    def test_create_quiz_answer(
        self,
        attempt,
        question,
    ):
        """A quiz answer can be created."""
        answer = QuizAnswer.objects.create(
            attempt=attempt,
            question=question,
            score_awarded=0.5,
        )

        choice = ChoiceFactory(
            question=question,
        )

        answer.selected_choices.add(choice)

        assert answer.attempt == attempt
        assert answer.question == question
        assert answer.score_awarded == 0.5
        assert answer.text_answer == ""
        assert list(answer.selected_choices.all()) == [choice]

    def test_string_representation(self):
        """String representation contains attempt and question order."""
        answer = QuizAnswerFactory()

        assert str(answer) == (f"{answer.attempt} - Question {answer.question.order}")

    def test_text_answer_defaults_to_empty(
        self,
        attempt,
        question,
    ):
        """Text answer defaults to an empty string."""
        answer = QuizAnswer.objects.create(
            attempt=attempt,
            question=question,
        )

        assert answer.text_answer == ""

    def test_selected_choices_is_optional(
        self,
        attempt,
        question,
    ):
        """Selected choices are optional."""
        answer = QuizAnswer.objects.create(
            attempt=attempt,
            question=question,
        )

        assert answer.selected_choices.count() == 0

    def test_score_defaults_to_zero(
        self,
        attempt,
        question,
    ):
        """Score awarded defaults to zero."""
        answer = QuizAnswer.objects.create(
            attempt=attempt,
            question=question,
        )

        assert answer.score_awarded == 0

    def test_attempt_can_have_multiple_answers(
        self,
        attempt,
    ):
        """A quiz attempt can contain multiple answers."""
        question1 = QuestionFactory(
            quiz=attempt.quiz,
            order=1,
        )
        question2 = QuestionFactory(
            quiz=attempt.quiz,
            order=2,
        )

        answer1 = QuizAnswerFactory(
            attempt=attempt,
            question=question1,
        )

        answer2 = QuizAnswerFactory(
            attempt=attempt,
            question=question2,
        )

        assert set(attempt.answers.all()) == {
            answer1,
            answer2,
        }

    def test_same_question_can_be_answered_in_different_attempts(
        self,
    ):
        """Different attempts may answer the same question."""
        attempt1 = QuizAttemptFactory()
        attempt2 = QuizAttemptFactory(
            enrollment=attempt1.enrollment,
            quiz=attempt1.quiz,
            attempt_number=2,
        )

        question = QuestionFactory(
            quiz=attempt1.quiz,
        )

        answer1 = QuizAnswerFactory(
            attempt=attempt1,
            question=question,
        )

        answer2 = QuizAnswerFactory(
            attempt=attempt2,
            question=question,
        )

        assert answer1.question == answer2.question

    def test_attempt_can_answer_question_only_once(
        self,
        attempt,
        question,
    ):
        """Each question may only have one answer per attempt."""
        QuizAnswerFactory(
            attempt=attempt,
            question=question,
        )

        with pytest.raises(IntegrityError):
            QuizAnswerFactory(
                attempt=attempt,
                question=question,
            )

    def test_question_must_belong_to_attempt_quiz(
        self,
        attempt,
    ):
        """Question must belong to the attempted quiz."""
        other_question = QuestionFactory()

        answer = QuizAnswer(
            attempt=attempt,
            question=other_question,
        )

        with pytest.raises(ValidationError):
            answer.full_clean()

    def test_score_cannot_be_negative(
        self,
        attempt,
        question,
    ):
        """Score awarded cannot be negative."""
        answer = QuizAnswer(
            attempt=attempt,
            question=question,
            score_awarded=-1,
        )

        with pytest.raises(ValidationError):
            answer.full_clean()

    def test_score_cannot_exceed_question_points(
        self,
        attempt,
        question,
    ):
        """Score awarded cannot exceed question points."""
        question.points = 2
        question.save()

        answer = QuizAnswer(
            attempt=attempt,
            question=question,
            score_awarded=3,
        )

        with pytest.raises(ValidationError):
            answer.full_clean()

    def test_deleting_attempt_deletes_answers(self):
        """Deleting an attempt cascades to its answers."""
        answer = QuizAnswerFactory()

        attempt = answer.attempt

        attempt.delete()

        assert not QuizAnswer.objects.filter(
            pk=answer.pk,
        ).exists()

    def test_deleting_question_deletes_answers(self):
        """Deleting a question cascades to its answers."""
        answer = QuizAnswerFactory()

        question = answer.question

        question.delete()

        assert not QuizAnswer.objects.filter(
            pk=answer.pk,
        ).exists()
