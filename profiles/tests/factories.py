# tests/factories.py
from datetime import date

import factory

from profiles.models import (
    Education,
    Experience,
    InstructorProfile,
    Language,
    Profile,
    Skill,
    SocialLink,
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

    profile = factory.SubFactory(ProfileFactory)

    name = factory.Sequence(lambda n: f"Skill {n}")
    slug = factory.Sequence(lambda n: f"skill-{n}")
    description = factory.Faker("sentence")


class EducationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Education

    profile = factory.SubFactory(ProfileFactory)

    institution = "University of Oxford"
    degree = "Master of Science"
    field_of_study = "Computer Science"
    description = "Master's degree"

    start_date = "2022-12-01"
    end_date = "2022-12-10"


class ExperienceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Experience

    profile = factory.SubFactory(ProfileFactory)

    company = "test_company"
    position = "Backend Developer"
    location = "San Francisco, US"
    position = "Backend Developer"
    start_date = date(2022, 1, 1)
    end_date = date(2024, 1, 1)
    is_current = False


class SocialLinkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SocialLink

    profile = factory.SubFactory(ProfileFactory)

    platform = "GitHub"
    url = "https://github.com/test_user"
    visibility = SocialLink.Visibility.PUBLIC
    display_order = 0


class LanguageFactory(factory.django.DjangoModelFactory):
    """Factory for creating Language instances."""

    class Meta:
        model = Language

    profile = factory.SubFactory(ProfileFactory)
    language = factory.Faker("language_name")
    proficiency = "native"
