import pytest
from django.db import IntegrityError

from certificates.models import Certificate
from certificates.tests.factories import CertificateFactory
from enrollments.tests.factories import EnrollmentFactory
from utils.test.files import file_field


@pytest.mark.django_db
class TestCertificateModel:
    """Tests for the Certificate model."""

    @pytest.fixture
    def enrollment(self):
        return EnrollmentFactory()

    def test_create_certificate(self, enrollment):
        """A certificate can be created."""
        certificate = Certificate.objects.create(
            enrollment=enrollment,
            certificate_number="CERT-2026-0001",
            verification_code="abc123xyz456",
            file=file_field(
                name="certificate.pdf",
                content=b"certificate",
            ),
        )

        assert certificate.enrollment == enrollment
        assert certificate.certificate_number == "CERT-2026-0001"
        assert certificate.verification_code == "abc123xyz456"
        assert certificate.file.name.endswith("certificate.pdf")
        assert certificate.issued_at is not None

    def test_string_representation(self):
        """String representation includes user and course."""
        certificate = CertificateFactory()

        assert (
            str(certificate) == f"{certificate.enrollment.user} - "
            f"{certificate.enrollment.course}"
        )

    def test_enrollment_can_have_only_one_certificate(
        self,
        enrollment,
    ):
        """Each enrollment can have only one certificate."""
        CertificateFactory(
            enrollment=enrollment,
        )

        with pytest.raises(IntegrityError):
            CertificateFactory(
                enrollment=enrollment,
            )

    def test_certificate_number_must_be_unique(self):
        """Certificate number must be unique."""
        CertificateFactory(
            certificate_number="CERT-0001",
        )

        with pytest.raises(IntegrityError):
            CertificateFactory(
                certificate_number="CERT-0001",
            )

    def test_verification_code_must_be_unique(self):
        """Verification code must be unique."""
        CertificateFactory(
            verification_code="verify-123",
        )

        with pytest.raises(IntegrityError):
            CertificateFactory(
                verification_code="verify-123",
            )

    def test_deleting_enrollment_deletes_certificate(self):
        """Deleting an enrollment cascades to its certificate."""
        certificate = CertificateFactory()

        enrollment = certificate.enrollment

        enrollment.delete()

        assert not Certificate.objects.filter(
            pk=certificate.pk,
        ).exists()

    def test_certificates_are_ordered_by_issue_date_descending(self):
        """Newest certificates appear first."""
        older = CertificateFactory()
        newer = CertificateFactory()

        certificates = list(Certificate.objects.all())

        assert certificates == [
            newer,
            older,
        ]
