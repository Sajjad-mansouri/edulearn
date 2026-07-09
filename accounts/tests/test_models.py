import pytest
from django.db import IntegrityError

from accounts.models import Role, User

from .factories import RoleFactory, UserFactory


@pytest.mark.django_db
class TestUserModel:
    def test_default_email_verified(self):
        user = UserFactory()

        assert user.email_verified is False

    def test_email_unique(self):
        UserFactory(email="john@example.com")

        with pytest.raises(IntegrityError):
            UserFactory(email="john@example.com")

    def test_required_fields(self):
        assert User.REQUIRED_FIELDS == ["email"]

    def test_username_index_exists(self):
        index = User._meta.indexes[0]

        assert index.fields == ["username"]


@pytest.mark.django_db
class TestRoleModel:
    """Tests for the Role model."""

    def test_create_role(self):
        """A role can be created successfully."""
        role = Role.objects.create(
            name="student",
            description="Student role",
        )

        assert role.name == "student"
        assert role.description == "Student role"

    def test_add_single_user(self):
        """A user can be assigned to a role."""
        role = RoleFactory()
        user = UserFactory()

        role.user.add(user)

        assert role.user.count() == 1
        assert role.user.first() == user

    def test_add_multiple_users(self):
        """Multiple users can be assigned to the same role."""
        role = RoleFactory()

        users = UserFactory.create_batch(3)

        role.user.add(*users)

        assert role.user.count() == 3
        assert set(role.user.all()) == set(users)

    def test_reverse_relation_from_user(self):
        """Users should access assigned roles through the related_name."""
        user = UserFactory()
        role = RoleFactory()

        role.user.add(user)

        assert user.roles.count() == 1
        assert user.roles.first() == role

    def test_name_field_configuration(self):
        """The name field should have the expected configuration."""
        field = Role._meta.get_field("name")

        assert field.max_length == 18
        assert field.choices == Role.ROLE_CHOICES

    def test_description_field_configuration(self):
        """The description field should be a TextField."""
        field = Role._meta.get_field("description")

        assert field.get_internal_type() == "TextField"

    def test_user_field_configuration(self):
        """The user field should be configured correctly."""
        field = Role._meta.get_field("user")

        assert field.many_to_many is True
        assert field.related_model.__name__ == "User"
        assert field.remote_field.related_name == "roles"

    def test_all_role_choices_are_available(self):
        """All expected role choices should be defined."""
        expected = {
            "guest",
            "student",
            "instructor",
            "teaching assistant",
            "moderator",
            "support agent",
            "admin",
        }

        actual = {choice for choice, _ in Role.ROLE_CHOICES}

        assert actual == expected

    def test_model_verbose_names(self):
        """Field verbose names should be defined correctly."""
        assert Role._meta.get_field("user").verbose_name == "User"
        assert Role._meta.get_field("name").verbose_name == "Name"
        assert Role._meta.get_field("description").verbose_name == "Description"

    def test_string_representation(self):
        role = RoleFactory(name="student")

        assert str(role) == "Student"
