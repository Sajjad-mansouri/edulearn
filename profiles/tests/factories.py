# tests/factories.py
from datetime import date

import factory

from profiles.models import (
    Education,
    Experience,
    InstructorProfile,
    Profile,
    Skill,
    StudentProfile,
)


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


class EducationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Education

    profile = factory.SubFactory(Profile)

    institution = "University of Oxford"
    degree = "Master of Science"
    field_of_study = "Computer Science"

    start_year = 2020
    end_year = 2022


class ExperienceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Experience

    profile = factory.SubFactory(Profile)

    company = "test_company"
    position = "Backend Developer"
    start_date = date(2022, 1, 1)
    end_date = date(2024, 1, 1)
    is_current = False
