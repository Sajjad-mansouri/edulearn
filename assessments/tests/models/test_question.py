from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

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


class TestQuestionCreation:
    def test_creates_question(self, question, quiz_content):
        assert question.pk is not None
        assert question.quiz == quiz_content

    def test_default_values(self, question):
        assert question.question_type == Question.Type.SINGLE_CHOICE
        assert question.difficulty == Question.Difficulty.MEDIUM
        assert question.points == 1
        assert question.explanation == ""
        assert question.is_required is True
        assert question.estimated_time is None

    def test_str_returns_question_text(self, question):
        assert str(question) == "Which statement is correct?"

    def test_reverse_relation_from_quiz(self, quiz_content, question):
        assert list(quiz_content.questions.all()) == [question]


class TestQuestionTypes:
    @pytest.mark.parametrize(
        "question_type",
        [
            Question.Type.SINGLE_CHOICE,
            Question.Type.MULTIPLE_CHOICE,
            Question.Type.TRUE_FALSE,
            Question.Type.SHORT_ANSWER,
        ],
    )
    def test_accepts_question_type(self, question, question_type):
        question.question_type = question_type

        question.full_clean()

        assert question.question_type == question_type


class TestQuestionDifficulty:
    @pytest.mark.parametrize(
        "difficulty",
        [
            Question.Difficulty.EASY,
            Question.Difficulty.MEDIUM,
            Question.Difficulty.HARD,
        ],
    )
    def test_accepts_difficulty(self, question, difficulty):
        question.difficulty = difficulty

        question.full_clean()

        assert question.difficulty == difficulty


class TestQuestionFields:
    def test_accepts_custom_text(self, question):
        question.text = "What is Django?"

        question.full_clean()

        assert question.text == "What is Django?"

    def test_accepts_zero_points(self, question):
        question.points = 0

        question.full_clean()

        assert question.points == 0

    @pytest.mark.parametrize("points", [1, 2, 5, 100])
    def test_accepts_positive_points(self, question, points):
        question.points = points

        question.full_clean()

        assert question.points == points

    def test_accepts_blank_explanation(self, question):
        question.explanation = ""

        question.full_clean()

        assert question.explanation == ""

    def test_accepts_explanation(self, question):
        question.explanation = "The correct answer is explained here."

        question.full_clean()

        assert question.explanation == ("The correct answer is explained here.")

    def test_accepts_optional_estimated_time(self, question):
        question.estimated_time = timedelta(minutes=2)

        question.full_clean()

        assert question.estimated_time == timedelta(minutes=2)

    def test_accepts_null_estimated_time(self, question):
        question.estimated_time = None

        question.full_clean()

        assert question.estimated_time is None

    @pytest.mark.parametrize("is_required", [True, False])
    def test_is_required_can_be_changed(self, question, is_required):
        question.is_required = is_required

        question.full_clean()

        assert question.is_required is is_required


class TestQuestionValidation:
    def test_quiz_is_required(self, db):
        question = Question(
            text="Which statement is correct?",
            order=1,
        )

        with pytest.raises(ValidationError) as exc_info:
            question.full_clean()

        assert "quiz" in exc_info.value.message_dict

    def test_text_is_required(self, question):
        question.text = ""

        with pytest.raises(ValidationError) as exc_info:
            question.full_clean()

        assert "text" in exc_info.value.message_dict

    def test_order_is_required(self, quiz_content):
        question = Question(
            quiz=quiz_content,
            text="Which statement is correct?",
        )

        with pytest.raises(ValidationError) as exc_info:
            question.full_clean()

        assert "order" in exc_info.value.message_dict

    def test_negative_order_is_rejected(self, question):
        question.order = -1

        with pytest.raises(ValidationError) as exc_info:
            question.full_clean()

        assert "order" in exc_info.value.message_dict

    def test_negative_points_are_rejected(self, question):
        question.points = -1

        with pytest.raises(ValidationError) as exc_info:
            question.full_clean()

        assert "points" in exc_info.value.message_dict


