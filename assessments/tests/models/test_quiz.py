import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

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


class TestQuizContentCreation:
    def test_creates_quiz_content(self, quiz_content, lesson_content):
        assert quiz_content.pk is not None
        assert quiz_content.content == lesson_content

    def test_default_values(self, quiz_content):
        assert quiz_content.instructions == ""
        assert quiz_content.passing_score == 70
        assert quiz_content.time_limit is None
        assert quiz_content.max_attempts == 1
        assert quiz_content.shuffle_questions is False
        assert quiz_content.shuffle_choices is False
        assert quiz_content.show_correct_answers is True

    def test_str_returns_content_title(self, quiz_content):
        assert str(quiz_content) == "Knowledge Check"

    def test_reverse_relation_from_lesson_content(
        self,
        lesson_content,
        quiz_content,
    ):
        assert lesson_content.quiz == quiz_content


class TestQuizContentFields:
    @pytest.mark.parametrize(
        ("passing_score", "expected"),
        [
            (0, 0),
            (1, 1),
            (70, 70),
            (100, 100),
        ],
    )
    def test_accepts_valid_passing_scores(
        self,
        quiz_content,
        passing_score,
        expected,
    ):
        quiz_content.passing_score = passing_score

        quiz_content.full_clean()

        assert quiz_content.passing_score == expected

    @pytest.mark.parametrize("time_limit", [0, 1, 30, 120])
    def test_accepts_time_limit_values(self, quiz_content, time_limit):
        quiz_content.time_limit = time_limit

        quiz_content.full_clean()

        assert quiz_content.time_limit == time_limit

    @pytest.mark.parametrize("max_attempts", [0, 1, 2, 10])
    def test_accepts_max_attempts_values(self, quiz_content, max_attempts):
        quiz_content.max_attempts = max_attempts

        quiz_content.full_clean()

        assert quiz_content.max_attempts == max_attempts

    def test_allows_null_passing_score_in_database(self, quiz_content):
        quiz_content.passing_score = None
        quiz_content.save()

        refreshed = QuizContent.objects.get(pk=quiz_content.pk)

        assert refreshed.passing_score is None

    def test_allows_null_max_attempts_in_database(self, quiz_content):
        quiz_content.max_attempts = None
        quiz_content.save()

        refreshed = QuizContent.objects.get(pk=quiz_content.pk)

        assert refreshed.max_attempts is None

    def test_allows_blank_instructions(self, quiz_content):
        quiz_content.instructions = ""

        quiz_content.full_clean()

        assert quiz_content.instructions == ""

    def test_allows_custom_instructions(self, quiz_content):
        quiz_content.instructions = "Answer all questions before submitting the quiz."

        quiz_content.full_clean()

        assert (
            quiz_content.instructions
            == "Answer all questions before submitting the quiz."
        )


class TestQuizContentPassingScoreValidation:
    def test_rejects_passing_score_above_100(self, quiz_content):
        quiz_content.passing_score = 101

        with pytest.raises(ValidationError) as exc_info:
            quiz_content.full_clean()

        assert "passing_score" in exc_info.value.message_dict
        assert exc_info.value.message_dict["passing_score"] == [
            "Passing score must be between 0 and 100."
        ]

    def test_rejects_large_passing_score(self, quiz_content):
        quiz_content.passing_score = 1000

        with pytest.raises(ValidationError) as exc_info:
            quiz_content.full_clean()

        assert "passing_score" in exc_info.value.message_dict

    def test_accepts_passing_score_of_exactly_100(self, quiz_content):
        quiz_content.passing_score = 100

        quiz_content.full_clean()

        assert quiz_content.passing_score == 100

    def test_accepts_passing_score_of_zero(self, quiz_content):
        quiz_content.passing_score = 0

        quiz_content.full_clean()

        assert quiz_content.passing_score == 0


