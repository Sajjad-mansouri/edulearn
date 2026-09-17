from datetime import timedelta

import pytest
from django.db.models import Count, Sum

from courses.api.serializers.course_curriculum import (
    CourseCurriculumSerializer,
    CoursesSectionLessonSerializer,
)
from curriculums.models import Lesson, LessonContent, Section, VideoContent

pytestmark = pytest.mark.django_db


class TestCoursesSectionLessonSerializer:
    @pytest.fixture
    def section(self, course):
        return Section.objects.create(
            course=course,
            title="Django Fundamentals",
            description="Django fundamentals section.",
            order=1,
            is_published=True,
            duration=timedelta(hours=2),
        )

    @pytest.fixture
    def lesson(self, section):
        return Lesson.objects.create(
            section=section,
            title="Introduction to Django",
            description="Introduction to Django.",
            slug="introduction-to-django",
            duration=timedelta(minutes=45),
            order=1,
            is_published=True,
            is_preview=True,
        )

    @pytest.fixture
    def lesson_without_content(self, section):
        return Lesson.objects.create(
            section=section,
            title="Lesson Without Content",
            description="Lesson without content.",
            slug="lesson-without-content",
            duration=timedelta(minutes=30),
            order=2,
            is_published=True,
            is_preview=False,
        )

    @pytest.fixture
    def lesson_content(self, lesson):
        return LessonContent.objects.create(
            lesson=lesson,
            is_main_content=True,
            title="Introduction Video",
            content_type=LessonContent.Type.VIDEO,
            order=1,
        )

    @pytest.fixture
    def video_content(self, lesson_content):
        return VideoContent.objects.create(
            content=lesson_content,
            source=VideoContent.Source.URL,
            external_url="https://example.com/video.mp4",
            duration=timedelta(minutes=40),
        )

    @pytest.fixture
    def serializer(self, lesson):
        return CoursesSectionLessonSerializer(lesson)

    def test_serializes_expected_fields(self, serializer):
        assert set(serializer.data.keys()) == {
            "id",
            "title",
            "type",
            "duration",
            "is_previewable",
            "video_url",
        }

    def test_serializes_id(self, serializer, lesson):
        assert serializer.data["id"] == lesson.id

    def test_serializes_title(self, serializer, lesson):
        assert serializer.data["title"] == lesson.title

    def test_type_returns_content_type(
        self,
        serializer,
        lesson_content,
    ):
        assert serializer.data["type"] == lesson_content.content_type

    def test_type_returns_none_when_lesson_has_no_content(
        self,
        lesson_without_content,
    ):
        serializer = CoursesSectionLessonSerializer(lesson_without_content)

        assert serializer.data["type"] is None

    def test_duration_uses_format_duration(
        self,
        lesson,
        mocker,
    ):
        mock_format_duration = mocker.patch(
            "courses.api.serializers.course_curriculum.format_duration",
            return_value="45 min",
        )

        serializer = CoursesSectionLessonSerializer(lesson)

        assert serializer.data["duration"] == "45 min"
        mock_format_duration.assert_called_once_with(lesson.duration)

    def test_is_previewable_returns_is_preview(
        self,
        serializer,
        lesson,
    ):
        assert serializer.data["is_previewable"] == lesson.is_preview

    def test_is_previewable_is_false_when_lesson_is_not_preview(
        self,
        lesson_without_content,
    ):
        serializer = CoursesSectionLessonSerializer(lesson_without_content)

        assert serializer.data["is_previewable"] is False

    def test_video_url_is_none_without_content(
        self,
        lesson_without_content,
    ):
        serializer = CoursesSectionLessonSerializer(lesson_without_content)

        assert serializer.data["video_url"] is None

    def test_video_url_is_none_for_non_video_content(
        self,
        lesson,
    ):
        LessonContent.objects.create(
            lesson=lesson,
            is_main_content=True,
            title="Article",
            content_type=LessonContent.Type.ARTICLE,
            order=1,
        )

        serializer = CoursesSectionLessonSerializer(lesson)

        assert serializer.data["video_url"] is None

    def test_serializes_video_lesson_type(
        self,
        lesson,
        lesson_content,
        video_content,
    ):
        serializer = CoursesSectionLessonSerializer(lesson)

        assert serializer.data["type"] == LessonContent.Type.VIDEO

    def test_serializer_does_not_modify_lesson(
        self,
        serializer,
        lesson,
    ):
        original_title = lesson.title
        original_duration = lesson.duration
        original_is_preview = lesson.is_preview

        lesson.refresh_from_db()

        assert lesson.title == original_title
        assert lesson.duration == original_duration
        assert lesson.is_preview == original_is_preview


