import datetime

import factory

from courses.tests.factories import CourseFactory
from curriculums.models import Section


class SectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Section

    course = factory.SubFactory(CourseFactory)
    title = factory.Sequence(lambda n: f"Section {n}")
    description = factory.Faker("paragraph")
    order = factory.Sequence(lambda n: n + 1)
    is_published = False
    estimated_duration = datetime.timedelta(minutes=30)
