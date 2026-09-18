from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from assessments.models import (
    AcceptedAnswer,
    BooleanAnswer,
    Choice,
    Question,
    QuizAnswer,
    QuizAttempt,
    QuizContent,
)
from courses.models import Course
from curriculums.models import Lesson, LessonContent, Section
from enrollments.models import Enrollment, LessonProgress


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def section(course):
    return Section.objects.create(
        course=course,
        title="Quiz Section",
        order=1,
    )


@pytest.fixture
def lesson(section):
    return Lesson.objects.create(
        section=section,
        title="Python Quiz",
        slug="python-quiz",
        order=1,
    )


@pytest.fixture
def quiz_lesson_content(lesson):
    return LessonContent.objects.create(
        lesson=lesson,
        title="Python Quiz",
        content_type=LessonContent.Type.QUIZ,
        order=1,
        is_main_content=True,
    )


@pytest.fixture
def quiz_content(quiz_lesson_content):
    return QuizContent.objects.create(
        content=quiz_lesson_content,
        passing_score=70,
        max_attempts=3,
        show_correct_answers=True,
    )


@pytest.fixture
def single_choice_question(quiz_content):
    return Question.objects.create(
        quiz=quiz_content,
        text="Which language is Django written in?",
        question_type=Question.Type.SINGLE_CHOICE,
        order=1,
        points=1,
    )


@pytest.fixture
def single_choice_choices(single_choice_question):
    correct = Choice.objects.create(
        question=single_choice_question,
        text="Python",
        is_correct=True,
        order=1,
    )
    incorrect = Choice.objects.create(
        question=single_choice_question,
        text="Java",
        is_correct=False,
        order=2,
    )
    return correct, incorrect


@pytest.fixture
def multiple_choice_question(quiz_content):
    return Question.objects.create(
        quiz=quiz_content,
        text="Which are Python web frameworks?",
        question_type=Question.Type.MULTIPLE_CHOICE,
        order=2,
        points=1,
    )


@pytest.fixture
def multiple_choice_choices(multiple_choice_question):
    django = Choice.objects.create(
        question=multiple_choice_question,
        text="Django",
        is_correct=True,
        order=1,
    )
    flask = Choice.objects.create(
        question=multiple_choice_question,
        text="Flask",
        is_correct=True,
        order=2,
    )
    java = Choice.objects.create(
        question=multiple_choice_question,
        text="Spring",
        is_correct=False,
        order=3,
    )
    return django, flask, java


@pytest.fixture
def true_false_question(quiz_content):
    return Question.objects.create(
        quiz=quiz_content,
        text="Django is a Python web framework.",
        question_type=Question.Type.TRUE_FALSE,
        order=3,
        points=1,
    )


@pytest.fixture
def boolean_answer(true_false_question):
    return BooleanAnswer.objects.create(
        question=true_false_question,
        answer=True,
    )


@pytest.fixture
def short_answer_question(quiz_content):
    return Question.objects.create(
        quiz=quiz_content,
        text="What language is Django written in?",
        question_type=Question.Type.SHORT_ANSWER,
        order=4,
        points=1,
    )


@pytest.fixture
def accepted_answer(short_answer_question):
    return AcceptedAnswer.objects.create(
        question=short_answer_question,
        answer="Python",
    )


@pytest.fixture
def quiz_submit_url(enrollment, lesson):
    return reverse(
        "enrollment_api:quiz_submit",
        kwargs={
            "enrollment_id": enrollment.id,
            "lesson_id": lesson.id,
        },
    )


