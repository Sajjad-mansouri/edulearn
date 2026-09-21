# certificates/tests/services/test_certificate_service.py

from unittest.mock import Mock, patch

import pytest
from django.db import IntegrityError, transaction

from certificates.models import Certificate
from certificates.services.certificate_service import (
    create_certificate,
    generate_certificate_number,
    generate_certificate_pdf,
)


@pytest.mark.django_db
class TestGenerateCertificatePdf:
    def test_generates_pdf_from_certificate_template(self, enrollment):
        certificate = Mock()
        certificate.enrollment = enrollment

        expected_html = "<html>certificate</html>"
        expected_pdf = b"%PDF-test-content"

        with (
            patch(
                "certificates.services.certificate_service.render_to_string",
                return_value=expected_html,
            ) as render_to_string,
            patch(
                "certificates.services.certificate_service.HTML",
            ) as html_class,
        ):
            html_class.return_value.write_pdf.return_value = expected_pdf

            result = generate_certificate_pdf(certificate)

        assert result == expected_pdf

        render_to_string.assert_called_once_with(
            "certificates/certificate.html",
            {
                "certificate": certificate,
                "student": enrollment.user,
                "course": enrollment.course,
            },
        )

        html_class.assert_called_once_with(string=expected_html)
        html_class.return_value.write_pdf.assert_called_once_with()

    def test_template_context_contains_certificate(self, enrollment):
        certificate = Mock()
        certificate.enrollment = enrollment

        with (
            patch(
                "certificates.services.certificate_service.render_to_string",
                return_value="<html></html>",
            ) as render_to_string,
            patch(
                "certificates.services.certificate_service.HTML",
            ) as html_class,
        ):
            html_class.return_value.write_pdf.return_value = b"pdf"

            generate_certificate_pdf(certificate)

        context = render_to_string.call_args.args[1]

        assert context["certificate"] is certificate

    def test_template_context_contains_enrollment_user(self, enrollment):
        certificate = Mock()
        certificate.enrollment = enrollment

        with (
            patch(
                "certificates.services.certificate_service.render_to_string",
                return_value="<html></html>",
            ) as render_to_string,
            patch(
                "certificates.services.certificate_service.HTML",
            ) as html_class,
        ):
            html_class.return_value.write_pdf.return_value = b"pdf"

            generate_certificate_pdf(certificate)

        context = render_to_string.call_args.args[1]

        assert context["student"] is enrollment.user

    def test_template_context_contains_enrollment_course(self, enrollment):
        certificate = Mock()
        certificate.enrollment = enrollment

        with (
            patch(
                "certificates.services.certificate_service.render_to_string",
                return_value="<html></html>",
            ) as render_to_string,
            patch(
                "certificates.services.certificate_service.HTML",
            ) as html_class,
        ):
            html_class.return_value.write_pdf.return_value = b"pdf"

            generate_certificate_pdf(certificate)

        context = render_to_string.call_args.args[1]

        assert context["course"] is enrollment.course

    def test_returns_pdf_generated_by_weasyprint(self, enrollment):
        certificate = Mock()
        certificate.enrollment = enrollment
        expected_pdf = b"%PDF-generated-content"

        with (
            patch(
                "certificates.services.certificate_service.render_to_string",
                return_value="<html></html>",
            ),
            patch(
                "certificates.services.certificate_service.HTML",
            ) as html_class,
        ):
            html_class.return_value.write_pdf.return_value = expected_pdf

            result = generate_certificate_pdf(certificate)

        assert result == expected_pdf

    def test_template_rendering_error_is_propagated(self, enrollment):
        certificate = Mock()
        certificate.enrollment = enrollment

        with patch(
            "certificates.services.certificate_service.render_to_string",
            side_effect=RuntimeError("template rendering failed"),
        ):
            with pytest.raises(
                RuntimeError,
                match="template rendering failed",
            ):
                generate_certificate_pdf(certificate)

    def test_pdf_generation_error_is_propagated(self, enrollment):
        certificate = Mock()
        certificate.enrollment = enrollment

        with (
            patch(
                "certificates.services.certificate_service.render_to_string",
                return_value="<html></html>",
            ),
            patch(
                "certificates.services.certificate_service.HTML",
            ) as html_class,
        ):
            html_class.return_value.write_pdf.side_effect = RuntimeError(
                "PDF generation failed"
            )

            with pytest.raises(
                RuntimeError,
                match="PDF generation failed",
            ):
                generate_certificate_pdf(certificate)


