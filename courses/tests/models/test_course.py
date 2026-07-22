import pytest
from django.core.exceptions import ValidationError

from accounts.tests.factories import UserFactory
from courses.models import Course
from courses.tests.factories import (
    CategoryFactory,
    CourseFactory,
    TagFactory,
)


@pytest.mark.django_db
class TestCourseModel:
    """Tests for the Course model."""

    @pytest.fixture
    def owner(self):
        return UserFactory()

    @pytest.fixture
    def instructor(self):
        return UserFactory()

    @pytest.fixture
    def category(self):
        return CategoryFactory()

    def test_create_course(
        self,
        owner,
        instructor,
        category,
    ):
        """A course can be created."""
        course = Course.objects.create(
            owner=owner,
            category=category,
            title="Python Fundamentals",
            subtitle="Learn Python from scratch",
            slug="python-fundamentals",
            description="Course description",
        )

        course.instructors.add(instructor)

        assert course.owner == owner
        assert course.category == category
        assert course.title == "Python Fundamentals"
        assert course.subtitle == "Learn Python from scratch"
        assert course.slug == "python-fundamentals"
        assert course.description == "Course description"
        assert instructor in course.instructors.all()

    def test_string_representation(self):
        """The string representation returns the course title."""
        course = CourseFactory(title="Python Fundamentals")

        assert str(course) == "Python Fundamentals"

    def test_default_values(
        self,
        owner,
        category,
    ):
        """Default field values are applied."""
        course = Course.objects.create(
            owner=owner,
            category=category,
            title="Python Fundamentals",
            slug="python-fundamentals",
            description="Description",
        )

        assert course.level == Course.Level.ALL_LEVELS
        assert course.status == Course.Status.DRAFT
        assert course.visibility == Course.Visibility.PUBLIC
        assert course.language == "English"
        assert course.version == "1.0.0"
        assert course.thumbnail.name == ""
        assert course.promotional_video == ""
        assert course.published_at is None

    def test_slug_must_be_unique(self):
        """Slug values must be unique."""
        CourseFactory(slug="python")

        with pytest.raises(ValidationError) as exc:
            CourseFactory(slug="python")
        assert "slug" in exc.value.message_dict

    def test_generates_slug_when_slug_not_provided(
        self,
        owner,
        category,
    ):
        """Slug is generated automatically."""
        course = Course.objects.create(
            owner=owner,
            category=category,
            title="Machine Learning",
            description="Description",
        )

        assert course.slug == "machine-learning"

    def test_preserves_existing_slug(
        self,
        owner,
        category,
    ):
        """An explicitly provided slug is preserved."""
        course = Course.objects.create(
            owner=owner,
            category=category,
            title="Machine Learning",
            slug="ml",
            description="Description",
        )

        assert course.slug == "ml"

    def test_slug_does_not_change_when_title_changes(self):
        """Changing the title does not modify the slug."""
        course = CourseFactory(
            title="Python",
            slug="python",
        )

        original_slug = course.slug

        course.title = "Advanced Python"
        course.save()

        course.refresh_from_db()

        assert course.slug == original_slug

    def test_blank_title_is_invalid(
        self,
        owner,
        category,
    ):
        """A title containing only whitespace is rejected."""
        course = Course(
            owner=owner,
            category=category,
            title="   ",
            slug="python",
            description="Description",
        )

        with pytest.raises(ValidationError):
            course.full_clean()

    def test_can_assign_tags(self):
        """A course can have multiple tags."""
        course = CourseFactory()

        tag1 = TagFactory(name="Python")
        tag2 = TagFactory(name="Backend")

        course.tags.add(tag1, tag2)

        assert set(course.tags.all()) == {
            tag1,
            tag2,
        }

    def test_can_assign_multiple_instructors(self):
        """A course can have multiple instructors."""
        course = CourseFactory()

        instructor1 = UserFactory()
        instructor2 = UserFactory()

        course.instructors.add(
            instructor1,
            instructor2,
        )

        assert set(course.instructors.all()) == {
            instructor1,
            instructor2,
        }

    def test_category_can_access_courses(self):
        """A category exposes its related courses."""
        category = CategoryFactory()

        course1 = CourseFactory(category=category)
        course2 = CourseFactory(category=category)

        assert set(category.courses.all()) == {
            course1,
            course2,
        }

    def test_tag_can_access_courses(self):
        """A tag exposes its related courses."""
        tag = TagFactory()

        course = CourseFactory()
        course.tags.add(tag)

        assert course in tag.courses.all()

    def test_owner_can_access_owned_courses(self):
        """The owner exposes owned courses."""
        owner = UserFactory()

        course = CourseFactory(owner=owner)

        assert course in owner.owned_courses.all()

    def test_instructor_can_access_teaching_courses(self):
        """An instructor exposes teaching courses."""
        instructor = UserFactory()

        course = CourseFactory()
        course.instructors.add(instructor)

        assert course in instructor.teaching_courses.all()
