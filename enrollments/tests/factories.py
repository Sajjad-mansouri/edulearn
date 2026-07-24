import factory

from accounts.tests.factories import UserFactory
from courses.tests.factories import CourseFactory
from enrollments.models import Enrollment


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