class TestQuestionOrdering:
    def test_questions_are_ordered_by_order(self, quiz_content):
        question_2 = Question.objects.create(
            quiz=quiz_content,
            text="Second question",
            order=2,
        )
        question_1 = Question.objects.create(
            quiz=quiz_content,
            text="First question",
            order=1,
        )
        question_3 = Question.objects.create(
            quiz=quiz_content,
            text="Third question",
            order=3,
        )

        questions = list(Question.objects.all())

        assert questions == [
            question_1,
            question_2,
            question_3,
        ]

    def test_ordering_applies_across_different_quizzes(
        self,
        quiz_content,
        db,
    ):
        second_lesson = Lesson.objects.create(
            section=quiz_content.content.lesson.section,
            title="Second Quiz Lesson",
            slug="second-quiz-lesson",
        )
        second_content = LessonContent.objects.create(
            lesson=second_lesson,
            title="Second Quiz",
            content_type=LessonContent.Type.QUIZ,
            order=1,
        )
        second_quiz = QuizContent.objects.create(
            content=second_content,
        )

        question_2 = Question.objects.create(
            quiz=second_quiz,
            text="Question 2",
            order=2,
        )
        question_1 = Question.objects.create(
            quiz=quiz_content,
            text="Question 1",
            order=1,
        )

        assert list(Question.objects.all()) == [
            question_1,
            question_2,
        ]


class TestQuestionOrderConstraint:
    def test_duplicate_order_within_same_quiz_is_rejected(
        self,
        question,
        quiz_content,
    ):
        with pytest.raises(IntegrityError):
            Question.objects.create(
                quiz=quiz_content,
                text="Another question",
                order=question.order,
            )

    def test_same_order_is_allowed_in_different_quizzes(
        self,
        quiz_content,
    ):
        second_lesson = Lesson.objects.create(
            section=quiz_content.content.lesson.section,
            title="Another Quiz Lesson",
            slug="another-quiz-lesson",
        )
        second_content = LessonContent.objects.create(
            lesson=second_lesson,
            title="Another Quiz",
            content_type=LessonContent.Type.QUIZ,
            order=1,
        )
        second_quiz = QuizContent.objects.create(
            content=second_content,
        )

        first_question = Question.objects.create(
            quiz=quiz_content,
            text="First question",
            order=1,
        )
        second_question = Question.objects.create(
            quiz=second_quiz,
            text="First question",
            order=1,
        )

        assert first_question.order == second_question.order == 1


class TestQuestionRelationships:
    def test_deleting_quiz_deletes_questions(
        self,
        quiz_content,
        question,
    ):
        question_id = question.pk

        quiz_content.delete()

        assert not Question.objects.filter(pk=question_id).exists()

    def test_deleting_question_does_not_delete_quiz(
        self,
        quiz_content,
        question,
    ):
        quiz_id = quiz_content.pk

        question.delete()

        assert QuizContent.objects.filter(pk=quiz_id).exists()

    def test_question_belongs_to_expected_quiz(
        self,
        question,
        quiz_content,
    ):
        assert question.quiz_id == quiz_content.pk


class TestQuestionPersistence:
    def test_custom_values_are_persisted(self, question):
        question.text = "Updated question"
        question.question_type = Question.Type.MULTIPLE_CHOICE
        question.difficulty = Question.Difficulty.HARD
        question.order = 5
        question.points = 10
        question.explanation = "Updated explanation."
        question.is_required = False
        question.estimated_time = timedelta(seconds=90)

        question.save()

        refreshed = Question.objects.get(pk=question.pk)

        assert refreshed.text == "Updated question"
        assert refreshed.question_type == Question.Type.MULTIPLE_CHOICE
        assert refreshed.difficulty == Question.Difficulty.HARD
        assert refreshed.order == 5
        assert refreshed.points == 10
        assert refreshed.explanation == "Updated explanation."
        assert refreshed.is_required is False
        assert refreshed.estimated_time == timedelta(seconds=90)

    def test_zero_points_are_persisted(self, question):
        question.points = 0
        question.save()

        refreshed = Question.objects.get(pk=question.pk)

        assert refreshed.points == 0

    def test_zero_order_is_persisted(self, question):
        question.order = 0
        question.save()

        refreshed = Question.objects.get(pk=question.pk)

        assert refreshed.order == 0
