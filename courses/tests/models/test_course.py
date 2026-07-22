import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from accounts.tests.factories import UserFactory
from courses.models import Course, CourseCollaborator, LearningOutcome, Prerequisite
from courses.tests.factories import (
    CategoryFactory,
    CourseCollaboratorFactory,
    CourseFactory,
    LearningOutcomeFactory,
    PrerequisiteFactory,
    TagFactory,
)


@pytest.mark.django_db
class TestCourseModel:
    """Tests for the Course model."""

    @pytest.fixture
    def owner(self):
        return UserFactory()

    @pytest.fixture
    def category(self):
        return CategoryFactory()

    def test_create_course(
        self,
        owner,
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

        collaborator = CourseCollaborator.objects.create(
            course=course,
            user=owner,
            role=CourseCollaborator.Role.LEAD_INSTRUCTOR,
        )

        assert course.owner == owner
        assert course.category == category
        assert course.title == "Python Fundamentals"
        assert course.subtitle == "Learn Python from scratch"
        assert course.slug == "python-fundamentals"
        assert course.description == "Course description"

        assert collaborator.course == course
        assert collaborator.user == owner
        assert collaborator.role == CourseCollaborator.Role.LEAD_INSTRUCTOR

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

    def test_course_can_have_multiple_collaborators(self, owner, category):
        """A course can have multiple collaborators."""
        user1 = UserFactory()
        user2 = UserFactory()

        course = Course.objects.create(
            owner=owner,
            category=category,
            title="Python Fundamentals",
            subtitle="Learn Python from scratch",
            slug="python-fundamentals",
            description="Course description",
        )
        collaborator1 = CourseCollaboratorFactory(
            course=course,
            user=user1,
            role=CourseCollaborator.Role.LEAD_INSTRUCTOR,
        )

        collaborator2 = CourseCollaboratorFactory(
            course=course,
            user=user2,
            role=CourseCollaborator.Role.INSTRUCTOR,
        )

        assert set(course.course_collaborators.all()) == {
            collaborator1,
            collaborator2,
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

    def test_owner_can_access_course_collaborations(self):
        user = UserFactory()

        collaborator = CourseCollaboratorFactory(user=user)

        assert collaborator in user.course_collaborations.all()


@pytest.mark.django_db
class TestLearningOutcomeModel:
    """Tests for the LearningOutcome model."""

    @pytest.fixture
    def course(self):
        return CourseFactory()

    def test_create_learning_outcome(self, course):
        """A learning outcome can be created."""
        outcome = LearningOutcome.objects.create(
            course=course,
            order=1,
            description="Understand Python fundamentals.",
        )

        assert outcome.course == course
        assert outcome.order == 1
        assert outcome.description == "Understand Python fundamentals."

    def test_string_representation(self):
        """The string representation includes the course title and order."""
        outcome = LearningOutcomeFactory(order=2)

        assert str(outcome) == f"{outcome.course.title} - 2"

    def test_course_can_have_multiple_learning_outcomes(self, course):
        """A course can have multiple learning outcomes."""
        outcome1 = LearningOutcomeFactory(
            course=course,
            order=1,
        )
        outcome2 = LearningOutcomeFactory(
            course=course,
            order=2,
        )

        assert set(course.learning_outcomes.all()) == {
            outcome1,
            outcome2,
        }

    def test_learning_outcomes_are_ordered_by_order(self, course):
        """Learning outcomes are returned in ascending order."""
        LearningOutcomeFactory(course=course, order=3)
        LearningOutcomeFactory(course=course, order=1)
        LearningOutcomeFactory(course=course, order=2)

        orders = list(
            course.learning_outcomes.values_list(
                "order",
                flat=True,
            )
        )

        assert orders == [1, 2, 3]

    def test_order_must_be_unique_per_course(self, course):
        """The same course cannot contain duplicate order values."""
        LearningOutcomeFactory(
            course=course,
            order=1,
        )

        with pytest.raises(IntegrityError):
            LearningOutcome.objects.create(
                course=course,
                order=1,
                description="Duplicate order",
            )

    def test_same_order_can_be_used_for_different_courses(self):
        """Different courses may reuse the same order value."""
        course1 = CourseFactory()
        course2 = CourseFactory()

        outcome1 = LearningOutcomeFactory(
            course=course1,
            order=1,
        )
        outcome2 = LearningOutcomeFactory(
            course=course2,
            order=1,
        )

        assert outcome1.order == outcome2.order == 1

    def test_deleting_course_deletes_learning_outcomes(self):
        """Deleting a course cascades to its learning outcomes."""
        course = CourseFactory()

        outcome = LearningOutcomeFactory(
            course=course,
        )

        course.delete()

        assert not LearningOutcome.objects.filter(
            pk=outcome.pk,
        ).exists()


@pytest.mark.django_db
class TestPrerequisiteModel:
    """Tests for the Prerequisite model."""

    @pytest.fixture
    def course(self):
        return CourseFactory()

    def test_create_prerequisite(self, course):
        """A prerequisite can be created."""
        prerequisite = Prerequisite.objects.create(
            course=course,
            order=1,
            description="Basic Python knowledge.",
        )

        assert prerequisite.course == course
        assert prerequisite.order == 1
        assert prerequisite.description == "Basic Python knowledge."

    def test_string_representation(self):
        """The string representation includes the course title and order."""
        prerequisite = PrerequisiteFactory(order=2)

        assert str(prerequisite) == f"{prerequisite.course.title} - 2"

    def test_course_can_have_multiple_prerequisites(self, course):
        """A course can have multiple prerequisites."""
        prerequisite1 = PrerequisiteFactory(
            course=course,
            order=1,
        )
        prerequisite2 = PrerequisiteFactory(
            course=course,
            order=2,
        )

        assert set(course.prerequisites.all()) == {
            prerequisite1,
            prerequisite2,
        }

    def test_prerequisites_are_ordered_by_order(self, course):
        """Prerequisites are returned in ascending order."""
        PrerequisiteFactory(course=course, order=3)
        PrerequisiteFactory(course=course, order=1)
        PrerequisiteFactory(course=course, order=2)

        orders = list(
            course.prerequisites.values_list(
                "order",
                flat=True,
            )
        )

        assert orders == [1, 2, 3]

    def test_order_must_be_unique_per_course(self, course):
        """The same course cannot contain duplicate order values."""
        PrerequisiteFactory(
            course=course,
            order=1,
        )

        with pytest.raises(IntegrityError):
            Prerequisite.objects.create(
                course=course,
                order=1,
                description="Duplicate order",
            )

    def test_same_order_can_be_used_for_different_courses(self):
        """Different courses may reuse the same order value."""
        course1 = CourseFactory()
        course2 = CourseFactory()

        prerequisite1 = PrerequisiteFactory(
            course=course1,
            order=1,
        )
        prerequisite2 = PrerequisiteFactory(
            course=course2,
            order=1,
        )

        assert prerequisite1.order == prerequisite2.order == 1

    def test_deleting_course_deletes_prerequisites(self):
        """Deleting a course cascades to its prerequisites."""
        course = CourseFactory()

        prerequisite = PrerequisiteFactory(
            course=course,
        )

        course.delete()

        assert not Prerequisite.objects.filter(
            pk=prerequisite.pk,
        ).exists()


@pytest.mark.django_db
class TestCourseCollaboratorModel:
    """Tests for the CourseCollaborator model."""

    @pytest.fixture
    def course(self):
        return CourseFactory()

    @pytest.fixture
    def user(self):
        return UserFactory()

    def test_create_course_collaborator(self, course, user):
        """A collaborator can be assigned to a course."""
        collaborator = CourseCollaborator.objects.create(
            course=course,
            user=user,
            role=CourseCollaborator.Role.INSTRUCTOR,
        )

        assert collaborator.course == course
        assert collaborator.user == user
        assert collaborator.role == CourseCollaborator.Role.INSTRUCTOR

    def test_string_representation(self):
        """The string representation returns the user and role."""
        collaborator = CourseCollaboratorFactory(
            role=CourseCollaborator.Role.TEACHING_ASSISTANT,
        )

        assert (
            str(collaborator)
            == f"{collaborator.user} ({collaborator.get_role_display()})"
        )

    def test_same_user_cannot_be_added_twice_to_same_course(self, course, user):
        """A user cannot collaborate on the same course twice."""
        CourseCollaboratorFactory(
            course=course,
            user=user,
        )

        with pytest.raises(IntegrityError):
            CourseCollaborator.objects.create(
                course=course,
                user=user,
                role=CourseCollaborator.Role.TEACHING_ASSISTANT,
            )

    def test_same_user_can_collaborate_on_multiple_courses(self, user):
        """A user may collaborate on different courses."""
        course1 = CourseFactory()
        course2 = CourseFactory()

        collaborator1 = CourseCollaboratorFactory(
            course=course1,
            user=user,
        )
        collaborator2 = CourseCollaboratorFactory(
            course=course2,
            user=user,
        )

        assert collaborator1.user == collaborator2.user

    def test_course_can_have_multiple_collaborators(self, course):
        """A course may have multiple collaborators."""
        collaborator1 = CourseCollaboratorFactory(
            course=course,
        )
        collaborator2 = CourseCollaboratorFactory(
            course=course,
            user=UserFactory(),
        )

        assert set(course.course_collaborators.all()) == {
            collaborator1,
            collaborator2,
        }

    def test_user_can_access_course_collaborations(self, user):
        """A user exposes their course collaborations."""
        collaborator = CourseCollaboratorFactory(
            user=user,
        )

        assert collaborator in user.course_collaborations.all()

    def test_course_can_access_collaborators(self, course):
        """A course exposes its collaborators."""
        collaborator = CourseCollaboratorFactory(
            course=course,
        )

        assert collaborator in course.course_collaborators.all()

    def test_deleting_course_deletes_collaborators(self):
        """Deleting a course cascades to collaborators."""
        course = CourseFactory()

        collaborator = CourseCollaboratorFactory(
            course=course,
        )

        course.delete()

        assert not CourseCollaborator.objects.filter(
            pk=collaborator.pk,
        ).exists()

    def test_deleting_user_deletes_collaborations(self):
        """Deleting a user cascades to course collaborations."""
        user = UserFactory()

        collaborator = CourseCollaboratorFactory(
            user=user,
        )

        user.delete()

        assert not CourseCollaborator.objects.filter(
            pk=collaborator.pk,
        ).exists()
