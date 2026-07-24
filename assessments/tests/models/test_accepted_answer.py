import pytest
from django.db import IntegrityError

from assessments.models import AcceptedAnswer
from assessments.tests.factories import (
    AcceptedAnswerFactory,
    QuestionFactory,
)


@pytest.mark.django_db
class TestAcceptedAnswerModel:
    """Tests for the AcceptedAnswer model."""

    @pytest.fixture
    def question(self):
        return QuestionFactory()

    def test_create_accepted_answer(self, question):
        """An accepted answer can be created."""
        accepted_answer = AcceptedAnswer.objects.create(
            question=question,
            answer="def",
        )

        assert accepted_answer.question == question
        assert accepted_answer.answer == "def"

    def test_string_representation(self):
        """The string representation should return the answer."""
        accepted_answer = AcceptedAnswerFactory(
            answer="return",
        )

        assert str(accepted_answer) == "return"

    def test_question_can_have_multiple_accepted_answers(self, question):
        """A question can have multiple accepted answers."""
        answer1 = AcceptedAnswerFactory(
            question=question,
            answer="def",
        )

        answer2 = AcceptedAnswerFactory(
            question=question,
            answer="DEF",
        )

        assert set(question.accepted_answers.all()) == {
            answer1,
            answer2,
        }

    def test_deleting_question_deletes_accepted_answers(self):
        """Deleting a question cascades to its accepted answers."""
        question = QuestionFactory()

        accepted_answer = AcceptedAnswerFactory(
            question=question,
        )

        question.delete()

        assert not AcceptedAnswer.objects.filter(
            pk=accepted_answer.pk,
        ).exists()

    def test_question_cannot_have_duplicate_accepted_answers(self, question):
        """A question cannot have duplicate accepted answers."""
        AcceptedAnswerFactory(
            question=question,
            answer="def",
        )

        with pytest.raises(IntegrityError):
            AcceptedAnswerFactory(
                question=question,
                answer="def",
            )
