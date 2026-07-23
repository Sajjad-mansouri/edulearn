import datetime

import pytest
from django.db import IntegrityError

from curriculums.models import Lesson
from curriculums.tests.factories import LessonFactory, SectionFactory


@pytest.mark.django_db
class TestLessonModel:
    """Tests for the Lesson model."""

    @pytest.fixture
    def section(self):
        return SectionFactory()

    def test_create_lesson(self, section):
        """A lesson can be created."""
        lesson = Lesson.objects.create(
            section=section,
            title="Introduction",
            slug="introduction",
            lesson_type=Lesson.Type.VIDEO,
            duration=datetime.timedelta(minutes=15),
            order=1,
            is_published=True,
            is_preview=True,
            completion_criteria=Lesson.CompletionCriteria.WATCH_VIDEO,
        )

        assert lesson.section == section
        assert lesson.title == "Introduction"
        assert lesson.slug == "introduction"
        assert lesson.lesson_type == Lesson.Type.VIDEO
        assert lesson.duration == datetime.timedelta(minutes=15)
        assert lesson.order == 1
        assert lesson.is_published is True
        assert lesson.is_preview is True
        assert lesson.completion_criteria == Lesson.CompletionCriteria.WATCH_VIDEO

    def test_string_representation(self):
        """The string representation should return the lesson title."""
        lesson = LessonFactory(title="Variables")

        assert str(lesson) == "Variables"

    def test_generates_slug_when_slug_is_not_provided(self, section):
        """Slug is generated automatically from the title."""
        lesson = Lesson.objects.create(
            section=section,
            title="Python Basics",
            lesson_type=Lesson.Type.ARTICLE,
        )

        assert lesson.slug == "python-basics"

    def test_does_not_override_existing_slug(self, section):
        """An existing slug is preserved."""
        lesson = Lesson.objects.create(
            section=section,
            title="Python Basics",
            slug="custom-slug",
            lesson_type=Lesson.Type.ARTICLE,
        )

        assert lesson.slug == "custom-slug"

    def test_slug_does_not_change_when_title_changes(self):
        """Changing the title does not change the slug."""
        lesson = LessonFactory()

        original_slug = lesson.slug

        lesson.title = "New Lesson Title"
        lesson.save()

        lesson.refresh_from_db()

        assert lesson.slug == original_slug

    def test_duration_is_optional(self, section):
        """A lesson can be created without a duration."""
        lesson = Lesson.objects.create(
            section=section,
            title="Introduction",
            lesson_type=Lesson.Type.ARTICLE,
        )

        assert lesson.duration is None

    def test_is_published_defaults_to_false(self, section):
        """Lessons are unpublished by default."""
        lesson = Lesson.objects.create(
            section=section,
            title="Introduction",
            lesson_type=Lesson.Type.ARTICLE,
        )

        assert lesson.is_published is False

    def test_is_preview_defaults_to_false(self, section):
        """Preview is disabled by default."""
        lesson = Lesson.objects.create(
            section=section,
            title="Introduction",
            lesson_type=Lesson.Type.ARTICLE,
        )

        assert lesson.is_preview is False

    def test_completion_criteria_defaults_to_manual(self, section):
        """Completion criteria defaults to manual."""
        lesson = Lesson.objects.create(
            section=section,
            title="Introduction",
            lesson_type=Lesson.Type.ARTICLE,
        )

        assert lesson.completion_criteria == Lesson.CompletionCriteria.MANUAL

    def test_order_must_be_unique_per_section(self, section):
        """A section cannot contain two lessons with the same order."""
        LessonFactory(
            section=section,
            order=1,
        )

        with pytest.raises(IntegrityError):
            Lesson.objects.create(
                section=section,
                title="Duplicate",
                lesson_type=Lesson.Type.VIDEO,
                order=1,
            )

    def test_same_order_can_be_used_in_different_sections(self):
        """Different sections may reuse the same order."""
        section1 = SectionFactory()
        section2 = SectionFactory()

        lesson1 = LessonFactory(
            section=section1,
            order=1,
        )

        lesson2 = LessonFactory(
            section=section2,
            order=1,
        )

        assert lesson1.order == lesson2.order == 1

    def test_section_can_have_multiple_lessons(self, section):
        """A section can have multiple lessons."""
        lesson1 = LessonFactory(
            section=section,
            order=1,
        )

        lesson2 = LessonFactory(
            section=section,
            order=2,
        )

        assert set(section.lessons.all()) == {
            lesson1,
            lesson2,
        }

    def test_lessons_are_ordered_by_order(self, section):
        """Lessons are returned in ascending order."""
        LessonFactory(section=section, order=3)
        LessonFactory(section=section, order=1)
        LessonFactory(section=section, order=2)

        orders = list(
            section.lessons.values_list(
                "order",
                flat=True,
            )
        )

        assert orders == [1, 2, 3]

    def test_deleting_section_deletes_lessons(self):
        """Deleting a section cascades to its lessons."""
        section = SectionFactory()

        lesson = LessonFactory(
            section=section,
        )

        section.delete()

        assert not Lesson.objects.filter(
            pk=lesson.pk,
        ).exists()
