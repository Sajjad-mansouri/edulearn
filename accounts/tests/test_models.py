# accounts/tests/test_models.py
import time

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from accounts.models import LoginHistory, Role, User, UserSession


@pytest.mark.django_db
class TestUserModel:
    def test_email_is_unique(self):
        User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username="another_user",
                email="test_user@example.com",
                password="another-password",
            )

    def test_email_verified_defaults_to_false(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

        assert user.email_verified is False

    def test_email_verified_can_be_set_to_true(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

        user.email_verified = True
        user.save(update_fields=["email_verified"])

        user.refresh_from_db()

        assert user.email_verified is True

    def test_email_can_be_blank(self):
        user = User.objects.create_user(
            username="test_user",
            email="",
            password="test-password",
        )

        assert user.email == ""

    def test_avatar_returns_none_when_profile_does_not_exist(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

        assert user.avatar is None


@pytest.mark.django_db
class TestRoleModel:
    def test_create_role_with_student_role(self):
        role = Role.objects.create(
            name=Role.Roles.STUDENT,
            description="Student role",
        )

        assert role.name == Role.Roles.STUDENT
        assert role.description == "Student role"

    def test_create_role_with_instructor_role(self):
        role = Role.objects.create(
            name=Role.Roles.INSTRUCTOR,
            description="Instructor role",
        )

        assert role.name == Role.Roles.INSTRUCTOR
        assert role.description == "Instructor role"

    def test_role_name_choices_are_defined_correctly(self):
        assert Role.Roles.STUDENT == "student"
        assert Role.Roles.INSTRUCTOR == "instructor"

    def test_role_name_max_length_supports_defined_choices(self):
        field = Role._meta.get_field("name")

        assert field.max_length == 18

    def test_role_can_be_assigned_to_a_user(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )
        role = Role.objects.create(
            name=Role.Roles.STUDENT,
            description="Student role",
        )

        role.users.add(user)

        assert role.users.filter(pk=user.pk).exists()

    def test_user_can_have_multiple_roles(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )
        student_role = Role.objects.create(
            name=Role.Roles.STUDENT,
            description="Student role",
        )
        instructor_role = Role.objects.create(
            name=Role.Roles.INSTRUCTOR,
            description="Instructor role",
        )

        student_role.users.add(user)
        instructor_role.users.add(user)

        assert set(user.roles.values_list("pk", flat=True)) == {
            student_role.pk,
            instructor_role.pk,
        }

    def test_role_can_have_multiple_users(self):
        first_user = User.objects.create_user(
            username="test_user_1",
            email="test_user_1@example.com",
            password="test-password",
        )
        second_user = User.objects.create_user(
            username="test_user_2",
            email="test_user_2@example.com",
            password="test-password",
        )
        role = Role.objects.create(
            name=Role.Roles.STUDENT,
            description="Student role",
        )

        role.users.add(first_user, second_user)

        assert set(role.users.values_list("pk", flat=True)) == {
            first_user.pk,
            second_user.pk,
        }

    def test_user_roles_reverse_relationship_returns_assigned_roles(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )
        student_role = Role.objects.create(
            name=Role.Roles.STUDENT,
            description="Student role",
        )
        instructor_role = Role.objects.create(
            name=Role.Roles.INSTRUCTOR,
            description="Instructor role",
        )

        student_role.users.add(user)
        instructor_role.users.add(user)

        roles = list(user.roles.all())

        assert student_role in roles
        assert instructor_role in roles

    def test_user_roles_reverse_relationship_is_empty_when_no_roles_are_assigned(
        self,
    ):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

        assert not user.roles.exists()

    def test_role_str_returns_human_readable_role_name_for_student(self):
        role = Role.objects.create(
            name=Role.Roles.STUDENT,
            description="Student role",
        )

        assert str(role) == "Student"

    def test_role_str_returns_human_readable_role_name_for_instructor(self):
        role = Role.objects.create(
            name=Role.Roles.INSTRUCTOR,
            description="Instructor role",
        )

        assert str(role) == "Instructor"

    def test_role_description_is_stored_correctly(self):
        description = "A user who can access student functionality."

        role = Role.objects.create(
            name=Role.Roles.STUDENT,
            description=description,
        )

        role.refresh_from_db()

        assert role.description == description

    def test_role_description_can_contain_multiple_lines(self):
        description = (
            "Student role.\nCan enroll in courses.\nCan track learning progress."
        )

        role = Role.objects.create(
            name=Role.Roles.STUDENT,
            description=description,
        )

        role.refresh_from_db()

        assert role.description == description

    def test_same_user_can_be_added_to_same_role_only_once(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )
        role = Role.objects.create(
            name=Role.Roles.STUDENT,
            description="Student role",
        )

        role.users.add(user)
        role.users.add(user)

        assert role.users.filter(pk=user.pk).count() == 1
        assert role.users.count() == 1


@pytest.mark.django_db
class TestUserSessionModel:
    def test_user_session_can_be_created(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

        session = UserSession.objects.create(
            user=user,
            device="Desktop",
            ip_address="192.168.1.10",
            user_agent="Mozilla/5.0",
        )

        assert session.user == user
        assert session.device == "Desktop"
        assert session.ip_address == "192.168.1.10"
        assert session.user_agent == "Mozilla/5.0"
        assert session.is_revoked is False

    def test_is_revoked_defaults_to_false(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

        session = UserSession.objects.create(
            user=user,
            device="Desktop",
            ip_address="192.168.1.10",
            user_agent="Mozilla/5.0",
        )

        assert session.is_revoked is False

    def test_is_revoked_can_be_set_to_true(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

        session = UserSession.objects.create(
            user=user,
            device="Desktop",
            ip_address="192.168.1.10",
            user_agent="Mozilla/5.0",
            is_revoked=True,
        )

        assert session.is_revoked is True

    def test_user_can_have_multiple_sessions(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

        first_session = UserSession.objects.create(
            user=user,
            device="Desktop",
            ip_address="192.168.1.10",
            user_agent="Mozilla/5.0",
        )
        second_session = UserSession.objects.create(
            user=user,
            device="Mobile",
            ip_address="192.168.1.11",
            user_agent="Mobile Browser",
        )

        sessions = user.sessions.all()

        assert sessions.count() == 2
        assert first_session in sessions
        assert second_session in sessions

    def test_user_session_reverse_relationship_uses_sessions_related_name(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

        session = UserSession.objects.create(
            user=user,
            device="Desktop",
            ip_address="192.168.1.10",
            user_agent="Mozilla/5.0",
        )

        assert session in user.sessions.all()

    def test_user_session_is_deleted_when_user_is_deleted(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

        session = UserSession.objects.create(
            user=user,
            device="Desktop",
            ip_address="192.168.1.10",
            user_agent="Mozilla/5.0",
        )
        session_id = session.pk

        user.delete()

        assert not UserSession.objects.filter(pk=session_id).exists()

    def test_login_at_is_set_automatically_when_session_is_created(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

        session = UserSession.objects.create(
            user=user,
            device="Desktop",
            ip_address="192.168.1.10",
            user_agent="Mozilla/5.0",
        )

        assert session.login_at is not None

    def test_last_activity_at_is_set_automatically_when_session_is_created(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

        session = UserSession.objects.create(
            user=user,
            device="Desktop",
            ip_address="192.168.1.10",
            user_agent="Mozilla/5.0",
        )

        assert session.last_activity_at is not None

    def test_last_activity_at_is_updated_when_session_is_saved(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

        session = UserSession.objects.create(
            user=user,
            device="Desktop",
            ip_address="192.168.1.10",
            user_agent="Mozilla/5.0",
        )

        original_last_activity = session.last_activity_at

        time.sleep(0.01)

        session.device = "Mobile"
        session.save()

        assert session.last_activity_at > original_last_activity

    def test_login_at_is_not_changed_when_session_is_saved(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

        session = UserSession.objects.create(
            user=user,
            device="Desktop",
            ip_address="192.168.1.10",
            user_agent="Mozilla/5.0",
        )

        original_login_at = session.login_at

        time.sleep(0.01)

        session.device = "Mobile"
        session.save()

        assert session.login_at == original_login_at

    def test_sessions_are_ordered_by_most_recent_login_first(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

        first_session = UserSession.objects.create(
            user=user,
            device="Desktop",
            ip_address="192.168.1.10",
            user_agent="Mozilla/5.0",
        )

        time.sleep(0.01)

        second_session = UserSession.objects.create(
            user=user,
            device="Mobile",
            ip_address="192.168.1.11",
            user_agent="Mobile Browser",
        )

        sessions = list(UserSession.objects.all())

        assert sessions[0] == second_session
        assert sessions[1] == first_session

    def test_str_returns_user_and_device(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

        session = UserSession.objects.create(
            user=user,
            device="Desktop",
            ip_address="192.168.1.10",
            user_agent="Mozilla/5.0",
        )

        assert str(session) == f"{user} - Desktop"

    def test_ipv4_address_is_accepted(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

        session = UserSession(
            user=user,
            device="Desktop",
            ip_address="192.168.1.10",
            user_agent="Mozilla/5.0",
        )

        session.full_clean()

    def test_ipv6_address_is_accepted(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

        session = UserSession(
            user=user,
            device="Desktop",
            ip_address="2001:db8::1",
            user_agent="Mozilla/5.0",
        )

        session.full_clean()

    def test_invalid_ip_address_fails_validation(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

        session = UserSession(
            user=user,
            device="Desktop",
            ip_address="not-an-ip-address",
            user_agent="Mozilla/5.0",
        )

        with pytest.raises(ValidationError):
            session.full_clean()

    def test_device_can_contain_long_value_up_to_field_limit(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )
        device = "D" * 255

        session = UserSession.objects.create(
            user=user,
            device=device,
            ip_address="192.168.1.10",
            user_agent="Mozilla/5.0",
        )

        assert session.device == device

    def test_user_agent_can_contain_long_text(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )
        user_agent = "Mozilla/5.0 " + ("A" * 1000)

        session = UserSession.objects.create(
            user=user,
            device="Desktop",
            ip_address="192.168.1.10",
            user_agent=user_agent,
        )

        assert session.user_agent == user_agent


@pytest.mark.django_db
class TestLoginHistoryModel:
    def test_login_history_can_be_created_for_user(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

        history = LoginHistory.objects.create(
            user=user,
            is_successful=True,
            ip_address="192.168.1.10",
            device="Desktop",
        )

        assert history.user == user
        assert history.is_successful is True
        assert history.ip_address == "192.168.1.10"
        assert history.device == "Desktop"
        assert history.location == ""

    def test_successful_login_history_stores_successful_status(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

        history = LoginHistory.objects.create(
            user=user,
            is_successful=True,
            ip_address="192.168.1.10",
            device="Desktop",
        )

        assert history.is_successful is True

    def test_failed_login_history_stores_failed_status(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

        history = LoginHistory.objects.create(
            user=user,
            is_successful=False,
            ip_address="192.168.1.10",
            device="Desktop",
        )

        assert history.is_successful is False

    def test_location_is_optional(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

        history = LoginHistory.objects.create(
            user=user,
            is_successful=True,
            ip_address="192.168.1.10",
            device="Desktop",
        )

        assert history.location == ""

    def test_location_is_stored_when_provided(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

        history = LoginHistory.objects.create(
            user=user,
            is_successful=True,
            ip_address="192.168.1.10",
            device="Desktop",
            location="Test Location",
        )

        assert history.location == "Test Location"

    def test_timestamp_is_set_automatically_on_creation(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

        history = LoginHistory.objects.create(
            user=user,
            is_successful=True,
            ip_address="192.168.1.10",
            device="Desktop",
        )

        assert history.timestamp is not None

    def test_timestamp_is_not_changed_when_history_is_updated(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

        history = LoginHistory.objects.create(
            user=user,
            is_successful=True,
            ip_address="192.168.1.10",
            device="Desktop",
        )

        original_timestamp = history.timestamp

        time.sleep(0.01)

        history.device = "Mobile"
        history.save()

        assert history.timestamp == original_timestamp

    def test_login_history_is_ordered_by_most_recent_timestamp_first(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

        first_history = LoginHistory.objects.create(
            user=user,
            is_successful=True,
            ip_address="192.168.1.10",
            device="Desktop",
        )

        time.sleep(0.01)

        second_history = LoginHistory.objects.create(
            user=user,
            is_successful=False,
            ip_address="192.168.1.11",
            device="Mobile",
        )

        histories = list(LoginHistory.objects.all())

        assert histories[0] == second_history
        assert histories[1] == first_history

    def test_user_can_have_multiple_login_history_records(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

        first_history = LoginHistory.objects.create(
            user=user,
            is_successful=True,
            ip_address="192.168.1.10",
            device="Desktop",
        )
        second_history = LoginHistory.objects.create(
            user=user,
            is_successful=False,
            ip_address="192.168.1.11",
            device="Mobile",
        )

        histories = user.login_history.all()

        assert histories.count() == 2
        assert first_history in histories
        assert second_history in histories

    def test_login_history_is_deleted_when_user_is_deleted(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

        history = LoginHistory.objects.create(
            user=user,
            is_successful=True,
            ip_address="192.168.1.10",
            device="Desktop",
        )
        history_id = history.pk

        user.delete()

        assert not LoginHistory.objects.filter(pk=history_id).exists()

    def test_ipv4_address_is_valid(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

        history = LoginHistory(
            user=user,
            is_successful=True,
            ip_address="192.168.1.10",
            device="Desktop",
        )

        history.full_clean()

    def test_ipv6_address_is_valid(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

        history = LoginHistory(
            user=user,
            is_successful=True,
            ip_address="2001:db8::1",
            device="Desktop",
        )

        history.full_clean()

    def test_invalid_ip_address_fails_validation(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

        history = LoginHistory(
            user=user,
            is_successful=True,
            ip_address="not-an-ip-address",
            device="Desktop",
        )

        with pytest.raises(ValidationError):
            history.full_clean()

    def test_str_returns_success_for_successful_login(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

        history = LoginHistory.objects.create(
            user=user,
            is_successful=True,
            ip_address="192.168.1.10",
            device="Desktop",
        )

        expected = f"{user} - Success ({history.timestamp:%Y-%m-%d %H:%M:%S})"

        assert str(history) == expected

    def test_str_returns_failed_for_unsuccessful_login(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

        history = LoginHistory.objects.create(
            user=user,
            is_successful=False,
            ip_address="192.168.1.10",
            device="Desktop",
        )

        expected = f"{user} - Failed ({history.timestamp:%Y-%m-%d %H:%M:%S})"

        assert str(history) == expected

    def test_device_can_store_value_at_maximum_field_length(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )
        device = "D" * 255

        history = LoginHistory.objects.create(
            user=user,
            is_successful=True,
            ip_address="192.168.1.10",
            device=device,
        )

        assert history.device == device

    def test_location_can_store_value_at_maximum_field_length(self):
        user = User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )
        location = "L" * 255

        history = LoginHistory.objects.create(
            user=user,
            is_successful=True,
            ip_address="192.168.1.10",
            device="Desktop",
            location=location,
        )

        assert history.location == location
