import pytest
from django.contrib.auth import get_user_model

from accounts.models import Role

User = get_user_model()


@pytest.fixture
def test_user(db):
    return User.objects.create_user(
        username="test_user",
        email="test_user@example.com",
        password="test-password",
    )


@pytest.fixture
def instructor_role(db):
    return Role.objects.create(
        name=Role.Roles.INSTRUCTOR,
    )


@pytest.fixture
def student_role(db):
    return Role.objects.create(
        name=Role.Roles.STUDENT,
    )
