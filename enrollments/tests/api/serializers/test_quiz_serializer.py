import pytest

from assessments.models import Choice, Question, QuizContent
from curriculums.models import Lesson, LessonContent, Section
from enrollments.api.serializers.quiz import (
    ChoiceSerializer,
    QuestionSerializer,
    QuizSerializer,
    QuizSubmission,
)


@pytest.fixture
def quiz_section(course):
    return Section.objects.create(
        course=course,
        title="Quiz Section",
        order=1,
    )


@pytest.fixture
def quiz_lesson(quiz_section):
    return Lesson.objects.create(
        section=quiz_section,
        title="Quiz Lesson",
        slug="quiz-lesson",
        order=1,
    )


@pytest.fixture
def quiz_lesson_content(quiz_lesson):
    return LessonContent.objects.create(
        lesson=quiz_lesson,
        title="Python Quiz",
        content_type=LessonContent.Type.QUIZ,
        order=1,
        is_main_content=True,
    )


@pytest.fixture
def quiz_content(quiz_lesson_content):
    return QuizContent.objects.create(
        content=quiz_lesson_content,
        instructions="Answer all questions.",
        passing_score=70,
        time_limit=30,
        max_attempts=3,
        shuffle_questions=False,
        shuffle_choices=False,
        show_correct_answers=True,
    )


@pytest.fixture
def question(quiz_content):
    return Question.objects.create(
        quiz=quiz_content,
        text="What is Python?",
        question_type=Question.Type.SINGLE_CHOICE,
        difficulty=Question.Difficulty.EASY,
        order=1,
        points=2,
        explanation="Python is a programming language.",
        is_required=True,
    )


@pytest.fixture
def choices(question):
    return Choice.objects.bulk_create(
        [
            Choice(
                question=question,
                text="A programming language",
                is_correct=True,
                order=1,
            ),
            Choice(
                question=question,
                text="A database",
                is_correct=False,
                order=2,
            ),
            Choice(
                question=question,
                text="An operating system",
                is_correct=False,
                order=3,
            ),
        ]
    )


@pytest.fixture
def second_question(quiz_content):
    return Question.objects.create(
        quiz=quiz_content,
        text="Which type represents true or false?",
        question_type=Question.Type.TRUE_FALSE,
        difficulty=Question.Difficulty.MEDIUM,
        order=2,
        points=1,
        explanation="True/false questions have two logical states.",
        is_required=True,
    )


@pytest.fixture
def second_question_choices(second_question):
    return Choice.objects.bulk_create(
        [
            Choice(
                question=second_question,
                text="True",
                is_correct=True,
                order=1,
            ),
            Choice(
                question=second_question,
                text="False",
                is_correct=False,
                order=2,
            ),
        ]
    )


@pytest.mark.django_db
class TestChoiceSerializer:
    def test_exposes_only_public_choice_fields(self):
        serializer = ChoiceSerializer()

        assert set(serializer.fields.keys()) == {"id", "text"}

    def test_does_not_expose_correct_answer_information(self):
        serializer = ChoiceSerializer()

        assert "is_correct" not in serializer.fields
        assert "order" not in serializer.fields
        assert "question" not in serializer.fields

    def test_serializes_choice(self, question):
        choice = Choice.objects.create(
            question=question,
            text="A programming language",
            is_correct=True,
            order=1,
        )

        data = ChoiceSerializer(choice).data

        assert data == {
            "id": choice.id,
            "text": "A programming language",
        }

    def test_serializes_choice_without_exposing_is_correct(
        self,
        question,
    ):
        choice = Choice.objects.create(
            question=question,
            text="A hidden-answer choice",
            is_correct=True,
            order=1,
        )

        data = ChoiceSerializer(choice).data

        assert data["id"] == choice.id
        assert data["text"] == "A hidden-answer choice"
        assert "is_correct" not in data

    def test_serializes_multiple_choices_in_model_order(
        self,
        question,
    ):
        first = Choice.objects.create(
            question=question,
            text="First choice",
            is_correct=False,
            order=1,
        )
        second = Choice.objects.create(
            question=question,
            text="Second choice",
            is_correct=True,
            order=2,
        )
        third = Choice.objects.create(
            question=question,
            text="Third choice",
            is_correct=False,
            order=3,
        )

        data = ChoiceSerializer(
            question.choices.all(),
            many=True,
        ).data

        assert data == [
            {
                "id": first.id,
                "text": "First choice",
            },
            {
                "id": second.id,
                "text": "Second choice",
            },
            {
                "id": third.id,
                "text": "Third choice",
            },
        ]


