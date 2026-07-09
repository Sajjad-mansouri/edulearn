# tests/factories.py

import factory

from profiles.models import InstructorProfile, Profile, Skill, StudentProfile


class ProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Profile

    user = factory.SubFactory("accounts.tests.factories.UserFactory")
    biography = factory.Faker("paragraph")
    headline = factory.Faker("job")
    website = factory.Faker("url")
    country = factory.Faker("country")
    timezone = "UTC"
    language = "en"
    linkedin = factory.Faker("url")
    github = factory.Faker("url")
    company = factory.Faker("company")
    job_title = factory.Faker("job")


class InstructorProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = InstructorProfile

    profile = factory.SubFactory(ProfileFactory)
    professional_title = factory.Faker("job")
    organization = factory.Faker("company")
    years_of_experience = factory.Faker(
        "random_int",
        min=0,
        max=30,
    )


class StudentProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StudentProfile

    profile = factory.SubFactory(ProfileFactory)

    learning_goal = factory.Faker("sentence")
    current_streak = 5
    longest_streak = 10


class SkillFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Skill

    name = factory.Sequence(lambda n: f"Skill {n}")
    slug = factory.Sequence(lambda n: f"skill-{n}")
    description = factory.Faker("sentence")
