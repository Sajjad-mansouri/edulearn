from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError

from curriculums.models.lesson import Lesson


@pytest.mark.django_db
class TestLessonModel:
    def test_create_lesson(self, section):
        lesson = Lesson.objects.create(
            section=section,
            title="Getting Started",
            slug="getting-started",
        )

        assert lesson.pk is not None
        assert lesson.section == section
        assert lesson.title == "Getting Started"
        assert lesson.slug == "getting-started"

    def test_description_is_optional(self, section):
        lesson = Lesson.objects.create(
            section=section,
            title="Getting Started",
            slug="getting-started",
        )

        assert lesson.description == ""

    def test_duration_is_optional(self, section):
        lesson = Lesson.objects.create(
            section=section,
            title="Getting Started",
            slug="getting-started",
        )

        assert lesson.duration is None

    def test_order_defaults_to_one(self, section):
        lesson = Lesson.objects.create(
            section=section,
            title="Getting Started",
            slug="getting-started",
        )

        assert lesson.order == 1

    def test_is_published_defaults_to_false(self, section):
        lesson = Lesson.objects.create(
            section=section,
            title="Getting Started",
            slug="getting-started",
        )

        assert lesson.is_published is False

    def test_is_preview_defaults_to_false(self, section):
        lesson = Lesson.objects.create(
            section=section,
            title="Getting Started",
            slug="getting-started",
        )

        assert lesson.is_preview is False

    def test_str_returns_title(self, section):
        lesson = Lesson.objects.create(
            section=section,
            title="Getting Started",
            slug="getting-started",
        )

        assert str(lesson) == "Getting Started"

    def test_slug_is_generated_from_title_when_empty(self, section):
        lesson = Lesson.objects.create(
            section=section,
            title="Getting Started With Django",
            slug="",
        )

        assert lesson.slug == "getting-started-with-django"

    def test_slug_is_preserved_when_provided(self, section):
        lesson = Lesson.objects.create(
            section=section,
            title="Getting Started With Django",
            slug="django-basics",
        )

        assert lesson.slug == "django-basics"

    def test_slug_generation_handles_special_characters(self, section):
        lesson = Lesson.objects.create(
            section=section,
            title="Django & REST Framework!",
            slug="",
        )

        assert lesson.slug == "django-rest-framework"

    def test_updating_title_does_not_change_existing_slug(self, section):
        lesson = Lesson.objects.create(
            section=section,
            title="Getting Started",
            slug="getting-started",
        )

        lesson.title = "Advanced Django"
        lesson.save()

        lesson.refresh_from_db()

        assert lesson.title == "Advanced Django"
        assert lesson.slug == "getting-started"

    def test_lesson_accepts_description(self, section):
        lesson = Lesson.objects.create(
            section=section,
            title="Getting Started",
            slug="getting-started",
            description="Introduction to Django.",
        )

        assert lesson.description == "Introduction to Django."

    def test_lesson_accepts_duration(self, section):
        duration = timedelta(minutes=45)

        lesson = Lesson.objects.create(
            section=section,
            title="Getting Started",
            slug="getting-started",
            duration=duration,
        )

        assert lesson.duration == duration

    def test_lesson_accepts_explicit_order(self, section):
        lesson = Lesson.objects.create(
            section=section,
            title="Getting Started",
            slug="getting-started",
            order=3,
        )

        assert lesson.order == 3

    def test_lesson_can_be_published(self, section):
        lesson = Lesson.objects.create(
            section=section,
            title="Getting Started",
            slug="getting-started",
            is_published=True,
        )

        assert lesson.is_published is True

    def test_lesson_can_be_preview(self, section):
        lesson = Lesson.objects.create(
            section=section,
            title="Getting Started",
            slug="getting-started",
            is_preview=True,
        )

        assert lesson.is_preview is True

    def test_section_is_required(self):
        lesson = Lesson(
            title="Getting Started",
            slug="getting-started",
        )

        with pytest.raises(ValidationError) as exc_info:
            lesson.full_clean()

        assert "section" in exc_info.value.message_dict

    def test_title_is_required(self, section):
        lesson = Lesson(
            section=section,
            slug="getting-started",
        )

        with pytest.raises(ValidationError) as exc_info:
            lesson.full_clean()

        assert "title" in exc_info.value.message_dict

    def test_slug_is_required_when_full_clean_is_called(
        self,
        section,
    ):
        lesson = Lesson(
            section=section,
            title="Getting Started",
        )

        with pytest.raises(ValidationError) as exc_info:
            lesson.full_clean()

        assert "slug" in exc_info.value.message_dict

    def test_title_cannot_exceed_max_length(self, section):
        lesson = Lesson(
            section=section,
            title="a" * 256,
            slug="getting-started",
        )

        with pytest.raises(ValidationError) as exc_info:
            lesson.full_clean()

        assert "title" in exc_info.value.message_dict

    def test_slug_cannot_exceed_max_length(self, section):
        lesson = Lesson(
            section=section,
            title="Getting Started",
            slug="a" * 281,
        )

        with pytest.raises(ValidationError) as exc_info:
            lesson.full_clean()

        assert "slug" in exc_info.value.message_dict

    def test_negative_order_is_rejected(self, section):
        lesson = Lesson(
            section=section,
            title="Getting Started",
            slug="getting-started",
            order=-1,
        )

        with pytest.raises(ValidationError) as exc_info:
            lesson.full_clean()

        assert "order" in exc_info.value.message_dict

    def test_deleting_section_deletes_lessons(self, section):
        lesson = Lesson.objects.create(
            section=section,
            title="Getting Started",
            slug="getting-started",
        )
        lesson_id = lesson.pk

        section.delete()

        assert not Lesson.objects.filter(pk=lesson_id).exists()

    def test_reverse_section_relation(self, section):
        lesson = Lesson.objects.create(
            section=section,
            title="Getting Started",
            slug="getting-started",
        )

        assert lesson in section.lessons.all()

    def test_lesson_can_be_updated(self, section):
        lesson = Lesson.objects.create(
            section=section,
            title="Getting Started",
            slug="getting-started",
        )

        lesson.title = "Updated Lesson"
        lesson.description = "Updated description."
        lesson.order = 2
        lesson.is_published = True
        lesson.is_preview = True
        lesson.save()

        lesson.refresh_from_db()

        assert lesson.title == "Updated Lesson"
        assert lesson.description == "Updated description."
        assert lesson.order == 2
        assert lesson.is_published is True
        assert lesson.is_preview is True
        assert lesson.slug == "getting-started"

    def test_ordering_is_by_section_then_order(self, section):
        first = Lesson.objects.create(
            section=section,
            title="Second Lesson",
            slug="second-lesson",
            order=2,
        )

        second = Lesson.objects.create(
            section=section,
            title="First Lesson",
            slug="first-lesson",
            order=1,
        )

        lessons = list(Lesson.objects.all())

        assert lessons == [second, first]

    def test_lessons_from_different_sections_are_ordered_by_section_then_order(
        self,
        course,
    ):
        from curriculums.models.section import Section

        first_section = Section.objects.create(
            course=course,
            title="First Section",
            order=1,
        )
        second_section = Section.objects.create(
            course=course,
            title="Second Section",
            order=2,
        )

        first_section_lesson = Lesson.objects.create(
            section=first_section,
            title="First Section Lesson",
            slug="first-section-lesson",
            order=2,
        )

        second_section_lesson = Lesson.objects.create(
            section=second_section,
            title="Second Section Lesson",
            slug="second-section-lesson",
            order=1,
        )

        another_first_section_lesson = Lesson.objects.create(
            section=first_section,
            title="Another First Section Lesson",
            slug="another-first-section-lesson",
            order=1,
        )

        lessons = list(Lesson.objects.all())

        assert lessons == [
            another_first_section_lesson,
            first_section_lesson,
            second_section_lesson,
        ]
