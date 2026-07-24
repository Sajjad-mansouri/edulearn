import datetime

import factory
from django.utils import timezone

from accounts.tests.factories import UserFactory
from courses.tests.factories import CourseFactory
from curriculums.tests.factories import (
    LessonContentFactory,
    LessonFactory,
    SectionFactory,
)
from enrollments.models import (
    Enrollment,
    LessonContentProgress,
    LessonProgress,
    SectionProgress,
)


class EnrollmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Enrollment

    user = factory.SubFactory(UserFactory)

    course = factory.SubFactory(CourseFactory)

    status = Enrollment.Status.ACTIVE

    completed_at = None

    class Params:
        completed = factory.Trait(
            status=Enrollment.Status.COMPLETED,
            completed_at=factory.Faker("date_time_this_year", tzinfo=None),
        )

        cancelled = factory.Trait(
            status=Enrollment.Status.CANCELLED,
        )

        suspended = factory.Trait(
            status=Enrollment.Status.SUSPENDED,
        )


class LessonContentProgressFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LessonContentProgress

    enrollment = factory.SubFactory(EnrollmentFactory)

    content = factory.SubFactory(LessonContentFactory)

    status = LessonContentProgress.Status.NOT_STARTED

    watch_percentage = 0

    resume_position = None

    started_at = None

    completed_at = None

    class Params:
        in_progress = factory.Trait(
            status=LessonContentProgress.Status.IN_PROGRESS,
            started_at=factory.LazyFunction(timezone.now),
            watch_percentage=50,
            resume_position=datetime.timedelta(minutes=10),
        )

        completed = factory.Trait(
            status=LessonContentProgress.Status.COMPLETED,
            started_at=factory.LazyFunction(timezone.now),
            completed_at=factory.LazyFunction(timezone.now),
            watch_percentage=100,
        )


class LessonProgressFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LessonProgress

    enrollment = factory.SubFactory(EnrollmentFactory)
    lesson = factory.SubFactory(LessonFactory)

    status = LessonProgress.Status.NOT_STARTED
    progress_percentage = 0

    started_at = None
    completed_at = None

    class Params:
        in_progress = factory.Trait(
            status=LessonProgress.Status.IN_PROGRESS,
            progress_percentage=50,
            started_at=factory.LazyFunction(timezone.now),
        )

        completed = factory.Trait(
            status=LessonProgress.Status.COMPLETED,
            progress_percentage=100,
            started_at=factory.LazyFunction(timezone.now),
            completed_at=factory.LazyFunction(timezone.now),
        )


class SectionProgressFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SectionProgress

    enrollment = factory.SubFactory(EnrollmentFactory)
    section = factory.SubFactory(SectionFactory)

    status = SectionProgress.Status.NOT_STARTED
    progress_percentage = 0

    started_at = None
    completed_at = None

    class Params:
        in_progress = factory.Trait(
            status=SectionProgress.Status.IN_PROGRESS,
            progress_percentage=50,
            started_at=factory.LazyFunction(timezone.now),
        )

        completed = factory.Trait(
            status=SectionProgress.Status.COMPLETED,
            progress_percentage=100,
            started_at=factory.LazyFunction(timezone.now),
            completed_at=factory.LazyFunction(timezone.now),
        )
