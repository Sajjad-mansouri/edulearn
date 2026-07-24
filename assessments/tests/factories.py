import factory

from assessments.models import (
    AcceptedAnswer,
    Choice,
    Question,
    QuizContent,
)
from curriculums.tests.factories import LessonContentFactory


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
