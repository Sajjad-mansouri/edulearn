import pytest
from django.db import IntegrityError

from assessments.models import Choice
from assessments.tests.factories import (
    ChoiceFactory,
    QuestionFactory,
)


@pytest.mark.django_db
class TestChoiceModel:
    """Tests for the Choice model."""

    @pytest.fixture
    def question(self):
        return QuestionFactory()

    def test_create_choice(self, question):
        """A choice can be created."""
        choice = Choice.objects.create(
            question=question,
            text="Python",
            is_correct=True,
            order=1,
        )

        assert choice.question == question
        assert choice.text == "Python"
        assert choice.is_correct is True
        assert choice.order == 1

    def test_string_representation(self):
        """The string representation should return the choice text."""
        choice = ChoiceFactory(
            text="Django",
        )

        assert str(choice) == "Django"

    def test_is_correct_defaults_to_false(self, question):
        """Choices are incorrect by default."""
        choice = Choice.objects.create(
            question=question,
            text="Python",
            order=1,
        )

        assert choice.is_correct is False

    def test_question_can_have_multiple_choices(self, question):
        """A question can contain multiple choices."""
        choice1 = ChoiceFactory(
            question=question,
            order=1,
        )

        choice2 = ChoiceFactory(
            question=question,
            order=2,
        )

        assert set(question.choices.all()) == {
            choice1,
            choice2,
        }

    def test_order_must_be_unique_per_question(self, question):
        """A question cannot contain two choices with the same order."""
        ChoiceFactory(
            question=question,
            order=1,
        )

        with pytest.raises(IntegrityError):
            ChoiceFactory(
                question=question,
                order=1,
            )

    def test_same_order_can_be_used_in_different_questions(self):
        """Different questions may reuse the same choice order."""
        question1 = QuestionFactory()
        question2 = QuestionFactory()

        choice1 = ChoiceFactory(
            question=question1,
            order=1,
        )

        choice2 = ChoiceFactory(
            question=question2,
            order=1,
        )

        assert choice1.order == choice2.order == 1

    def test_choices_are_ordered_by_order(self, question):
        """Choices are returned in ascending order."""
        ChoiceFactory(question=question, order=3)
        ChoiceFactory(question=question, order=1)
        ChoiceFactory(question=question, order=2)

        orders = list(
            question.choices.values_list(
                "order",
                flat=True,
            )
        )

        assert orders == [1, 2, 3]

    def test_deleting_question_deletes_choices(self):
        """Deleting a question cascades to its choices."""
        question = QuestionFactory()

        choice = ChoiceFactory(
            question=question,
        )

        question.delete()

        assert not Choice.objects.filter(
            pk=choice.pk,
        ).exists()
