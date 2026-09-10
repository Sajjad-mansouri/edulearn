import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from assessments.models.bool_answer import BooleanAnswer
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
        text="Django is a Python framework.",
        question_type=Question.Type.TRUE_FALSE,
        order=1,
    )


@pytest.fixture
def boolean_answer(db, question):
    return BooleanAnswer.objects.create(
        question=question,
    )


class TestBooleanAnswerCreation:
    def test_creates_boolean_answer(self, boolean_answer, question):
        assert boolean_answer.pk is not None
        assert boolean_answer.question == question

    def test_default_answer_is_false(self, boolean_answer):
        assert boolean_answer.answer is False

    @pytest.mark.parametrize(
        ("answer", "expected_string"),
        [
            (True, "True"),
            (False, "False"),
        ],
    )
    def test_str_representation(
        self,
        boolean_answer,
        answer,
        expected_string,
    ):
        boolean_answer.answer = answer

        assert str(boolean_answer) == expected_string


class TestBooleanAnswerFields:
    @pytest.mark.parametrize("answer", [True, False])
    def test_accepts_boolean_values(self, boolean_answer, answer):
        boolean_answer.answer = answer

        boolean_answer.full_clean()

        assert boolean_answer.answer is answer

    def test_answer_can_be_changed_from_false_to_true(self, boolean_answer):
        assert boolean_answer.answer is False

        boolean_answer.answer = True
        boolean_answer.save()

        refreshed = BooleanAnswer.objects.get(pk=boolean_answer.pk)

        assert refreshed.answer is True

    def test_answer_can_be_changed_from_true_to_false(
        self,
        boolean_answer,
    ):
        boolean_answer.answer = True
        boolean_answer.save()

        boolean_answer.answer = False
        boolean_answer.save()

        refreshed = BooleanAnswer.objects.get(pk=boolean_answer.pk)

        assert refreshed.answer is False


class TestBooleanAnswerValidation:
    def test_question_is_required(self, db):
        boolean_answer = BooleanAnswer()

        with pytest.raises(ValidationError) as exc_info:
            boolean_answer.full_clean()

        assert "question" in exc_info.value.message_dict


class TestBooleanAnswerRelationship:
    def test_question_has_reverse_boolean_answer_relation(
        self,
        question,
        boolean_answer,
    ):
        assert question.boolean_answer == boolean_answer

    def test_question_relation_is_one_to_one(
        self,
        question,
        boolean_answer,
    ):
        assert boolean_answer.question_id == question.pk
        assert question.boolean_answer.pk == boolean_answer.pk

    def test_second_boolean_answer_for_same_question_is_rejected(
        self,
        question,
        boolean_answer,
    ):
        with pytest.raises(IntegrityError):
            BooleanAnswer.objects.create(
                question=question,
            )

    def test_deleting_question_deletes_boolean_answer(
        self,
        question,
        boolean_answer,
    ):
        boolean_answer_id = boolean_answer.pk

        question.delete()

        assert not BooleanAnswer.objects.filter(pk=boolean_answer_id).exists()

    def test_deleting_boolean_answer_does_not_delete_question(
        self,
        question,
        boolean_answer,
    ):
        question_id = question.pk

        boolean_answer.delete()

        assert Question.objects.filter(pk=question_id).exists()


class TestBooleanAnswerPersistence:
    @pytest.mark.parametrize("answer", [True, False])
    def test_answer_is_persisted(
        self,
        boolean_answer,
        answer,
    ):
        boolean_answer.answer = answer
        boolean_answer.save()

        refreshed = BooleanAnswer.objects.get(pk=boolean_answer.pk)

        assert refreshed.answer is answer
