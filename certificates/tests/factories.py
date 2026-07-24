import factory

from certificates.models import Certificate
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
