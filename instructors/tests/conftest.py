import shutil
import tempfile

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings

from accounts.models import Role
from courses.models import Course
from enrollments.models import Enrollment

User = get_user_model()


@pytest.fixture(autouse=True)
def media_root():
    temp_dir = tempfile.mkdtemp()

    with override_settings(MEDIA_ROOT=temp_dir):
        yield

    shutil.rmtree(temp_dir)


@pytest.fixture
def instructor_user(db):
    user = User.objects.create_user(
        username="test_instructor",
        email="test_instructor@example.com",
        password="test-password",
    )

    role, _ = Role.objects.get_or_create(
        name=Role.Roles.INSTRUCTOR,
    )
    user.roles.add(role)

    return user


@pytest.fixture
def student_user(db):
    user = User.objects.create_user(
        username="test_student",
        email="test_student@example.com",
        password="test-password",
    )

    role, _ = Role.objects.get_or_create(
        name=Role.Roles.STUDENT,
    )
    user.roles.add(role)

    return user


@pytest.fixture
def instructor_course(db, instructor_user):
    return Course.objects.create(
        title="Django Testing",
        slug="django-testing",
        owner=instructor_user,
    )


@pytest.fixture
def instructor_enrollment(db, instructor_user, instructor_course):
    return Enrollment.objects.create(
        user=instructor_user,
        course=instructor_course,
    )
