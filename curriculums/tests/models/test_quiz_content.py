import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from curriculums.models import QuizContent
from curriculums.tests.factories import (
    LessonContentFactory,
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
