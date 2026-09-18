from datetime import timedelta

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from certificates.models import Certificate
from courses.models import Course
from enrollments.api.serializers import StudentCourseCertificateSerializer
from enrollments.models import Enrollment


def create_certificate(enrollment, certificate_number):
    return Certificate.objects.create(
        enrollment=enrollment,
        certificate_number=certificate_number,
        verification_code=f"verification-{certificate_number}",
        file=SimpleUploadedFile(
            f"{certificate_number}.pdf",
            b"certificate content",
            content_type="application/pdf",
        ),
    )


@pytest.fixture
def student_certificates_url():
    return reverse("enrollment_api:student_certificates")


class TestStudentCertificatesApiViewAuthentication:
    def test_unauthenticated_user_cannot_access_certificates(
        self,
        api_client,
        student_certificates_url,
    ):
        # Arrange
        url = student_certificates_url

        # Act
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_non_student_user_cannot_access_certificates(
        self,
        api_client,
        test_user,
        student_certificates_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        # Act
        response = api_client.get(student_certificates_url)

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_student_user_can_access_certificates(
        self,
        api_client,
        student_user,
        student_certificates_url,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        # Act
        response = api_client.get(student_certificates_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK


class TestStudentCertificatesApiViewQueryset:
    def test_returns_only_current_students_certificates(
        self,
        api_client,
        student_user,
        another_user_enrollment,
        enrollment,
        student_certificates_url,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        student_certificate = create_certificate(
            enrollment=enrollment,
            certificate_number="CERT-STUDENT-001",
        )

        create_certificate(
            enrollment=another_user_enrollment,
            certificate_number="CERT-OTHER-001",
        )

        # Act
        response = api_client.get(student_certificates_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert len(response.data["results"]) == 1

        expected = StudentCourseCertificateSerializer(student_certificate).data

        assert response.data["results"][0] == expected

    def test_returns_empty_results_when_student_has_no_certificates(
        self,
        api_client,
        student_user,
        student_certificates_url,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        # Act
        response = api_client.get(student_certificates_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0
        assert response.data["results"] == []

    def test_returns_all_certificates_belonging_to_current_student(
        self,
        api_client,
        student_user,
        course,
        enrollment,
        student_certificates_url,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        second_course = Course.objects.create(
            title="Second Course",
            owner=student_user,
            category=course.category,
        )

        second_enrollment = Enrollment.objects.create(
            user=student_user,
            course=second_course,
            status=Enrollment.Status.COMPLETED,
        )

        first_certificate = create_certificate(
            enrollment=enrollment,
            certificate_number="CERT-001",
        )
        second_certificate = create_certificate(
            enrollment=second_enrollment,
            certificate_number="CERT-002",
        )

        # Act
        response = api_client.get(student_certificates_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2
        assert len(response.data["results"]) == 2

        expected = {
            StudentCourseCertificateSerializer(first_certificate).data[
                "certificate_number"
            ],
            StudentCourseCertificateSerializer(second_certificate).data[
                "certificate_number"
            ],
        }

        returned = {item["certificate_number"] for item in response.data["results"]}

        assert returned == expected

    def test_does_not_return_certificates_belonging_to_another_student(
        self,
        api_client,
        student_user,
        another_user_enrollment,
        student_certificates_url,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        other_certificate = create_certificate(
            enrollment=another_user_enrollment,
            certificate_number="CERT-OTHER-001",
        )

        # Act
        response = api_client.get(student_certificates_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0
        assert response.data["results"] == []

        returned_numbers = {
            item["certificate_number"] for item in response.data["results"]
        }

        assert other_certificate.certificate_number not in returned_numbers

    @pytest.mark.parametrize(
        "enrollment_status",
        [
            Enrollment.Status.ACTIVE,
            Enrollment.Status.COMPLETED,
            Enrollment.Status.CANCELLED,
            Enrollment.Status.SUSPENDED,
            Enrollment.Status.PENDING,
        ],
    )
    def test_returns_certificate_regardless_of_enrollment_status(
        self,
        api_client,
        student_user,
        course,
        enrollment,
        enrollment_status,
        student_certificates_url,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        enrollment.status = enrollment_status
        enrollment.save(update_fields=["status"])

        certificate = create_certificate(
            enrollment=enrollment,
            certificate_number=f"CERT-{enrollment_status}",
        )

        # Act
        response = api_client.get(student_certificates_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

        expected = StudentCourseCertificateSerializer(certificate).data

        assert response.data["results"][0] == expected


class TestStudentCertificatesApiViewOrdering:
    def test_returns_certificates_newest_first(
        self,
        api_client,
        student_user,
        course,
        enrollment,
        student_certificates_url,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        second_course = Course.objects.create(
            title="Second Course",
            owner=student_user,
            category=course.category,
        )

        second_enrollment = Enrollment.objects.create(
            user=student_user,
            course=second_course,
            status=Enrollment.Status.COMPLETED,
        )

        oldest = create_certificate(
            enrollment=enrollment,
            certificate_number="CERT-OLDEST",
        )

        middle = create_certificate(
            enrollment=second_enrollment,
            certificate_number="CERT-MIDDLE",
        )

        third_course = Course.objects.create(
            title="Third Course",
            owner=student_user,
            category=course.category,
        )

        third_enrollment = Enrollment.objects.create(
            user=student_user,
            course=third_course,
            status=Enrollment.Status.COMPLETED,
        )

        newest = create_certificate(
            enrollment=third_enrollment,
            certificate_number="CERT-NEWEST",
        )

        base_time = timezone.now()

        Certificate.objects.filter(pk=oldest.pk).update(
            issued_at=base_time - timedelta(days=3)
        )
        Certificate.objects.filter(pk=middle.pk).update(
            issued_at=base_time - timedelta(days=2)
        )
        Certificate.objects.filter(pk=newest.pk).update(
            issued_at=base_time - timedelta(days=1)
        )

        # Act
        response = api_client.get(student_certificates_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        returned_numbers = [
            item["certificate_number"] for item in response.data["results"]
        ]

        assert returned_numbers == [
            newest.certificate_number,
            middle.certificate_number,
            oldest.certificate_number,
        ]

    def test_ordering_is_based_on_issued_at_not_certificate_number(
        self,
        api_client,
        student_user,
        course,
        enrollment,
        student_certificates_url,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        second_course = Course.objects.create(
            title="Second Course",
            owner=student_user,
            category=course.category,
        )

        second_enrollment = Enrollment.objects.create(
            user=student_user,
            course=second_course,
            status=Enrollment.Status.COMPLETED,
        )

        first_certificate = create_certificate(
            enrollment=enrollment,
            certificate_number="CERT-Z",
        )

        second_certificate = create_certificate(
            enrollment=second_enrollment,
            certificate_number="CERT-A",
        )

        base_time = timezone.now()

        Certificate.objects.filter(pk=first_certificate.pk).update(
            issued_at=base_time - timedelta(days=2)
        )
        Certificate.objects.filter(pk=second_certificate.pk).update(issued_at=base_time)

        # Act
        response = api_client.get(student_certificates_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        returned_numbers = [
            item["certificate_number"] for item in response.data["results"]
        ]

        assert returned_numbers == [
            second_certificate.certificate_number,
            first_certificate.certificate_number,
        ]


class TestStudentCertificatesApiViewSerializer:
    def test_response_matches_student_certificate_serializer(
        self,
        api_client,
        student_user,
        enrollment,
        student_certificates_url,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        certificate = create_certificate(
            enrollment=enrollment,
            certificate_number="CERT-001",
        )

        # Act
        response = api_client.get(student_certificates_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        expected = StudentCourseCertificateSerializer(certificate).data

        assert response.data["results"][0] == expected

    def test_serializes_each_certificate_independently(
        self,
        api_client,
        student_user,
        course,
        enrollment,
        student_certificates_url,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        second_course = Course.objects.create(
            title="Second Course",
            owner=student_user,
            category=course.category,
        )

        second_enrollment = Enrollment.objects.create(
            user=student_user,
            course=second_course,
            status=Enrollment.Status.COMPLETED,
        )

        first_certificate = create_certificate(
            enrollment=enrollment,
            certificate_number="CERT-001",
        )
        second_certificate = create_certificate(
            enrollment=second_enrollment,
            certificate_number="CERT-002",
        )

        # Act
        response = api_client.get(student_certificates_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        returned = response.data["results"]

        expected = {
            first_certificate.certificate_number: (
                StudentCourseCertificateSerializer(first_certificate).data
            ),
            second_certificate.certificate_number: (
                StudentCourseCertificateSerializer(second_certificate).data
            ),
        }

        for item in returned:
            assert item["certificate_number"] in expected
            assert item == expected[item["certificate_number"]]


class TestStudentCertificatesApiViewPagination:
    def test_returns_paginated_response(
        self,
        api_client,
        student_user,
        enrollment,
        student_certificates_url,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        create_certificate(
            enrollment=enrollment,
            certificate_number="CERT-001",
        )

        # Act
        response = api_client.get(student_certificates_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "count" in response.data
        assert "next" in response.data
        assert "previous" in response.data
        assert "results" in response.data

        assert response.data["count"] == 1
        assert len(response.data["results"]) == 1

    def test_empty_paginated_response_contains_empty_results(
        self,
        api_client,
        student_user,
        student_certificates_url,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        # Act
        response = api_client.get(student_certificates_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0
        assert response.data["results"] == []


class TestStudentCertificatesApiViewIsolation:
    def test_current_student_can_have_certificate_for_multiple_courses(
        self,
        api_client,
        student_user,
        course,
        enrollment,
        student_certificates_url,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        second_course = Course.objects.create(
            title="Another Course",
            owner=student_user,
            category=course.category,
        )

        second_enrollment = Enrollment.objects.create(
            user=student_user,
            course=second_course,
            status=Enrollment.Status.COMPLETED,
        )

        first_certificate = create_certificate(
            enrollment=enrollment,
            certificate_number="CERT-001",
        )
        second_certificate = create_certificate(
            enrollment=second_enrollment,
            certificate_number="CERT-002",
        )

        # Act
        response = api_client.get(student_certificates_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        returned_numbers = {
            item["certificate_number"] for item in response.data["results"]
        }

        assert returned_numbers == {
            first_certificate.certificate_number,
            second_certificate.certificate_number,
        }

    def test_other_students_certificates_do_not_change_current_students_count(
        self,
        api_client,
        student_user,
        enrollment,
        another_user_enrollment,
        student_certificates_url,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        create_certificate(
            enrollment=enrollment,
            certificate_number="CERT-STUDENT",
        )
        create_certificate(
            enrollment=another_user_enrollment,
            certificate_number="CERT-OTHER",
        )

        # Act
        response = api_client.get(student_certificates_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
