import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import Http404, HttpResponse
from django.test import RequestFactory
from django.views import View

from courses.models.category import Category
from courses.models.course import Course
from enrollments.mixins import EnrollmentOrOwnerRequiredMixin
from enrollments.models import Enrollment

User = get_user_model()


class TestEnrollmentOrOwnerRequiredMixin:
    @pytest.fixture
    def request_factory(self):
        return RequestFactory()

    @pytest.fixture
    def test_user(self, db):
        return User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

    @pytest.fixture
    def another_user(self, db):
        return User.objects.create_user(
            username="another_user",
            email="another_user@example.com",
            password="test-password",
        )

    @pytest.fixture
    def category(self, db):
        return Category.objects.create(
            name="Programming",
            slug="programming",
            description="Programming courses",
        )

    @pytest.fixture
    def course(self, test_user, category):
        return Course.objects.create(
            title="Django Development",
            owner=test_user,
            category=category,
        )

    @pytest.fixture
    def enrollment(self, test_user, course):
        return Enrollment.objects.create(
            user=test_user,
            course=course,
            status=Enrollment.Status.ACTIVE,
        )

    @pytest.fixture
    def completed_enrollment(self, test_user, course):
        return Enrollment.objects.create(
            user=test_user,
            course=course,
            status=Enrollment.Status.COMPLETED,
        )

    @staticmethod
    def get_view():
        class TestView(EnrollmentOrOwnerRequiredMixin, View):
            def get(self, request, *args, **kwargs):
                return HttpResponse("success")

        return TestView.as_view()

    def test_authenticated_user_with_active_enrollment_can_access(
        self,
        request_factory,
        test_user,
        enrollment,
    ):
        # Arrange
        request = request_factory.get("/enrollments/")
        request.user = test_user

        view = self.get_view()

        # Act
        response = view(
            request,
            enrollment_id=enrollment.id,
        )

        # Assert
        assert response.status_code == 200
        assert response.content == b"success"

    def test_authenticated_user_with_completed_enrollment_can_access(
        self,
        request_factory,
        test_user,
        completed_enrollment,
    ):
        # Arrange
        request = request_factory.get("/enrollments/")
        request.user = test_user

        view = self.get_view()

        # Act
        response = view(
            request,
            enrollment_id=completed_enrollment.id,
        )

        # Assert
        assert response.status_code == 200
        assert response.content == b"success"

    @pytest.mark.parametrize(
        "enrollment_status",
        [
            Enrollment.Status.PENDING,
            Enrollment.Status.CANCELLED,
            Enrollment.Status.SUSPENDED,
        ],
    )
    def test_user_cannot_access_enrollment_with_invalid_status(
        self,
        request_factory,
        test_user,
        course,
        enrollment_status,
    ):
        # Arrange
        enrollment = Enrollment.objects.create(
            user=test_user,
            course=course,
            status=enrollment_status,
        )

        request = request_factory.get("/enrollments/")
        request.user = test_user

        view = self.get_view()

        # Act / Assert
        with pytest.raises(Http404):
            view(
                request,
                enrollment_id=enrollment.id,
            )

    def test_user_cannot_access_another_users_enrollment(
        self,
        request_factory,
        test_user,
        another_user,
        course,
    ):
        # Arrange
        enrollment = Enrollment.objects.create(
            user=another_user,
            course=course,
            status=Enrollment.Status.ACTIVE,
        )

        request = request_factory.get("/enrollments/")
        request.user = test_user

        view = self.get_view()

        # Act / Assert
        with pytest.raises(Http404):
            view(
                request,
                enrollment_id=enrollment.id,
            )

    def test_nonexistent_enrollment_returns_404(
        self,
        request_factory,
        test_user,
    ):
        # Arrange
        request = request_factory.get("/enrollments/")
        request.user = test_user

        view = self.get_view()

        # Act / Assert
        with pytest.raises(Http404):
            view(
                request,
                enrollment_id=999999,
            )

    def test_authenticated_course_owner_can_access_without_enrollment(
        self,
        request_factory,
        test_user,
        course,
    ):
        # Arrange
        request = request_factory.get("/courses/")
        request.user = test_user

        view = self.get_view()

        # Act
        response = view(
            request,
            course_id=course.id,
        )

        # Assert
        assert response.status_code == 200
        assert response.content == b"success"

    def test_course_owner_branch_sets_enrollment_to_none(
        self,
        request_factory,
        test_user,
        course,
    ):
        # Arrange
        request = request_factory.get("/courses/")
        request.user = test_user

        captured_enrollment = {}

        class TestView(EnrollmentOrOwnerRequiredMixin, View):
            def get(self, request, *args, **kwargs):
                captured_enrollment["value"] = self.enrollment
                return HttpResponse("success")

        view = TestView.as_view()

        # Act
        response = view(
            request,
            course_id=course.id,
        )

        # Assert
        assert response.status_code == 200
        assert response.content == b"success"
        assert captured_enrollment["value"] is None

    def test_non_owner_cannot_access_course_owner_branch(
        self,
        request_factory,
        another_user,
        course,
    ):
        # Arrange
        request = request_factory.get("/courses/")
        request.user = another_user

        view = self.get_view()

        # Act / Assert
        with pytest.raises(Http404):
            view(
                request,
                course_id=course.id,
            )

    def test_nonexistent_course_returns_404(
        self,
        request_factory,
        test_user,
    ):
        # Arrange
        request = request_factory.get("/courses/")
        request.user = test_user

        view = self.get_view()

        # Act / Assert
        with pytest.raises(Http404):
            view(
                request,
                course_id=999999,
            )

    def test_missing_enrollment_id_and_course_id_returns_404(
        self,
        request_factory,
        test_user,
    ):
        # Arrange
        request = request_factory.get("/enrollments/")
        request.user = test_user

        view = self.get_view()

        # Act / Assert
        with pytest.raises(Http404):
            view(request)

    def test_unauthenticated_user_is_redirected_to_login(
        self,
        request_factory,
        settings,
    ):
        # Arrange
        settings.LOGIN_URL = "/accounts/login/"

        request = request_factory.get("/enrollments/")
        request.user = AnonymousUser()

        view = self.get_view()

        # Act
        response = view(
            request,
            enrollment_id=999999,
        )

        # Assert
        assert response.status_code == 302
        assert response.url.startswith("/accounts/login/")

    def test_authenticated_enrollment_is_attached_to_view(
        self,
        request_factory,
        test_user,
        enrollment,
    ):
        # Arrange
        request = request_factory.get("/enrollments/")
        request.user = test_user

        captured_enrollment = {}

        class TestView(EnrollmentOrOwnerRequiredMixin, View):
            def get(self, request, *args, **kwargs):
                captured_enrollment["value"] = self.enrollment
                return HttpResponse("success")

        view = TestView.as_view()

        # Act
        response = view(
            request,
            enrollment_id=enrollment.id,
        )

        # Assert
        assert response.status_code == 200
        assert captured_enrollment["value"].pk == enrollment.pk
        assert captured_enrollment["value"].course_id == enrollment.course_id
        assert captured_enrollment["value"].user_id == enrollment.user_id
