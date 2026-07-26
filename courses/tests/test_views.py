import pytest
from django.urls import reverse
from pytest_django.asserts import assertTemplateUsed

from accounts.tests.factories import (
    RoleFactory,
    UserFactory,
)


@pytest.mark.django_db
class TestCourseCreateTemplateView:
    @pytest.fixture
    def url(self):
        return reverse("courses:create_course")

    @pytest.fixture
    def instructor_role(self):
        return RoleFactory(name="instructor")

    def test_anonymous_user_is_redirected_to_login(
        self,
        client,
        url,
    ):
        response = client.get(url)

        assert response.status_code == 302
        assert response.url.startswith(reverse("accounts:login"))

    def test_instructor_can_access_page(
        self,
        client,
        url,
        instructor_role,
    ):
        user = UserFactory()
        user.roles.add(instructor_role)

        client.force_login(user)

        response = client.get(url)

        assert response.status_code == 200
        assert "courses/create_course.html" in {
            template.name for template in response.templates
        }

    def test_authenticated_non_instructor_gets_404(
        self,
        client,
        url,
    ):
        user = UserFactory()

        client.force_login(user)

        response = client.get(url)

        assert response.status_code == 404

    def test_user_with_multiple_roles_including_instructor_can_access(
        self,
        client,
        url,
        instructor_role,
    ):
        student_role = RoleFactory(name="student")

        user = UserFactory()
        user.roles.add(
            student_role,
            instructor_role,
        )

        client.force_login(user)

        response = client.get(url)

        assert response.status_code == 200

    def test_correct_template_is_used(
        self,
        client,
        url,
        instructor_role,
    ):
        user = UserFactory()
        user.roles.add(instructor_role)

        client.force_login(user)

        response = client.get(url)

        assert response.status_code == 200
        assertTemplateUsed(
            response,
            "courses/create_course.html",
        )
