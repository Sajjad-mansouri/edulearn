import datetime

import factory
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile

from courses.tests.factories import CourseFactory
from curriculums.models import (
    ArticleContent,
    Attachment,
    FileContent,
    Lesson,
    LessonContent,
    Section,
    VideoCaption,
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
    duration = datetime.timedelta(minutes=30)


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

    video_file = factory.LazyFunction(
        lambda: file_field(
            "video.mp4",
            b"video-content",
        )
    )

    external_url = ""

    duration = datetime.timedelta(minutes=10)

    transcript = factory.Faker("paragraph")

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


class VideoCaptionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = VideoCaption

    video = factory.SubFactory(VideoContentFactory)

    language = factory.Sequence(lambda n: f"lang{n}")

    label = factory.LazyAttribute(lambda obj: obj.language.upper())

    @factory.lazy_attribute
    def file(self):
        extension = self.file_format

        return ContentFile(
            b"WEBVTT\n\n00:00:00.000 --> 00:00:02.000\nHello World",
            name=f"caption.{extension}",
        )

    file_format = VideoCaption.Format.VTT

    is_default = False


class AttachmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Attachment

    course = factory.SubFactory(CourseFactory)
    lesson_content = None

    title = factory.Sequence(lambda n: f"Attachment {n}")

    description = ""

    file = factory.LazyFunction(
        lambda: SimpleUploadedFile(
            "attachment.pdf",
            b"Dummy attachment content",
            content_type="application/pdf",
        )
    )

    file_url = ""

    is_downloadable = True
