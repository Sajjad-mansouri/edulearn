import pytest
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIRequestFactory

from enrollments.api.permissions import IsEnrolled, IsOwner, IsStudent
from enrollments.models import Enrollment


class DummyView:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class TestIsEnrolled:
    @pytest.fixture
    def factory(self):
        return APIRequestFactory()

    @pytest.fixture
    def permission(self):
        return IsEnrolled()

    def test_authenticated_user_with_active_enrollment_has_permission(
        self,
        factory,
        permission,
        test_user,
        enrollment,
    ):
        request = factory.get("/")
        request.user = test_user

        view = DummyView(
            enrollment_id=enrollment.id,
        )

        result = permission.has_permission(request, view)

        assert result is True
        assert view.enrollment == enrollment

    def test_authenticated_user_with_completed_enrollment_has_permission(
        self,
        factory,
        permission,
        test_user,
        course,
    ):
        enrollment = Enrollment.objects.create(
            user=test_user,
            course=course,
            status=Enrollment.Status.COMPLETED,
        )

        request = factory.get("/")
        request.user = test_user

        view = DummyView(
            enrollment_id=enrollment.id,
        )

        result = permission.has_permission(request, view)

        assert result is True
        assert view.enrollment == enrollment

    @pytest.mark.parametrize(
        "status",
        [
            Enrollment.Status.PENDING,
            Enrollment.Status.CANCELLED,
            Enrollment.Status.SUSPENDED,
        ],
    )
    def test_user_without_active_or_completed_enrollment_is_denied(
        self,
        factory,
        permission,
        test_user,
        course,
        status,
    ):
        enrollment = Enrollment.objects.create(
            user=test_user,
            course=course,
            status=status,
        )

        request = factory.get("/")
        request.user = test_user

        view = DummyView(
            enrollment_id=enrollment.id,
        )

        result = permission.has_permission(request, view)

        assert result is False
        assert not hasattr(view, "enrollment")

    def test_user_cannot_access_another_users_enrollment(
        self,
        factory,
        permission,
        test_user,
        another_user_enrollment,
    ):
        request = factory.get("/")
        request.user = test_user

        view = DummyView(
            enrollment_id=another_user_enrollment.id,
        )

        result = permission.has_permission(request, view)

        assert result is False
        assert not hasattr(view, "enrollment")

    def test_nonexistent_enrollment_is_denied(
        self,
        factory,
        permission,
        test_user,
    ):
        request = factory.get("/")
        request.user = test_user

        view = DummyView(
            enrollment_id=999999,
        )

        result = permission.has_permission(request, view)

        assert result is False
        assert not hasattr(view, "enrollment")

    def test_unauthenticated_user_is_denied(
        self,
        factory,
        permission,
    ):
        request = factory.get("/")
        request.user = AnonymousUser()

        view = DummyView(
            enrollment_id=1,
        )

        result = permission.has_permission(request, view)

        assert result is False
        assert not hasattr(view, "enrollment")

    def test_missing_enrollment_id_is_denied(
        self,
        factory,
        permission,
        test_user,
    ):
        request = factory.get("/")
        request.user = test_user

        view = DummyView()

        result = permission.has_permission(request, view)

        assert result is False
        assert not hasattr(view, "enrollment")

    def test_empty_enrollment_id_is_denied(
        self,
        factory,
        permission,
        test_user,
    ):
        request = factory.get("/")
        request.user = test_user

        view = DummyView(
            enrollment_id=None,
        )

        result = permission.has_permission(request, view)

        assert result is False
        assert not hasattr(view, "enrollment")

    def test_permission_uses_authenticated_users_enrollment(
        self,
        factory,
        permission,
        test_user,
        course,
    ):
        enrollment = Enrollment.objects.create(
            user=test_user,
            course=course,
            status=Enrollment.Status.ACTIVE,
        )

        request = factory.get("/")
        request.user = test_user

        view = DummyView(
            enrollment_id=enrollment.id,
        )

        result = permission.has_permission(request, view)

        assert result is True
        assert view.enrollment.pk == enrollment.pk
        assert view.enrollment.user_id == test_user.pk
        assert view.enrollment.course_id == course.pk

    def test_resolved_enrollment_has_course_loaded(
        self,
        factory,
        permission,
        test_user,
        enrollment,
    ):
        request = factory.get("/")
        request.user = test_user

        view = DummyView(
            enrollment_id=enrollment.id,
        )

        result = permission.has_permission(request, view)

        assert result is True
        assert view.enrollment.course.pk == enrollment.course.pk

        assert "course" in view.enrollment._state.fields_cache


