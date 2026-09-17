import pytest
from django.urls import reverse

from enrollments.models import Enrollment


class TestCourseLearningView:
    def test_authenticated_user_with_active_enrollment_can_access_page(
        self,
        client,
        test_user,
        enrollment,
    ):
        client.force_login(test_user)

        response = client.get(
            reverse(
                "enrollments:learn",
                kwargs={"enrollment_id": enrollment.id},
            )
        )

        assert response.status_code == 200
        assert "enrollments/course_learning.html" in [
            template.name for template in response.templates
        ]

    def test_authenticated_user_with_completed_enrollment_can_access_page(
        self,
        client,
        test_user,
        course,
    ):
        enrollment = Enrollment.objects.create(
            user=test_user,
            course=course,
            status=Enrollment.Status.COMPLETED,
        )

        client.force_login(test_user)

        response = client.get(
            reverse(
                "enrollments:learn",
                kwargs={"enrollment_id": enrollment.id},
            )
        )

        assert response.status_code == 200
        assert "enrollments/course_learning.html" in [
            template.name for template in response.templates
        ]

    @pytest.mark.parametrize(
        "status",
        [
            Enrollment.Status.PENDING,
            Enrollment.Status.CANCELLED,
            Enrollment.Status.SUSPENDED,
        ],
    )
    def test_user_cannot_access_ineligible_enrollment(
        self,
        client,
        test_user,
        course,
        status,
    ):
        enrollment = Enrollment.objects.create(
            user=test_user,
            course=course,
            status=status,
        )

        client.force_login(test_user)

        response = client.get(
            reverse(
                "enrollments:learn",
                kwargs={"enrollment_id": enrollment.id},
            )
        )

        assert response.status_code == 404

    def test_user_cannot_access_another_users_enrollment(
        self,
        client,
        test_user,
        another_user_enrollment,
    ):
        client.force_login(test_user)

        response = client.get(
            reverse(
                "enrollments:learn",
                kwargs={
                    "enrollment_id": another_user_enrollment.id,
                },
            )
        )

        assert response.status_code == 404

    def test_nonexistent_enrollment_returns_404(
        self,
        client,
        test_user,
    ):
        client.force_login(test_user)

        response = client.get(
            reverse(
                "enrollments:learn",
                kwargs={"enrollment_id": 999999},
            )
        )

        assert response.status_code == 404

    def test_unauthenticated_user_is_redirected(
        self,
        client,
        enrollment,
    ):
        response = client.get(
            reverse(
                "enrollments:learn",
                kwargs={"enrollment_id": enrollment.id},
            )
        )

        assert response.status_code == 302

    def test_enrollment_is_available_to_view(
        self,
        client,
        test_user,
        enrollment,
    ):
        client.force_login(test_user)

        response = client.get(
            reverse(
                "enrollments:learn",
                kwargs={"enrollment_id": enrollment.id},
            )
        )

        assert response.status_code == 200
        assert response.context["view"].enrollment == enrollment


class TestStudentCoursesView:
    def test_student_can_access_courses_page(
        self,
        client,
        student_user,
    ):
        client.force_login(student_user)

        response = client.get(
            reverse("enrollments:student_courses"),
        )

        assert response.status_code == 200
        assert "enrollments/student_courses.html" in [
            template.name for template in response.templates
        ]

    def test_non_student_cannot_access_courses_page(
        self,
        client,
        test_user,
    ):
        client.force_login(test_user)

        response = client.get(
            reverse("enrollments:student_courses"),
        )

        assert response.status_code == 404

    def test_unauthenticated_user_is_redirected(
        self,
        client,
    ):
        response = client.get(
            reverse("enrollments:student_courses"),
        )

        assert response.status_code == 302


class TestStudentWishlistView:
    def test_student_can_access_wishlist_page(
        self,
        client,
        student_user,
    ):
        client.force_login(student_user)

        response = client.get(
            reverse("enrollments:student_wishlist"),
        )

        assert response.status_code == 200
        assert "enrollments/wishlist.html" in [
            template.name for template in response.templates
        ]

    def test_non_student_cannot_access_wishlist_page(
        self,
        client,
        test_user,
    ):
        client.force_login(test_user)

        response = client.get(
            reverse("enrollments:student_wishlist"),
        )

        assert response.status_code == 404

    def test_unauthenticated_user_is_redirected(
        self,
        client,
    ):
        response = client.get(
            reverse("enrollments:student_wishlist"),
        )

        assert response.status_code == 302


class TestStudentCertificatesView:
    def test_student_can_access_certificates_page(
        self,
        client,
        student_user,
    ):
        client.force_login(student_user)

        response = client.get(
            reverse("enrollments:student_certificates"),
        )

        assert response.status_code == 200
        assert "enrollments/certificates.html" in [
            template.name for template in response.templates
        ]

    def test_non_student_cannot_access_certificates_page(
        self,
        client,
        test_user,
    ):
        client.force_login(test_user)

        response = client.get(
            reverse("enrollments:student_certificates"),
        )

        assert response.status_code == 404

    def test_unauthenticated_user_is_redirected(
        self,
        client,
    ):
        response = client.get(
            reverse("enrollments:student_certificates"),
        )

        assert response.status_code == 302
