import pytest
from django.contrib.auth import get_user_model

from accounts.api.serializers import CurrentUserSerializer

User = get_user_model()


@pytest.mark.django_db
class TestCurrentUserSerializer:
    def test_fields_are_defined_correctly(self):
        serializer = CurrentUserSerializer()

        assert set(serializer.fields) == {
            "id",
            "username",
            "email",
            "is_authenticated",
            "is_instructor",
            "is_student",
            "avatar",
            "first_name",
            "last_name",
        }

    def test_serializes_user_fields(self, test_user):
        serializer = CurrentUserSerializer(test_user)

        assert serializer.data["id"] == test_user.id
        assert serializer.data["username"] == test_user.username
        assert serializer.data["email"] == test_user.email
        assert serializer.data["first_name"] == test_user.first_name
        assert serializer.data["last_name"] == test_user.last_name

    def test_is_authenticated_is_true(self, test_user):
        serializer = CurrentUserSerializer(test_user)

        assert serializer.data["is_authenticated"] is True

    def test_user_without_roles_is_not_instructor_or_student(
        self,
        test_user,
    ):
        serializer = CurrentUserSerializer(test_user)

        assert serializer.data["is_instructor"] is False
        assert serializer.data["is_student"] is False

    def test_instructor_user_is_identified_correctly(
        self,
        test_user,
        instructor_role,
    ):
        test_user.roles.add(instructor_role)

        serializer = CurrentUserSerializer(test_user)

        assert serializer.data["is_instructor"] is True
        assert serializer.data["is_student"] is False

    def test_student_user_is_identified_correctly(
        self,
        test_user,
        student_role,
    ):
        test_user.roles.add(student_role)

        serializer = CurrentUserSerializer(test_user)

        assert serializer.data["is_instructor"] is False
        assert serializer.data["is_student"] is True

    def test_user_with_both_roles_is_identified_correctly(
        self,
        test_user,
        instructor_role,
        student_role,
    ):
        test_user.roles.add(
            instructor_role,
            student_role,
        )

        serializer = CurrentUserSerializer(test_user)

        assert serializer.data["is_instructor"] is True
        assert serializer.data["is_student"] is True

    def test_avatar_is_serialized(
        self,
        test_user,
        monkeypatch,
    ):
        avatar = "https://example.com/avatar.jpg"

        monkeypatch.setattr(
            type(test_user),
            "avatar",
            property(lambda self: avatar),
        )

        serializer = CurrentUserSerializer(test_user)

        assert serializer.data["avatar"] == avatar

    def test_avatar_is_empty_when_user_has_no_avatar(
        self,
        test_user,
    ):
        serializer = CurrentUserSerializer(test_user)

        assert serializer.data["avatar"] == test_user.avatar

    def test_password_is_not_exposed(self, test_user):
        serializer = CurrentUserSerializer(test_user)

        assert "password" not in serializer.data

    def test_serializer_output_contains_only_declared_fields(
        self,
        test_user,
    ):
        serializer = CurrentUserSerializer(test_user)

        assert set(serializer.data.keys()) == {
            "id",
            "username",
            "email",
            "is_authenticated",
            "is_instructor",
            "is_student",
            "avatar",
            "first_name",
            "last_name",
        }

    def test_get_is_authenticated_returns_true(self, test_user):
        serializer = CurrentUserSerializer()

        assert serializer.get_is_authenticated(test_user) is True

    def test_get_is_instructor_returns_true_for_instructor(
        self,
        test_user,
        instructor_role,
    ):
        test_user.roles.add(instructor_role)

        serializer = CurrentUserSerializer()

        assert serializer.get_is_instructor(test_user) is True

    def test_get_is_instructor_returns_false_for_non_instructor(
        self,
        test_user,
        student_role,
    ):
        test_user.roles.add(student_role)

        serializer = CurrentUserSerializer()

        assert serializer.get_is_instructor(test_user) is False

    def test_get_is_student_returns_true_for_student(
        self,
        test_user,
        student_role,
    ):
        test_user.roles.add(student_role)

        serializer = CurrentUserSerializer()

        assert serializer.get_is_student(test_user) is True

    def test_get_is_student_returns_false_for_non_student(
        self,
        test_user,
        instructor_role,
    ):
        test_user.roles.add(instructor_role)

        serializer = CurrentUserSerializer()

        assert serializer.get_is_student(test_user) is False
