import factory

from accounts.tests.factories import UserFactory
from courses.models import (
    Category,
    Course,
    CourseCollaborator,
    LearningOutcome,
    Prerequisite,
    Tag,
)


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    parent = None
    name = factory.Sequence(lambda n: f"Category {n}")
    slug = factory.Sequence(lambda n: f"category-{n}")
    description = factory.Faker("sentence")
    display_order = factory.Sequence(lambda n: n)
    is_active = True


class TagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tag

    name = factory.Sequence(lambda n: f"Tag {n}")
    slug = factory.Sequence(lambda n: f"tag-{n}")


class CourseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Course
        skip_postgeneration_save = True

    owner = factory.SubFactory(UserFactory)
    category = factory.SubFactory(CategoryFactory)

    title = factory.Sequence(lambda n: f"Course {n}")
    slug = factory.Sequence(lambda n: f"course-{n}")
    subtitle = factory.Faker("sentence")
    description = factory.Faker("paragraph")

    language = "English"
    level = Course.Level.ALL_LEVELS
    status = Course.Status.DRAFT
    visibility = Course.Visibility.PUBLIC
    version = "1.0.0"

    @factory.post_generation
    def instructors(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for instructor in extracted:
                self.instructors.add(instructor)


class LearningOutcomeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LearningOutcome

    course = factory.SubFactory(CourseFactory)
    order = factory.Sequence(lambda n: n + 1)
    description = factory.Faker("sentence")


class PrerequisiteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Prerequisite

    course = factory.SubFactory(CourseFactory)
    order = factory.Sequence(lambda n: n + 1)
    description = factory.Faker("sentence")


class CourseCollaboratorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CourseCollaborator

    course = factory.SubFactory(CourseFactory)
    user = factory.SubFactory(UserFactory)
    role = CourseCollaborator.Role.INSTRUCTOR
