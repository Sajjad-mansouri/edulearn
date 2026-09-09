# assessments/tests/test_models.py

import pytest
from django.core.exceptions import ValidationError

from assessments.models import QuizContent


@pytest.mark.django_db
class TestQuizContentModel:
    def test_quiz_content_can_be_created(self, lesson_content):
        quiz = QuizContent.objects.create(
            content=lesson_content,
        )

        assert quiz.content == lesson_content

    def test_instructions_are_optional(self, lesson_content):
        quiz = QuizContent.objects.create(
            content=lesson_content,
        )

        assert quiz.instructions == ""

    def test_instructions_are_stored(self, lesson_content):
        instructions = "Read every question carefully before submitting your answers."

        quiz = QuizContent.objects.create(
            content=lesson_content,
            instructions=instructions,
        )

        assert quiz.instructions == instructions

    def test_passing_score_defaults_to_70(self, lesson_content):
        quiz = QuizContent.objects.create(
            content=lesson_content,
        )

        assert quiz.passing_score == 70

    def test_passing_score_can_be_zero(self, lesson_content):
        quiz = QuizContent.objects.create(
            content=lesson_content,
            passing_score=0,
        )

        assert quiz.passing_score == 0

    def test_passing_score_can_be_100(self, lesson_content):
        quiz = QuizContent.objects.create(
            content=lesson_content,
            passing_score=100,
        )

        quiz.full_clean()

        assert quiz.passing_score == 100

    def test_passing_score_greater_than_100_fails_validation(
        self,
        lesson_content,
    ):
        quiz = QuizContent(
            content=lesson_content,
            passing_score=101,
        )

        with pytest.raises(ValidationError) as exc_info:
            quiz.full_clean()

        assert "passing_score" in exc_info.value.message_dict
        assert exc_info.value.message_dict["passing_score"] == [
            "Passing score must be between 0 and 100."
        ]

    def test_passing_score_none_is_allowed_when_no_passing_score_is_required(
        self,
        lesson_content,
    ):
        quiz = QuizContent(
            content=lesson_content,
            passing_score=None,
        )

        quiz.full_clean()

        assert quiz.passing_score is None

    def test_time_limit_defaults_to_none(self, lesson_content):
        quiz = QuizContent.objects.create(
            content=lesson_content,
        )

        assert quiz.time_limit is None

    def test_time_limit_can_be_set(self, lesson_content):
        quiz = QuizContent.objects.create(
            content=lesson_content,
            time_limit=30,
        )

        assert quiz.time_limit == 30

    def test_max_attempts_defaults_to_1(self, lesson_content):
        quiz = QuizContent.objects.create(
            content=lesson_content,
        )

        assert quiz.max_attempts == 1

    def test_max_attempts_can_be_zero_for_unlimited_attempts(
        self,
        lesson_content,
    ):
        quiz = QuizContent.objects.create(
            content=lesson_content,
            max_attempts=0,
        )

        assert quiz.max_attempts == 0

    def test_max_attempts_can_be_set(self, lesson_content):
        quiz = QuizContent.objects.create(
            content=lesson_content,
            max_attempts=5,
        )

        assert quiz.max_attempts == 5

    def test_shuffle_questions_defaults_to_false(self, lesson_content):
        quiz = QuizContent.objects.create(
            content=lesson_content,
        )

        assert quiz.shuffle_questions is False

    def test_shuffle_choices_defaults_to_false(self, lesson_content):
        quiz = QuizContent.objects.create(
            content=lesson_content,
        )

        assert quiz.shuffle_choices is False

    def test_show_correct_answers_defaults_to_true(self, lesson_content):
        quiz = QuizContent.objects.create(
            content=lesson_content,
        )

        assert quiz.show_correct_answers is True

    def test_shuffle_questions_can_be_enabled(self, lesson_content):
        quiz = QuizContent.objects.create(
            content=lesson_content,
            shuffle_questions=True,
        )

        assert quiz.shuffle_questions is True

    def test_shuffle_choices_can_be_enabled(self, lesson_content):
        quiz = QuizContent.objects.create(
            content=lesson_content,
            shuffle_choices=True,
        )

        assert quiz.shuffle_choices is True

    def test_show_correct_answers_can_be_disabled(self, lesson_content):
        quiz = QuizContent.objects.create(
            content=lesson_content,
            show_correct_answers=False,
        )

        assert quiz.show_correct_answers is False

    def test_quiz_content_has_one_to_one_relationship_with_lesson_content(
        self,
        lesson_content,
    ):
        quiz = QuizContent.objects.create(
            content=lesson_content,
        )

        assert lesson_content.quiz == quiz

    def test_quiz_content_is_deleted_when_lesson_content_is_deleted(
        self,
        lesson_content,
    ):
        quiz = QuizContent.objects.create(
            content=lesson_content,
        )
        quiz_id = quiz.pk

        lesson_content.delete()

        assert not QuizContent.objects.filter(pk=quiz_id).exists()

    def test_str_returns_lesson_content_title(self, lesson_content):
        quiz = QuizContent.objects.create(
            content=lesson_content,
        )

        assert str(quiz) == lesson_content.title

    def test_full_clean_accepts_valid_default_configuration(
        self,
        lesson_content,
    ):
        quiz = QuizContent(
            content=lesson_content,
        )

        quiz.full_clean()

    def test_full_clean_accepts_valid_configuration(
        self,
        lesson_content,
    ):
        quiz = QuizContent(
            content=lesson_content,
            instructions="Complete the quiz carefully.",
            passing_score=70,
            time_limit=30,
            max_attempts=3,
            shuffle_questions=True,
            shuffle_choices=True,
            show_correct_answers=False,
        )

        quiz.full_clean()
