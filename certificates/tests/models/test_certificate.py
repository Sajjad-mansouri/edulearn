from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import IntegrityError
from django.utils import timezone

from certificates.models import (
    Certificate,
    CertificateTemplate,
    file_upload_path,
)
from enrollments.models import Enrollment


class TestCertificate:
    def test_creates_certificate_with_expected_fields(
        self,
        db,
        enrollment,
    ):
        certificate = Certificate.objects.create(
            enrollment=enrollment,
            certificate_number="CERT-000001",
            verification_code="VERIFY-000001",
            file=ContentFile(
                b"certificate content",
                name="certificate.pdf",
            ),
        )

        assert certificate.enrollment == enrollment
        assert certificate.certificate_number == "CERT-000001"
        assert certificate.verification_code == "VERIFY-000001"
        assert certificate.file.name.endswith("certificate.pdf")
        assert certificate.issued_at is not None

    def test_str_returns_user_and_course(
        self,
        db,
        enrollment,
    ):
        certificate = Certificate.objects.create(
            enrollment=enrollment,
            certificate_number="CERT-000001",
            verification_code="VERIFY-000001",
            file=ContentFile(
                b"certificate content",
                name="certificate.pdf",
            ),
        )

        assert str(certificate) == (f"{enrollment.user} - {enrollment.course}")

    def test_enrollment_is_one_to_one(
        self,
        db,
        enrollment,
    ):
        Certificate.objects.create(
            enrollment=enrollment,
            certificate_number="CERT-000001",
            verification_code="VERIFY-000001",
            file=ContentFile(
                b"certificate content",
                name="certificate.pdf",
            ),
        )

        with pytest.raises(IntegrityError):
            Certificate.objects.create(
                enrollment=enrollment,
                certificate_number="CERT-000002",
                verification_code="VERIFY-000002",
                file=ContentFile(
                    b"certificate content",
                    name="certificate-2.pdf",
                ),
            )

    def test_enrollment_reverse_relation_returns_certificate(
        self,
        db,
        enrollment,
    ):
        certificate = Certificate.objects.create(
            enrollment=enrollment,
            certificate_number="CERT-000001",
            verification_code="VERIFY-000001",
            file=ContentFile(
                b"certificate content",
                name="certificate.pdf",
            ),
        )

        assert enrollment.certificate == certificate

    def test_certificate_number_must_be_unique(
        self,
        db,
        enrollment,
        another_enrollment,
    ):
        Certificate.objects.create(
            enrollment=enrollment,
            certificate_number="CERT-000001",
            verification_code="VERIFY-000001",
            file=ContentFile(
                b"certificate content",
                name="certificate.pdf",
            ),
        )

        with pytest.raises(IntegrityError):
            Certificate.objects.create(
                enrollment=another_enrollment,
                certificate_number="CERT-000001",
                verification_code="VERIFY-000002",
                file=ContentFile(
                    b"certificate content",
                    name="certificate-2.pdf",
                ),
            )

    def test_verification_code_must_be_unique(
        self,
        db,
        enrollment,
        another_enrollment,
    ):
        Certificate.objects.create(
            enrollment=enrollment,
            certificate_number="CERT-000001",
            verification_code="VERIFY-000001",
            file=ContentFile(
                b"certificate content",
                name="certificate.pdf",
            ),
        )

        with pytest.raises(IntegrityError):
            Certificate.objects.create(
                enrollment=another_enrollment,
                certificate_number="CERT-000002",
                verification_code="VERIFY-000001",
                file=ContentFile(
                    b"certificate content",
                    name="certificate-2.pdf",
                ),
            )

    def test_certificate_number_is_required(
        self,
        db,
        enrollment,
    ):
        certificate = Certificate(
            enrollment=enrollment,
            verification_code="VERIFY-000001",
            file=ContentFile(
                b"certificate content",
                name="certificate.pdf",
            ),
        )

        with pytest.raises(ValidationError) as exc_info:
            Certificate._meta.get_field("certificate_number").validate(
                certificate.certificate_number,
                certificate,
            )

        assert exc_info.value.messages

    def test_verification_code_is_required(
        self,
        db,
        enrollment,
    ):
        certificate = Certificate(
            enrollment=enrollment,
            certificate_number="CERT-000001",
            file=ContentFile(
                b"certificate content",
                name="certificate.pdf",
            ),
        )

        with pytest.raises(ValidationError) as exc_info:
            Certificate._meta.get_field("verification_code").validate(
                certificate.verification_code,
                certificate,
            )

        assert exc_info.value.messages

    def test_enrollment_is_required(
        self,
        db,
    ):
        certificate = Certificate(
            certificate_number="CERT-000001",
            verification_code="VERIFY-000001",
            file=ContentFile(
                b"certificate content",
                name="certificate.pdf",
            ),
        )

        with pytest.raises(ValidationError) as exc_info:
            Certificate._meta.get_field("enrollment").validate(
                certificate.enrollment_id,
                certificate,
            )

        assert exc_info.value.messages

    def test_file_is_required(
        self,
        db,
        enrollment,
    ):
        certificate = Certificate(
            enrollment=enrollment,
            certificate_number="CERT-000001",
            verification_code="VERIFY-000001",
        )

        with pytest.raises(ValidationError) as exc_info:
            Certificate._meta.get_field("file").validate(
                certificate.file,
                certificate,
            )

        assert exc_info.value.messages

    def test_issued_at_is_set_automatically(
        self,
        db,
        enrollment,
    ):
        before = timezone.now()

        certificate = Certificate.objects.create(
            enrollment=enrollment,
            certificate_number="CERT-000001",
            verification_code="VERIFY-000001",
            file=ContentFile(
                b"certificate content",
                name="certificate.pdf",
            ),
        )

        after = timezone.now()

        assert before <= certificate.issued_at <= after

    def test_certificate_ordering_is_by_latest_issued_first(
        self,
        db,
        enrollment,
        another_user,
        course,
    ):
        second_enrollment = Enrollment.objects.create(
            user=another_user,
            course=course,
            status=Enrollment.Status.COMPLETED,
        )

        first = Certificate.objects.create(
            enrollment=enrollment,
            certificate_number="CERT-000001",
            verification_code="VERIFY-000001",
            file=ContentFile(
                b"certificate content",
                name="first.pdf",
            ),
        )

        second = Certificate.objects.create(
            enrollment=second_enrollment,
            certificate_number="CERT-000002",
            verification_code="VERIFY-000002",
            file=ContentFile(
                b"certificate content",
                name="second.pdf",
            ),
        )

        Certificate.objects.filter(pk=first.pk).update(
            issued_at=timezone.now() - timedelta(minutes=1),
        )
        Certificate.objects.filter(pk=second.pk).update(
            issued_at=timezone.now(),
        )

        certificates = list(Certificate.objects.all())

        assert certificates == [second, first]

    def test_deleting_enrollment_deletes_certificate(
        self,
        db,
        enrollment,
    ):
        certificate = Certificate.objects.create(
            enrollment=enrollment,
            certificate_number="CERT-000001",
            verification_code="VERIFY-000001",
            file=ContentFile(
                b"certificate content",
                name="certificate.pdf",
            ),
        )

        certificate_id = certificate.pk

        enrollment.delete()

        assert not Certificate.objects.filter(pk=certificate_id).exists()

    def test_certificate_persists_after_reload(
        self,
        db,
        enrollment,
    ):
        certificate = Certificate.objects.create(
            enrollment=enrollment,
            certificate_number="CERT-000001",
            verification_code="VERIFY-000001",
            file=ContentFile(
                b"certificate content",
                name="certificate.pdf",
            ),
        )

        certificate.refresh_from_db()

        assert certificate.certificate_number == "CERT-000001"
        assert certificate.verification_code == "VERIFY-000001"
        assert certificate.enrollment_id == enrollment.pk
        assert certificate.file.name.endswith("certificate.pdf")