@pytest.mark.django_db
class TestQuestionSerializer:
    def test_exposes_expected_fields(self):
        serializer = QuestionSerializer()

        expected_fields = {
            "id",
            "text",
            "question_type",
            "explanation",
            "choices",
        }

        assert set(serializer.fields.keys()) == expected_fields

    def test_does_not_expose_unserialized_question_fields(self):
        serializer = QuestionSerializer()

        assert "difficulty" not in serializer.fields
        assert "points" not in serializer.fields
        assert "order" not in serializer.fields
        assert "is_required" not in serializer.fields
        assert "estimated_time" not in serializer.fields
        assert "quiz" not in serializer.fields

    def test_serializes_question_fields(
        self,
        question,
        choices,
    ):
        data = QuestionSerializer(question).data

        assert data["id"] == question.id
        assert data["text"] == question.text
        assert data["question_type"] == question.question_type
        assert data["explanation"] == question.explanation

    def test_serializes_nested_choices(
        self,
        question,
        choices,
    ):
        data = QuestionSerializer(question).data

        assert data["choices"] == [
            {
                "id": choices[0].id,
                "text": choices[0].text,
            },
            {
                "id": choices[1].id,
                "text": choices[1].text,
            },
            {
                "id": choices[2].id,
                "text": choices[2].text,
            },
        ]

    def test_nested_choices_do_not_expose_correct_answer(
        self,
        question,
        choices,
    ):
        data = QuestionSerializer(question).data

        for choice_data in data["choices"]:
            assert "is_correct" not in choice_data

    def test_serializes_question_without_choices(self, question):
        data = QuestionSerializer(question).data

        assert data["choices"] == []

    def test_serializes_multiple_questions_in_model_order(
        self,
        question,
        choices,
        second_question,
        second_question_choices,
    ):
        data = QuestionSerializer(
            Question.objects.filter(
                quiz=question.quiz,
            ),
            many=True,
        ).data

        assert [item["id"] for item in data] == [
            question.id,
            second_question.id,
        ]

        assert [item["text"] for item in data] == [
            question.text,
            second_question.text,
        ]


@pytest.mark.django_db
class TestQuizSerializer:
    def test_exposes_expected_fields(self):
        serializer = QuizSerializer()

        assert set(serializer.fields.keys()) == {
            "passing_score",
            "questions",
        }

    def test_does_not_expose_unserialized_quiz_fields(self):
        serializer = QuizSerializer()

        assert "content" not in serializer.fields
        assert "instructions" not in serializer.fields
        assert "time_limit" not in serializer.fields
        assert "max_attempts" not in serializer.fields
        assert "shuffle_questions" not in serializer.fields
        assert "shuffle_choices" not in serializer.fields
        assert "show_correct_answers" not in serializer.fields

    def test_serializes_passing_score(
        self,
        quiz_content,
    ):
        data = QuizSerializer(quiz_content).data

        assert data["passing_score"] == 70

    def test_serializes_nested_questions(
        self,
        quiz_content,
        question,
        choices,
        second_question,
        second_question_choices,
    ):
        data = QuizSerializer(quiz_content).data

        assert len(data["questions"]) == 2

        assert data["questions"][0]["id"] == question.id
        assert data["questions"][0]["text"] == question.text
        assert data["questions"][0]["question_type"] == (Question.Type.SINGLE_CHOICE)

        assert data["questions"][1]["id"] == second_question.id
        assert data["questions"][1]["text"] == second_question.text
        assert data["questions"][1]["question_type"] == (Question.Type.TRUE_FALSE)

    def test_nested_questions_include_nested_choices(
        self,
        quiz_content,
        question,
        choices,
        second_question,
        second_question_choices,
    ):
        data = QuizSerializer(quiz_content).data

        first_question = data["questions"][0]
        second_question_data = data["questions"][1]

        assert first_question["choices"] == [
            {
                "id": choices[0].id,
                "text": choices[0].text,
            },
            {
                "id": choices[1].id,
                "text": choices[1].text,
            },
            {
                "id": choices[2].id,
                "text": choices[2].text,
            },
        ]

        assert second_question_data["choices"] == [
            {
                "id": second_question_choices[0].id,
                "text": second_question_choices[0].text,
            },
            {
                "id": second_question_choices[1].id,
                "text": second_question_choices[1].text,
            },
        ]

    def test_does_not_expose_correct_answers_through_nested_questions(
        self,
        quiz_content,
        question,
        choices,
    ):
        data = QuizSerializer(quiz_content).data

        for question_data in data["questions"]:
            for choice_data in question_data["choices"]:
                assert "is_correct" not in choice_data

    def test_serializes_quiz_without_questions(self, quiz_content):
        data = QuizSerializer(quiz_content).data

        assert data["passing_score"] == 70
        assert data["questions"] == []

    @pytest.mark.parametrize(
        "passing_score",
        [0, 1, 50, 70, 100, None],
    )
    def test_serializes_valid_passing_score_values(
        self,
        quiz_content,
        passing_score,
    ):
        quiz_content.passing_score = passing_score

        data = QuizSerializer(quiz_content).data

        assert data["passing_score"] == passing_score


