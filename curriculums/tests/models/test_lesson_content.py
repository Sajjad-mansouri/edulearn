import pytest
from django.db import IntegrityError

from curriculums.models import LessonContent
from curriculums.tests.factories import LessonContentFactory, LessonFactory


@pytest.mark.django_db
class TestLessonContentModel:
    """Tests for the LessonContent model."""

    @pytest.fixture
    def lesson(self):
        return LessonFactory()

    def test_create_lesson_content(self, lesson):
        """Lesson content can be created."""
        content = LessonContent.objects.create(
            lesson=lesson,
            title="Introduction Video",
            content_type=LessonContent.Type.VIDEO,
            order=1,
            is_published=True,
        )

        assert content.lesson == lesson
        assert content.title == "Introduction Video"
        assert content.content_type == LessonContent.Type.VIDEO
        assert content.order == 1
        assert content.is_published is True

    def test_string_representation(self):
        """The string representation should return the content title."""
        content = LessonContentFactory(title="Variables Video")

        assert str(content) == "Variables Video"

    def test_is_published_defaults_to_false(self, lesson):
        """Content is unpublished by default."""
        content = LessonContent.objects.create(
            lesson=lesson,
            title="Introduction",
            content_type=LessonContent.Type.ARTICLE,
            order=1,
        )

        assert content.is_published is False

    def test_order_must_be_unique_per_lesson(self, lesson):
        """A lesson cannot contain two content items with the same order."""
        LessonContentFactory(
            lesson=lesson,
            order=1,
        )

        with pytest.raises(IntegrityError):
            LessonContent.objects.create(
                lesson=lesson,
                title="Duplicate",
                content_type=LessonContent.Type.FILE,
                order=1,
            )

    def test_same_order_can_be_used_in_different_lessons(self):
        """Different lessons may reuse the same order."""
        lesson1 = LessonFactory()
        lesson2 = LessonFactory()

        content1 = LessonContentFactory(
            lesson=lesson1,
            order=1,
        )

        content2 = LessonContentFactory(
            lesson=lesson2,
            order=1,
        )

        assert content1.order == content2.order == 1

    def test_lesson_can_have_multiple_contents(self, lesson):
        """A lesson can contain multiple content items."""
        content1 = LessonContentFactory(
            lesson=lesson,
            order=1,
        )

        content2 = LessonContentFactory(
            lesson=lesson,
            order=2,
        )

        assert set(lesson.contents.all()) == {
            content1,
            content2,
        }

    def test_lesson_can_access_its_contents(self, lesson):
        """A lesson should access its contents through the reverse relation."""
        content = LessonContentFactory(
            lesson=lesson,
        )

        assert content in lesson.contents.all()

    def test_contents_are_ordered_by_order(self, lesson):
        """Contents are returned in ascending order."""
        LessonContentFactory(
            lesson=lesson,
            order=3,
        )
        LessonContentFactory(
            lesson=lesson,
            order=1,
        )
        LessonContentFactory(
            lesson=lesson,
            order=2,
        )

        orders = list(
            lesson.contents.values_list(
                "order",
                flat=True,
            )
        )

        assert orders == [1, 2, 3]

    def test_deleting_lesson_deletes_contents(self):
        """Deleting a lesson cascades to its contents."""
        lesson = LessonFactory()

        content = LessonContentFactory(
            lesson=lesson,
        )

        lesson.delete()

        assert not LessonContent.objects.filter(
            pk=content.pk,
        ).exists()

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
    def test_accepts_all_content_types(self, lesson, content_type):
        """All supported content types can be saved."""
        content = LessonContent.objects.create(
            lesson=lesson,
            title="Content",
            content_type=content_type,
            order=1,
        )

        assert content.content_type == content_type
