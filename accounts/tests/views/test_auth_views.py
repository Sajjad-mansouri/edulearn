import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestLoginView:
    url_name = "accounts:login"
    template_name = "accounts/login.html"

    def test_get_returns_200(self, client):
        response = client.get(reverse(self.url_name))

        assert response.status_code == 200

    def test_uses_correct_template(self, client):
        response = client.get(reverse(self.url_name))

        assert response.template_name == [self.template_name]

    def test_renders_correct_template(self, client):
        response = client.get(reverse(self.url_name))

        assert self.template_name in [template.name for template in response.templates]


@pytest.mark.django_db
class TestRegisterStudentView:
    url_name = "accounts:register_student"
    template_name = "accounts/register_student.html"

    def test_get_returns_200(self, client):
        response = client.get(reverse(self.url_name))

        assert response.status_code == 200

    def test_uses_correct_template(self, client):
        response = client.get(reverse(self.url_name))

        assert response.template_name == [self.template_name]

    def test_renders_correct_template(self, client):
        response = client.get(reverse(self.url_name))

        assert self.template_name in [template.name for template in response.templates]


@pytest.mark.django_db
class TestRegisterInstructorView:
    url_name = "accounts:register_instructor"
    template_name = "register/register_instructor.html"

    def test_get_returns_200(self, client):
        response = client.get(reverse(self.url_name))

        assert response.status_code == 200

    def test_uses_correct_template(self, client):
        response = client.get(reverse(self.url_name))

        assert response.template_name == [self.template_name]

    def test_renders_correct_template(self, client):
        response = client.get(reverse(self.url_name))

        assert self.template_name in [template.name for template in response.templates]
