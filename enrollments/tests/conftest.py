import shutil
import tempfile

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings

from accounts.models import Role
from courses.models.category import Category
from courses.models.course import Course
from enrollments.models import Enrollment

User = get_user_model()


@pytest.fixture(autouse=True)
def media_root():
    temp_dir = tempfile.mkdtemp()

    with override_settings(MEDIA_ROOT=temp_dir):
        yield

    shutil.rmtree(temp_dir)


@pytest.fixture
def test_user(db):
    return User.objects.create_user(
        username="test_user",
        email="test_user@example.com",
        password="test-password",
    )


@pytest.fixture
def another_user(db):
    return User.objects.create_user(
        username="another_user",
        email="another_user@example.com",
        password="test-password",
    )


@pytest.fixture
def student_user(test_user):
    test_user.roles.create(name=Role.Roles.STUDENT)
    return test_user


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


@pytest.fixture
def enrollment(test_user, course):
    return Enrollment.objects.create(
        user=test_user,
        course=course,
        status=Enrollment.Status.ACTIVE,
    )


@pytest.fixture
def another_user_enrollment(another_user, course):
    return Enrollment.objects.create(
        user=another_user,
        course=course,
        status=Enrollment.Status.ACTIVE,
    )
