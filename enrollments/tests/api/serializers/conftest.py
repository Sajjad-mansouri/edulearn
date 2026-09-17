import pytest
from django.contrib.auth import get_user_model

from accounts.models import Role
from assessments.models import Assignment, AssignmentSubmission
from courses.models.category import Category
from courses.models.course import Course
from curriculums.models import Lesson, LessonCompletionCriteria, LessonContent, Section
from enrollments.models import Enrollment

User = get_user_model()


@pytest.fixture
def assignment_submission_course(db):
    category = Category.objects.create(
        name="Programming",
        slug="programming",
        description="Programming courses",
    )

    owner = User.objects.create_user(
        username="assignment_owner",
        email="assignment_owner@example.com",
        password="test-password",
    )

    return Course.objects.create(
        title="Django Development",
        owner=owner,
        category=category,
    )


@pytest.fixture
def assignment_submission_student(db):
    user = User.objects.create_user(
        username="assignment_student",
        email="assignment_student@example.com",
        password="test-password",
    )

    user.roles.create(name=Role.Roles.STUDENT)

    return user


@pytest.fixture
def assignment_submission_enrollment(
    assignment_submission_course,
    assignment_submission_student,
):
    return Enrollment.objects.create(
        user=assignment_submission_student,
        course=assignment_submission_course,
        status=Enrollment.Status.ACTIVE,
    )


@pytest.fixture
def assignment_submission_assignment(assignment_submission_course):
    section = Section.objects.create(
        course=assignment_submission_course,
        title="Assignments",
        order=1,
    )

    lesson = Lesson.objects.create(
        section=section,
        title="Assignment Lesson",
        slug="assignment-lesson",
        order=1,
    )

    content = LessonContent.objects.create(
        lesson=lesson,
        title="Programming Assignment",
        content_type=LessonContent.Type.ASSIGNMENT,
        order=1,
        is_main_content=True,
    )

    return Assignment.objects.create(
        content=content,
        instructions="Complete the assignment.",
        passing_score=70,
        max_score=100,
        max_attempts=3,
        max_file_size_mb=50,
    )


@pytest.fixture
def assignment_submission(
    assignment_submission_assignment,
    assignment_submission_enrollment,
):
    return AssignmentSubmission.objects.create(
        assignment=assignment_submission_assignment,
        enrollment=assignment_submission_enrollment,
        attempt_number=1,
        status=AssignmentSubmission.Status.DRAFT,
        submission_text="Assignment submission.",
    )


@pytest.fixture
def attachment_lesson_content(course):
    section = Section.objects.create(
        course=course,
        title="Attachments",
        order=1,
    )

    lesson = Lesson.objects.create(
        section=section,
        title="Attachment Lesson",
        slug="attachment-lesson",
        order=1,
    )

    return LessonContent.objects.create(
        lesson=lesson,
        title="Lesson Attachment",
        content_type=LessonContent.Type.FILE,
        order=1,
        is_main_content=True,
    )


@pytest.fixture
def lesson_section(course):
    return Section.objects.create(
        course=course,
        title="Python Basics",
        order=1,
    )


@pytest.fixture
def lesson(lesson_section):
    return Lesson.objects.create(
        section=lesson_section,
        title="Introduction to Python",
        description="Learn the fundamentals of Python.",
        slug="introduction-to-python",
        order=1,
    )


@pytest.fixture
def lesson_content(lesson):
    return LessonContent.objects.create(
        lesson=lesson,
        title="Introduction Video",
        content_type=LessonContent.Type.VIDEO,
        order=1,
        is_main_content=True,
    )


@pytest.fixture
def lesson_completion_criteria(lesson):
    return LessonCompletionCriteria.objects.create(
        lesson=lesson,
        criteria_type=LessonCompletionCriteria.CriteriaType.MANUAL,
    )