class TestCourseCurriculumSerializer:
    @pytest.fixture
    def section(self, course):
        return Section.objects.create(
            course=course,
            title="Django Fundamentals",
            description="Django fundamentals section.",
            order=1,
            is_published=True,
        )

    @pytest.fixture
    def first_lesson(self, section):
        return Lesson.objects.create(
            section=section,
            title="Introduction to Django",
            description="Introduction to Django.",
            slug="introduction-to-django",
            duration=timedelta(minutes=30),
            order=1,
            is_published=True,
            is_preview=True,
        )

    @pytest.fixture
    def second_lesson(self, section):
        return Lesson.objects.create(
            section=section,
            title="Django Models",
            description="Working with Django models.",
            slug="django-models",
            duration=timedelta(minutes=45),
            order=2,
            is_published=True,
            is_preview=False,
        )

    @pytest.fixture
    def first_lesson_content(self, first_lesson):
        return LessonContent.objects.create(
            lesson=first_lesson,
            is_main_content=True,
            title="Introduction Video",
            content_type=LessonContent.Type.VIDEO,
            order=1,
        )

    @pytest.fixture
    def second_lesson_content(self, second_lesson):
        return LessonContent.objects.create(
            lesson=second_lesson,
            is_main_content=True,
            title="Models Video",
            content_type=LessonContent.Type.VIDEO,
            order=1,
        )

    @pytest.fixture
    def annotated_section(
        self,
        section,
        first_lesson,
        second_lesson,
    ):
        return (
            Section.objects.filter(pk=section.pk)
            .annotate(
                section_duration=Sum("lessons__duration"),
                lessons_count=Count(
                    "lessons",
                    distinct=True,
                ),
            )
            .get()
        )

    @pytest.fixture
    def serializer(self, annotated_section):
        return CourseCurriculumSerializer(
            annotated_section,
            context={},
        )

    def test_serializes_expected_fields(self, serializer):
        assert set(serializer.data.keys()) == {
            "id",
            "title",
            "total_duration",
            "lessons_count",
            "lessons",
        }

    def test_serializes_id(self, serializer, section):
        assert serializer.data["id"] == section.id

    def test_serializes_title(self, serializer, section):
        assert serializer.data["title"] == section.title

    def test_total_duration_uses_section_duration(
        self,
        annotated_section,
        mocker,
    ):
        mock_format_duration = mocker.patch(
            "courses.api.serializers.course_curriculum.format_duration",
            return_value="1h 15m",
        )

        serializer = CourseCurriculumSerializer(
            annotated_section,
        )

        result = serializer.get_total_duration(annotated_section)

        assert result == "1h 15m"

        mock_format_duration.assert_called_once_with(
            annotated_section.section_duration,
        )

    def test_lessons_count_is_serialized(
        self,
        serializer,
        annotated_section,
    ):
        assert serializer.data["lessons_count"] == (annotated_section.lessons_count)

    def test_lessons_are_nested(
        self,
        serializer,
        first_lesson,
        second_lesson,
        first_lesson_content,
        second_lesson_content,
    ):
        lessons = serializer.data["lessons"]

        assert len(lessons) == 2

        lesson_ids = {lesson["id"] for lesson in lessons}

        assert lesson_ids == {
            first_lesson.id,
            second_lesson.id,
        }

    def test_nested_lessons_contain_expected_fields(
        self,
        serializer,
        first_lesson,
        first_lesson_content,
    ):
        lesson = serializer.data["lessons"][0]

        assert set(lesson.keys()) == {
            "id",
            "title",
            "type",
            "duration",
            "is_previewable",
            "video_url",
        }

        assert lesson["id"] == first_lesson.id
        assert lesson["title"] == first_lesson.title
        assert lesson["type"] == first_lesson_content.content_type
        assert lesson["is_previewable"] == first_lesson.is_preview

    def test_nested_lessons_use_their_actual_durations(
        self,
        serializer,
        first_lesson,
        second_lesson,
        first_lesson_content,
        second_lesson_content,
    ):
        lessons = {lesson["id"]: lesson for lesson in serializer.data["lessons"]}

        assert lessons[first_lesson.id]["duration"]
        assert lessons[second_lesson.id]["duration"]

    def test_lessons_count_matches_related_lessons(
        self,
        annotated_section,
        first_lesson,
        second_lesson,
    ):
        assert annotated_section.lessons_count == 2

    def test_zero_lessons_are_supported(
        self,
        course,
    ):
        empty_section = Section.objects.create(
            course=course,
            title="Empty Section",
            description="Section without lessons.",
            order=1,
            is_published=True,
        )

        annotated_section = (
            Section.objects.filter(pk=empty_section.pk)
            .annotate(
                section_duration=Sum("lessons__duration"),
                lessons_count=Count(
                    "lessons",
                    distinct=True,
                ),
            )
            .get()
        )

        serializer = CourseCurriculumSerializer(
            annotated_section,
        )

        assert serializer.data["lessons_count"] == 0
        assert serializer.data["lessons"] == []

    def test_total_duration_is_formatted_as_zero_when_duration_is_none(
        self,
        course,
        mocker,
    ):
        section = Section.objects.create(
            course=course,
            title="Empty Section",
            order=1,
        )

        annotated_section = (
            Section.objects.filter(pk=section.pk)
            .annotate(
                section_duration=Sum("lessons__duration"),
                lessons_count=Count(
                    "lessons",
                    distinct=True,
                ),
            )
            .get()
        )

        mock_format_duration = mocker.patch(
            "courses.api.serializers.course_curriculum.format_duration",
            return_value="0m",
        )

        serializer = CourseCurriculumSerializer(
            annotated_section,
        )

        assert serializer.data["total_duration"] == "0m"

        mock_format_duration.assert_called_once_with(
            annotated_section.section_duration,
        )

    def test_serializer_does_not_modify_section(
        self,
        serializer,
        section,
    ):
        original_title = section.title

        section.refresh_from_db()

        assert section.title == original_title
