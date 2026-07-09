import pytest
from django.db import IntegrityError
from django.utils import timezone

from accounts.models import Role, User, UserSession

from .factories import RoleFactory, UserFactory, UserSessionFactory


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


@pytest.mark.django_db
class TestUserSessionModel:
    @pytest.fixture
    def user(self):
        return UserFactory()

    @pytest.fixture
    def session(self, user):
        return UserSessionFactory(user=user)

    def test_create_session(self, user):
        """A session can be created successfully."""
        session = UserSession.objects.create(
            user=user,
            device="Chrome",
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0",
        )

        assert session.user == user
        assert session.device == "Chrome"
        assert session.ip_address == "127.0.0.1"
        assert session.user_agent == "Mozilla/5.0"

    def test_string_representation(self, session):
        """The string representation includes the username and device."""
        expected = f"{session.user} - {session.device}"

        assert str(session) == expected

    def test_session_is_not_revoked_by_default(self, session):
        """New sessions should be active by default."""
        assert session.is_revoked is False

    def test_login_time_is_set_on_creation(self, session):
        """Creating a session should automatically set the login time."""
        assert session.login_at is not None
        assert session.login_at <= timezone.now()

    def test_last_activity_time_is_set_on_creation(self, session):
        """Creating a session should automatically set the last activity time."""
        assert session.last_activity_at is not None
        assert session.last_activity_at <= timezone.now()

    def test_last_activity_time_updates_after_save(self, session):
        """Saving a session should update its last activity timestamp."""
        original = session.last_activity_at

        session.device = "Firefox"
        session.save()

        session.refresh_from_db()

        assert session.last_activity_at >= original

    def test_user_can_access_its_sessions(self, user):
        """A user should access related sessions through the sessions relation."""
        session = UserSessionFactory(user=user)

        assert session in user.sessions.all()

    def test_deleting_user_deletes_related_sessions(self, user):
        """Deleting a user should cascade and remove its sessions."""
        UserSessionFactory.create_batch(3, user=user)

        user.delete()

        assert UserSession.objects.count() == 0

    def test_sessions_are_returned_newest_first(self, user):
        """Sessions should be ordered by most recent login."""
        older = UserSessionFactory(user=user)
        newer = UserSessionFactory(user=user)

        older.login_at = timezone.now() - timezone.timedelta(days=1)
        older.save(update_fields=["login_at"])

        newer.login_at = timezone.now()
        newer.save(update_fields=["login_at"])

        sessions = list(UserSession.objects.all())

        assert sessions == [newer, older]