class TestGenerateCertificateNumber:
    def test_returns_expected_certificate_number(self):
        with patch("uuid.uuid4") as uuid4:
            uuid4.return_value.hex = "abcdef1234567890"

            result = generate_certificate_number()

        assert result == "CERT_ABCDEF123456"

    def test_certificate_number_has_cert_prefix(self):
        with patch("uuid.uuid4") as uuid4:
            uuid4.return_value.hex = "abcdef1234567890"

            result = generate_certificate_number()

        assert result.startswith("CERT_")

    def test_certificate_number_has_expected_length(self):
        with patch("uuid.uuid4") as uuid4:
            uuid4.return_value.hex = "abcdef1234567890"

            result = generate_certificate_number()

        # CERT_ = 5 characters + 12 UUID characters.
        assert len(result) == 17

    def test_uses_first_twelve_uuid_hex_characters(self):
        with patch("uuid.uuid4") as uuid4:
            uuid4.return_value.hex = "1234567890abcdef"

            result = generate_certificate_number()

        assert result == "CERT_1234567890AB"

    def test_uuid_suffix_is_uppercase(self):
        with patch("uuid.uuid4") as uuid4:
            uuid4.return_value.hex = "abcdef1234567890"

            result = generate_certificate_number()

        assert result == "CERT_ABCDEF123456"

    def test_characters_after_first_twelve_are_ignored(self):
        with patch("uuid.uuid4") as uuid4:
            uuid4.return_value.hex = "1234567890abffffffffffff"

            result = generate_certificate_number()

        assert result == "CERT_1234567890AB"

    def test_calls_uuid4_once(self):
        with patch("uuid.uuid4") as uuid4:
            uuid4.return_value.hex = "abcdef1234567890"

            generate_certificate_number()

        uuid4.assert_called_once_with()

    def test_different_uuid_values_produce_different_numbers(self):
        with patch(
            "uuid.uuid4",
            side_effect=[
                Mock(hex="111111111111aaaaaaaa"),
                Mock(hex="222222222222bbbbbbbb"),
            ],
        ):
            first = generate_certificate_number()
            second = generate_certificate_number()

        assert first == "CERT_111111111111"
        assert second == "CERT_222222222222"
        assert first != second


