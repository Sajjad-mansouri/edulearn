import shutil
import tempfile

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings

from courses.models import Course
from curriculums.models import FileContent, Lesson, LessonContent, Section

User = get_user_model()


@pytest.fixture
def lesson_content(db, lesson):
    return LessonContent.objects.create(
        lesson=lesson,
        title="File Content",
        content_type=LessonContent.Type.FILE,
        order=1,
    )


@pytest.fixture
def file_content(db, lesson_content):
    return FileContent.objects.create(
        content=lesson_content,
        file_url="https://example.com/material.pdf",
    )


@pytest.fixture
def test_user(db):
    return User.objects.create_user(
        username="test_user",
        email="test_user@example.com",
        password="test-password",
    )


@pytest.fixture
def course(db, test_user):
    return Course.objects.create(
        title="Django Development",
        owner=test_user,
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


@pytest.fixture(autouse=True)
def media_root():
    temp_dir = tempfile.mkdtemp()

    with override_settings(MEDIA_ROOT=temp_dir):
        yield

    shutil.rmtree(temp_dir)
