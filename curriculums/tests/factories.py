import datetime

import factory

from courses.tests.factories import CourseFactory
from curriculums.models import (
    AcceptedAnswer,
    ArticleContent,
    Choice,
    FileContent,
    Lesson,
    LessonContent,
    Question,
    QuizContent,
    Section,
    VideoContent,
)
from utils.test.files import file_field


class SectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Section

    course = factory.SubFactory(CourseFactory)
    title = factory.Sequence(lambda n: f"Section {n}")
    description = factory.Faker("paragraph")
    order = factory.Sequence(lambda n: n + 1)
    is_published = False
    estimated_duration = datetime.timedelta(minutes=30)


class LessonFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Lesson

    section = factory.SubFactory(SectionFactory)
    title = factory.Sequence(lambda n: f"Lesson {n}")
    slug = factory.LazyAttribute(lambda obj: obj.title.lower().replace(" ", "-"))
    duration = datetime.timedelta(minutes=15)
    order = factory.Sequence(lambda n: n + 1)
    is_published = False
    is_preview = False
    completion_criteria = Lesson.CompletionCriteria.MANUAL


class LessonContentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LessonContent

    lesson = factory.SubFactory(LessonFactory)
    title = factory.Sequence(lambda n: f"Content {n}")
    content_type = LessonContent.Type.VIDEO
    order = factory.Sequence(lambda n: n + 1)
    is_published = False


class VideoContentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = VideoContent

    content = factory.SubFactory(LessonContentFactory)

    source = VideoContent.Source.FILE

    uploaded_video = factory.LazyFunction(
        lambda: file_field(
            "video.mp4",
            b"video-content",
        )
    )

    external_url = ""

    duration = datetime.timedelta(minutes=10)

    transcript = factory.Faker("paragraph")

    captions = factory.LazyFunction(
        lambda: file_field(
            "captions.vtt",
            b"WEBVTT",
        )
    )

    class Params:
        external = factory.Trait(
            source=VideoContent.Source.URL,
            uploaded_video=None,
            captions=None,
            external_url="https://www.youtube.com/watch?v=test_video",
        )


class FileContentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FileContent

    content = factory.SubFactory(LessonContentFactory)

    file = factory.LazyFunction(
        lambda: file_field(
            "document.pdf",
            b"test file",
            content_type="application/pdf",
        )
    )

    display_name = factory.Sequence(lambda n: f"Document {n}")

    description = factory.Faker("paragraph")

    is_downloadable = True


class ArticleContentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ArticleContent

    content = factory.SubFactory(LessonContentFactory)

    body = factory.Faker("paragraph", nb_sentences=10)

    estimated_read_time = 5


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