@pytest.mark.django_db
class TestCreateCertificate:
    def test_creates_certificate_for_enrollment(self, enrollment):
        with (
            patch(
                "certificates.services.certificate_service.generate_certificate_number",
                return_value="CERT_123456789ABC",
            ),
            patch(
                "certificates.services.certificate_service.generate_certificate_pdf",
                return_value=b"%PDF-test",
            ),
        ):
            certificate = create_certificate(enrollment)

        assert isinstance(certificate, Certificate)
        assert certificate.pk is not None
        assert certificate.enrollment == enrollment

        assert Certificate.objects.filter(
            pk=certificate.pk,
        ).exists()

    def test_uses_generated_certificate_number(self, enrollment):
        certificate_number = "CERT_123456789ABC"

        with (
            patch(
                "certificates.services.certificate_service.generate_certificate_number",
                return_value=certificate_number,
            ) as generate_number,
            patch(
                "certificates.services.certificate_service.generate_certificate_pdf",
                return_value=b"%PDF-test",
            ),
        ):
            certificate = create_certificate(enrollment)

        generate_number.assert_called_once_with()
        assert certificate.certificate_number == certificate_number

    def test_generates_pdf_for_created_certificate(self, enrollment):
        expected_pdf = b"%PDF-certificate"

        with (
            patch(
                "certificates.services.certificate_service.generate_certificate_number",
                return_value="CERT_123456789ABC",
            ),
            patch(
                "certificates.services.certificate_service.generate_certificate_pdf",
                return_value=expected_pdf,
            ) as generate_pdf,
        ):
            certificate = create_certificate(enrollment)

        generate_pdf.assert_called_once_with(certificate)

    def test_saves_generated_pdf_to_certificate_file(self, enrollment):
        certificate_number = "CERT_123456789ABC"
        expected_pdf = b"%PDF-certificate"

        with (
            patch(
                "certificates.services.certificate_service.generate_certificate_number",
                return_value=certificate_number,
            ),
            patch(
                "certificates.services.certificate_service.generate_certificate_pdf",
                return_value=expected_pdf,
            ),
        ):
            certificate = create_certificate(enrollment)

        assert certificate.file

        expected_path = (
            f"certificates/{enrollment.user_id}/"
            f"{enrollment.course_id}/"
            f"{certificate_number}.pdf"
        )

        assert certificate.file.name == expected_path

    def test_saved_pdf_contains_generated_content(self, enrollment):
        expected_pdf = b"%PDF-certificate-content"

        with (
            patch(
                "certificates.services.certificate_service.generate_certificate_number",
                return_value="CERT_123456789ABC",
            ),
            patch(
                "certificates.services.certificate_service.generate_certificate_pdf",
                return_value=expected_pdf,
            ),
        ):
            certificate = create_certificate(enrollment)

        with certificate.file.open("rb") as file_handle:
            assert file_handle.read() == expected_pdf

    def test_saved_pdf_has_expected_size(self, enrollment):
        expected_pdf = b"%PDF-certificate-content"

        with (
            patch(
                "certificates.services.certificate_service.generate_certificate_number",
                return_value="CERT_123456789ABC",
            ),
            patch(
                "certificates.services.certificate_service.generate_certificate_pdf",
                return_value=expected_pdf,
            ),
        ):
            certificate = create_certificate(enrollment)

        assert certificate.file.size == len(expected_pdf)

    def test_file_name_uses_certificate_number(self, enrollment):
        certificate_number = "CERT_A1B2C3D4E5F6"

        with (
            patch(
                "certificates.services.certificate_service.generate_certificate_number",
                return_value=certificate_number,
            ),
            patch(
                "certificates.services.certificate_service.generate_certificate_pdf",
                return_value=b"pdf",
            ),
        ):
            certificate = create_certificate(enrollment)

        assert certificate.file.name.endswith(f"{certificate_number}.pdf")

    def test_returns_created_certificate(self, enrollment):
        with (
            patch(
                "certificates.services.certificate_service.generate_certificate_number",
                return_value="CERT_123456789ABC",
            ),
            patch(
                "certificates.services.certificate_service.generate_certificate_pdf",
                return_value=b"pdf",
            ),
        ):
            result = create_certificate(enrollment)

        assert isinstance(result, Certificate)
        assert result.pk is not None
        assert result.enrollment == enrollment

    def test_certificate_is_persisted_after_file_save(self, enrollment):
        certificate_number = "CERT_123456789ABC"

        with (
            patch(
                "certificates.services.certificate_service.generate_certificate_number",
                return_value=certificate_number,
            ),
            patch(
                "certificates.services.certificate_service.generate_certificate_pdf",
                return_value=b"pdf",
            ),
        ):
            certificate = create_certificate(enrollment)

        persisted = Certificate.objects.get(
            pk=certificate.pk,
        )

        assert persisted.enrollment_id == enrollment.pk
        assert persisted.certificate_number == certificate_number
        assert persisted.file.name == certificate.file.name

    def test_pdf_generation_error_is_propagated(self, enrollment):
        with (
            patch(
                "certificates.services.certificate_service.generate_certificate_number",
                return_value="CERT_123456789ABC",
            ),
            patch(
                "certificates.services.certificate_service.generate_certificate_pdf",
                side_effect=RuntimeError("PDF generation failed"),
            ),
        ):
            with pytest.raises(
                RuntimeError,
                match="PDF generation failed",
            ):
                create_certificate(enrollment)

    def test_pdf_generation_failure_leaves_certificate_without_file(
        self,
        enrollment,
    ):
        with (
            patch(
                "certificates.services.certificate_service.generate_certificate_number",
                return_value="CERT_123456789ABC",
            ),
            patch(
                "certificates.services.certificate_service.generate_certificate_pdf",
                side_effect=RuntimeError("PDF generation failed"),
            ),
        ):
            with pytest.raises(
                RuntimeError,
                match="PDF generation failed",
            ):
                create_certificate(enrollment)

        certificate = Certificate.objects.get(
            enrollment=enrollment,
        )

        assert not certificate.file

    def test_duplicate_enrollment_raises_integrity_error(self, enrollment):
        existing = Certificate.objects.create(
            enrollment=enrollment,
            certificate_number="CERT_EXISTING123",
            verification_code="VERIFY_EXISTING",
        )

        with patch(
            "certificates.services.certificate_service.generate_certificate_number",
            return_value="CERT_NEW123456",
        ):
            with pytest.raises(IntegrityError):
                with transaction.atomic():
                    create_certificate(enrollment)

        persisted = Certificate.objects.get(pk=existing.pk)

        assert persisted.certificate_number == "CERT_EXISTING123"
        assert persisted.verification_code == "VERIFY_EXISTING"

    def test_duplicate_enrollment_does_not_create_second_certificate(
        self,
        enrollment,
    ):
        existing = Certificate.objects.create(
            enrollment=enrollment,
            certificate_number="CERT_EXISTING123",
            verification_code="VERIFY_EXISTING",
        )

        with patch(
            "certificates.services.certificate_service.generate_certificate_number",
            return_value="CERT_NEW123456",
        ):
            with pytest.raises(IntegrityError):
                with transaction.atomic():
                    create_certificate(enrollment)

        assert (
            Certificate.objects.filter(
                enrollment=enrollment,
            ).count()
            == 1
        )

        assert Certificate.objects.filter(
            pk=existing.pk,
        ).exists()
