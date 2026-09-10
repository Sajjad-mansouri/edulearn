import shutil
import tempfile

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings

from courses.models.course import Course
from curriculums.models.lesson import Lesson
from curriculums.models.lesson_content import LessonContent
from curriculums.models.section import Section
from enrollments.models.enrollment import Enrollment

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
def course(db, test_user):
    return Course.objects.create(
        title="Django Development",
        owner=test_user,
    )


@pytest.fixture
def another_course(db, another_user):
    return Course.objects.create(
        title="Python Development",
        owner=another_user,
    )


@pytest.fixture
def section(db, course):
    return Section.objects.create(
        course=course,
        title="Introduction",
    )


@pytest.fixture
def lesson(db, section):
    return Lesson.objects.create(
        section=section,
        title="Getting Started",
        slug="getting-started",
    )


@pytest.fixture
def lesson_content(db, lesson):
    return LessonContent.objects.create(
        lesson=lesson,
        title="Introduction",
        content_type=LessonContent.Type.ARTICLE,
        order=1,
    )


@pytest.fixture
def enrollment(db, test_user, course):
    return Enrollment.objects.create(
        user=test_user,
        course=course,
        status=Enrollment.Status.ACTIVE,
    )


@pytest.fixture
def another_enrollment(db, another_user, another_course):
    return Enrollment.objects.create(
        user=another_user,
        course=another_course,
        status=Enrollment.Status.ACTIVE,
    )
