import datetime

import factory

from courses.tests.factories import CourseFactory
from curriculums.models import Lesson, Section


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
    lesson_type = Lesson.Type.VIDEO
    duration = datetime.timedelta(minutes=15)
    order = factory.Sequence(lambda n: n + 1)
    is_published = False
    is_preview = False
    completion_criteria = Lesson.CompletionCriteria.MANUAL
