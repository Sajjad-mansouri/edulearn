import pytest
from django.contrib.auth import get_user_model

from profiles.api.serializers.skill import SkillSerializer
from profiles.models import Profile, Skill

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="skill_test_user",
        email="skill_test@example.com",
        password="test-password",
    )


@pytest.fixture
def profile(db, user):
    return Profile.objects.create(user=user)


@pytest.fixture
def skill(db, profile):
    return Skill.objects.create(
        profile=profile,
        name="Python",
        description="Python programming language",
    )


@pytest.fixture
def serializer():
    return SkillSerializer()


class TestSkillSerializer:
    def test_fields(self, serializer):
        assert set(serializer.fields) == {
            "id",
            "name",
            "description",
        }

    def test_id_is_read_only(self, serializer):
        assert serializer.fields["id"].read_only is True

    def test_name_is_required(self, serializer):
        field = serializer.fields["name"]

        assert field.required is True
        assert field.allow_null is False
        assert field.allow_blank is False

    def test_description_is_optional(self, serializer):
        field = serializer.fields["description"]

        assert field.required is False
        assert field.allow_null is False
        assert field.allow_blank is True

    def test_name_max_length(self, serializer):
        assert serializer.fields["name"].max_length == 100

    def test_slug_is_not_exposed(self, serializer):
        assert "slug" not in serializer.fields

    def test_profile_is_not_exposed(self, serializer):
        assert "profile" not in serializer.fields

    def test_valid_complete_input(self):
        data = {
            "name": "Python",
            "description": "Python programming language",
        }

        serializer = SkillSerializer(data=data)

        assert serializer.is_valid() is True
        assert serializer.errors == {}
        assert serializer.validated_data == data

    def test_valid_input_without_description(self):
        serializer = SkillSerializer(
            data={
                "name": "Python",
            }
        )

        assert serializer.is_valid() is True
        assert serializer.errors == {}
        assert serializer.validated_data == {
            "name": "Python",
        }

    def test_empty_description_is_valid(self):
        serializer = SkillSerializer(
            data={
                "name": "Python",
                "description": "",
            }
        )

        assert serializer.is_valid() is True
        assert serializer.errors == {}
        assert serializer.validated_data == {
            "name": "Python",
            "description": "",
        }

    def test_missing_name_is_rejected(self):
        serializer = SkillSerializer(
            data={
                "description": "Python programming language",
            }
        )

        assert serializer.is_valid() is False
        assert "name" in serializer.errors

    def test_empty_name_is_rejected(self):
        serializer = SkillSerializer(
            data={
                "name": "",
                "description": "Python programming language",
            }
        )

        assert serializer.is_valid() is False
        assert "name" in serializer.errors

    def test_null_name_is_rejected(self):
        serializer = SkillSerializer(
            data={
                "name": None,
                "description": "Python programming language",
            }
        )

        assert serializer.is_valid() is False
        assert "name" in serializer.errors

    def test_null_description_is_rejected(self):
        serializer = SkillSerializer(
            data={
                "name": "Python",
                "description": None,
            }
        )

        assert serializer.is_valid() is False
        assert "description" in serializer.errors

    def test_name_at_max_length_is_valid(self):
        name = "A" * 100

        serializer = SkillSerializer(
            data={
                "name": name,
                "description": "A skill description",
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["name"] == name

    def test_name_over_max_length_is_rejected(self):
        name = "A" * 101

        serializer = SkillSerializer(
            data={
                "name": name,
                "description": "A skill description",
            }
        )

        assert serializer.is_valid() is False
        assert "name" in serializer.errors

    def test_unicode_name_is_valid(self):
        data = {
            "name": "برنامه‌نویسی",
            "description": "مهارت برنامه‌نویسی",
        }

        serializer = SkillSerializer(data=data)

        assert serializer.is_valid() is True
        assert serializer.validated_data == data

    def test_unicode_description_is_valid(self):
        data = {
            "name": "Python",
            "description": "مهارت برنامه‌نویسی پایتون",
        }

        serializer = SkillSerializer(data=data)

        assert serializer.is_valid() is True
        assert serializer.validated_data == data

    def test_name_with_spaces_is_valid(self):
        data = {
            "name": "Machine Learning",
            "description": "Machine learning skill",
        }

        serializer = SkillSerializer(data=data)

        assert serializer.is_valid() is True
        assert serializer.validated_data == data

    def test_name_with_hyphen_is_valid(self):
        data = {
            "name": "Problem-Solving",
            "description": "Problem-solving skill",
        }

        serializer = SkillSerializer(data=data)

        assert serializer.is_valid() is True
        assert serializer.validated_data == data

    def test_name_whitespace_is_trimmed(self):
        serializer = SkillSerializer(
            data={
                "name": "  Python  ",
                "description": "Programming language",
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["name"] == "Python"

    def test_description_whitespace_is_trimmed(self):
        serializer = SkillSerializer(
            data={
                "name": "Python",
                "description": "  Python programming language  ",
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["description"] == (
            "Python programming language"
        )

    def test_unknown_slug_input_is_ignored(self):
        serializer = SkillSerializer(
            data={
                "name": "Python",
                "description": "Python programming language",
                "slug": "python",
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data == {
            "name": "Python",
            "description": "Python programming language",
        }
        assert "slug" not in serializer.validated_data

    def test_profile_input_is_ignored(self, profile):
        serializer = SkillSerializer(
            data={
                "name": "Python",
                "description": "Python programming language",
                "profile": profile.pk,
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data == {
            "name": "Python",
            "description": "Python programming language",
        }
        assert "profile" not in serializer.validated_data

    def test_id_input_is_ignored(self):
        serializer = SkillSerializer(
            data={
                "id": 999999,
                "name": "Python",
                "description": "Python programming language",
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data == {
            "name": "Python",
            "description": "Python programming language",
        }
        assert "id" not in serializer.validated_data

    def test_partial_update_can_change_name(self, skill):
        serializer = SkillSerializer(
            skill,
            data={"name": "Django"},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data == {
            "name": "Django",
        }

    def test_partial_update_can_change_description(self, skill):
        serializer = SkillSerializer(
            skill,
            data={"description": "Django web framework skill"},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data == {
            "description": "Django web framework skill",
        }

    def test_partial_update_can_clear_description(self, skill):
        serializer = SkillSerializer(
            skill,
            data={"description": ""},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data == {
            "description": "",
        }

    def test_partial_update_can_change_both_fields(self, skill):
        data = {
            "name": "Django",
            "description": "Django web framework skill",
        }

        serializer = SkillSerializer(
            skill,
            data=data,
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data == data

    def test_partial_update_allows_empty_data(self, skill):
        serializer = SkillSerializer(
            skill,
            data={},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data == {}

    def test_full_update_requires_name(self, skill):
        serializer = SkillSerializer(
            skill,
            data={
                "description": "Updated description",
            },
        )

        assert serializer.is_valid() is False
        assert "name" in serializer.errors

    def test_full_update_does_not_require_description(self, skill):
        serializer = SkillSerializer(
            skill,
            data={
                "name": "Django",
            },
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data == {
            "name": "Django",
        }

    def test_full_update(self, skill):
        data = {
            "name": "Django",
            "description": "Django web framework skill",
        }

        serializer = SkillSerializer(
            skill,
            data=data,
        )

        assert serializer.is_valid() is True

        updated_skill = serializer.save()

        assert updated_skill.name == "Django"
        assert updated_skill.description == ("Django web framework skill")

    def test_update_does_not_change_profile(
        self,
        skill,
        profile,
    ):
        original_profile_id = skill.profile_id

        serializer = SkillSerializer(
            skill,
            data={
                "name": "Django",
                "description": "Django web framework skill",
            },
        )

        assert serializer.is_valid() is True

        updated_skill = serializer.save()

        assert updated_skill.profile_id == original_profile_id
        assert updated_skill.profile_id == profile.pk

    def test_update_cannot_change_id(self, skill):
        original_id = skill.pk

        serializer = SkillSerializer(
            skill,
            data={
                "id": original_id + 100,
                "name": "Django",
                "description": "Django web framework skill",
            },
        )

        assert serializer.is_valid() is True
        assert "id" not in serializer.validated_data

        updated_skill = serializer.save()

        assert updated_skill.pk == original_id

    def test_update_ignores_slug_input(self, skill):
        original_slug = skill.slug

        serializer = SkillSerializer(
            skill,
            data={
                "name": "Django",
                "description": "Django web framework skill",
                "slug": "custom-slug",
            },
        )

        assert serializer.is_valid() is True
        assert "slug" not in serializer.validated_data

        updated_skill = serializer.save()

        assert updated_skill.slug == original_slug
        assert updated_skill.name == "Django"

    def test_update_ignores_profile_input(
        self,
        skill,
        profile,
    ):
        original_profile_id = skill.profile_id

        serializer = SkillSerializer(
            skill,
            data={
                "name": "Django",
                "description": "Django web framework skill",
                "profile": profile.pk + 100,
            },
        )

        assert serializer.is_valid() is True
        assert "profile" not in serializer.validated_data

        updated_skill = serializer.save()

        assert updated_skill.profile_id == original_profile_id

    def test_representation(self, skill):
        serializer = SkillSerializer(skill)

        assert serializer.data == {
            "id": skill.pk,
            "name": "Python",
            "description": "Python programming language",
        }

    def test_representation_with_empty_description(
        self,
        skill,
    ):
        skill.description = ""
        skill.save(update_fields=["description"])

        serializer = SkillSerializer(skill)

        assert serializer.data == {
            "id": skill.pk,
            "name": "Python",
            "description": "",
        }

    def test_representation_does_not_expose_slug(self, skill):
        serializer = SkillSerializer(skill)

        assert "slug" not in serializer.data

    def test_representation_does_not_expose_profile(self, skill):
        serializer = SkillSerializer(skill)

        assert "profile" not in serializer.data

    def test_serialization_does_not_modify_instance(self, skill):
        original_values = {
            "pk": skill.pk,
            "profile_id": skill.profile_id,
            "name": skill.name,
            "slug": skill.slug,
            "description": skill.description,
        }

        serializer = SkillSerializer(skill)

        _ = serializer.data

        assert skill.pk == original_values["pk"]
        assert skill.profile_id == original_values["profile_id"]
        assert skill.name == original_values["name"]
        assert skill.slug == original_values["slug"]
        assert skill.description == original_values["description"]
