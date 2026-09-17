from datetime import timedelta
from unittest.mock import patch

from django.db.models import Count, Exists, OuterRef, Subquery

from curriculums.models import (
    Attachment,
    Lesson,
    LessonCompletionCriteria,
    LessonContent,
)
from enrollments.api.serializers.lessons import (
    EnrollmentLessonSerializer,
    LessonCompletionSerializer,
)


def get_annotated_lesson(lesson):
    return (
        Lesson.objects.filter(pk=lesson.pk)
        .annotate(
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
        .get()
    )


class TestLessonCompletionSerializer:
    def test_serializes_expected_fields(self, lesson_completion_criteria):
        data = LessonCompletionSerializer(instance=lesson_completion_criteria).data

        assert set(data) == {
            "criteria_type",
            "video_watch_percentage",
            "quiz_passing_score",
        }

    def test_serializes_manual_criteria(self, lesson_completion_criteria):
        data = LessonCompletionSerializer(instance=lesson_completion_criteria).data

        assert data == {
            "criteria_type": LessonCompletionCriteria.CriteriaType.MANUAL,
            "video_watch_percentage": None,
            "quiz_passing_score": None,
        }

    def test_serializes_video_completion_criteria(self, lesson):
        criteria = LessonCompletionCriteria.objects.create(
            lesson=lesson,
            criteria_type=(LessonCompletionCriteria.CriteriaType.WATCH_VIDEO),
            video_watch_percentage=80,
        )

        data = LessonCompletionSerializer(instance=criteria).data

        assert data == {
            "criteria_type": (LessonCompletionCriteria.CriteriaType.WATCH_VIDEO),
            "video_watch_percentage": 80,
            "quiz_passing_score": None,
        }

    def test_serializes_quiz_completion_criteria(self, lesson):
        criteria = LessonCompletionCriteria.objects.create(
            lesson=lesson,
            criteria_type=LessonCompletionCriteria.CriteriaType.PASS_QUIZ,
            quiz_passing_score=70,
        )

        data = LessonCompletionSerializer(instance=criteria).data

        assert data == {
            "criteria_type": (LessonCompletionCriteria.CriteriaType.PASS_QUIZ),
            "video_watch_percentage": None,
            "quiz_passing_score": 70,
        }

    def test_does_not_expose_lesson(self, lesson_completion_criteria):
        data = LessonCompletionSerializer(instance=lesson_completion_criteria).data

        assert "lesson" not in data

    def test_does_not_expose_timestamps(self, lesson_completion_criteria):
        data = LessonCompletionSerializer(instance=lesson_completion_criteria).data

        assert "created_at" not in data
        assert "updated_at" not in data


class TestEnrollmentLessonSerializer:
    def test_serializes_expected_fields(
        self,
        lesson,
        lesson_content,
        lesson_completion_criteria,
    ):
        annotated_lesson = get_annotated_lesson(lesson)

        data = EnrollmentLessonSerializer(instance=annotated_lesson).data

        assert set(data) == {
            "id",
            "title",
            "type",
            "duration",
            "duration_seconds",
            "order",
            "has_resources",
            "completion_criteria",
            "description",
        }

    def test_serializes_basic_lesson_fields(
        self,
        lesson,
        lesson_content,
        lesson_completion_criteria,
    ):
        annotated_lesson = get_annotated_lesson(lesson)

        data = EnrollmentLessonSerializer(instance=annotated_lesson).data

        assert data["id"] == lesson.id
        assert data["title"] == lesson.title
        assert data["order"] == lesson.order
        assert data["description"] == lesson.description

    def test_serializes_main_content_type(
        self,
        lesson,
        lesson_content,
        lesson_completion_criteria,
    ):
        annotated_lesson = get_annotated_lesson(lesson)

        data = EnrollmentLessonSerializer(instance=annotated_lesson).data

        assert data["type"] == LessonContent.Type.VIDEO

    def test_serializes_has_resources_false_without_attachment(
        self,
        lesson,
        lesson_content,
        lesson_completion_criteria,
    ):
        annotated_lesson = get_annotated_lesson(lesson)

        data = EnrollmentLessonSerializer(instance=annotated_lesson).data

        assert data["has_resources"] is False

    def test_serializes_has_resources_true_with_attachment(
        self,
        lesson,
        lesson_content,
        lesson_completion_criteria,
    ):
        Attachment.objects.create(
            course=lesson.section.course,
            lesson_content=lesson_content,
            file_url="https://example.com/resource.pdf",
            title="Resource",
        )

        annotated_lesson = get_annotated_lesson(lesson)

        data = EnrollmentLessonSerializer(instance=annotated_lesson).data

        assert data["has_resources"] is True

    def test_serializes_duration(
        self,
        lesson,
        lesson_content,
        lesson_completion_criteria,
    ):
        lesson.duration = timedelta(
            hours=1,
            minutes=30,
            seconds=15,
        )
        lesson.save()

        annotated_lesson = get_annotated_lesson(lesson)

        with patch(
            "enrollments.api.serializers.lessons.format_duration",
            return_value="1h 30m 15s",
        ) as format_duration:
            data = EnrollmentLessonSerializer(instance=annotated_lesson).data

        assert data["duration"] == "1h 30m 15s"
        format_duration.assert_called_once_with(lesson.duration)

    def test_serializes_duration_seconds(
        self,
        lesson,
        lesson_content,
        lesson_completion_criteria,
    ):
        lesson.duration = timedelta(
            hours=1,
            minutes=30,
            seconds=15,
        )
        lesson.save()

        annotated_lesson = get_annotated_lesson(lesson)

        data = EnrollmentLessonSerializer(instance=annotated_lesson).data

        assert data["duration_seconds"] == 5415.0

    def test_serializes_null_duration(
        self,
        lesson,
        lesson_content,
        lesson_completion_criteria,
    ):
        lesson.duration = None
        lesson.save()

        annotated_lesson = get_annotated_lesson(lesson)

        data = EnrollmentLessonSerializer(instance=annotated_lesson).data

        assert data["duration"] is None
        assert data["duration_seconds"] is None

    def test_serializes_completion_criteria(
        self,
        lesson,
        lesson_content,
        lesson_completion_criteria,
    ):
        annotated_lesson = get_annotated_lesson(lesson)

        data = EnrollmentLessonSerializer(instance=annotated_lesson).data

        assert data["completion_criteria"] == {
            "criteria_type": (lesson_completion_criteria.criteria_type),
            "video_watch_percentage": (
                lesson_completion_criteria.video_watch_percentage
            ),
            "quiz_passing_score": (lesson_completion_criteria.quiz_passing_score),
        }

    def test_serializes_video_completion_criteria(
        self,
        lesson,
        lesson_content,
    ):
        LessonCompletionCriteria.objects.create(
            lesson=lesson,
            criteria_type=(LessonCompletionCriteria.CriteriaType.WATCH_VIDEO),
            video_watch_percentage=90,
        )

        annotated_lesson = get_annotated_lesson(lesson)

        data = EnrollmentLessonSerializer(instance=annotated_lesson).data

        assert data["completion_criteria"] == {
            "criteria_type": (LessonCompletionCriteria.CriteriaType.WATCH_VIDEO),
            "video_watch_percentage": 90,
            "quiz_passing_score": None,
        }

    def test_serializes_quiz_completion_criteria(
        self,
        lesson,
        lesson_content,
    ):
        LessonCompletionCriteria.objects.create(
            lesson=lesson,
            criteria_type=LessonCompletionCriteria.CriteriaType.PASS_QUIZ,
            quiz_passing_score=75,
        )

        annotated_lesson = get_annotated_lesson(lesson)

        data = EnrollmentLessonSerializer(instance=annotated_lesson).data

        assert data["completion_criteria"] == {
            "criteria_type": (LessonCompletionCriteria.CriteriaType.PASS_QUIZ),
            "video_watch_percentage": None,
            "quiz_passing_score": 75,
        }

    def test_does_not_expose_section(
        self,
        lesson,
        lesson_content,
        lesson_completion_criteria,
    ):
        annotated_lesson = get_annotated_lesson(lesson)

        data = EnrollmentLessonSerializer(instance=annotated_lesson).data

        assert "section" not in data

    def test_does_not_expose_slug(
        self,
        lesson,
        lesson_content,
        lesson_completion_criteria,
    ):
        annotated_lesson = get_annotated_lesson(lesson)

        data = EnrollmentLessonSerializer(instance=annotated_lesson).data

        assert "slug" not in data

    def test_does_not_expose_is_published(
        self,
        lesson,
        lesson_content,
        lesson_completion_criteria,
    ):
        annotated_lesson = get_annotated_lesson(lesson)

        data = EnrollmentLessonSerializer(instance=annotated_lesson).data

        assert "is_published" not in data

    def test_does_not_expose_is_preview(
        self,
        lesson,
        lesson_content,
        lesson_completion_criteria,
    ):
        annotated_lesson = get_annotated_lesson(lesson)

        data = EnrollmentLessonSerializer(instance=annotated_lesson).data

        assert "is_preview" not in data
