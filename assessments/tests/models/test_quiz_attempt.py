from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from assessments.models.quiz import QuizContent
from assessments.models.quiz_attempt import QuizAttempt
from courses.models.course import Course
from curriculums.models.lesson import Lesson
from curriculums.models.lesson_content import LessonContent
from curriculums.models.section import Section
from enrollments.models.enrollment import Enrollment


@pytest.fixture
def test_user(db, django_user_model):
    return django_user_model.objects.create_user(
        username="test_user",
        email="test_user@example.com",
        password="test-password",
    )


@pytest.fixture
def another_user(db, django_user_model):
    return django_user_model.objects.create_user(
        username="another_user",
        email="another_user@example.com",
        password="test-password",
    )


@pytest.fixture
def course(db, test_user):
    return Course.objects.create(
        title="Django Development",
        owner=test_user,
    )


@pytest.fixture
def another_course(db, another_user):
    return Course.objects.create(
        title="Python Development",
        owner=another_user,
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
def enrollment(db, test_user, course):
    return Enrollment.objects.create(
        user=test_user,
        course=course,
        status=Enrollment.Status.ACTIVE,
    )


@pytest.fixture
def another_enrollment(db, another_user, another_course):
    return Enrollment.objects.create(
        user=another_user,
        course=another_course,
        status=Enrollment.Status.ACTIVE,
    )


@pytest.fixture
def quiz_attempt(db, quiz_content, enrollment):
    return QuizAttempt.objects.create(
        quiz=quiz_content,
        enrollment=enrollment,
        attempt_number=1,
    )


class TestQuizAttemptCreation:
    def test_creates_quiz_attempt(
        self,
        quiz_attempt,
        quiz_content,
        enrollment,
    ):
        assert quiz_attempt.pk is not None
        assert quiz_attempt.quiz == quiz_content
        assert quiz_attempt.enrollment == enrollment

    def test_default_score_is_zero(self, quiz_attempt):
        assert quiz_attempt.score == Decimal("0")

    def test_attempt_number_is_persisted(self, quiz_attempt):
        assert quiz_attempt.attempt_number == 1

    def test_started_at_is_set_automatically(self, quiz_attempt):
        assert quiz_attempt.started_at is not None

    def test_submitted_at_defaults_to_none(self, quiz_attempt):
        assert quiz_attempt.submitted_at is None

    def test_str_representation(
        self,
        quiz_attempt,
        enrollment,
        quiz_content,
    ):
        expected = f"{enrollment.user} - {quiz_content} (Attempt 1)"

        assert str(quiz_attempt) == expected

    def test_reverse_relation_from_quiz(
        self,
        quiz_content,
        quiz_attempt,
    ):
        assert list(quiz_content.attempts.all()) == [quiz_attempt]

    def test_reverse_relation_from_enrollment(
        self,
        enrollment,
        quiz_attempt,
    ):
        assert list(enrollment.quiz_attempts.all()) == [quiz_attempt]


class TestQuizAttemptFields:
    @pytest.mark.parametrize(
        "score",
        [
            Decimal("0"),
            Decimal("0.01"),
            Decimal("50"),
            Decimal("99.99"),
            Decimal("100"),
        ],
    )
    def test_accepts_valid_scores(
        self,
        quiz_attempt,
        score,
    ):
        quiz_attempt.score = score

        quiz_attempt.full_clean()

        assert quiz_attempt.score == score

    @pytest.mark.parametrize("attempt_number", [1, 2, 3, 10])
    def test_accepts_positive_attempt_numbers(
        self,
        quiz_attempt,
        attempt_number,
    ):
        quiz_attempt.attempt_number = attempt_number

        quiz_attempt.full_clean()

        assert quiz_attempt.attempt_number == attempt_number

    def test_accepts_submitted_at(
        self,
        quiz_attempt,
    ):
        submitted_at = quiz_attempt.started_at + timedelta(minutes=10)
        quiz_attempt.submitted_at = submitted_at

        quiz_attempt.full_clean()

        assert quiz_attempt.submitted_at == submitted_at


class TestQuizAttemptValidation:
    def test_quiz_is_required(self, enrollment):
        attempt = QuizAttempt(
            enrollment=enrollment,
            attempt_number=1,
        )

        with pytest.raises(ValidationError) as exc_info:
            QuizAttempt._meta.get_field("quiz").validate(
                attempt.quiz_id,
                attempt,
            )

        assert "This field cannot be null." in exc_info.value.messages

    def test_enrollment_is_required(self, quiz_content):
        attempt = QuizAttempt(
            quiz=quiz_content,
            attempt_number=1,
        )

        with pytest.raises(ValidationError) as exc_info:
            QuizAttempt._meta.get_field("enrollment").validate(
                attempt.enrollment_id,
                attempt,
            )

        assert "This field cannot be null." in exc_info.value.messages

    def test_attempt_number_is_required(self, quiz_content, enrollment):
        attempt = QuizAttempt(
            quiz=quiz_content,
            enrollment=enrollment,
        )

        with pytest.raises(ValidationError) as exc_info:
            QuizAttempt._meta.get_field("attempt_number").validate(
                attempt.attempt_number,
                attempt,
            )

        assert "This field cannot be null." in exc_info.value.messages

    @pytest.mark.parametrize(
        "score",
        [
            Decimal("-0.01"),
            Decimal("-1"),
            Decimal("100.01"),
            Decimal("101"),
        ],
    )
    def test_rejects_score_outside_zero_to_one_hundred(
        self,
        quiz_attempt,
        score,
    ):
        quiz_attempt.score = score

        with pytest.raises(ValidationError) as exc_info:
            quiz_attempt.full_clean()

        assert "score" in exc_info.value.message_dict
        assert exc_info.value.message_dict["score"] == [
            "Score must be between 0 and 100."
        ]

    def test_rejects_submission_before_start(self, quiz_attempt):
        quiz_attempt.submitted_at = quiz_attempt.started_at - timedelta(seconds=1)

        with pytest.raises(ValidationError) as exc_info:
            quiz_attempt.full_clean()

        assert "submitted_at" in exc_info.value.message_dict
        assert exc_info.value.message_dict["submitted_at"] == [
            "Submission time cannot be before the start time."
        ]


class TestQuizAttemptCourseValidation:
    def test_enrollment_must_belong_to_quiz_course(
        self,
        quiz_attempt,
        another_enrollment,
    ):
        quiz_attempt.enrollment = another_enrollment

        with pytest.raises(ValidationError) as exc_info:
            quiz_attempt.full_clean()

        assert "enrollment" in exc_info.value.message_dict
        assert exc_info.value.message_dict["enrollment"] == [
            "Enrollment must belong to the quiz course."
        ]

    def test_same_course_enrollment_is_valid(
        self,
        quiz_attempt,
        enrollment,
    ):
        quiz_attempt.enrollment = enrollment

        quiz_attempt.full_clean()

        assert quiz_attempt.enrollment_id == enrollment.pk

    def test_different_course_is_rejected_even_with_valid_score(
        self,
        quiz_attempt,
        another_enrollment,
    ):
        quiz_attempt.enrollment = another_enrollment
        quiz_attempt.score = Decimal("75")

        with pytest.raises(ValidationError) as exc_info:
            quiz_attempt.full_clean()

        assert "enrollment" in exc_info.value.message_dict


class TestQuizAttemptUniqueness:
    def test_duplicate_attempt_number_for_same_quiz_and_enrollment_is_rejected(
        self,
        quiz_attempt,
        quiz_content,
        enrollment,
    ):
        with pytest.raises(IntegrityError):
            QuizAttempt.objects.create(
                quiz=quiz_content,
                enrollment=enrollment,
                attempt_number=quiz_attempt.attempt_number,
            )

    def test_different_attempt_number_is_allowed(
        self,
        quiz_attempt,
        quiz_content,
        enrollment,
    ):
        second_attempt = QuizAttempt.objects.create(
            quiz=quiz_content,
            enrollment=enrollment,
            attempt_number=2,
        )

        assert second_attempt.pk is not None
        assert second_attempt.attempt_number == 2

    def test_same_attempt_number_is_allowed_for_different_enrollments(
        self,
        quiz_attempt,
        quiz_content,
        another_enrollment,
    ):
        second_attempt = QuizAttempt.objects.create(
            quiz=quiz_content,
            enrollment=another_enrollment,
            attempt_number=1,
        )

        assert second_attempt.pk is not None
        assert second_attempt.attempt_number == 1

    def test_same_attempt_number_is_allowed_for_different_quizzes(
        self,
        quiz_attempt,
        enrollment,
        another_course,
        another_user,
    ):
        second_section = Section.objects.create(
            course=another_course,
            title="Second Introduction",
        )
        second_lesson = Lesson.objects.create(
            section=second_section,
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

        # The enrollment must belong to the second quiz's course.
        second_enrollment = Enrollment.objects.create(
            user=another_user,
            course=another_course,
            status=Enrollment.Status.ACTIVE,
        )

        second_attempt = QuizAttempt.objects.create(
            quiz=second_quiz,
            enrollment=second_enrollment,
            attempt_number=1,
        )

        assert second_attempt.pk is not None
        assert second_attempt.attempt_number == 1


class TestQuizAttemptOrdering:
    def test_attempts_are_ordered_by_latest_started_at_first(
        self,
        quiz_content,
        enrollment,
    ):
        first_attempt = QuizAttempt.objects.create(
            quiz=quiz_content,
            enrollment=enrollment,
            attempt_number=1,
        )

        second_attempt = QuizAttempt.objects.create(
            quiz=quiz_content,
            enrollment=enrollment,
            attempt_number=2,
        )

        third_attempt = QuizAttempt.objects.create(
            quiz=quiz_content,
            enrollment=enrollment,
            attempt_number=3,
        )

        attempts = list(QuizAttempt.objects.all())

        assert attempts == [
            third_attempt,
            second_attempt,
            first_attempt,
        ]


class TestQuizAttemptRelationships:
    def test_deleting_quiz_deletes_attempts(
        self,
        quiz_content,
        quiz_attempt,
    ):
        attempt_id = quiz_attempt.pk

        quiz_content.delete()

        assert not QuizAttempt.objects.filter(pk=attempt_id).exists()

    def test_deleting_enrollment_deletes_attempts(
        self,
        enrollment,
        quiz_attempt,
    ):
        attempt_id = quiz_attempt.pk

        enrollment.delete()

        assert not QuizAttempt.objects.filter(pk=attempt_id).exists()

    def test_deleting_attempt_does_not_delete_quiz(
        self,
        quiz_content,
        quiz_attempt,
    ):
        quiz_id = quiz_content.pk

        quiz_attempt.delete()

        assert QuizContent.objects.filter(pk=quiz_id).exists()

    def test_deleting_attempt_does_not_delete_enrollment(
        self,
        enrollment,
        quiz_attempt,
    ):
        enrollment_id = enrollment.pk

        quiz_attempt.delete()

        assert Enrollment.objects.filter(pk=enrollment_id).exists()


class TestQuizAttemptPersistence:
    def test_score_is_persisted(
        self,
        quiz_attempt,
    ):
        quiz_attempt.score = Decimal("87.50")

        quiz_attempt.save()

        refreshed = QuizAttempt.objects.get(pk=quiz_attempt.pk)

        assert refreshed.score == Decimal("87.50")

    def test_submission_time_is_persisted(
        self,
        quiz_attempt,
    ):
        submitted_at = quiz_attempt.started_at + timedelta(minutes=15)
        quiz_attempt.submitted_at = submitted_at

        quiz_attempt.save()

        refreshed = QuizAttempt.objects.get(pk=quiz_attempt.pk)

        assert refreshed.submitted_at == submitted_at

    def test_attempt_number_is_persisted(
        self,
        quiz_attempt,
    ):
        quiz_attempt.attempt_number = 2

        quiz_attempt.save()

        refreshed = QuizAttempt.objects.get(pk=quiz_attempt.pk)

        assert refreshed.attempt_number == 2
