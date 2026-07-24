import factory

from certificates.models import Certificate, CertificateTemplate
from courses.tests.factories import CourseFactory
from enrollments.tests.factories import EnrollmentFactory
from utils.test.files import file_field


class CertificateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Certificate

    enrollment = factory.SubFactory(
        EnrollmentFactory,
    )

    certificate_number = factory.Sequence(lambda n: f"CERT-{n:06d}")

    verification_code = factory.Faker(
        "uuid4",
    )

    file = factory.LazyFunction(
        lambda: file_field(
            name="certificate.pdf",
            content=b"certificate",
        )
    )


class CertificateTemplateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CertificateTemplate

    course = factory.SubFactory(CourseFactory)

    name = factory.Sequence(lambda n: f"Certificate Template {n}")

    version = 1

    background = factory.LazyFunction(
        lambda: file_field(
            name="certificate_template.pdf",
            content=b"certificate template",
        )
    )

    is_active = False

    class Params:
        active = factory.Trait(
            is_active=True,
        )

        global_template = factory.Trait(
            course=None,
        )
