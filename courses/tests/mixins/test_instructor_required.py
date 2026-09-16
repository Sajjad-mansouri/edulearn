from urllib.parse import parse_qs, urlparse

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import RequestFactory
from django.views import View

from accounts.models import Role
from courses.mixins import InstructorRequiredMixin

User = get_user_model()

pytestmark = pytest.mark.django_db


class InstructorOnlyView(InstructorRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return HttpResponse("Instructor content")


class TestInstructorRequiredMixin:
    @pytest.fixture
    def request_factory(self):
        return RequestFactory()

    @pytest.fixture
    def instructor_role(self, db):
        return Role.objects.create(
            name=Role.Roles.INSTRUCTOR,
        )

    @pytest.fixture
    def student_role(self, db):
        return Role.objects.create(
            name=Role.Roles.STUDENT,
        )

    @pytest.fixture
    def view(self):
        return InstructorOnlyView.as_view()

    def test_anonymous_user_is_redirected_to_login(
        self,
        request_factory,
        view,
        settings,
    ):
        request = request_factory.get("/courses/create/")
        request.user = AnonymousUser()

        settings.LOGIN_URL = "/login/"

        response = view(request)

        assert response.status_code == 302
        assert response.url.startswith("/login/")

    def test_anonymous_user_redirect_contains_original_path(
        self,
        request_factory,
        view,
        settings,
    ):
        settings.LOGIN_URL = "/login/"

        request = request_factory.get("/courses/create/")

        request.user = AnonymousUser()

        response = view(request)

        assert response.status_code == 302
        assert response.url.startswith("/login/")
        query_params = parse_qs(urlparse(response.url).query)
        assert query_params["next"] == ["/courses/create/"]

    def test_authenticated_instructor_can_access_view(
        self,
        request_factory,
        view,
        test_user,
        instructor_role,
    ):
        instructor_role.users.add(test_user)

        request = request_factory.get("/courses/create/")
        request.user = test_user

        response = view(request)

        assert response.status_code == 200
        assert response.content == b"Instructor content"

    def test_authenticated_non_instructor_receives_404(
        self,
        request_factory,
        view,
        test_user,
    ):
        request = request_factory.get("/courses/create/")
        request.user = test_user

        with pytest.raises(Exception) as exc_info:
            view(request)

        assert exc_info.value.__class__.__name__ == "Http404"

    def test_student_cannot_access_instructor_view(
        self,
        request_factory,
        view,
        test_user,
        student_role,
    ):
        student_role.users.add(test_user)

        request = request_factory.get("/courses/create/")
        request.user = test_user

        with pytest.raises(Exception) as exc_info:
            view(request)

        assert exc_info.value.__class__.__name__ == "Http404"

    def test_user_with_no_roles_cannot_access_view(
        self,
        request_factory,
        view,
        test_user,
    ):
        request = request_factory.get("/courses/create/")
        request.user = test_user

        with pytest.raises(Exception) as exc_info:
            view(request)

        assert exc_info.value.__class__.__name__ == "Http404"

    def test_user_with_both_student_and_instructor_roles_can_access_view(
        self,
        request_factory,
        view,
        test_user,
        student_role,
        instructor_role,
    ):
        student_role.users.add(test_user)
        instructor_role.users.add(test_user)

        request = request_factory.get("/courses/create/")
        request.user = test_user

        response = view(request)

        assert response.status_code == 200
        assert response.content == b"Instructor content"

    def test_instructor_role_is_checked_by_role_name(
        self,
        request_factory,
        view,
        test_user,
        db,
    ):
        Role.objects.create(
            name="teacher",
        )

        request = request_factory.get("/courses/create/")
        request.user = test_user

        with pytest.raises(Exception) as exc_info:
            view(request)

        assert exc_info.value.__class__.__name__ == "Http404"

    def test_instructor_role_allows_access_even_with_other_roles(
        self,
        request_factory,
        view,
        test_user,
        instructor_role,
        student_role,
    ):
        instructor_role.users.add(test_user)
        student_role.users.add(test_user)

        request = request_factory.get("/courses/create/")
        request.user = test_user

        response = view(request)

        assert response.status_code == 200

    def test_post_request_is_allowed_for_authenticated_instructor(
        self,
        request_factory,
        view,
        test_user,
        instructor_role,
    ):
        instructor_role.users.add(test_user)

        request = request_factory.post("/courses/create/")
        request.user = test_user

        response = view(request)

        assert response.status_code == 405
