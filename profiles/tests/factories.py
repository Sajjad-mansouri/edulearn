# tests/factories.py

import factory

from profiles.models import Profile


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