class TestQuizSubmitApiView:
    def test_requires_authentication(
        self,
        api_client,
        quiz_submit_url,
    ):
        response = api_client.post(
            quiz_submit_url,
            {"answers": []},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_rejects_another_users_enrollment(
        self,
        api_client,
        test_user,
        another_user_enrollment,
        quiz_submit_url,
        single_choice_question,
        single_choice_choices,
    ):
        api_client.force_authenticate(user=test_user)

        correct_choice, _ = single_choice_choices

        response = api_client.post(
            reverse(
                "enrollment_api:quiz_submit",
                kwargs={
                    "enrollment_id": another_user_enrollment.id,
                    "lesson_id": single_choice_question.quiz.content.lesson.id,
                },
            ),
            {
                "answers": [
                    {
                        "questionId": single_choice_question.id,
                        "questionType": "single_choice",
                        "selectedValues": [correct_choice.id],
                    }
                ]
            },
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

        assert not QuizAttempt.objects.filter(
            enrollment=another_user_enrollment
        ).exists()

    @pytest.mark.parametrize(
        "enrollment_status",
        [
            Enrollment.Status.CANCELLED,
            Enrollment.Status.SUSPENDED,
            Enrollment.Status.PENDING,
        ],
    )
    def test_rejects_inactive_enrollment(
        self,
        api_client,
        test_user,
        course,
        lesson,
        enrollment_status,
        single_choice_question,
        single_choice_choices,
    ):
        enrollment = Enrollment.objects.create(
            user=test_user,
            course=course,
            status=enrollment_status,
        )

        api_client.force_authenticate(user=test_user)

        correct_choice, _ = single_choice_choices

        url = reverse(
            "enrollment_api:quiz_submit",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lesson.id,
            },
        )

        response = api_client.post(
            url,
            {
                "answers": [
                    {
                        "questionId": single_choice_question.id,
                        "questionType": "single_choice",
                        "selectedValues": [correct_choice.id],
                    }
                ]
            },
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

        assert not QuizAttempt.objects.filter(enrollment=enrollment).exists()

    def test_allows_completed_enrollment(
        self,
        api_client,
        test_user,
        course,
        lesson,
        single_choice_question,
        single_choice_choices,
    ):
        enrollment = Enrollment.objects.create(
            user=test_user,
            course=course,
            status=Enrollment.Status.COMPLETED,
        )

        api_client.force_authenticate(user=test_user)

        correct_choice, _ = single_choice_choices

        url = reverse(
            "enrollment_api:quiz_submit",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lesson.id,
            },
        )

        response = api_client.post(
            url,
            {
                "answers": [
                    {
                        "questionId": single_choice_question.id,
                        "questionType": "single_choice",
                        "selectedValues": [correct_choice.id],
                    }
                ]
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_rejects_missing_answers(
        self,
        api_client,
        test_user,
        quiz_submit_url,
        quiz_content,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            quiz_submit_url,
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {"error": "No answers provided"}

    def test_rejects_empty_answers_list(
        self,
        api_client,
        test_user,
        quiz_submit_url,
        quiz_content,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            quiz_submit_url,
            {"answers": []},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {"error": "No answers provided"}

        assert not QuizAttempt.objects.filter(
            enrollment__user=test_user,
            quiz=quiz_content,
        ).exists()

    def test_rejects_invalid_answer_payload(
        self,
        api_client,
        test_user,
        quiz_submit_url,
        quiz_content,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            quiz_submit_url,
            {
                "answers": [
                    {
                        "questionId": "invalid",
                    }
                ]
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "errors" in response.data

        assert not QuizAttempt.objects.filter(
            enrollment__user=test_user,
            quiz=quiz_content,
        ).exists()

    def test_submits_correct_single_choice_answer(
        self,
        api_client,
        test_user,
        enrollment,
        lesson,
        single_choice_question,
        single_choice_choices,
    ):
        api_client.force_authenticate(user=test_user)

        correct_choice, _ = single_choice_choices

        url = reverse(
            "enrollment_api:quiz_submit",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lesson.id,
            },
        )

        response = api_client.post(
            url,
            {
                "answers": [
                    {
                        "questionId": single_choice_question.id,
                        "questionType": "single_choice",
                        "selectedValues": [correct_choice.id],
                    }
                ]
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["score"] == 1
        assert response.data["totalQuestions"] == 1
        assert response.data["percentage"] == 100.0
        assert response.data["passed"] is True
        assert response.data["passScore"] == 70
        assert response.data["questionResults"][0]["questionId"] == (
            single_choice_question.id
        )
        assert response.data["questionResults"][0]["isCorrect"] is True
        assert response.data["questionResults"][0]["correctAnswer"] == ["Python"]
        assert response.data["questionResults"][0]["userAnswer"] == ["Python"]

        attempt = QuizAttempt.objects.get(
            enrollment=enrollment,
            quiz=single_choice_question.quiz,
        )

        assert attempt.attempt_number == 1
        assert attempt.score == 100

        answer = QuizAnswer.objects.get(
            attempt=attempt,
            question=single_choice_question,
        )

        assert list(answer.selected_choices.values_list("id", flat=True)) == [
            correct_choice.id
        ]

    def test_submits_incorrect_single_choice_answer(
        self,
        api_client,
        test_user,
        enrollment,
        lesson,
        single_choice_question,
        single_choice_choices,
    ):
        api_client.force_authenticate(user=test_user)

        _, incorrect_choice = single_choice_choices

        url = reverse(
            "enrollment_api:quiz_submit",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lesson.id,
            },
        )

        response = api_client.post(
            url,
            {
                "answers": [
                    {
                        "questionId": single_choice_question.id,
                        "questionType": "single_choice",
                        "selectedValues": [incorrect_choice.id],
                    }
                ]
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["score"] == 0
        assert response.data["percentage"] == 0.0
        assert response.data["passed"] is False
        assert response.data["questionResults"][0]["isCorrect"] is False
        assert response.data["questionResults"][0]["correctAnswer"] == ["Python"]
        assert response.data["questionResults"][0]["userAnswer"] == ["Java"]

        attempt = QuizAttempt.objects.get(
            enrollment=enrollment,
            quiz=single_choice_question.quiz,
        )
        assert attempt.score == 0

    def test_single_choice_requires_exact_correct_choice_set(
        self,
        api_client,
        test_user,
        enrollment,
        lesson,
        single_choice_question,
        single_choice_choices,
    ):
        api_client.force_authenticate(user=test_user)

        correct_choice, incorrect_choice = single_choice_choices

        url = reverse(
            "enrollment_api:quiz_submit",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lesson.id,
            },
        )

        response = api_client.post(
            url,
            {
                "answers": [
                    {
                        "questionId": single_choice_question.id,
                        "questionType": "single_choice",
                        "selectedValues": [
                            correct_choice.id,
                            incorrect_choice.id,
                        ],
                    }
                ]
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["questionResults"][0]["isCorrect"] is False
        assert response.data["score"] == 0

    def test_submits_correct_multiple_choice_answer(
        self,
        api_client,
        test_user,
        enrollment,
        lesson,
        multiple_choice_question,
        multiple_choice_choices,
    ):
        api_client.force_authenticate(user=test_user)

        django, flask, _ = multiple_choice_choices

        url = reverse(
            "enrollment_api:quiz_submit",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lesson.id,
            },
        )

        response = api_client.post(
            url,
            {
                "answers": [
                    {
                        "questionId": multiple_choice_question.id,
                        "questionType": "multiple_choice",
                        "selectedValues": [django.id, flask.id],
                    }
                ]
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["score"] == 1
        assert response.data["percentage"] == 100.0
        assert response.data["passed"] is True

        result = response.data["questionResults"][0]

        assert result["isCorrect"] is True
        assert set(result["correctAnswer"]) == {"Django", "Flask"}
        assert set(result["userAnswer"]) == {"Django", "Flask"}

    def test_multiple_choice_rejects_missing_correct_choice(
        self,
        api_client,
        test_user,
        enrollment,
        lesson,
        multiple_choice_question,
        multiple_choice_choices,
    ):
        api_client.force_authenticate(user=test_user)

        django, _, _ = multiple_choice_choices

        url = reverse(
            "enrollment_api:quiz_submit",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lesson.id,
            },
        )

        response = api_client.post(
            url,
            {
                "answers": [
                    {
                        "questionId": multiple_choice_question.id,
                        "questionType": "multiple_choice",
                        "selectedValues": [django.id],
                    }
                ]
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["questionResults"][0]["isCorrect"] is False
        assert response.data["score"] == 0

    def test_submits_correct_true_false_answer(
        self,
        api_client,
        test_user,
        enrollment,
        lesson,
        true_false_question,
        boolean_answer,
    ):
        api_client.force_authenticate(user=test_user)

        url = reverse(
            "enrollment_api:quiz_submit",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lesson.id,
            },
        )

        response = api_client.post(
            url,
            {
                "answers": [
                    {
                        "questionId": true_false_question.id,
                        "questionType": "true_false",
                        "boolValue": True,
                    }
                ]
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["score"] == 1
        assert response.data["percentage"] == 100.0
        assert response.data["passed"] is True

        result = response.data["questionResults"][0]

        assert result["questionId"] == true_false_question.id
        assert result["isCorrect"] is True
        assert result["correctAnswer"] is True
        assert result["userAnswer"] is True

        attempt = QuizAttempt.objects.get(
            enrollment=enrollment,
            quiz=true_false_question.quiz,
        )

        answer = QuizAnswer.objects.get(
            attempt=attempt,
            question=true_false_question,
        )

        assert answer.bool_answer is True

    def test_submits_incorrect_true_false_answer(
        self,
        api_client,
        test_user,
        enrollment,
        lesson,
        true_false_question,
        boolean_answer,
    ):
        api_client.force_authenticate(user=test_user)

        url = reverse(
            "enrollment_api:quiz_submit",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lesson.id,
            },
        )

        response = api_client.post(
            url,
            {
                "answers": [
                    {
                        "questionId": true_false_question.id,
                        "questionType": "true_false",
                        "boolValue": False,
                    }
                ]
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["score"] == 0
        assert response.data["percentage"] == 0.0
        assert response.data["passed"] is False
        assert response.data["questionResults"][0]["isCorrect"] is False

    def test_submits_correct_short_answer_case_insensitively(
        self,
        api_client,
        test_user,
        enrollment,
        lesson,
        short_answer_question,
        accepted_answer,
    ):
        api_client.force_authenticate(user=test_user)

        url = reverse(
            "enrollment_api:quiz_submit",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lesson.id,
            },
        )

        response = api_client.post(
            url,
            {
                "answers": [
                    {
                        "questionId": short_answer_question.id,
                        "questionType": "short_answer",
                        "textAnswer": "  python  ",
                    }
                ]
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["score"] == 1
        assert response.data["percentage"] == 100.0
        assert response.data["passed"] is True

        result = response.data["questionResults"][0]

        assert result["questionId"] == short_answer_question.id
        assert result["isCorrect"] is True
        assert result["correctAnswer"] == "Python"
        assert result["userAnswer"] == "python"

        attempt = QuizAttempt.objects.get(
            enrollment=enrollment,
            quiz=short_answer_question.quiz,
        )

        answer = QuizAnswer.objects.get(
            attempt=attempt,
            question=short_answer_question,
        )

        assert answer.text_answer == "python"

    def test_submits_incorrect_short_answer(
        self,
        api_client,
        test_user,
        enrollment,
        lesson,
        short_answer_question,
        accepted_answer,
    ):
        api_client.force_authenticate(user=test_user)

        url = reverse(
            "enrollment_api:quiz_submit",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lesson.id,
            },
        )

        response = api_client.post(
            url,
            {
                "answers": [
                    {
                        "questionId": short_answer_question.id,
                        "questionType": "short_answer",
                        "textAnswer": "Java",
                    }
                ]
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["score"] == 0
        assert response.data["percentage"] == 0.0
        assert response.data["passed"] is False
        assert response.data["questionResults"][0]["isCorrect"] is False

    def test_multiple_accepted_short_answers_are_supported(
        self,
        api_client,
        test_user,
        enrollment,
        lesson,
        short_answer_question,
        accepted_answer,
    ):
        AcceptedAnswer.objects.create(
            question=short_answer_question,
            answer="python3",
        )

        api_client.force_authenticate(user=test_user)

        url = reverse(
            "enrollment_api:quiz_submit",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lesson.id,
            },
        )

        response = api_client.post(
            url,
            {
                "answers": [
                    {
                        "questionId": short_answer_question.id,
                        "questionType": "short_answer",
                        "textAnswer": "PYTHON3",
                    }
                ]
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["questionResults"][0]["isCorrect"] is True

    def test_marks_lesson_completed_when_quiz_is_passed(
        self,
        api_client,
        test_user,
        enrollment,
        lesson,
        single_choice_question,
        single_choice_choices,
    ):
        api_client.force_authenticate(user=test_user)

        correct_choice, _ = single_choice_choices

        url = reverse(
            "enrollment_api:quiz_submit",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lesson.id,
            },
        )

        response = api_client.post(
            url,
            {
                "answers": [
                    {
                        "questionId": single_choice_question.id,
                        "questionType": "single_choice",
                        "selectedValues": [correct_choice.id],
                    }
                ]
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["passed"] is True
        assert response.data["lessonCompleted"] is True

        lesson_progress = LessonProgress.objects.get(
            lesson=lesson,
            enrollment=enrollment,
        )

        assert lesson_progress.status == LessonProgress.Status.COMPLETED
        assert lesson_progress.completed_at is not None

    def test_does_not_complete_lesson_when_quiz_is_failed(
        self,
        api_client,
        test_user,
        enrollment,
        lesson,
        single_choice_question,
        single_choice_choices,
    ):
        api_client.force_authenticate(user=test_user)

        _, incorrect_choice = single_choice_choices

        url = reverse(
            "enrollment_api:quiz_submit",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lesson.id,
            },
        )

        response = api_client.post(
            url,
            {
                "answers": [
                    {
                        "questionId": single_choice_question.id,
                        "questionType": "single_choice",
                        "selectedValues": [incorrect_choice.id],
                    }
                ]
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["passed"] is False
        assert response.data["lessonCompleted"] is False

        assert not LessonProgress.objects.filter(
            lesson=lesson,
            enrollment=enrollment,
            status=LessonProgress.Status.COMPLETED,
        ).exists()

    def test_already_completed_lesson_remains_completed_after_failed_attempt(
        self,
        api_client,
        test_user,
        enrollment,
        lesson,
        single_choice_question,
        single_choice_choices,
    ):
        lesson_progress = LessonProgress.objects.create(
            lesson=lesson,
            enrollment=enrollment,
            status=LessonProgress.Status.COMPLETED,
        )

        api_client.force_authenticate(user=test_user)

        _, incorrect_choice = single_choice_choices

        url = reverse(
            "enrollment_api:quiz_submit",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lesson.id,
            },
        )

        response = api_client.post(
            url,
            {
                "answers": [
                    {
                        "questionId": single_choice_question.id,
                        "questionType": "single_choice",
                        "selectedValues": [incorrect_choice.id],
                    }
                ]
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["passed"] is False
        assert response.data["lessonCompleted"] is True

        lesson_progress.refresh_from_db()
        assert lesson_progress.status == LessonProgress.Status.COMPLETED

    def test_creates_first_attempt_with_attempt_number_one(
        self,
        api_client,
        test_user,
        enrollment,
        lesson,
        single_choice_question,
        single_choice_choices,
    ):
        api_client.force_authenticate(user=test_user)

        correct_choice, _ = single_choice_choices

        url = reverse(
            "enrollment_api:quiz_submit",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lesson.id,
            },
        )

        response = api_client.post(
            url,
            {
                "answers": [
                    {
                        "questionId": single_choice_question.id,
                        "questionType": "single_choice",
                        "selectedValues": [correct_choice.id],
                    }
                ]
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        attempt = QuizAttempt.objects.get(
            enrollment=enrollment,
            quiz=single_choice_question.quiz,
        )

        assert attempt.attempt_number == 1

    def test_increments_attempt_number(
        self,
        api_client,
        test_user,
        enrollment,
        lesson,
        quiz_content,
        single_choice_question,
        single_choice_choices,
    ):
        QuizAttempt.objects.create(
            enrollment=enrollment,
            quiz=quiz_content,
            attempt_number=1,
            score=50,
        )

        api_client.force_authenticate(user=test_user)

        correct_choice, _ = single_choice_choices

        url = reverse(
            "enrollment_api:quiz_submit",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lesson.id,
            },
        )

        response = api_client.post(
            url,
            {
                "answers": [
                    {
                        "questionId": single_choice_question.id,
                        "questionType": "single_choice",
                        "selectedValues": [correct_choice.id],
                    }
                ]
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        attempts = QuizAttempt.objects.filter(
            enrollment=enrollment,
            quiz=quiz_content,
        ).order_by("attempt_number")

        assert attempts.count() == 2
        assert [attempt.attempt_number for attempt in attempts] == [1, 2]

    def test_rejects_submission_when_max_attempts_reached(
        self,
        api_client,
        test_user,
        enrollment,
        lesson,
        quiz_content,
        single_choice_question,
        single_choice_choices,
    ):
        quiz_content.max_attempts = 2
        quiz_content.save(update_fields=["max_attempts"])

        QuizAttempt.objects.create(
            enrollment=enrollment,
            quiz=quiz_content,
            attempt_number=1,
            score=50,
        )
        QuizAttempt.objects.create(
            enrollment=enrollment,
            quiz=quiz_content,
            attempt_number=2,
            score=80,
        )

        api_client.force_authenticate(user=test_user)

        correct_choice, _ = single_choice_choices

        url = reverse(
            "enrollment_api:quiz_submit",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lesson.id,
            },
        )

        response = api_client.post(
            url,
            {
                "answers": [
                    {
                        "questionId": single_choice_question.id,
                        "questionType": "single_choice",
                        "selectedValues": [correct_choice.id],
                    }
                ]
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False
        assert response.data["max_attempts"] == 2
        assert response.data["attempts_used"] == 2
        assert response.data["attempts_remaining"] == 0
        assert response.data["best_score"] == 80
        assert response.data["message"] == "Maximum attempts (2) reached"

        assert (
            QuizAttempt.objects.filter(
                enrollment=enrollment,
                quiz=quiz_content,
            ).count()
            == 2
        )

    def test_zero_max_attempts_allows_unlimited_attempts(
        self,
        api_client,
        test_user,
        enrollment,
        lesson,
        quiz_content,
        single_choice_question,
        single_choice_choices,
    ):
        quiz_content.max_attempts = 0
        quiz_content.save(update_fields=["max_attempts"])

        QuizAttempt.objects.create(
            enrollment=enrollment,
            quiz=quiz_content,
            attempt_number=1,
            score=50,
        )

        api_client.force_authenticate(user=test_user)

        correct_choice, _ = single_choice_choices

        url = reverse(
            "enrollment_api:quiz_submit",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lesson.id,
            },
        )

        response = api_client.post(
            url,
            {
                "answers": [
                    {
                        "questionId": single_choice_question.id,
                        "questionType": "single_choice",
                        "selectedValues": [correct_choice.id],
                    }
                ]
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        assert (
            QuizAttempt.objects.filter(
                enrollment=enrollment,
                quiz=quiz_content,
            ).count()
            == 2
        )

    def test_only_quiz_main_content_is_used(
        self,
        api_client,
        test_user,
        enrollment,
        lesson,
        quiz_content,
        single_choice_question,
        single_choice_choices,
    ):
        quiz_content.content.is_main_content = False
        quiz_content.content.save(update_fields=["is_main_content"])

        api_client.force_authenticate(user=test_user)

        correct_choice, _ = single_choice_choices

        url = reverse(
            "enrollment_api:quiz_submit",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lesson.id,
            },
        )

        response = api_client.post(
            url,
            {
                "answers": [
                    {
                        "questionId": single_choice_question.id,
                        "questionType": "single_choice",
                        "selectedValues": [correct_choice.id],
                    }
                ]
            },
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_rejects_lesson_from_another_course(
        self,
        api_client,
        test_user,
        enrollment,
        another_user,
        category,
    ):
        another_course = Course.objects.create(
            title="Another Course",
            owner=another_user,
            category=category,
        )
        another_section = Section.objects.create(
            course=another_course,
            title="Another Section",
            order=1,
        )
        another_lesson = Lesson.objects.create(
            section=another_section,
            title="Another Quiz",
            slug="another-quiz",
            order=1,
        )

        api_client.force_authenticate(user=test_user)

        url = reverse(
            "enrollment_api:quiz_submit",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": another_lesson.id,
            },
        )

        response = api_client.post(
            url,
            {"answers": [{"questionId": 1}]},
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_rejects_non_quiz_lesson(
        self,
        api_client,
        test_user,
        enrollment,
        lesson,
    ):
        api_client.force_authenticate(user=test_user)

        url = reverse(
            "enrollment_api:quiz_submit",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lesson.id,
            },
        )

        response = api_client.post(
            url,
            {
                "answers": [
                    {
                        "questionId": 999999,
                        "questionType": "single_choice",
                        "selectedValues": [],
                    }
                ],
            },
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_does_not_accept_question_from_another_quiz(
        self,
        api_client,
        test_user,
        enrollment,
        lesson,
        quiz_content,
        single_choice_question,
        single_choice_choices,
        category,
        another_user,
    ):
        other_course = Course.objects.create(
            title="Other Course",
            owner=another_user,
            category=category,
        )
        other_section = Section.objects.create(
            course=other_course,
            title="Other Section",
            order=1,
        )
        other_lesson = Lesson.objects.create(
            section=other_section,
            title="Other Lesson",
            slug="other-lesson",
            order=1,
        )
        other_content = LessonContent.objects.create(
            lesson=other_lesson,
            title="Other Quiz",
            content_type=LessonContent.Type.QUIZ,
            order=1,
            is_main_content=True,
        )
        other_quiz = QuizContent.objects.create(
            content=other_content,
            passing_score=70,
            max_attempts=3,
        )
        other_question = Question.objects.create(
            quiz=other_quiz,
            text="Question from another quiz",
            question_type=Question.Type.TRUE_FALSE,
            order=1,
        )
        BooleanAnswer.objects.create(
            question=other_question,
            answer=True,
        )

        api_client.force_authenticate(user=test_user)

        correct_choice, _ = single_choice_choices

        url = reverse(
            "enrollment_api:quiz_submit",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lesson.id,
            },
        )

        response = api_client.post(
            url,
            {
                "answers": [
                    {
                        "questionId": other_question.id,
                        "questionType": "true_false",
                        "boolValue": True,
                    },
                    {
                        "questionId": single_choice_question.id,
                        "questionType": "single_choice",
                        "selectedValues": [correct_choice.id],
                    },
                ]
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        assert response.data["totalQuestions"] == 1
        assert response.data["score"] == 1

        attempt = QuizAttempt.objects.get(
            enrollment=enrollment,
            quiz=quiz_content,
        )

        assert not QuizAnswer.objects.filter(
            attempt=attempt,
            question=other_question,
        ).exists()

    def test_returns_progress_data_for_course(
        self,
        api_client,
        test_user,
        enrollment,
        lesson,
        single_choice_question,
        single_choice_choices,
    ):
        second_lesson = Lesson.objects.create(
            section=lesson.section,
            title="Second Lesson",
            slug="second-lesson",
            order=2,
        )

        LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=second_lesson,
            status=LessonProgress.Status.COMPLETED,
        )

        api_client.force_authenticate(user=test_user)

        correct_choice, _ = single_choice_choices

        url = reverse(
            "enrollment_api:quiz_submit",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lesson.id,
            },
        )

        response = api_client.post(
            url,
            {
                "answers": [
                    {
                        "questionId": single_choice_question.id,
                        "questionType": "single_choice",
                        "selectedValues": [correct_choice.id],
                    }
                ]
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_lessons"] == 2
        assert response.data["completedCount"] == 2
        assert response.data["overallProgress"] == 100

        assert set(response.data["completedLessons"]) == {
            lesson.id,
            second_lesson.id,
        }

    def test_hides_question_results_when_correct_answers_disabled(
        self,
        api_client,
        test_user,
        enrollment,
        lesson,
        quiz_content,
        single_choice_question,
        single_choice_choices,
    ):
        quiz_content.show_correct_answers = False
        quiz_content.save(update_fields=["show_correct_answers"])

        api_client.force_authenticate(user=test_user)

        correct_choice, _ = single_choice_choices

        url = reverse(
            "enrollment_api:quiz_submit",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lesson.id,
            },
        )

        response = api_client.post(
            url,
            {
                "answers": [
                    {
                        "questionId": single_choice_question.id,
                        "questionType": "single_choice",
                        "selectedValues": [correct_choice.id],
                    }
                ]
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["includeCorrectAnswers"] is False
        assert response.data["questionResults"] == []

    def test_includes_question_results_when_correct_answers_enabled(
        self,
        api_client,
        test_user,
        enrollment,
        lesson,
        quiz_content,
        single_choice_question,
        single_choice_choices,
    ):
        quiz_content.show_correct_answers = True
        quiz_content.save(update_fields=["show_correct_answers"])

        api_client.force_authenticate(user=test_user)

        correct_choice, _ = single_choice_choices

        url = reverse(
            "enrollment_api:quiz_submit",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lesson.id,
            },
        )

        response = api_client.post(
            url,
            {
                "answers": [
                    {
                        "questionId": single_choice_question.id,
                        "questionType": "single_choice",
                        "selectedValues": [correct_choice.id],
                    }
                ]
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["includeCorrectAnswers"] is True
        assert len(response.data["questionResults"]) == 1

    def test_creates_one_quiz_answer_per_question(
        self,
        api_client,
        test_user,
        enrollment,
        lesson,
        single_choice_question,
        single_choice_choices,
        true_false_question,
        boolean_answer,
        short_answer_question,
        accepted_answer,
    ):
        api_client.force_authenticate(user=test_user)

        correct_choice, _ = single_choice_choices

        url = reverse(
            "enrollment_api:quiz_submit",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lesson.id,
            },
        )

        response = api_client.post(
            url,
            {
                "answers": [
                    {
                        "questionId": single_choice_question.id,
                        "questionType": "single_choice",
                        "selectedValues": [correct_choice.id],
                    },
                    {
                        "questionId": true_false_question.id,
                        "questionType": "true_false",
                        "boolValue": True,
                    },
                    {
                        "questionId": short_answer_question.id,
                        "questionType": "short_answer",
                        "textAnswer": "Python",
                    },
                ]
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        attempt = QuizAttempt.objects.get(
            enrollment=enrollment,
            quiz=single_choice_question.quiz,
        )

        assert QuizAnswer.objects.filter(attempt=attempt).count() == 3

        assert set(
            QuizAnswer.objects.filter(attempt=attempt).values_list(
                "question_id",
                flat=True,
            )
        ) == {
            single_choice_question.id,
            true_false_question.id,
            short_answer_question.id,
        }

    def test_calculates_score_from_processed_questions(
        self,
        api_client,
        test_user,
        enrollment,
        lesson,
        quiz_content,
        single_choice_question,
        single_choice_choices,
        true_false_question,
        boolean_answer,
        short_answer_question,
        accepted_answer,
    ):
        api_client.force_authenticate(user=test_user)

        correct_choice, incorrect_choice = single_choice_choices

        url = reverse(
            "enrollment_api:quiz_submit",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lesson.id,
            },
        )

        response = api_client.post(
            url,
            {
                "answers": [
                    {
                        "questionId": single_choice_question.id,
                        "questionType": "single_choice",
                        "selectedValues": [correct_choice.id],
                    },
                    {
                        "questionId": true_false_question.id,
                        "questionType": "true_false",
                        "boolValue": False,
                    },
                    {
                        "questionId": short_answer_question.id,
                        "questionType": "short_answer",
                        "textAnswer": "Python",
                    },
                ]
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["totalQuestions"] == 3
        assert response.data["score"] == 2
        assert response.data["percentage"] == pytest.approx(66.67)
        assert response.data["passed"] is False

        attempt = QuizAttempt.objects.get(
            enrollment=enrollment,
            quiz=quiz_content,
        )

        assert attempt.score == Decimal("66.67")

    def test_rejects_nonexistent_lesson(
        self,
        api_client,
        test_user,
        enrollment,
    ):
        api_client.force_authenticate(user=test_user)

        url = reverse(
            "enrollment_api:quiz_submit",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": 999999,
            },
        )

        response = api_client.post(
            url,
            {"answers": []},
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_submission_is_atomic_when_answer_processing_fails(
        self,
        api_client,
        test_user,
        enrollment,
        lesson,
        quiz_content,
        single_choice_question,
        single_choice_choices,
        monkeypatch,
    ):
        api_client.force_authenticate(user=test_user)

        correct_choice, _ = single_choice_choices

        def raise_error(*args, **kwargs):
            raise ValueError("processing failed")

        from enrollments.api.views import QuizSubmitApiView

        monkeypatch.setattr(
            QuizSubmitApiView,
            "process_answers",
            raise_error,
        )

        url = reverse(
            "enrollment_api:quiz_submit",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lesson.id,
            },
        )

        with pytest.raises(ValueError, match="processing failed"):
            api_client.post(
                url,
                {
                    "answers": [
                        {
                            "questionId": single_choice_question.id,
                            "questionType": "single_choice",
                            "selectedValues": [correct_choice.id],
                        }
                    ]
                },
                format="json",
            )

        assert not QuizAttempt.objects.filter(
            enrollment=enrollment,
            quiz=quiz_content,
        ).exists()

    def test_short_answer_without_accepted_answer_is_marked_incorrect(
        self,
        api_client,
        test_user,
        enrollment,
        quiz_content,
        short_answer_question,
        quiz_submit_url,
    ):
        api_client.force_authenticate(user=test_user)

        # Ensure the question has no accepted answers.
        AcceptedAnswer.objects.filter(
            question=short_answer_question,
        ).delete()

        response = api_client.post(
            quiz_submit_url,
            {
                "answers": [
                    {
                        "questionId": short_answer_question.id,
                        "questionType": "short_answer",
                        "textAnswer": "Python",
                    }
                ]
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["score"] == 0
        assert response.data["totalQuestions"] == 1
        assert response.data["percentage"] == 0
        assert response.data["passed"] is False

        question_result = response.data["questionResults"][0]

        assert question_result["questionId"] == short_answer_question.id
        assert question_result["isCorrect"] is False
        assert question_result["correctAnswer"] == ""
        assert question_result["userAnswer"] == "Python"
        assert question_result["questionType"] == "short_answer"

        attempt = QuizAttempt.objects.get(
            enrollment=enrollment,
            quiz=quiz_content,
        )

        answer = QuizAnswer.objects.get(
            attempt=attempt,
            question=short_answer_question,
        )

        assert answer.text_answer == "Python"
