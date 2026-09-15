import pytest
from django.contrib.auth.models import AnonymousUser
from django.http import Http404, HttpResponse
from django.test import RequestFactory
from django.views import View

from accounts.mixins import InstructorRequiredMixin, StudentRequiredMixin
from accounts.models import Role


class InstructorOnlyView(InstructorRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return HttpResponse("instructor")


class StudentOnlyView(StudentRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return HttpResponse("student")


@pytest.fixture
def request_factory():
    return RequestFactory()


@pytest.fixture
def instructor_role(db):
    return Role.objects.create(name=Role.Roles.INSTRUCTOR)


@pytest.fixture
def student_role(db):
    return Role.objects.create(name=Role.Roles.STUDENT)


@pytest.mark.django_db
class TestInstructorRequiredMixin:
    def test_unauthenticated_user_is_redirected_to_login(
        self,
        request_factory,
    ):
        request = request_factory.get("/instructor/")
        request.user = AnonymousUser()

        response = InstructorOnlyView.as_view()(request)

        assert response.status_code == 302

    def test_instructor_can_access_view(
        self,
        request_factory,
        test_user,
        instructor_role,
    ):
        test_user.roles.add(instructor_role)

        request = request_factory.get("/instructor/")
        request.user = test_user

        response = InstructorOnlyView.as_view()(request)

        assert response.status_code == 200
        assert response.content == b"instructor"

    def test_user_without_instructor_role_gets_404(
        self,
        request_factory,
        test_user,
        student_role,
    ):
        test_user.roles.add(student_role)

        request = request_factory.get("/instructor/")
        request.user = test_user

        with pytest.raises(Http404):
            InstructorOnlyView.as_view()(request)

    def test_authenticated_user_without_any_role_gets_404(
        self,
        request_factory,
        test_user,
    ):
        request = request_factory.get("/instructor/")
        request.user = test_user

        with pytest.raises(Http404):
            InstructorOnlyView.as_view()(request)

    def test_user_with_both_roles_can_access_view(
        self,
        request_factory,
        test_user,
        instructor_role,
        student_role,
    ):
        test_user.roles.add(instructor_role, student_role)

        request = request_factory.get("/instructor/")
        request.user = test_user

        response = InstructorOnlyView.as_view()(request)

        assert response.status_code == 200
        assert response.content == b"instructor"


@pytest.mark.django_db
class TestStudentRequiredMixin:
    def test_unauthenticated_user_is_redirected_to_login(
        self,
        request_factory,
    ):
        request = request_factory.get("/student/")
        request.user = AnonymousUser()

        response = StudentOnlyView.as_view()(request)

        assert response.status_code == 302

    def test_student_can_access_view(
        self,
        request_factory,
        test_user,
        student_role,
    ):
        test_user.roles.add(student_role)

        request = request_factory.get("/student/")
        request.user = test_user

        response = StudentOnlyView.as_view()(request)

        assert response.status_code == 200
        assert response.content == b"student"

    def test_user_without_student_role_gets_404(
        self,
        request_factory,
        test_user,
        instructor_role,
    ):
        test_user.roles.add(instructor_role)

        request = request_factory.get("/student/")
        request.user = test_user

        with pytest.raises(Http404):
            StudentOnlyView.as_view()(request)

    def test_authenticated_user_without_any_role_gets_404(
        self,
        request_factory,
        test_user,
    ):
        request = request_factory.get("/student/")
        request.user = test_user

        with pytest.raises(Http404):
            StudentOnlyView.as_view()(request)

    def test_user_with_both_roles_can_access_view(
        self,
        request_factory,
        test_user,
        instructor_role,
        student_role,
    ):
        test_user.roles.add(instructor_role, student_role)

        request = request_factory.get("/student/")
        request.user = test_user

        response = StudentOnlyView.as_view()(request)

        assert response.status_code == 200
        assert response.content == b"student"
