from django.db.models import Count, Exists, OuterRef, Prefetch, Subquery

from curriculums.models import Attachment, LessonContent, Section
from enrollments.api.serializers.sections import EnrollmentSectionSerializer


def get_annotated_section(section):
    annotated_lessons = section.lessons.all().annotate(
        has_attachments=Exists(
            Attachment.objects.filter(lesson_content__lesson=OuterRef("pk"))
        ),
        attachment_count=Count(
            "content__attachments",
            distinct=True,
        ),
        type=Subquery(
            LessonContent.objects.filter(
                lesson=OuterRef("pk"),
                is_main_content=True,
            ).values("content_type")[:1]
        ),
    )

    return (
        Section.objects.filter(pk=section.pk)
        .prefetch_related(
            Prefetch(
                "lessons",
                queryset=annotated_lessons,
            )
        )
        .get()
    )


class TestEnrollmentSectionSerializer:
    def test_serializes_expected_fields(
        self,
        lesson_section,
        lesson,
        lesson_content,
        lesson_completion_criteria,
    ):
        section = get_annotated_section(lesson_section)

        data = EnrollmentSectionSerializer(instance=section).data

        assert set(data) == {
            "id",
            "title",
            "order",
            "lessons",
        }

    def test_serializes_section_fields(
        self,
        lesson_section,
        lesson,
        lesson_content,
        lesson_completion_criteria,
    ):
        section = get_annotated_section(lesson_section)

        data = EnrollmentSectionSerializer(instance=section).data

        assert data["id"] == lesson_section.id
        assert data["title"] == lesson_section.title
        assert data["order"] == lesson_section.order

    def test_serializes_nested_lessons(
        self,
        lesson_section,
        lesson,
        lesson_content,
        lesson_completion_criteria,
    ):
        section = get_annotated_section(lesson_section)

        data = EnrollmentSectionSerializer(instance=section).data

        assert len(data["lessons"]) == 1

        serialized_lesson = data["lessons"][0]

        assert serialized_lesson["id"] == lesson.id
        assert serialized_lesson["title"] == lesson.title
        assert serialized_lesson["order"] == lesson.order
        assert serialized_lesson["description"] == lesson.description

    def test_serializes_nested_lesson_type(
        self,
        lesson_section,
        lesson,
        lesson_content,
        lesson_completion_criteria,
    ):
        section = get_annotated_section(lesson_section)

        data = EnrollmentSectionSerializer(instance=section).data

        serialized_lesson = data["lessons"][0]

        assert serialized_lesson["type"] == LessonContent.Type.VIDEO

    def test_serializes_nested_completion_criteria(
        self,
        lesson_section,
        lesson,
        lesson_content,
        lesson_completion_criteria,
    ):
        section = get_annotated_section(lesson_section)

        data = EnrollmentSectionSerializer(instance=section).data

        serialized_lesson = data["lessons"][0]

        assert serialized_lesson["completion_criteria"] == {
            "criteria_type": lesson_completion_criteria.criteria_type,
            "video_watch_percentage": (
                lesson_completion_criteria.video_watch_percentage
            ),
            "quiz_passing_score": (lesson_completion_criteria.quiz_passing_score),
        }

    def test_serializes_empty_lessons(
        self,
        course,
    ):
        section = Section.objects.create(
            course=course,
            title="Empty Section",
            order=1,
        )

        section = get_annotated_section(section)

        data = EnrollmentSectionSerializer(instance=section).data

        assert data["lessons"] == []

    def test_serializes_multiple_lessons(
        self,
        lesson_section,
        lesson,
        lesson_content,
        lesson_completion_criteria,
    ):
        second_lesson = lesson.__class__.objects.create(
            section=lesson_section,
            title="Advanced Python",
            description="Advanced Python concepts.",
            slug="advanced-python",
            order=2,
        )

        LessonContent.objects.create(
            lesson=second_lesson,
            title="Advanced Video",
            content_type=LessonContent.Type.VIDEO,
            order=1,
            is_main_content=True,
        )

        from curriculums.models import LessonCompletionCriteria

        LessonCompletionCriteria.objects.create(
            lesson=second_lesson,
            criteria_type=LessonCompletionCriteria.CriteriaType.MANUAL,
        )

        section = get_annotated_section(lesson_section)

        data = EnrollmentSectionSerializer(instance=section).data

        assert len(data["lessons"]) == 2

        serialized_lessons = data["lessons"]

        assert serialized_lessons[0]["id"] == lesson.id
        assert serialized_lessons[1]["id"] == second_lesson.id

    def test_preserves_lesson_order(
        self,
        lesson_section,
        lesson,
        lesson_content,
        lesson_completion_criteria,
    ):
        second_lesson = lesson.__class__.objects.create(
            section=lesson_section,
            title="Second Lesson",
            description="Second lesson.",
            slug="second-lesson",
            order=2,
        )

        LessonContent.objects.create(
            lesson=second_lesson,
            title="Second Lesson Content",
            content_type=LessonContent.Type.ARTICLE,
            order=1,
            is_main_content=True,
        )

        from curriculums.models import LessonCompletionCriteria

        LessonCompletionCriteria.objects.create(
            lesson=second_lesson,
            criteria_type=LessonCompletionCriteria.CriteriaType.MANUAL,
        )

        section = get_annotated_section(lesson_section)

        data = EnrollmentSectionSerializer(instance=section).data

        assert [item["id"] for item in data["lessons"]] == [
            lesson.id,
            second_lesson.id,
        ]

        assert [item["order"] for item in data["lessons"]] == [1, 2]

    def test_does_not_expose_course(
        self,
        lesson_section,
        lesson,
        lesson_content,
        lesson_completion_criteria,
    ):
        section = get_annotated_section(lesson_section)

        data = EnrollmentSectionSerializer(instance=section).data

        assert "course" not in data

    def test_does_not_expose_description(
        self,
        lesson_section,
        lesson,
        lesson_content,
        lesson_completion_criteria,
    ):
        section = get_annotated_section(lesson_section)

        data = EnrollmentSectionSerializer(instance=section).data

        assert "description" not in data

    def test_does_not_expose_is_published(
        self,
        lesson_section,
        lesson,
        lesson_content,
        lesson_completion_criteria,
    ):
        section = get_annotated_section(lesson_section)

        data = EnrollmentSectionSerializer(instance=section).data

        assert "is_published" not in data

    def test_does_not_expose_duration(
        self,
        lesson_section,
        lesson,
        lesson_content,
        lesson_completion_criteria,
    ):
        section = get_annotated_section(lesson_section)

        data = EnrollmentSectionSerializer(instance=section).data

        assert "duration" not in data
