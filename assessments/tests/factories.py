import factory
from django.utils import timezone

from assessments.models import (
    AcceptedAnswer,
    Choice,
    Question,
    QuizAttempt,
    QuizContent,
)
from curriculums.tests.factories import LessonContentFactory
from enrollments.tests.factories import EnrollmentFactory


class QuizContentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = QuizContent

    content = factory.SubFactory(LessonContentFactory)

    instructions = factory.Faker(
        "paragraph",
        nb_sentences=3,
    )

    passing_score = 70

    time_limit = 30

    max_attempts = 1

    shuffle_questions = False

    shuffle_choices = False

    show_correct_answers = True


class QuestionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Question

    quiz = factory.SubFactory(QuizContentFactory)

    text = factory.Sequence(lambda n: f"What is question {n}?")

    question_type = Question.Type.SINGLE_CHOICE

    order = factory.Sequence(lambda n: n + 1)

    points = 1

    explanation = factory.Faker("sentence")


class ChoiceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Choice

    question = factory.SubFactory(QuestionFactory)
    text = factory.Sequence(lambda n: f"Choice {n}")
    is_correct = False
    order = factory.Sequence(lambda n: n + 1)


class AcceptedAnswerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AcceptedAnswer

    question = factory.SubFactory(QuestionFactory)

    answer = factory.Sequence(lambda n: f"answer_{n}")


class QuizAttemptFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = QuizAttempt

    enrollment = factory.SubFactory(EnrollmentFactory)

    quiz = factory.SubFactory(QuizContentFactory)

    attempt_number = 1
    score = 0

    started_at = factory.LazyFunction(timezone.now)
    submitted_at = None