@pytest.mark.django_db
class TestQuizSubmission:
    def test_exposes_expected_fields(self):
        serializer = QuizSubmission()

        expected_fields = {
            "questionType",
            "boolValue",
            "textAnswer",
            "questionId",
            "selectedValues",
        }

        assert set(serializer.fields.keys()) == expected_fields

    def test_question_type_is_required(self):
        serializer = QuizSubmission(data={})

        assert not serializer.is_valid()

        assert "questionType" in serializer.errors

    @pytest.mark.parametrize(
        "question_type",
        [
            "single_choice",
            "short_answer",
            "true_false",
            "multiple_choice",
        ],
    )
    def test_accepts_supported_question_types(self, question_type):
        serializer = QuizSubmission(
            data={
                "questionType": question_type,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["questionType"] == question_type

    def test_rejects_unsupported_question_type(self):
        serializer = QuizSubmission(
            data={
                "questionType": "unsupported",
            }
        )

        assert not serializer.is_valid()

        assert "questionType" in serializer.errors

    def test_optional_fields_can_be_omitted(self):
        serializer = QuizSubmission(
            data={
                "questionType": "single_choice",
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["questionType"] == "single_choice"
        assert "boolValue" not in serializer.validated_data
        assert "textAnswer" not in serializer.validated_data
        assert "questionId" not in serializer.validated_data
        assert "selectedValues" not in serializer.validated_data

    def test_accepts_boolean_value(self):
        serializer = QuizSubmission(
            data={
                "questionType": "true_false",
                "boolValue": True,
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["boolValue"] is True

    def test_accepts_false_boolean_value(self):
        serializer = QuizSubmission(
            data={
                "questionType": "true_false",
                "boolValue": False,
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["boolValue"] is False

    def test_rejects_invalid_boolean_value(self):
        serializer = QuizSubmission(
            data={
                "questionType": "true_false",
                "boolValue": "not-a-boolean",
            }
        )

        assert not serializer.is_valid()

        assert "boolValue" in serializer.errors

    def test_accepts_text_answer(self):
        serializer = QuizSubmission(
            data={
                "questionType": "short_answer",
                "textAnswer": "Python",
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["textAnswer"] == "Python"

    def test_coerces_integer_text_answer_to_string(self):
        serializer = QuizSubmission(
            data={
                "questionType": "short_answer",
                "textAnswer": 123,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["textAnswer"] == "123"

    def test_accepts_question_id(self):
        serializer = QuizSubmission(
            data={
                "questionType": "single_choice",
                "questionId": 42,
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["questionId"] == 42

    def test_rejects_non_integer_question_id(self):
        serializer = QuizSubmission(
            data={
                "questionType": "single_choice",
                "questionId": "not-an-integer",
            }
        )

        assert not serializer.is_valid()

        assert "questionId" in serializer.errors

    def test_accepts_selected_values(self):
        serializer = QuizSubmission(
            data={
                "questionType": "multiple_choice",
                "selectedValues": [1, 3, 5],
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["selectedValues"] == [1, 3, 5]

    def test_accepts_empty_selected_values(self):
        serializer = QuizSubmission(
            data={
                "questionType": "multiple_choice",
                "selectedValues": [],
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["selectedValues"] == []

    def test_rejects_non_integer_selected_value(self):
        serializer = QuizSubmission(
            data={
                "questionType": "multiple_choice",
                "selectedValues": [1, "invalid", 3],
            }
        )

        assert not serializer.is_valid()

        assert "selectedValues" in serializer.errors

    def test_accepts_complete_submission_payload(self):
        data = {
            "questionType": "multiple_choice",
            "boolValue": False,
            "textAnswer": "Python",
            "questionId": 10,
            "selectedValues": [1, 3],
        }

        serializer = QuizSubmission(data=data)

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data == {
            "questionType": "multiple_choice",
            "boolValue": False,
            "textAnswer": "Python",
            "questionId": 10,
            "selectedValues": [1, 3],
        }

    def test_question_type_choices_are_case_sensitive(self):
        serializer = QuizSubmission(
            data={
                "questionType": "SINGLE_CHOICE",
            }
        )

        assert not serializer.is_valid()

        assert "questionType" in serializer.errors
