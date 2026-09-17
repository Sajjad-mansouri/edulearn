# enrollments/tests/conftest.py

import pytest
from django.contrib.auth import get_user_model

from courses.models.category import Category
from courses.models.course import Course

User = get_user_model()


@pytest.fixture
def test_user(db):
    return User.objects.create_user(
        username="test_user",
        email="test_user@example.com",
        password="test-password",
    )


@pytest.fixture
def category(db):
    return Category.objects.create(
        name="Programming",
        slug="programming",
        description="Programming courses",
    )


@pytest.fixture
def course(test_user, category):
    return Course.objects.create(
        title="Django Development",
        owner=test_user,
        category=category,
    )
