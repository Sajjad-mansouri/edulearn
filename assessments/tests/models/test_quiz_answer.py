import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from assessments.models.choice import Choice
from assessments.models.question import Question
from assessments.models.quiz import QuizContent
from assessments.models.quiz_answer import QuizAnswer
from assessments.models.quiz_attempt import QuizAttempt
from courses.models.course import Course
from curriculums.models.lesson import Lesson
from curriculums.models.lesson_content import LessonContent
from curriculums.models.section import Section
from enrollments.models.enrollment import Enrollment


@pytest.fixture
def quiz_answer_user(db):
    from django.contrib.auth import get_user_model

    User = get_user_model()

    return User.objects.create_user(
        username="quiz_answer_user",
        email="quiz_answer_user@example.com",
        password="test-password",
    )


@pytest.fixture
def quiz_answer_course(db, quiz_answer_user):
    return Course.objects.create(
        title="Quiz Answer Course",
        owner=quiz_answer_user,
    )


@pytest.fixture
def quiz_answer_section(db, quiz_answer_course):
    return Section.objects.create(
        course=quiz_answer_course,
        title="Quiz Section",
    )


@pytest.fixture
def quiz_answer_lesson(db, quiz_answer_section):
    return Lesson.objects.create(
        section=quiz_answer_section,
        title="Quiz Lesson",
        slug="quiz-lesson",
    )


@pytest.fixture
def quiz_answer_content(db, quiz_answer_lesson):
    return LessonContent.objects.create(
        lesson=quiz_answer_lesson,
        title="Quiz Content",
        content_type=LessonContent.Type.QUIZ,
        order=1,
    )


@pytest.fixture
def quiz_content(db, quiz_answer_content):
    return QuizContent.objects.create(
        content=quiz_answer_content,
        instructions="Answer the questions.",
        passing_score=70,
        max_attempts=3,
    )


@pytest.fixture
def question(db, quiz_content):
    return Question.objects.create(
        quiz=quiz_content,
        text="What is Django?",
        question_type=Question.Type.SINGLE_CHOICE,
        difficulty=Question.Difficulty.MEDIUM,
        order=1,
        points=10,
    )


@pytest.fixture
def second_question(db, quiz_content):
    return Question.objects.create(
        quiz=quiz_content,
        text="What is Python?",
        question_type=Question.Type.SINGLE_CHOICE,
        difficulty=Question.Difficulty.EASY,
        order=2,
        points=5,
    )


@pytest.fixture
def another_quiz_answer_course(db, quiz_answer_user):
    return Course.objects.create(
        title="Another Quiz Course",
        owner=quiz_answer_user,
    )


@pytest.fixture
def another_quiz_answer_section(db, another_quiz_answer_course):
    return Section.objects.create(
        course=another_quiz_answer_course,
        title="Another Quiz Section",
    )


@pytest.fixture
def another_quiz_answer_lesson(db, another_quiz_answer_section):
    return Lesson.objects.create(
        section=another_quiz_answer_section,
        title="Another Quiz Lesson",
        slug="another-quiz-lesson",
    )


@pytest.fixture
def another_quiz_answer_content(db, another_quiz_answer_lesson):
    return LessonContent.objects.create(
        lesson=another_quiz_answer_lesson,
        title="Another Quiz Content",
        content_type=LessonContent.Type.QUIZ,
        order=1,
    )


@pytest.fixture
def another_quiz_content(db, another_quiz_answer_content):
    return QuizContent.objects.create(
        content=another_quiz_answer_content,
        instructions="Another quiz.",
        passing_score=70,
        max_attempts=3,
    )


@pytest.fixture
def another_question(db, another_quiz_content):
    return Question.objects.create(
        quiz=another_quiz_content,
        text="What is another question?",
        question_type=Question.Type.SINGLE_CHOICE,
        difficulty=Question.Difficulty.MEDIUM,
        order=1,
        points=10,
    )


@pytest.fixture
def enrollment(db, quiz_answer_user, quiz_answer_course):
    return Enrollment.objects.create(
        user=quiz_answer_user,
        course=quiz_answer_course,
        status=Enrollment.Status.ACTIVE,
    )


@pytest.fixture
def quiz_attempt(db, quiz_content, enrollment):
    return QuizAttempt.objects.create(
        quiz=quiz_content,
        enrollment=enrollment,
        attempt_number=1,
    )


