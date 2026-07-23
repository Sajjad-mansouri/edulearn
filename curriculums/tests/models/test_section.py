import datetime

import pytest
from django.db import IntegrityError

from courses.tests.factories import CourseFactory
from curriculums.models import Section
from curriculums.tests.factories import SectionFactory


@pytest.mark.django_db
class TestSectionModel:
    """Tests for the Section model."""

    @pytest.fixture
    def course(self):
        return CourseFactory()

    def test_create_section(self, course):
        """A section can be created."""
        section = Section.objects.create(
            course=course,
            title="Getting Started",
            description="Introduction to the course.",
            order=1,
            is_published=True,
            estimated_duration=datetime.timedelta(minutes=45),
        )

        assert section.course == course
        assert section.title == "Getting Started"
        assert section.description == "Introduction to the course."
        assert section.order == 1
        assert section.is_published is True
        assert section.estimated_duration == datetime.timedelta(minutes=45)

    def test_string_representation(self):
        """The string representation should return the section title."""
        section = SectionFactory(title="Introduction")

        assert str(section) == "Introduction"

    def test_description_is_optional(self, course):
        """A section can be created without a description."""
        section = Section.objects.create(
            course=course,
            title="Introduction",
            order=1,
        )

        assert section.description == ""

    def test_estimated_duration_is_optional(self, course):
        """A section can be created without an estimated duration."""
        section = Section.objects.create(
            course=course,
            title="Introduction",
            order=1,
        )

        assert section.estimated_duration is None

    def test_is_published_defaults_to_false(self, course):
        """Sections are unpublished by default."""
        section = Section.objects.create(
            course=course,
            title="Introduction",
            order=1,
        )

        assert section.is_published is False

    def test_order_must_be_unique_per_course(self, course):
        """A course cannot have two sections with the same order."""
        SectionFactory(
            course=course,
            order=1,
        )

        with pytest.raises(IntegrityError):
            Section.objects.create(
                course=course,
                title="Duplicate",
                order=1,
            )

    def test_same_order_can_be_used_for_different_courses(self):
        """Different courses may use the same section order."""
        course1 = CourseFactory()
        course2 = CourseFactory()

        section1 = SectionFactory(
            course=course1,
            order=1,
        )

        section2 = SectionFactory(
            course=course2,
            order=1,
        )

        assert section1.order == section2.order == 1

    def test_course_can_have_multiple_sections(self, course):
        """A course can have multiple sections."""
        section1 = SectionFactory(
            course=course,
            order=1,
        )
        section2 = SectionFactory(
            course=course,
            order=2,
        )

        assert set(course.sections.all()) == {
            section1,
            section2,
        }

    def test_sections_are_ordered_by_order(self, course):
        """Sections are returned in ascending order."""
        SectionFactory(course=course, order=3)
        SectionFactory(course=course, order=1)
        SectionFactory(course=course, order=2)

        orders = list(
            course.sections.values_list(
                "order",
                flat=True,
            )
        )

        assert orders == [1, 2, 3]

    def test_deleting_course_deletes_sections(self):
        """Deleting a course cascades to its sections."""
        course = CourseFactory()

        section = SectionFactory(
            course=course,
        )

        course.delete()

        assert not Section.objects.filter(
            pk=section.pk,
        ).exists()
