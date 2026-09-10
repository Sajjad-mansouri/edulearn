import pytest
from django.core.exceptions import ValidationError

from assessments.models.accepted_answer import AcceptedAnswer
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
        text="What programming language is Django written in?",
        question_type=Question.Type.SHORT_ANSWER,
        order=1,
    )


@pytest.fixture
def accepted_answer(db, question):
    return AcceptedAnswer.objects.create(
        question=question,
        answer="Python",
    )


class TestAcceptedAnswerCreation:
    def test_creates_accepted_answer(
        self,
        accepted_answer,
        question,
    ):
        assert accepted_answer.pk is not None
        assert accepted_answer.question == question
        assert accepted_answer.answer == "Python"

    def test_str_returns_answer(self, accepted_answer):
        assert str(accepted_answer) == "Python"

    def test_reverse_relation_from_question(
        self,
        question,
        accepted_answer,
    ):
        assert list(question.accepted_answers.all()) == [accepted_answer]


class TestAcceptedAnswerFields:
    def test_accepts_custom_answer(
        self,
        accepted_answer,
    ):
        accepted_answer.answer = "Django"

        accepted_answer.full_clean()

        assert accepted_answer.answer == "Django"

    def test_accepts_maximum_answer_length(
        self,
        accepted_answer,
    ):
        accepted_answer.answer = "a" * 255

        accepted_answer.full_clean()

        assert len(accepted_answer.answer) == 255

    def test_accepts_answer_with_spaces(
        self,
        accepted_answer,
    ):
        accepted_answer.answer = "  Python programming  "

        accepted_answer.full_clean()

        assert accepted_answer.answer == "  Python programming  "


class TestAcceptedAnswerValidation:
    def test_question_is_required(self, db):
        accepted_answer = AcceptedAnswer(
            answer="Python",
        )

        with pytest.raises(ValidationError) as exc_info:
            accepted_answer.full_clean()

        assert "question" in exc_info.value.message_dict

    def test_answer_is_required(self, question):
        accepted_answer = AcceptedAnswer(
            question=question,
        )

        with pytest.raises(ValidationError) as exc_info:
            accepted_answer.full_clean()

        assert "answer" in exc_info.value.message_dict

    def test_answer_longer_than_max_length_is_rejected(
        self,
        accepted_answer,
    ):
        accepted_answer.answer = "a" * 256

        with pytest.raises(ValidationError) as exc_info:
            accepted_answer.full_clean()

        assert "answer" in exc_info.value.message_dict


class TestAcceptedAnswerRelationships:
    def test_multiple_accepted_answers_are_allowed(
        self,
        question,
        accepted_answer,
    ):
        second_answer = AcceptedAnswer.objects.create(
            question=question,
            answer="Python programming language",
        )

        assert question.accepted_answers.count() == 2
        assert accepted_answer in question.accepted_answers.all()
        assert second_answer in question.accepted_answers.all()

    def test_deleting_question_deletes_accepted_answers(
        self,
        question,
        accepted_answer,
    ):
        accepted_answer_id = accepted_answer.pk

        question.delete()

        assert not AcceptedAnswer.objects.filter(pk=accepted_answer_id).exists()

    def test_deleting_accepted_answer_does_not_delete_question(
        self,
        question,
        accepted_answer,
    ):
        question_id = question.pk

        accepted_answer.delete()

        assert Question.objects.filter(pk=question_id).exists()


class TestAcceptedAnswerPersistence:
    def test_answer_is_persisted(
        self,
        accepted_answer,
    ):
        accepted_answer.answer = "Updated answer"
        accepted_answer.save()

        refreshed = AcceptedAnswer.objects.get(pk=accepted_answer.pk)

        assert refreshed.answer == "Updated answer"

    def test_question_relationship_is_persisted(
        self,
        accepted_answer,
        question,
    ):
        accepted_answer_id = accepted_answer.pk

        refreshed = AcceptedAnswer.objects.get(pk=accepted_answer_id)

        assert refreshed.question_id == question.pk