class TestCertificateFileUploadPath:
    def test_file_upload_path_uses_user_and_course_ids(
        self,
        enrollment,
    ):
        certificate = Certificate(
            enrollment=enrollment,
        )

        path = file_upload_path(
            certificate,
            "certificate.pdf",
        )

        assert path == (
            f"certificates/{enrollment.user_id}/{enrollment.course_id}/certificate.pdf"
        )

    def test_file_upload_path_preserves_filename(
        self,
        enrollment,
    ):
        certificate = Certificate(
            enrollment=enrollment,
        )

        path = file_upload_path(
            certificate,
            "certificate-final.pdf",
        )

        assert path.endswith("/certificate-final.pdf")


class TestCertificateTemplate:
    def test_creates_template_with_expected_fields(
        self,
        db,
        course,
    ):
        template = CertificateTemplate.objects.create(
            course=course,
            name="Standard Template",
            version=1,
            background=ContentFile(
                b"background content",
                name="background.pdf",
            ),
            is_active=False,
        )

        assert template.course == course
        assert template.name == "Standard Template"
        assert template.version == 1
        assert template.background.name.endswith("background.pdf")
        assert template.is_active is False
        assert template.created_at is not None
        assert template.updated_at is not None

    def test_str_returns_name_and_version(
        self,
        db,
        course,
    ):
        template = CertificateTemplate.objects.create(
            course=course,
            name="Standard Template",
            version=3,
            background=ContentFile(
                b"background content",
                name="background.pdf",
            ),
        )

        assert str(template) == "Standard Template v3"

    def test_course_is_optional(
        self,
        db,
    ):
        template = CertificateTemplate.objects.create(
            course=None,
            name="Global Template",
            version=1,
            background=ContentFile(
                b"background content",
                name="background.pdf",
            ),
        )

        assert template.course is None

    def test_course_reverse_relation(
        self,
        db,
        course,
    ):
        template = CertificateTemplate.objects.create(
            course=course,
            name="Standard Template",
            version=1,
            background=ContentFile(
                b"background content",
                name="background.pdf",
            ),
        )

        assert list(course.certificate_templates.all()) == [template]

    def test_version_defaults_to_one(
        self,
        db,
        course,
    ):
        template = CertificateTemplate.objects.create(
            course=course,
            name="Standard Template",
            background=ContentFile(
                b"background content",
                name="background.pdf",
            ),
        )

        assert template.version == 1

    def test_is_active_defaults_to_false(
        self,
        db,
        course,
    ):
        template = CertificateTemplate.objects.create(
            course=course,
            name="Standard Template",
            background=ContentFile(
                b"background content",
                name="background.pdf",
            ),
        )

        assert template.is_active is False

    def test_background_is_required(
        self,
        db,
        course,
    ):
        template = CertificateTemplate(
            course=course,
            name="Standard Template",
            version=1,
        )

        with pytest.raises(ValidationError) as exc_info:
            CertificateTemplate._meta.get_field("background").validate(
                template.background,
                template,
            )

        assert exc_info.value.messages

    def test_name_is_required(
        self,
        db,
        course,
    ):
        template = CertificateTemplate(
            course=course,
            background=ContentFile(
                b"background content",
                name="background.pdf",
            ),
        )

        with pytest.raises(ValidationError) as exc_info:
            CertificateTemplate._meta.get_field("name").validate(
                template.name,
                template,
            )

        assert exc_info.value.messages

    def test_unique_name_and_version(
        self,
        db,
        course,
    ):
        CertificateTemplate.objects.create(
            course=course,
            name="Standard Template",
            version=1,
            background=ContentFile(
                b"background content",
                name="background.pdf",
            ),
        )

        with pytest.raises(IntegrityError):
            CertificateTemplate.objects.create(
                course=course,
                name="Standard Template",
                version=1,
                background=ContentFile(
                    b"background content",
                    name="background-2.pdf",
                ),
            )

    def test_same_name_can_have_different_versions(
        self,
        db,
        course,
    ):
        first = CertificateTemplate.objects.create(
            course=course,
            name="Standard Template",
            version=1,
            background=ContentFile(
                b"background content",
                name="background-v1.pdf",
            ),
        )

        second = CertificateTemplate.objects.create(
            course=course,
            name="Standard Template",
            version=2,
            background=ContentFile(
                b"background content",
                name="background-v2.pdf",
            ),
        )

        assert first.pk != second.pk

    def test_same_version_can_have_different_names(
        self,
        db,
        course,
    ):
        first = CertificateTemplate.objects.create(
            course=course,
            name="Standard Template",
            version=1,
            background=ContentFile(
                b"background content",
                name="standard.pdf",
            ),
        )

        second = CertificateTemplate.objects.create(
            course=course,
            name="Alternative Template",
            version=1,
            background=ContentFile(
                b"background content",
                name="alternative.pdf",
            ),
        )

        assert first.pk != second.pk

    def test_active_template_is_valid_when_no_other_template_is_active(
        self,
        db,
        course,
    ):
        template = CertificateTemplate(
            course=course,
            name="Standard Template",
            version=1,
            background=ContentFile(
                b"background content",
                name="background.pdf",
            ),
            is_active=True,
        )

        template.full_clean()

    def test_only_one_active_template_is_allowed(
        self,
        db,
        course,
    ):
        CertificateTemplate.objects.create(
            course=course,
            name="First Template",
            version=1,
            background=ContentFile(
                b"background content",
                name="first.pdf",
            ),
            is_active=True,
        )

        second = CertificateTemplate(
            course=course,
            name="Second Template",
            version=1,
            background=ContentFile(
                b"background content",
                name="second.pdf",
            ),
            is_active=True,
        )

        with pytest.raises(ValidationError) as exc_info:
            second.full_clean()

        assert "is_active" in exc_info.value.message_dict
        assert (
            "Only one certificate template can be active."
            in exc_info.value.message_dict["is_active"]
        )

    def test_active_template_excludes_itself_during_update_validation(
        self,
        db,
        course,
    ):
        template = CertificateTemplate.objects.create(
            course=course,
            name="Standard Template",
            version=1,
            background=ContentFile(
                b"background content",
                name="background.pdf",
            ),
            is_active=True,
        )

        template.name = "Updated Template"

        template.full_clean()

        assert template.name == "Updated Template"

    def test_inactive_template_can_exist_alongside_active_template(
        self,
        db,
        course,
    ):
        active = CertificateTemplate.objects.create(
            course=course,
            name="Active Template",
            version=1,
            background=ContentFile(
                b"background content",
                name="active.pdf",
            ),
            is_active=True,
        )

        inactive = CertificateTemplate(
            course=course,
            name="Inactive Template",
            version=1,
            background=ContentFile(
                b"background content",
                name="inactive.pdf",
            ),
            is_active=False,
        )

        inactive.full_clean()

        assert active.is_active is True
        assert inactive.is_active is False

    def test_multiple_inactive_templates_are_allowed(
        self,
        db,
        course,
    ):
        first = CertificateTemplate.objects.create(
            course=course,
            name="First Template",
            version=1,
            background=ContentFile(
                b"background content",
                name="first.pdf",
            ),
            is_active=False,
        )

        second = CertificateTemplate.objects.create(
            course=course,
            name="Second Template",
            version=1,
            background=ContentFile(
                b"background content",
                name="second.pdf",
            ),
            is_active=False,
        )

        assert CertificateTemplate.objects.filter(is_active=False).count() == 2
        assert first.pk != second.pk

    def test_template_ordering(
        self,
        db,
        course,
    ):
        inactive_old = CertificateTemplate.objects.create(
            course=course,
            name="Template A",
            version=1,
            background=ContentFile(
                b"background content",
                name="old.pdf",
            ),
            is_active=False,
        )

        active = CertificateTemplate.objects.create(
            course=course,
            name="Template B",
            version=1,
            background=ContentFile(
                b"background content",
                name="active.pdf",
            ),
            is_active=True,
        )

        inactive_new = CertificateTemplate.objects.create(
            course=course,
            name="Template A",
            version=2,
            background=ContentFile(
                b"background content",
                name="newer.pdf",
            ),
            is_active=False,
        )

        templates = list(CertificateTemplate.objects.all())

        assert templates == [
            active,
            inactive_new,
            inactive_old,
        ]

    def test_created_at_is_set_automatically(
        self,
        db,
        course,
    ):
        before = timezone.now()

        template = CertificateTemplate.objects.create(
            course=course,
            name="Standard Template",
            version=1,
            background=ContentFile(
                b"background content",
                name="background.pdf",
            ),
        )

        after = timezone.now()

        assert before <= template.created_at <= after

    def test_updated_at_changes_when_template_is_saved(
        self,
        db,
        course,
    ):
        template = CertificateTemplate.objects.create(
            course=course,
            name="Standard Template",
            version=1,
            background=ContentFile(
                b"background content",
                name="background.pdf",
            ),
        )

        original_updated_at = template.updated_at

        template.name = "Updated Template"
        template.save()
        template.refresh_from_db()

        assert template.updated_at >= original_updated_at

    def test_deleting_course_deletes_course_template(
        self,
        db,
        course,
    ):
        template = CertificateTemplate.objects.create(
            course=course,
            name="Standard Template",
            version=1,
            background=ContentFile(
                b"background content",
                name="background.pdf",
            ),
        )

        template_id = template.pk

        course.delete()

        assert not CertificateTemplate.objects.filter(pk=template_id).exists()

    def test_template_persists_after_reload(
        self,
        db,
        course,
    ):
        template = CertificateTemplate.objects.create(
            course=course,
            name="Standard Template",
            version=2,
            background=ContentFile(
                b"background content",
                name="background.pdf",
            ),
            is_active=True,
        )

        template.refresh_from_db()

        assert template.name == "Standard Template"
        assert template.version == 2
        assert template.course_id == course.pk
        assert template.is_active is True
        assert template.background.name.endswith("background.pdf")
