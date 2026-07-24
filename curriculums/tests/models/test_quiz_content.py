import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from curriculums.models import AcceptedAnswer, Choice, Question, QuizContent
from curriculums.tests.factories import (
    AcceptedAnswerFactory,
    ChoiceFactory,
    LessonContentFactory,
    QuestionFactory,
    QuizContentFactory,
)


@pytest.mark.django_db
class TestQuizContentModel:
    """Tests for the QuizContent model."""

    @pytest.fixture
    def content(self):
        return LessonContentFactory()

    def test_create_quiz_content(self, content):
        """A quiz content can be created."""
        quiz = QuizContent.objects.create(
            content=content,
            instructions="Answer all questions.",
            passing_score=80,
            time_limit=30,
            max_attempts=3,
            shuffle_questions=True,
            shuffle_choices=True,
            show_correct_answers=False,
        )

        assert quiz.content == content
        assert quiz.instructions == "Answer all questions."
        assert quiz.passing_score == 80
        assert quiz.time_limit == 30
        assert quiz.max_attempts == 3
        assert quiz.shuffle_questions is True
        assert quiz.shuffle_choices is True
        assert quiz.show_correct_answers is False

    def test_string_representation(self):
        """The string representation should return the lesson content title."""
        quiz = QuizContentFactory()

        assert str(quiz) == quiz.content.title

    def test_instructions_are_optional(self, content):
        """Instructions are optional."""
        quiz = QuizContent.objects.create(
            content=content,
        )

        assert quiz.instructions == ""

    def test_time_limit_is_optional(self, content):
        """Time limit is optional."""
        quiz = QuizContent.objects.create(
            content=content,
        )

        assert quiz.time_limit is None

    def test_default_values(self, content):
        """Quiz fields have the expected defaults."""
        quiz = QuizContent.objects.create(
            content=content,
        )

        assert quiz.passing_score == 70
        assert quiz.max_attempts == 1
        assert quiz.shuffle_questions is False
        assert quiz.shuffle_choices is False
        assert quiz.show_correct_answers is True

    def test_passing_score_cannot_exceed_100(self, content):
        """Passing score must not be greater than 100."""
        quiz = QuizContent(
            content=content,
            passing_score=101,
        )

        with pytest.raises(ValidationError) as exc:
            quiz.full_clean()

        assert "passing_score" in exc.value.message_dict

    def test_passing_score_equal_to_100_is_valid(self, content):
        """Passing score of 100 is valid."""
        quiz = QuizContent(
            content=content,
            passing_score=100,
        )

        quiz.full_clean()

    def test_passing_score_equal_to_zero_is_valid(self, content):
        """Passing score of 0 is valid."""
        quiz = QuizContent(
            content=content,
            passing_score=0,
        )

        quiz.full_clean()

    def test_content_can_have_only_one_quiz(self, content):
        """Each lesson content can have only one quiz."""
        QuizContentFactory(content=content)

        with pytest.raises(IntegrityError):
            QuizContentFactory(content=content)

    def test_deleting_content_deletes_quiz(self):
        """Deleting lesson content cascades to its quiz."""
        content = LessonContentFactory()

        quiz = QuizContentFactory(
            content=content,
        )

        content.delete()

        assert not QuizContent.objects.filter(
            pk=quiz.pk,
        ).exists()


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
            order=1,
            points=5,
            explanation="Python is a programming language.",
        )

        assert question.quiz == quiz
        assert question.text == "What is Python?"
        assert question.question_type == Question.Type.SINGLE_CHOICE
        assert question.order == 1
        assert question.points == 5
        assert question.explanation == "Python is a programming language."

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
        QuestionFactory(quiz=quiz, order=3)
        QuestionFactory(quiz=quiz, order=1)
        QuestionFactory(quiz=quiz, order=2)

        orders = list(
            quiz.questions.values_list(
                "order",
                flat=True,
            )
        )

        assert orders == [1, 2, 3]


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
