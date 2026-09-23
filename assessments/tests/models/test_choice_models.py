import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from assessments.models.choice import Choice
from assessments.models.question import Question
from assessments.models.quiz import QuizContent
from courses.models.course import Course
from curriculums.models.lesson import Lesson
from curriculums.models.lesson_content import LessonContent
from curriculums.models.section import Section


@pytest.fixture
def test_user(db, django_user_model):
    return django_user_model.objects.create_user(
        username="test_user",
        email="test_user@example.com",
        password="test-password",
    )


@pytest.fixture
def course(db, test_user):
    return Course.objects.create(
        title="Django Development",
        owner=test_user,
    )


@pytest.fixture
def section(db, course):
    return Section.objects.create(
        course=course,
        title="Introduction",
    )


@pytest.fixture
def lesson(db, section):
    return Lesson.objects.create(
        section=section,
        title="Quiz Lesson",
        slug="quiz-lesson",
    )


@pytest.fixture
def lesson_content(db, lesson):
    return LessonContent.objects.create(
        lesson=lesson,
        title="Knowledge Check",
        content_type=LessonContent.Type.QUIZ,
        order=1,
    )


@pytest.fixture
def quiz_content(db, lesson_content):
    return QuizContent.objects.create(
        content=lesson_content,
    )


@pytest.fixture
def question(db, quiz_content):
    return Question.objects.create(
        quiz=quiz_content,
        text="Which statement is correct?",
        order=1,
    )


@pytest.fixture
def choice(db, question):
    return Choice.objects.create(
        question=question,
        text="Correct answer",
        order=1,
    )


class TestChoiceCreation:
    def test_creates_choice(self, choice, question):
        assert choice.pk is not None
        assert choice.question == question

    def test_default_is_correct_is_false(self, choice):
        assert choice.is_correct is False

    def test_str_returns_choice_text(self, choice):
        assert str(choice) == "Correct answer"

    def test_reverse_relation_from_question(self, question, choice):
        assert list(question.choices.all()) == [choice]


class TestChoiceFields:
    def test_accepts_correct_choice(self, choice):
        choice.is_correct = True

        choice.full_clean()

        assert choice.is_correct is True

    def test_accepts_incorrect_choice(self, choice):
        choice.is_correct = False

        choice.full_clean()

        assert choice.is_correct is False

    def test_accepts_zero_order(self, choice):
        choice.order = 0

        choice.full_clean()

        assert choice.order == 0

    @pytest.mark.parametrize("order", [1, 2, 5, 100])
    def test_accepts_positive_order(self, choice, order):
        choice.order = order

        choice.full_clean()

        assert choice.order == order

    def test_accepts_maximum_text_length(self, choice):
        choice.text = "a" * 500

        choice.full_clean()

        assert len(choice.text) == 500


class TestChoiceValidation:
    def test_question_is_required(self, db):
        choice = Choice(
            text="An answer",
            order=1,
        )

        with pytest.raises(ValidationError) as exc_info:
            choice.full_clean()

        assert "question" in exc_info.value.message_dict

    def test_text_is_required(self, question):
        choice = Choice(
            question=question,
            order=1,
        )

        with pytest.raises(ValidationError) as exc_info:
            choice.full_clean()

        assert "text" in exc_info.value.message_dict

    def test_order_is_required(self, question):
        choice = Choice(
            question=question,
            text="An answer",
        )

        with pytest.raises(ValidationError) as exc_info:
            choice.full_clean()

        assert "order" in exc_info.value.message_dict

    def test_negative_order_is_rejected(self, choice):
        choice.order = -1

        with pytest.raises(ValidationError) as exc_info:
            choice.full_clean()

        assert "order" in exc_info.value.message_dict

    def test_text_longer_than_max_length_is_rejected(self, choice):
        choice.text = "a" * 501

        with pytest.raises(ValidationError) as exc_info:
            choice.full_clean()

        assert "text" in exc_info.value.message_dict


class TestChoiceOrdering:
    def test_choices_are_ordered_by_order(self, question):
        choice_2 = Choice.objects.create(
            question=question,
            text="Second choice",
            order=2,
        )
        choice_1 = Choice.objects.create(
            question=question,
            text="First choice",
            order=1,
        )
        choice_3 = Choice.objects.create(
            question=question,
            text="Third choice",
            order=3,
        )

        choices = list(Choice.objects.all())

        assert choices == [
            choice_1,
            choice_2,
            choice_3,
        ]

    def test_reverse_relation_is_ordered(self, question):
        choice_2 = Choice.objects.create(
            question=question,
            text="Second choice",
            order=2,
        )
        choice_1 = Choice.objects.create(
            question=question,
            text="First choice",
            order=1,
        )

        assert list(question.choices.all()) == [
            choice_1,
            choice_2,
        ]


class TestChoiceOrderConstraint:
    def test_duplicate_order_within_same_question_is_rejected(
        self,
        question,
        choice,
    ):
        with pytest.raises(IntegrityError):
            Choice.objects.create(
                question=question,
                text="Another answer",
                order=choice.order,
            )

    def test_same_order_is_allowed_for_different_questions(
        self,
        question,
        quiz_content,
    ):
        second_question = Question.objects.create(
            quiz=quiz_content,
            text="Another question",
            order=2,
        )

        first_choice = Choice.objects.create(
            question=question,
            text="First answer",
            order=1,
        )
        second_choice = Choice.objects.create(
            question=second_question,
            text="First answer",
            order=1,
        )

        assert first_choice.order == 1
        assert second_choice.order == 1
        assert first_choice.question != second_choice.question


class TestChoiceRelationships:
    def test_deleting_question_deletes_choices(
        self,
        question,
        choice,
    ):
        choice_id = choice.pk

        question.delete()

        assert not Choice.objects.filter(pk=choice_id).exists()

    def test_deleting_choice_does_not_delete_question(
        self,
        question,
        choice,
    ):
        question_id = question.pk

        choice.delete()

        assert Question.objects.filter(pk=question_id).exists()

    def test_choice_belongs_to_expected_question(
        self,
        choice,
        question,
    ):
        assert choice.question_id == question.pk


class TestChoicePersistence:
    def test_custom_values_are_persisted(self, choice):
        choice.text = "Updated answer"
        choice.is_correct = True
        choice.order = 5

        choice.save()

        refreshed = Choice.objects.get(pk=choice.pk)

        assert refreshed.text == "Updated answer"
        assert refreshed.is_correct is True
        assert refreshed.order == 5

    def test_zero_order_is_persisted(self, choice):
        choice.order = 0

        choice.save()

        refreshed = Choice.objects.get(pk=choice.pk)

        assert refreshed.order == 0

    def test_is_correct_can_be_changed(self, choice):
        assert choice.is_correct is False

        choice.is_correct = True
        choice.save()

        refreshed = Choice.objects.get(pk=choice.pk)

        assert refreshed.is_correct is True