@pytest.fixture
def another_quiz_attempt(db, another_quiz_content, enrollment):
    """
    This fixture intentionally creates an attempt for a different quiz
    in the same course.
    """
    return QuizAttempt.objects.create(
        quiz=another_quiz_content,
        enrollment=enrollment,
        attempt_number=1,
    )


@pytest.fixture
def quiz_answer(db, quiz_attempt, question):
    return QuizAnswer.objects.create(
        attempt=quiz_attempt,
        question=question,
    )


@pytest.fixture
def selected_choice(db, question):
    return Choice.objects.create(
        question=question,
        text="Correct choice",
        is_correct=True,
        order=1,
    )


@pytest.fixture
def second_selected_choice(db, question):
    return Choice.objects.create(
        question=question,
        text="Another choice",
        is_correct=False,
        order=2,
    )


class TestQuizAnswerCreation:
    def test_creates_quiz_answer(self, quiz_answer, quiz_attempt, question):
        assert quiz_answer.pk is not None
        assert quiz_answer.attempt == quiz_attempt
        assert quiz_answer.question == question

    def test_score_awarded_defaults_to_zero(self, quiz_answer):
        assert quiz_answer.score_awarded == 0

    def test_bool_answer_defaults_to_none(self, quiz_answer):
        assert quiz_answer.bool_answer is None

    def test_text_answer_defaults_to_empty_string(self, quiz_answer):
        assert quiz_answer.text_answer == ""

    def test_selected_choices_defaults_to_empty(self, quiz_answer):
        assert quiz_answer.selected_choices.count() == 0

    def test_str_returns_attempt_and_question_order(
        self,
        quiz_answer,
        quiz_attempt,
        question,
    ):
        expected = f"{quiz_attempt} - Question {question.order}"

        assert str(quiz_answer) == expected


class TestQuizAnswerFields:
    def test_score_awarded_accepts_zero(self, quiz_attempt, question):
        answer = QuizAnswer.objects.create(
            attempt=quiz_attempt,
            question=question,
            score_awarded=0,
        )

        assert answer.score_awarded == 0

    def test_score_awarded_accepts_decimal_value(
        self,
        quiz_attempt,
        question,
    ):
        answer = QuizAnswer.objects.create(
            attempt=quiz_attempt,
            question=question,
            score_awarded="7.50",
        )

        answer.refresh_from_db()

        assert answer.score_awarded == 7.50

    @pytest.mark.parametrize("bool_answer", [True, False, None])
    def test_bool_answer_accepts_supported_values(
        self,
        quiz_attempt,
        question,
        bool_answer,
    ):
        answer = QuizAnswer.objects.create(
            attempt=quiz_attempt,
            question=question,
            bool_answer=bool_answer,
        )

        answer.refresh_from_db()

        assert answer.bool_answer is bool_answer

    @pytest.mark.parametrize(
        "text_answer",
        [
            "",
            "Python",
            "A longer text answer.",
        ],
    )
    def test_text_answer_accepts_values(
        self,
        quiz_attempt,
        question,
        text_answer,
    ):
        answer = QuizAnswer.objects.create(
            attempt=quiz_attempt,
            question=question,
            text_answer=text_answer,
        )

        answer.refresh_from_db()

        assert answer.text_answer == text_answer

    def test_selected_choices_can_contain_multiple_choices(
        self,
        quiz_answer,
        selected_choice,
        second_selected_choice,
    ):
        quiz_answer.selected_choices.add(
            selected_choice,
            second_selected_choice,
        )

        assert quiz_answer.selected_choices.count() == 2
        assert set(quiz_answer.selected_choices.all()) == {
            selected_choice,
            second_selected_choice,
        }


class TestQuizAnswerRequiredFields:
    def test_attempt_is_required(self, question):
        answer = QuizAnswer(
            question=question,
        )

        with pytest.raises(ValidationError) as exc_info:
            QuizAnswer._meta.get_field("attempt").validate(
                answer.attempt_id,
                answer,
            )

        assert exc_info.value.messages

    def test_question_is_required(self, quiz_attempt):
        answer = QuizAnswer(
            attempt=quiz_attempt,
        )

        with pytest.raises(ValidationError) as exc_info:
            QuizAnswer._meta.get_field("question").validate(
                answer.question_id,
                answer,
            )

        assert exc_info.value.messages

    def test_score_awarded_is_not_required(self, quiz_attempt, question):
        answer = QuizAnswer(
            attempt=quiz_attempt,
            question=question,
            score_awarded=None,
        )

        with pytest.raises(ValidationError):
            QuizAnswer._meta.get_field("score_awarded").validate(
                answer.score_awarded,
                answer,
            )