class TestQuizContentBooleanSettings:
    @pytest.mark.parametrize(
        "field_name",
        [
            "shuffle_questions",
            "shuffle_choices",
            "show_correct_answers",
        ],
    )
    def test_boolean_settings_can_be_enabled(
        self,
        quiz_content,
        field_name,
    ):
        setattr(quiz_content, field_name, True)

        quiz_content.full_clean()

        assert getattr(quiz_content, field_name) is True

    @pytest.mark.parametrize(
        "field_name",
        [
            "shuffle_questions",
            "shuffle_choices",
            "show_correct_answers",
        ],
    )
    def test_boolean_settings_can_be_disabled(
        self,
        quiz_content,
        field_name,
    ):
        setattr(quiz_content, field_name, False)

        quiz_content.full_clean()

        assert getattr(quiz_content, field_name) is False


class TestQuizContentRelationships:
    def test_content_relationship_is_one_to_one(
        self,
        lesson_content,
        quiz_content,
    ):
        assert quiz_content.content_id == lesson_content.pk
        assert lesson_content.quiz == quiz_content

    def test_second_quiz_for_same_content_is_rejected(
        self,
        lesson_content,
        quiz_content,
    ):
        with pytest.raises(IntegrityError):
            QuizContent.objects.create(
                content=lesson_content,
            )

    def test_deleting_lesson_content_deletes_quiz_content(
        self,
        lesson_content,
        quiz_content,
    ):
        quiz_id = quiz_content.pk

        lesson_content.delete()

        assert not QuizContent.objects.filter(pk=quiz_id).exists()

    def test_deleting_quiz_content_does_not_delete_lesson_content(
        self,
        lesson_content,
        quiz_content,
    ):
        content_id = lesson_content.pk

        quiz_content.delete()

        assert LessonContent.objects.filter(pk=content_id).exists()


class TestQuizContentValidation:
    def test_content_is_required(self, db):
        quiz_content = QuizContent(
            passing_score=70,
            max_attempts=1,
        )

        with pytest.raises(ValidationError) as exc_info:
            quiz_content.full_clean()

        assert "content" in exc_info.value.message_dict

    def test_negative_passing_score_is_rejected(self, quiz_content):
        quiz_content.passing_score = -1

        with pytest.raises(ValidationError) as exc_info:
            quiz_content.full_clean()

        assert "passing_score" in exc_info.value.message_dict

    def test_negative_time_limit_is_rejected(self, quiz_content):
        quiz_content.time_limit = -1

        with pytest.raises(ValidationError) as exc_info:
            quiz_content.full_clean()

        assert "time_limit" in exc_info.value.message_dict

    def test_negative_max_attempts_is_rejected(self, quiz_content):
        quiz_content.max_attempts = -1

        with pytest.raises(ValidationError) as exc_info:
            quiz_content.full_clean()

        assert "max_attempts" in exc_info.value.message_dict


class TestQuizContentPersistence:
    def test_custom_configuration_is_persisted(
        self,
        quiz_content,
    ):
        quiz_content.instructions = "Complete the quiz carefully."
        quiz_content.passing_score = 80
        quiz_content.time_limit = 30
        quiz_content.max_attempts = 3
        quiz_content.shuffle_questions = True
        quiz_content.shuffle_choices = True
        quiz_content.show_correct_answers = False

        quiz_content.save()

        refreshed = QuizContent.objects.get(pk=quiz_content.pk)

        assert refreshed.instructions == "Complete the quiz carefully."
        assert refreshed.passing_score == 80
        assert refreshed.time_limit == 30
        assert refreshed.max_attempts == 3
        assert refreshed.shuffle_questions is True
        assert refreshed.shuffle_choices is True
        assert refreshed.show_correct_answers is False

    def test_null_optional_values_are_persisted(
        self,
        quiz_content,
    ):
        quiz_content.passing_score = None
        quiz_content.time_limit = None
        quiz_content.max_attempts = None

        quiz_content.save()

        refreshed = QuizContent.objects.get(pk=quiz_content.pk)

        assert refreshed.passing_score is None
        assert refreshed.time_limit is None
        assert refreshed.max_attempts is None


class TestQuizContentMeta:
    def test_verbose_name(self):
        assert QuizContent._meta.verbose_name == "Quiz Content"

    def test_verbose_name_plural(self):
        assert QuizContent._meta.verbose_name_plural == "Quiz Contents"
