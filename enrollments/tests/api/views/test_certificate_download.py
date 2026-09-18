import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status


def create_certificate(enrollment, certificate_number="CERT-001"):
    from certificates.models import Certificate

    return Certificate.objects.create(
        enrollment=enrollment,
        certificate_number=certificate_number,
        verification_code=f"verification-{certificate_number}",
        file=SimpleUploadedFile(
            f"{certificate_number}.pdf",
            b"certificate pdf content",
            content_type="application/pdf",
        ),
    )


@pytest.fixture
def certificate_download_url():
    return lambda certificate_id: reverse(
        "enrollment_api:certificate_download",
        kwargs={"pk": certificate_id},
    )


class TestCertificateDownloadApiViewAuthentication:
    def test_unauthenticated_user_cannot_download_certificate(
        self,
        api_client,
        enrollment,
        certificate_download_url,
    ):
        # Arrange
        certificate = create_certificate(enrollment)

        # Act
        response = api_client.get(certificate_download_url(certificate.id))

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_non_student_user_cannot_download_certificate(
        self,
        api_client,
        test_user,
        enrollment,
        certificate_download_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)
        certificate = create_certificate(enrollment)

        # Act
        response = api_client.get(certificate_download_url(certificate.id))

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_student_user_can_download_certificate(
        self,
        api_client,
        student_user,
        enrollment,
        certificate_download_url,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)
        certificate = create_certificate(enrollment)

        # Act
        response = api_client.get(certificate_download_url(certificate.id))

        # Assert
        assert response.status_code == status.HTTP_200_OK


class TestCertificateDownloadApiViewAuthorization:
    def test_student_cannot_download_another_students_certificate(
        self,
        api_client,
        student_user,
        another_user_enrollment,
        certificate_download_url,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        certificate = create_certificate(
            another_user_enrollment,
            certificate_number="CERT-OTHER",
        )

        # Act
        response = api_client.get(certificate_download_url(certificate.id))

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_certificate_not_owned_by_request_user_returns_404(
        self,
        api_client,
        student_user,
        another_user_enrollment,
        certificate_download_url,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        certificate = create_certificate(
            another_user_enrollment,
            certificate_number="CERT-PRIVATE",
        )

        # Act
        response = api_client.get(certificate_download_url(certificate.pk))

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestCertificateDownloadApiViewCertificateLookup:
    def test_nonexistent_certificate_returns_404(
        self,
        api_client,
        student_user,
        certificate_download_url,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        nonexistent_certificate_id = 999999

        # Act
        response = api_client.get(certificate_download_url(nonexistent_certificate_id))

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_invalid_certificate_id_returns_404(
        self,
        api_client,
    ):
        response = api_client.get("/api/enrollments/certificate/invalid/download/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestCertificateDownloadApiViewFileResponse:
    def test_returns_certificate_file_as_attachment(
        self,
        api_client,
        student_user,
        enrollment,
        certificate_download_url,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        certificate = create_certificate(
            enrollment,
            certificate_number="CERT-2026-001",
        )

        # Act
        response = api_client.get(certificate_download_url(certificate.id))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "application/pdf"
        assert (
            response["Content-Disposition"]
            == 'attachment; filename="CERT-2026-001.pdf"'
        )

    def test_response_contains_certificate_file_content(
        self,
        api_client,
        student_user,
        enrollment,
        certificate_download_url,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        file_content = b"certificate pdf content"
        certificate = create_certificate(
            enrollment,
            certificate_number="CERT-CONTENT",
        )

        certificate.file.save(
            "certificate.pdf",
            SimpleUploadedFile(
                "certificate.pdf",
                file_content,
                content_type="application/pdf",
            ),
        )

        # Act
        response = api_client.get(certificate_download_url(certificate.id))

        # Assert
        assert response.status_code == status.HTTP_200_OK

        response_content = b"".join(response.streaming_content)

        assert response_content == file_content

    def test_download_filename_uses_certificate_number(
        self,
        api_client,
        student_user,
        enrollment,
        certificate_download_url,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        certificate = create_certificate(
            enrollment,
            certificate_number="SM-LMS-ABC-123",
        )

        # Act
        response = api_client.get(certificate_download_url(certificate.id))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert (
            response["Content-Disposition"]
            == 'attachment; filename="SM-LMS-ABC-123.pdf"'
        )

    def test_download_does_not_return_inline_disposition(
        self,
        api_client,
        student_user,
        enrollment,
        certificate_download_url,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        certificate = create_certificate(
            enrollment,
            certificate_number="CERT-ATTACHMENT",
        )

        # Act
        response = api_client.get(certificate_download_url(certificate.id))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "inline" not in response["Content-Disposition"]
        assert "attachment" in response["Content-Disposition"]


class TestCertificateDownloadApiViewIsolation:
    def test_student_can_download_own_certificate_when_other_certificates_exist(
        self,
        api_client,
        student_user,
        enrollment,
        another_user_enrollment,
        certificate_download_url,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        own_certificate = create_certificate(
            enrollment,
            certificate_number="CERT-OWN",
        )

        create_certificate(
            another_user_enrollment,
            certificate_number="CERT-OTHER",
        )

        # Act
        response = api_client.get(certificate_download_url(own_certificate.id))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Disposition"] == 'attachment; filename="CERT-OWN.pdf"'

    def test_other_students_certificate_is_not_exposed_by_id(
        self,
        api_client,
        student_user,
        another_user_enrollment,
        certificate_download_url,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        other_certificate = create_certificate(
            another_user_enrollment,
            certificate_number="CERT-PRIVATE",
        )

        # Act
        response = api_client.get(certificate_download_url(other_certificate.pk))

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