class TestIsOwner:
    def setup_method(self):
        self.factory = APIRequestFactory()
        self.permission = IsOwner()

    def _request(self, user):
        request = self.factory.get("/api/courses/")
        request.user = user
        return request

    def test_authenticated_course_owner_has_permission(
        self,
        test_user,
        course,
    ):
        # Arrange
        request = self._request(test_user)
        view = DummyView(course_id=course.id)

        # Act
        result = self.permission.has_permission(request, view)

        # Assert
        assert result is True
        assert view.enrollment is None

    def test_authenticated_non_owner_does_not_have_permission(
        self,
        another_user,
        course,
    ):
        # Arrange
        request = self._request(another_user)
        view = DummyView(course_id=course.id)

        # Act
        result = self.permission.has_permission(request, view)

        # Assert
        assert result is False
        assert not hasattr(view, "enrollment")

    def test_unauthenticated_user_does_not_have_permission(
        self,
        course,
    ):
        # Arrange
        request = self._request(AnonymousUser())
        view = DummyView(course_id=course.id)

        # Act
        result = self.permission.has_permission(request, view)

        # Assert
        assert result is False
        assert not hasattr(view, "enrollment")

    def test_nonexistent_course_does_not_have_permission(
        self,
        test_user,
    ):
        # Arrange
        request = self._request(test_user)
        view = DummyView(course_id=999999)

        # Act
        result = self.permission.has_permission(request, view)

        # Assert
        assert result is False
        assert not hasattr(view, "enrollment")

    def test_missing_course_id_does_not_have_permission(
        self,
        test_user,
    ):
        # Arrange
        request = self._request(test_user)
        view = DummyView()

        # Act
        result = self.permission.has_permission(request, view)

        # Assert
        assert result is False
        assert not hasattr(view, "enrollment")

    def test_empty_course_id_does_not_have_permission(
        self,
        test_user,
    ):
        # Arrange
        request = self._request(test_user)
        view = DummyView(course_id=None)

        # Act
        result = self.permission.has_permission(request, view)

        # Assert
        assert result is False
        assert not hasattr(view, "enrollment")

    def test_owner_permission_does_not_depend_on_enrollment(
        self,
        test_user,
        course,
    ):
        # Arrange
        request = self._request(test_user)
        view = DummyView(course_id=course.id)

        # Act
        result = self.permission.has_permission(request, view)

        # Assert
        assert result is True
        assert view.enrollment is None


class TestIsStudent:
    def setup_method(self):
        self.factory = APIRequestFactory()
        self.permission = IsStudent()

    def _request(self, user):
        request = self.factory.get("/api/enrollments/")
        request.user = user
        return request

    def test_student_user_has_permission(self, student_user):
        # Arrange
        request = self._request(student_user)
        view = object()

        # Act
        result = self.permission.has_permission(request, view)

        # Assert
        assert result is True

    def test_authenticated_user_without_student_role_does_not_have_permission(
        self,
        test_user,
    ):
        # Arrange
        request = self._request(test_user)
        view = object()

        # Act
        result = self.permission.has_permission(request, view)

        # Assert
        assert result is False

    def test_unauthenticated_user_does_not_have_permission(self):
        # Arrange
        request = self._request(AnonymousUser())
        view = object()

        # Act
        result = self.permission.has_permission(request, view)

        # Assert
        assert result is False

    def test_instructor_role_alone_does_not_grant_student_permission(
        self,
        another_user,
    ):
        # Arrange
        another_user.roles.create(name="instructor")
        request = self._request(another_user)
        view = object()

        # Act
        result = self.permission.has_permission(request, view)

        # Assert
        assert result is False

    def test_user_with_student_role_has_permission(
        self,
        test_user,
    ):
        # Arrange
        test_user.roles.create(name="student")
        request = self._request(test_user)
        view = object()

        # Act
        result = self.permission.has_permission(request, view)

        # Assert
        assert result is True
