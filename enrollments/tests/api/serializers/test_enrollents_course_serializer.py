import pytest
from django.db.models import Count, Exists, OuterRef, Prefetch, Subquery

from courses.models import Course
from curriculums.models import Attachment, Lesson, LessonContent, Section
from enrollments.api.serializers.course import EnrollmentCourseSerializer


def get_annotated_course(course):
    annotated_lessons = Lesson.objects.filter(section__course=course).annotate(
        has_attachments=Exists(
            Attachment.objects.filter(
                lesson_content__lesson=OuterRef("pk"),
            )
        ),
        attachment_count=Count(
            "content__attachments",
            distinct=True,
        ),
        type=Subquery(
            LessonContent.objects.filter(
                lesson=OuterRef("pk"),
                is_main_content=True,
            ).values("content_type")[:1],
        ),
    )

    annotated_sections = Section.objects.filter(
        course=course,
    ).prefetch_related(
        Prefetch(
            "lessons",
            queryset=annotated_lessons,
        )
    )

    return (
        Course.objects.filter(pk=course.pk)
        .annotate(
            total_lessons=Count(
                "sections__lessons",
                distinct=True,
            )
        )
        .prefetch_related(
            Prefetch(
                "sections",
                queryset=annotated_sections,
            )
        )
        .get()
    )


@pytest.fixture
def course_with_sections(course):
    section = Section.objects.create(
        course=course,
        title="Python Basics",
        order=1,
    )

    lesson = Lesson.objects.create(
        section=section,
        title="Introduction to Python",
        description="Learn the fundamentals of Python.",
        slug="introduction-to-python",
        order=1,
    )

    LessonContent.objects.create(
        lesson=lesson,
        title="Introduction Video",
        content_type=LessonContent.Type.VIDEO,
        order=1,
        is_main_content=True,
    )

    return course