class TestQuizAnswerValidation:
    def test_valid_score_zero_passes_validation(
        self,
        quiz_attempt,
        question,
    ):
        answer = QuizAnswer(
            attempt=quiz_attempt,
            question=question,
            score_awarded=0,
        )

        answer.full_clean()

    def test_valid_score_equal_to_question_points_passes_validation(
        self,
        quiz_attempt,
        question,
    ):
        answer = QuizAnswer(
            attempt=quiz_attempt,
            question=question,
            score_awarded=question.points,
        )

        answer.full_clean()

    def test_valid_score_between_zero_and_question_points_passes_validation(
        self,
        quiz_attempt,
        question,
    ):
        answer = QuizAnswer(
            attempt=quiz_attempt,
            question=question,
            score_awarded=5,
        )

        answer.full_clean()

    def test_negative_score_is_rejected(
        self,
        quiz_attempt,
        question,
    ):
        answer = QuizAnswer(
            attempt=quiz_attempt,
            question=question,
            score_awarded=-1,
        )

        with pytest.raises(ValidationError) as exc_info:
            answer.full_clean()

        assert "score_awarded" in exc_info.value.message_dict
        assert (
            "Score awarded cannot be negative."
            in exc_info.value.message_dict["score_awarded"]
        )

    def test_score_above_question_points_is_rejected(
        self,
        quiz_attempt,
        question,
    ):
        answer = QuizAnswer(
            attempt=quiz_attempt,
            question=question,
            score_awarded=question.points + 1,
        )

        with pytest.raises(ValidationError) as exc_info:
            answer.full_clean()

        assert "score_awarded" in exc_info.value.message_dict
        assert (
            "Score awarded cannot exceed the question points."
            in exc_info.value.message_dict["score_awarded"]
        )

    def test_score_equal_to_question_points_is_allowed(
        self,
        quiz_attempt,
        question,
    ):
        answer = QuizAnswer(
            attempt=quiz_attempt,
            question=question,
            score_awarded=question.points,
        )

        answer.full_clean()

        assert answer.score_awarded == question.points


class TestQuizAnswerQuizConsistency:
    def test_question_must_belong_to_attempt_quiz(
        self,
        another_quiz_attempt,
        question,
    ):
        answer = QuizAnswer(
            attempt=another_quiz_attempt,
            question=question,
        )

        with pytest.raises(ValidationError) as exc_info:
            answer.full_clean()

        assert "question" in exc_info.value.message_dict
        assert (
            "Question must belong to the quiz being attempted."
            in exc_info.value.message_dict["question"]
        )

    def test_question_from_same_quiz_passes_validation(
        self,
        quiz_attempt,
        question,
    ):
        answer = QuizAnswer(
            attempt=quiz_attempt,
            question=question,
        )

        answer.full_clean()

    def test_question_from_different_quiz_is_rejected_even_same_enrollment(
        self,
        quiz_attempt,
        another_question,
    ):
        answer = QuizAnswer(
            attempt=quiz_attempt,
            question=another_question,
        )

        with pytest.raises(ValidationError) as exc_info:
            answer.full_clean()

        assert "question" in exc_info.value.message_dict


class TestQuizAnswerUniqueness:
    def test_same_question_cannot_be_answered_twice_in_same_attempt(
        self,
        quiz_answer,
        quiz_attempt,
        question,
    ):
        duplicate = QuizAnswer(
            attempt=quiz_attempt,
            question=question,
        )

        with pytest.raises(IntegrityError):
            duplicate.save()

    def test_same_question_can_be_answered_in_different_attempts(
        self,
        quiz_answer,
        quiz_content,
        enrollment,
        question,
    ):
        second_attempt = QuizAttempt.objects.create(
            quiz=quiz_content,
            enrollment=enrollment,
            attempt_number=2,
        )

        second_answer = QuizAnswer.objects.create(
            attempt=second_attempt,
            question=question,
        )

        assert second_answer.pk is not None
        assert second_answer.question == question
        assert second_answer.attempt == second_attempt

    def test_different_questions_can_be_answered_in_same_attempt(
        self,
        quiz_answer,
        quiz_attempt,
        second_question,
    ):
        second_answer = QuizAnswer.objects.create(
            attempt=quiz_attempt,
            question=second_question,
        )

        assert second_answer.pk is not None
        assert quiz_attempt.answers.count() == 2


