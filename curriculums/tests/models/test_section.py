from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError

from curriculums.models.section import Section


@pytest.mark.django_db
class TestSectionModel:
    def test_create_section(self, course):
        section = Section.objects.create(
            course=course,
            title="Introduction",
        )

        assert section.pk is not None
        assert section.course == course
        assert section.title == "Introduction"
        assert section.description == ""
        assert section.order == 1
        assert section.is_published is False
        assert section.duration is None

    def test_str_returns_title(self, course):
        section = Section.objects.create(
            course=course,
            title="Introduction",
        )

        assert str(section) == "Introduction"

    def test_description_is_optional(self, course):
        section = Section.objects.create(
            course=course,
            title="Introduction",
        )

        assert section.description == ""

    def test_description_can_be_set(self, course):
        section = Section.objects.create(
            course=course,
            title="Introduction",
            description="This section introduces the course.",
        )

        assert section.description == ("This section introduces the course.")

    def test_order_defaults_to_one(self, course):
        section = Section.objects.create(
            course=course,
            title="Introduction",
        )

        assert section.order == 1

    def test_explicit_order_is_preserved(self, course):
        section = Section.objects.create(
            course=course,
            title="Advanced Topics",
            order=3,
        )

        assert section.order == 3

    def test_is_published_defaults_to_false(self, course):
        section = Section.objects.create(
            course=course,
            title="Introduction",
        )

        assert section.is_published is False

    def test_section_can_be_published(self, course):
        section = Section.objects.create(
            course=course,
            title="Introduction",
            is_published=True,
        )

        assert section.is_published is True

    def test_duration_is_optional(self, course):
        section = Section.objects.create(
            course=course,
            title="Introduction",
        )

        assert section.duration is None

    def test_duration_can_be_set(self, course):
        duration = timedelta(hours=1, minutes=30)

        section = Section.objects.create(
            course=course,
            title="Introduction",
            duration=duration,
        )

        assert section.duration == duration

    def test_course_is_required(self):
        section = Section(
            title="Introduction",
        )

        with pytest.raises(ValidationError) as exc_info:
            section.full_clean()

        assert "course" in exc_info.value.message_dict

    def test_title_is_required(self, course):
        section = Section(
            course=course,
        )

        with pytest.raises(ValidationError) as exc_info:
            section.full_clean()

        assert "title" in exc_info.value.message_dict

    def test_title_cannot_exceed_max_length(self, course):
        section = Section(
            course=course,
            title="a" * 256,
        )

        with pytest.raises(ValidationError) as exc_info:
            section.full_clean()

        assert "title" in exc_info.value.message_dict

    def test_title_at_max_length_is_valid(self, course):
        section = Section(
            course=course,
            title="a" * 255,
        )

        section.full_clean()

        assert len(section.title) == 255

    def test_negative_order_is_rejected(self, course):
        section = Section(
            course=course,
            title="Introduction",
            order=-1,
        )

        with pytest.raises(ValidationError) as exc_info:
            section.full_clean()

        assert "order" in exc_info.value.message_dict

    @pytest.mark.parametrize(
        "order",
        [0, 1, 2, 100, 65535],
    )
    def test_valid_order_values(self, course, order):
        section = Section(
            course=course,
            title=f"Section {order}",
            order=order,
        )

        section.full_clean()

        assert section.order == order

    def test_reverse_course_relation(self, course):
        section = Section.objects.create(
            course=course,
            title="Introduction",
        )

        assert section in course.sections.all()

    def test_deleting_course_deletes_sections(self, course):
        section = Section.objects.create(
            course=course,
            title="Introduction",
        )
        section_id = section.pk

        course.delete()

        assert not Section.objects.filter(pk=section_id).exists()

    def test_section_can_be_updated(self, course):
        section = Section.objects.create(
            course=course,
            title="Introduction",
        )

        new_duration = timedelta(minutes=45)

        section.title = "Advanced Topics"
        section.description = "Advanced course material."
        section.order = 2
        section.is_published = True
        section.duration = new_duration
        section.save()

        section.refresh_from_db()

        assert section.title == "Advanced Topics"
        assert section.description == "Advanced course material."
        assert section.order == 2
        assert section.is_published is True
        assert section.duration == new_duration

    def test_ordering_is_by_course_then_order(self, course):
        first = Section.objects.create(
            course=course,
            title="Second Section",
            order=2,
        )

        second = Section.objects.create(
            course=course,
            title="First Section",
            order=1,
        )

        sections = list(Section.objects.all())

        assert sections == [second, first]

    def test_sections_from_different_courses_are_ordered_by_course_then_order(
        self,
        course,
        test_user,
    ):
        from courses.models import Course

        another_course = Course.objects.create(
            title="Another Course",
            owner=test_user,
        )

        first_course_section = Section.objects.create(
            course=course,
            title="First Course Section",
            order=2,
        )

        another_course_section = Section.objects.create(
            course=another_course,
            title="Another Course Section",
            order=1,
        )

        second_first_course_section = Section.objects.create(
            course=course,
            title="Another First Course Section",
            order=1,
        )

        sections = list(Section.objects.all())

        assert sections == [
            another_course_section,
            second_first_course_section,
            first_course_section,
        ]
