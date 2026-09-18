from decimal import Decimal

from django.core.files.base import ContentFile

from certificates.models import Certificate
from enrollments.api.serializers.student import (
    StudentCourseCertificateSerializer,
)


def create_certificate(enrollment, **kwargs):
    defaults = {
        "certificate_number": "CERT-000001",
        "verification_code": "VERIFY-000001",
        "file": ContentFile(
            b"certificate content",
            name="certificate.pdf",
        ),
    }
    defaults.update(kwargs)

    return Certificate.objects.create(
        enrollment=enrollment,
        **defaults,
    )


class TestStudentCourseCertificateSerializer:
    def test_serializes_expected_fields(self, enrollment):
        certificate = create_certificate(enrollment)

        serializer = StudentCourseCertificateSerializer(certificate)

        assert set(serializer.data) == {
            "id",
            "certificate_number",
            "course_title",
            "course_slug",
            "instructor",
            "completion_date",
            "progress",
            "completed",
            "design",
            "student_name",
        }

    def test_serializes_id(self, enrollment):
        certificate = create_certificate(enrollment)

        serializer = StudentCourseCertificateSerializer(certificate)

        assert serializer.data["id"] == certificate.id

    def test_serializes_certificate_number(self, enrollment):
        certificate = create_certificate(enrollment)

        serializer = StudentCourseCertificateSerializer(certificate)

        assert serializer.data["certificate_number"] == certificate.certificate_number

    def test_serializes_course_title(self, enrollment, course):
        certificate = create_certificate(enrollment)

        serializer = StudentCourseCertificateSerializer(certificate)

        assert serializer.data["course_title"] == course.title

    def test_serializes_course_slug(self, enrollment, course):
        certificate = create_certificate(enrollment)

        serializer = StudentCourseCertificateSerializer(certificate)

        assert serializer.data["course_slug"] == course.slug

    def test_serializes_instructor_from_course_owner(
        self,
        enrollment,
        course,
    ):
        certificate = create_certificate(enrollment)

        serializer = StudentCourseCertificateSerializer(certificate)

        assert serializer.data["instructor"] == str(course.owner)

    def test_serializes_completion_date_from_issued_at(self, enrollment):
        certificate = create_certificate(enrollment)

        serializer = StudentCourseCertificateSerializer(certificate)

        expected = serializer.fields["completion_date"].to_representation(
            certificate.issued_at
        )

        assert serializer.data["completion_date"] == expected

    def test_serializes_progress_from_enrollment(
        self,
        enrollment,
    ):
        enrollment.progress = Decimal("75")
        enrollment.save(update_fields=["progress"])

        certificate = create_certificate(enrollment)

        serializer = StudentCourseCertificateSerializer(certificate)

        assert serializer.data["progress"] == 75.0

    def test_serializes_zero_progress(self, enrollment):
        enrollment.progress = Decimal("0")
        enrollment.save(update_fields=["progress"])

        certificate = create_certificate(enrollment)

        serializer = StudentCourseCertificateSerializer(certificate)

        assert serializer.data["progress"] == 0.0

    def test_serializes_completed_true_when_progress_is_100(
        self,
        enrollment,
    ):
        enrollment.progress = Decimal("100")
        enrollment.save(update_fields=["progress"])

        certificate = create_certificate(enrollment)

        serializer = StudentCourseCertificateSerializer(certificate)

        assert serializer.data["completed"] is True

    def test_serializes_completed_false_when_progress_is_less_than_100(
        self,
        enrollment,
    ):
        enrollment.progress = Decimal("99.99")
        enrollment.save(update_fields=["progress"])

        certificate = create_certificate(enrollment)

        serializer = StudentCourseCertificateSerializer(certificate)

        assert serializer.data["completed"] is False

    def test_serializes_completed_false_when_progress_is_zero(
        self,
        enrollment,
    ):
        enrollment.progress = Decimal("0")
        enrollment.save(update_fields=["progress"])

        certificate = create_certificate(enrollment)

        serializer = StudentCourseCertificateSerializer(certificate)

        assert serializer.data["completed"] is False

    def test_serializes_design(self, enrollment):
        certificate = create_certificate(enrollment)

        serializer = StudentCourseCertificateSerializer(certificate)

        assert serializer.data["design"] == "certificate-design-1"

    def test_serializes_student_full_name(
        self,
        enrollment,
        test_user,
    ):
        test_user.first_name = "John"
        test_user.last_name = "Doe"
        test_user.save(update_fields=["first_name", "last_name"])

        certificate = create_certificate(enrollment)

        serializer = StudentCourseCertificateSerializer(certificate)

        assert serializer.data["student_name"] == "John Doe"

    def test_serializes_student_name_using_user_get_full_name(
        self,
        enrollment,
        test_user,
    ):
        test_user.first_name = "John"
        test_user.last_name = "Smith"
        test_user.save(update_fields=["first_name", "last_name"])

        certificate = create_certificate(enrollment)

        serializer = StudentCourseCertificateSerializer(certificate)

        assert serializer.data["student_name"] == test_user.get_full_name()

    def test_serializes_empty_student_name_when_names_are_empty(
        self,
        enrollment,
        test_user,
    ):
        test_user.first_name = ""
        test_user.last_name = ""
        test_user.save(update_fields=["first_name", "last_name"])

        certificate = create_certificate(enrollment)

        serializer = StudentCourseCertificateSerializer(certificate)

        assert serializer.data["student_name"] == ""

    def test_completion_date_uses_issued_at_not_created_at(
        self,
        enrollment,
    ):
        certificate = create_certificate(enrollment)

        serializer = StudentCourseCertificateSerializer(certificate)

        assert "issued_at" not in serializer.data
        assert "completion_date" in serializer.data

    def test_does_not_expose_certificate_file(
        self,
        enrollment,
    ):
        certificate = create_certificate(enrollment)

        serializer = StudentCourseCertificateSerializer(certificate)

        assert "file" not in serializer.data

    def test_does_not_expose_verification_code(
        self,
        enrollment,
    ):
        certificate = create_certificate(enrollment)

        serializer = StudentCourseCertificateSerializer(certificate)

        assert "verification_code" not in serializer.data

    def test_completed_is_serializer_method_field(self):
        serializer = StudentCourseCertificateSerializer()

        assert serializer.fields["completed"].read_only is True

    def test_design_is_serializer_method_field(self):
        serializer = StudentCourseCertificateSerializer()

        assert serializer.fields["design"].read_only is True