class TestQuizAnswerOrdering:
    def test_answers_are_ordered_by_attempt_then_question_order(
        self,
        quiz_attempt,
        question,
        second_question,
    ):
        second_answer = QuizAnswer.objects.create(
            attempt=quiz_attempt,
            question=second_question,
        )

        first_answer = QuizAnswer.objects.create(
            attempt=quiz_attempt,
            question=question,
        )

        answers = list(QuizAnswer.objects.all())

        assert answers == [first_answer, second_answer]

    def test_question_order_determines_answer_order(
        self,
        quiz_attempt,
        question,
        second_question,
    ):
        first_answer = QuizAnswer.objects.create(
            attempt=quiz_attempt,
            question=question,
        )

        second_answer = QuizAnswer.objects.create(
            attempt=quiz_attempt,
            question=second_question,
        )

        answers = list(quiz_attempt.answers.all())

        assert answers[0] == first_answer
        assert answers[1] == second_answer


class TestQuizAnswerRelationships:
    def test_attempt_reverse_relation(self, quiz_answer, quiz_attempt):
        assert quiz_answer in quiz_attempt.answers.all()

    def test_question_reverse_relation(self, quiz_answer, question):
        assert quiz_answer in question.answers.all()

    def test_selected_choices_reverse_relation(
        self,
        quiz_answer,
        selected_choice,
    ):
        quiz_answer.selected_choices.add(selected_choice)

        assert quiz_answer in selected_choice.quiz_answers.all()

    def test_selected_choices_can_be_shared_by_multiple_answers(
        self,
        quiz_answer,
        selected_choice,
        quiz_attempt,
        second_question,
    ):
        second_answer = QuizAnswer.objects.create(
            attempt=quiz_attempt,
            question=second_question,
        )

        quiz_answer.selected_choices.add(selected_choice)
        second_answer.selected_choices.add(selected_choice)

        assert selected_choice.quiz_answers.count() == 2

    def test_deleting_attempt_cascades_to_answers(
        self,
        quiz_answer,
        quiz_attempt,
    ):
        answer_id = quiz_answer.pk

        quiz_attempt.delete()

        assert not QuizAnswer.objects.filter(pk=answer_id).exists()

    def test_deleting_question_cascades_to_answers(
        self,
        quiz_answer,
        question,
    ):
        answer_id = quiz_answer.pk

        question.delete()

        assert not QuizAnswer.objects.filter(pk=answer_id).exists()

    def test_deleting_answer_removes_many_to_many_relationship(
        self,
        quiz_answer,
        selected_choice,
    ):
        quiz_answer.selected_choices.add(selected_choice)

        quiz_answer.delete()

        assert not selected_choice.quiz_answers.filter(pk=quiz_answer.pk).exists()
        assert Choice.objects.filter(pk=selected_choice.pk).exists()


class TestQuizAnswerPersistence:
    def test_updates_score_awarded(
        self,
        quiz_answer,
    ):
        quiz_answer.score_awarded = 8.50
        quiz_answer.save()

        quiz_answer.refresh_from_db()

        assert quiz_answer.score_awarded == 8.50

    def test_updates_bool_answer(
        self,
        quiz_answer,
    ):
        quiz_answer.bool_answer = True
        quiz_answer.save()

        quiz_answer.refresh_from_db()

        assert quiz_answer.bool_answer is True

    def test_updates_text_answer(
        self,
        quiz_answer,
    ):
        quiz_answer.text_answer = "The answer is Python."

        quiz_answer.save()

        quiz_answer.refresh_from_db()

        assert quiz_answer.text_answer == "The answer is Python."

    def test_selected_choices_persist(
        self,
        quiz_answer,
        selected_choice,
        second_selected_choice,
    ):
        quiz_answer.selected_choices.set([selected_choice, second_selected_choice])

        quiz_answer.refresh_from_db()

        assert set(quiz_answer.selected_choices.all()) == {
            selected_choice,
            second_selected_choice,
        }
