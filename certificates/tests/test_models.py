import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from certificates.models import Certificate, CertificateTemplate
from certificates.tests.factories import CertificateFactory, CertificateTemplateFactory
from courses.tests.factories import CourseFactory
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


@pytest.mark.django_db
class TestCertificateTemplateModel:
    """Tests for the CertificateTemplate model."""

    @pytest.fixture
    def course(self):
        return CourseFactory()

    def test_create_certificate_template(self, course):
        """A certificate template can be created."""
        template = CertificateTemplate.objects.create(
            course=course,
            name="Default Template",
            version=1,
            background=file_field(
                name="template.pdf",
                content=b"pdf content",
            ),
            is_active=False,
        )

        assert template.course == course
        assert template.name == "Default Template"
        assert template.version == 1
        assert template.background.name.endswith("template.pdf")
        assert template.is_active is False
        assert template.created_at is not None
        assert template.updated_at is not None

    def test_string_representation(self):
        """String representation includes name and version."""
        template = CertificateTemplateFactory(
            name="Corporate",
            version=2,
        )

        assert str(template) == "Corporate v2"

    def test_course_is_optional(self):
        """A template may be global (not tied to a course)."""
        template = CertificateTemplate.objects.create(
            name="Global",
            background=file_field(),
        )

        assert template.course is None

    def test_version_defaults_to_one(self):
        """Version defaults to one."""
        template = CertificateTemplate.objects.create(
            name="Default",
            background=file_field(),
        )

        assert template.version == 1

    def test_is_active_defaults_to_false(self):
        """Templates are inactive by default."""
        template = CertificateTemplate.objects.create(
            name="Default",
            background=file_field(),
        )

        assert template.is_active is False

    def test_name_and_version_must_be_unique(self):
        """Name/version combination must be unique."""
        CertificateTemplateFactory(
            name="Default",
            version=1,
        )

        with pytest.raises(IntegrityError):
            CertificateTemplateFactory(
                name="Default",
                version=1,
            )

    def test_same_name_can_have_different_versions(self):
        """Different versions may reuse the same name."""
        template1 = CertificateTemplateFactory(
            name="Default",
            version=1,
        )

        template2 = CertificateTemplateFactory(
            name="Default",
            version=2,
        )

        assert template1.name == template2.name
        assert template1.version != template2.version

    def test_different_names_can_share_same_version(self):
        """Different template names may share the same version."""
        template1 = CertificateTemplateFactory(
            name="Default",
            version=1,
        )

        template2 = CertificateTemplateFactory(
            name="Corporate",
            version=1,
        )

        assert template1.version == template2.version

    def test_only_one_template_can_be_active(self):
        """Only one template may be active."""
        CertificateTemplateFactory(
            is_active=True,
        )

        template = CertificateTemplateFactory.build(
            is_active=True,
        )

        with pytest.raises(ValidationError):
            template.full_clean()

    def test_active_template_can_be_updated(self):
        """Updating the existing active template is allowed."""
        template = CertificateTemplateFactory(
            is_active=True,
        )

        template.name = "Updated"

        template.full_clean()

    def test_course_can_have_multiple_templates(self, course):
        """A course may have multiple certificate templates."""
        template1 = CertificateTemplateFactory(
            course=course,
            version=1,
        )

        template2 = CertificateTemplateFactory(
            course=course,
            version=2,
        )

        assert set(course.certificate_templates.all()) == {
            template1,
            template2,
        }

    def test_deleting_course_does_not_delete_global_template(self):
        """Global templates remain when unrelated courses are deleted."""
        course = CourseFactory()

        template = CertificateTemplateFactory(
            course=None,
        )

        course.delete()

        assert CertificateTemplate.objects.filter(
            pk=template.pk,
        ).exists()

    def test_deleting_course_deletes_course_template(self):
        """Deleting a course cascades to its templates."""
        course = CourseFactory()

        template = CertificateTemplateFactory(
            course=course,
        )

        course.delete()

        assert not CertificateTemplate.objects.filter(
            pk=template.pk,
        ).exists()

    def test_templates_are_ordered_by_active_name_and_version(self):
        """Templates are ordered by active, name, and descending version."""
        active = CertificateTemplateFactory(
            name="B",
            version=1,
            is_active=True,
        )

        inactive_v2 = CertificateTemplateFactory(
            name="A",
            version=2,
            is_active=False,
        )

        inactive_v1 = CertificateTemplateFactory(
            name="A",
            version=1,
            is_active=False,
        )

        templates = list(CertificateTemplate.objects.all())

        assert templates == [
            active,
            inactive_v2,
            inactive_v1,
        ]
