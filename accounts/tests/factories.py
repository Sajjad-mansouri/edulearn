import factory
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory

from accounts.models import LoginHistory, Role, UserSession

User = get_user_model()


class UserFactory(DjangoModelFactory):
    """Factory for creating User instance"""

    class Meta:
        model = User
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    password = factory.PostGenerationMethodCall("set_password", "secure_pass_1234")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")

    @classmethod
    def _after_postgeneration(cls, instance, create, results=None):
        if create:
            instance.save()


class RoleFactory(DjangoModelFactory):
    class Meta:
        model = Role

    name = "student"
    description = factory.Faker("paragraph")


class UserSessionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserSession

    user = factory.SubFactory(UserFactory)
    device = factory.Faker("word")
    ip_address = factory.Faker("ipv4")
    user_agent = factory.Faker("user_agent")


class LoginHistoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LoginHistory

    user = factory.SubFactory(UserFactory)
    is_successful = True
    ip_address = factory.Faker("ipv4")
    device = factory.Faker("word")
    location = factory.Faker("city")