class TestEnrollmentCourseSerializer:
    def test_exposes_exact_fields(self, course):
        annotated_course = get_annotated_course(course)

        serializer = EnrollmentCourseSerializer(
            annotated_course,
            context={"enrollment_id": 123},
        )

        assert set(serializer.data) == {
            "courseId",
            "courseTitle",
            "totalLessons",
            "enrollmentId",
            "sections",
        }

    def test_serializes_course_id(self, course):
        serializer = EnrollmentCourseSerializer(
            course,
            context={"enrollment_id": 123},
        )

        assert serializer.data["courseId"] == course.id

    def test_serializes_course_title(self, course):
        serializer = EnrollmentCourseSerializer(
            course,
            context={"enrollment_id": 123},
        )

        assert serializer.data["courseTitle"] == course.title

    def test_serializes_annotated_total_lessons(self, course_with_sections):
        annotated_course = get_annotated_course(course_with_sections)

        serializer = EnrollmentCourseSerializer(
            annotated_course,
            context={"enrollment_id": 123},
        )

        assert serializer.data["totalLessons"] == 1

    def test_serializes_zero_total_lessons_when_course_has_no_lessons(
        self,
        course,
    ):
        annotated_course = get_annotated_course(course)

        serializer = EnrollmentCourseSerializer(
            annotated_course,
            context={"enrollment_id": 123},
        )

        assert serializer.data["totalLessons"] == 0

    def test_serializes_enrollment_id_from_context(self, course):
        enrollment_id = 456

        serializer = EnrollmentCourseSerializer(
            course,
            context={"enrollment_id": enrollment_id},
        )

        assert serializer.data["enrollmentId"] == enrollment_id

    def test_enrollment_id_is_not_taken_from_course(self, course):
        serializer = EnrollmentCourseSerializer(
            course,
            context={"enrollment_id": 789},
        )

        assert serializer.data["enrollmentId"] == 789

    def test_serializes_empty_sections(self, course):
        annotated_course = get_annotated_course(course)

        serializer = EnrollmentCourseSerializer(
            annotated_course,
            context={"enrollment_id": 123},
        )

        assert serializer.data["sections"] == []

    def test_serializes_nested_sections(self, course_with_sections):
        annotated_course = get_annotated_course(course_with_sections)

        serializer = EnrollmentCourseSerializer(
            annotated_course,
            context={"enrollment_id": 123},
        )

        assert len(serializer.data["sections"]) == 1

        section_data = serializer.data["sections"][0]

        assert section_data["id"] == course_with_sections.sections.first().id
        assert section_data["title"] == "Python Basics"
        assert section_data["order"] == 1

    def test_serializes_nested_lessons_inside_sections(
        self,
        course_with_sections,
    ):
        annotated_course = get_annotated_course(course_with_sections)

        serializer = EnrollmentCourseSerializer(
            annotated_course,
            context={"enrollment_id": 123},
        )

        section_data = serializer.data["sections"][0]

        assert len(section_data["lessons"]) == 1

        lesson_data = section_data["lessons"][0]

        assert lesson_data["title"] == "Introduction to Python"
        assert lesson_data["order"] == 1
        assert lesson_data["type"] == LessonContent.Type.VIDEO

    def test_serializes_multiple_sections_and_lessons(
        self,
        course_with_sections,
    ):
        second_section = Section.objects.create(
            course=course_with_sections,
            title="Advanced Python",
            order=2,
        )

        second_lesson = Lesson.objects.create(
            section=second_section,
            title="Advanced Functions",
            description="Learn advanced Python functions.",
            slug="advanced-functions",
            order=1,
        )

        LessonContent.objects.create(
            lesson=second_lesson,
            title="Advanced Functions Video",
            content_type=LessonContent.Type.VIDEO,
            order=1,
            is_main_content=True,
        )

        annotated_course = get_annotated_course(course_with_sections)

        serializer = EnrollmentCourseSerializer(
            annotated_course,
            context={"enrollment_id": 123},
        )

        data = serializer.data

        assert data["totalLessons"] == 2
        assert len(data["sections"]) == 2

        assert data["sections"][0]["title"] == "Python Basics"
        assert data["sections"][1]["title"] == "Advanced Python"

        assert len(data["sections"][0]["lessons"]) == 1
        assert len(data["sections"][1]["lessons"]) == 1

    def test_serializes_sections_in_model_order(
        self,
        course_with_sections,
    ):
        second_section = Section.objects.create(
            course=course_with_sections,
            title="Advanced Python",
            order=2,
        )

        second_lesson = Lesson.objects.create(
            section=second_section,
            title="Advanced Functions",
            description="Learn advanced Python functions.",
            slug="advanced-functions",
            order=1,
        )

        LessonContent.objects.create(
            lesson=second_lesson,
            title="Advanced Functions Video",
            content_type=LessonContent.Type.VIDEO,
            order=1,
            is_main_content=True,
        )

        annotated_course = get_annotated_course(course_with_sections)

        serializer = EnrollmentCourseSerializer(
            annotated_course,
            context={"enrollment_id": 123},
        )

        section_titles = [section["title"] for section in serializer.data["sections"]]

        assert section_titles == [
            "Python Basics",
            "Advanced Python",
        ]

    def test_does_not_expose_unlisted_course_fields(
        self,
        course,
    ):
        serializer = EnrollmentCourseSerializer(
            course,
            context={"enrollment_id": 123},
        )

        data = serializer.data

        assert "id" not in data
        assert "slug" not in data
        assert "description" not in data
        assert "owner" not in data
        assert "category" not in data
        assert "status" not in data
        assert "price" not in data
        assert "price_type" not in data

    def test_requires_enrollment_id_context(self, course):
        serializer = EnrollmentCourseSerializer(course)

        with pytest.raises(KeyError):
            _ = serializer.data

    def test_enrollment_id_can_be_any_context_value(self, course):
        enrollment_id = "enrollment-reference"

        serializer = EnrollmentCourseSerializer(
            course,
            context={"enrollment_id": enrollment_id},
        )

        assert serializer.data["enrollmentId"] == enrollment_id
