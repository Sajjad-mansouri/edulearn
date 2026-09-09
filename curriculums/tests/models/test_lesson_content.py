import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from curriculums.models import Lesson, LessonContent


@pytest.mark.django_db
class TestLessonContentModel:
    def test_create_lesson_content(self, lesson):
        content = LessonContent.objects.create(
            lesson=lesson,
            title="Introduction Article",
            content_type=LessonContent.Type.ARTICLE,
            order=1,
        )

        assert content.pk is not None
        assert content.lesson == lesson
        assert content.title == "Introduction Article"
        assert content.content_type == LessonContent.Type.ARTICLE
        assert content.order == 1
        assert content.is_main_content is True

    def test_is_main_content_defaults_to_true(self, lesson):
        content = LessonContent.objects.create(
            lesson=lesson,
            title="Main Content",
            content_type=LessonContent.Type.ARTICLE,
            order=1,
        )

        assert content.is_main_content is True

    def test_is_main_content_can_be_false(self, lesson):
        content = LessonContent.objects.create(
            lesson=lesson,
            title="Supplementary Content",
            content_type=LessonContent.Type.FILE,
            order=1,
            is_main_content=False,
        )

        assert content.is_main_content is False

    def test_str_returns_title(self, lesson):
        content = LessonContent.objects.create(
            lesson=lesson,
            title="Introduction",
            content_type=LessonContent.Type.ARTICLE,
            order=1,
        )

        assert str(content) == "Introduction"

    def test_str_returns_lesson_title_when_title_is_empty(self, lesson):
        content = LessonContent(
            lesson=lesson,
            title="",
            content_type=LessonContent.Type.ARTICLE,
            order=1,
        )

        assert str(content) == f"{lesson.title} content"

    def test_reverse_lesson_relation(self, lesson):
        content = LessonContent.objects.create(
            lesson=lesson,
            title="Introduction",
            content_type=LessonContent.Type.ARTICLE,
            order=1,
        )

        assert lesson.content == content

    def test_lesson_is_required(self):
        content = LessonContent(
            title="Introduction",
            content_type=LessonContent.Type.ARTICLE,
            order=1,
        )

        with pytest.raises(ValidationError) as exc_info:
            content.full_clean()

        assert "lesson" in exc_info.value.message_dict

    def test_title_is_required(self, lesson):
        content = LessonContent(
            lesson=lesson,
            content_type=LessonContent.Type.ARTICLE,
            order=1,
        )

        with pytest.raises(ValidationError) as exc_info:
            content.full_clean()

        assert "title" in exc_info.value.message_dict

    def test_content_type_is_required(self, lesson):
        content = LessonContent(
            lesson=lesson,
            title="Introduction",
            order=1,
        )

        with pytest.raises(ValidationError) as exc_info:
            content.full_clean()

        assert "content_type" in exc_info.value.message_dict

    def test_order_is_required(self, lesson):
        content = LessonContent(
            lesson=lesson,
            title="Introduction",
            content_type=LessonContent.Type.ARTICLE,
        )

        with pytest.raises(ValidationError) as exc_info:
            content.full_clean()

        assert "order" in exc_info.value.message_dict

    @pytest.mark.parametrize(
        "content_type",
        [
            LessonContent.Type.VIDEO,
            LessonContent.Type.ARTICLE,
            LessonContent.Type.FILE,
            LessonContent.Type.QUIZ,
            LessonContent.Type.ASSIGNMENT,
            LessonContent.Type.LIVE_SESSION,
            LessonContent.Type.CODING_EXERCISE,
        ],
    )
    def test_all_content_types_are_valid(
        self,
        lesson,
        content_type,
    ):
        content = LessonContent(
            lesson=lesson,
            title="Lesson Content",
            content_type=content_type,
            order=1,
        )

        content.full_clean()

    def test_invalid_content_type_is_rejected(self, lesson):
        content = LessonContent(
            lesson=lesson,
            title="Lesson Content",
            content_type="invalid_type",
            order=1,
        )

        with pytest.raises(ValidationError) as exc_info:
            content.full_clean()

        assert "content_type" in exc_info.value.message_dict

    def test_title_cannot_exceed_max_length(self, lesson):
        content = LessonContent(
            lesson=lesson,
            title="a" * 256,
            content_type=LessonContent.Type.ARTICLE,
            order=1,
        )

        with pytest.raises(ValidationError) as exc_info:
            content.full_clean()

        assert "title" in exc_info.value.message_dict

    def test_title_at_max_length_is_valid(self, lesson):
        content = LessonContent(
            lesson=lesson,
            title="a" * 255,
            content_type=LessonContent.Type.ARTICLE,
            order=1,
        )

        content.full_clean()

        assert len(content.title) == 255

    @pytest.mark.parametrize(
        "order",
        [0, 1, 2, 100, 65535],
    )
    def test_valid_order_values(self, lesson, order):
        content = LessonContent(
            lesson=lesson,
            title=f"Content {order}",
            content_type=LessonContent.Type.ARTICLE,
            order=order,
        )

        content.full_clean()

        assert content.order == order

    def test_negative_order_is_rejected(self, lesson):
        content = LessonContent(
            lesson=lesson,
            title="Introduction",
            content_type=LessonContent.Type.ARTICLE,
            order=-1,
        )

        with pytest.raises(ValidationError) as exc_info:
            content.full_clean()

        assert "order" in exc_info.value.message_dict

    def test_one_lesson_can_have_only_one_content(
        self,
        lesson,
    ):
        LessonContent.objects.create(
            lesson=lesson,
            title="First Content",
            content_type=LessonContent.Type.ARTICLE,
            order=1,
        )

        second = LessonContent(
            lesson=lesson,
            title="Second Content",
            content_type=LessonContent.Type.VIDEO,
            order=2,
        )

        with pytest.raises(ValidationError) as exc_info:
            second.full_clean()

        assert "lesson" in exc_info.value.message_dict

    def test_one_lesson_can_have_only_one_content_at_database_level(
        self,
        lesson,
    ):
        LessonContent.objects.create(
            lesson=lesson,
            title="First Content",
            content_type=LessonContent.Type.ARTICLE,
            order=1,
        )

        with pytest.raises(IntegrityError):
            LessonContent.objects.create(
                lesson=lesson,
                title="Second Content",
                content_type=LessonContent.Type.VIDEO,
                order=2,
            )

    def test_same_order_is_allowed_for_different_lessons(
        self,
        lesson,
        section,
    ):
        another_lesson = Lesson.objects.create(
            section=section,
            title="Another Lesson",
            slug="another-lesson",
            order=2,
        )

        first = LessonContent.objects.create(
            lesson=lesson,
            title="First Content",
            content_type=LessonContent.Type.ARTICLE,
            order=1,
        )

        second = LessonContent.objects.create(
            lesson=another_lesson,
            title="Second Content",
            content_type=LessonContent.Type.ARTICLE,
            order=1,
        )

        assert first.order == second.order == 1

    def test_deleting_lesson_deletes_content(
        self,
        lesson,
    ):
        content = LessonContent.objects.create(
            lesson=lesson,
            title="Introduction",
            content_type=LessonContent.Type.ARTICLE,
            order=1,
        )
        content_id = content.pk

        lesson.delete()

        assert not LessonContent.objects.filter(pk=content_id).exists()

    def test_content_can_be_updated(self, lesson):
        content = LessonContent.objects.create(
            lesson=lesson,
            title="Introduction",
            content_type=LessonContent.Type.ARTICLE,
            order=1,
        )

        content.title = "Updated Introduction"
        content.content_type = LessonContent.Type.VIDEO
        content.is_main_content = False
        content.save()

        content.refresh_from_db()

        assert content.title == "Updated Introduction"
        assert content.content_type == LessonContent.Type.VIDEO
        assert content.is_main_content is False

    def test_ordering_is_by_lesson_then_order(
        self,
        section,
    ):
        first_lesson = Lesson.objects.create(
            section=section,
            title="First Lesson",
            slug="first-lesson",
            order=1,
        )
        second_lesson = Lesson.objects.create(
            section=section,
            title="Second Lesson",
            slug="second-lesson",
            order=2,
        )

        first_content = LessonContent.objects.create(
            lesson=first_lesson,
            title="First Content",
            content_type=LessonContent.Type.ARTICLE,
            order=1,
        )

        second_content = LessonContent.objects.create(
            lesson=second_lesson,
            title="Second Content",
            content_type=LessonContent.Type.ARTICLE,
            order=1,
        )

        contents = list(LessonContent.objects.all())

        assert contents == [
            first_content,
            second_content,
        ]
