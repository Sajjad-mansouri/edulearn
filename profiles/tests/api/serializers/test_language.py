import pytest
from django.contrib.auth import get_user_model

from profiles.api.serializers.language import LanguageSerializer
from profiles.models import Language, Profile

User = get_user_model()


@pytest.fixture
def profile(db):
    user = User.objects.create_user(
        username="language_test_user",
        email="language_test_user@example.com",
        password="test-password",
    )
    return Profile.objects.create(user=user)


@pytest.fixture
def language(db, profile):
    return Language.objects.create(
        profile=profile,
        language="English",
        proficiency="C1",
    )


@pytest.fixture
def serializer():
    return LanguageSerializer()


class TestLanguageSerializer:
    def test_fields(self, serializer):
        assert set(serializer.fields) == {
            "id",
            "language",
            "proficiency",
        }

    def test_id_is_read_only(self, serializer):
        assert serializer.fields["id"].read_only is True

    def test_language_is_required(self, serializer):
        field = serializer.fields["language"]

        assert field.required is True
        assert field.allow_null is False
        assert field.allow_blank is False

    def test_proficiency_is_required(self, serializer):
        field = serializer.fields["proficiency"]

        assert field.required is True
        assert field.allow_null is False
        assert field.allow_blank is False

    def test_language_max_length(self, serializer):
        assert serializer.fields["language"].max_length == 250

    def test_proficiency_choices(self, serializer):
        assert set(serializer.fields["proficiency"].choices) == {
            "Native",
            "C2",
            "C1",
            "B2",
            "B1",
            "A2",
            "A1",
        }

    def test_valid_complete_input(self):
        data = {
            "language": "English",
            "proficiency": "C1",
        }

        serializer = LanguageSerializer(data=data)

        assert serializer.is_valid() is True
        assert serializer.errors == {}
        assert serializer.validated_data == data

    def test_all_defined_proficiencies_are_valid(self):
        for proficiency, _ in Language.PROFICIENCIES:
            serializer = LanguageSerializer(
                data={
                    "language": "English",
                    "proficiency": proficiency,
                }
            )

            assert serializer.is_valid() is True
            assert serializer.errors == {}
            assert serializer.validated_data["proficiency"] == proficiency

    @pytest.mark.parametrize(
        "proficiency",
        [
            "C3",
            "B3",
            "A3",
            "Beginner",
            "Advanced",
            "",
            None,
        ],
    )
    def test_invalid_proficiency_is_rejected(self, proficiency):
        serializer = LanguageSerializer(
            data={
                "language": "English",
                "proficiency": proficiency,
            }
        )

        assert serializer.is_valid() is False
        assert "proficiency" in serializer.errors

    def test_missing_language_is_rejected(self):
        serializer = LanguageSerializer(
            data={
                "proficiency": "C1",
            }
        )

        assert serializer.is_valid() is False
        assert "language" in serializer.errors

    def test_missing_proficiency_is_rejected(self):
        serializer = LanguageSerializer(
            data={
                "language": "English",
            }
        )

        assert serializer.is_valid() is False
        assert "proficiency" in serializer.errors

    def test_empty_language_is_rejected(self):
        serializer = LanguageSerializer(
            data={
                "language": "",
                "proficiency": "C1",
            }
        )

        assert serializer.is_valid() is False
        assert "language" in serializer.errors

    def test_null_language_is_rejected(self):
        serializer = LanguageSerializer(
            data={
                "language": None,
                "proficiency": "C1",
            }
        )

        assert serializer.is_valid() is False
        assert "language" in serializer.errors

    def test_null_proficiency_is_rejected(self):
        serializer = LanguageSerializer(
            data={
                "language": "English",
                "proficiency": None,
            }
        )

        assert serializer.is_valid() is False
        assert "proficiency" in serializer.errors

    def test_language_with_unicode_is_valid(self):
        data = {
            "language": "فارسی",
            "proficiency": "Native",
        }

        serializer = LanguageSerializer(data=data)

        assert serializer.is_valid() is True
        assert serializer.validated_data == data

    def test_language_with_spaces_and_hyphen_is_valid(self):
        data = {
            "language": "American English",
            "proficiency": "C1",
        }

        serializer = LanguageSerializer(data=data)

        assert serializer.is_valid() is True
        assert serializer.validated_data == data

    def test_language_at_max_length_is_valid(self):
        language_name = "A" * 250

        serializer = LanguageSerializer(
            data={
                "language": language_name,
                "proficiency": "C1",
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["language"] == language_name

    def test_language_over_max_length_is_rejected(self):
        language_name = "A" * 251

        serializer = LanguageSerializer(
            data={
                "language": language_name,
                "proficiency": "C1",
            }
        )

        assert serializer.is_valid() is False
        assert "language" in serializer.errors

    def test_profile_is_not_exposed(self, serializer):
        assert "profile" not in serializer.fields

    def test_profile_input_is_ignored(self, profile):
        serializer = LanguageSerializer(
            data={
                "language": "English",
                "proficiency": "C1",
                "profile": profile.pk,
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data == {
            "language": "English",
            "proficiency": "C1",
        }
        assert "profile" not in serializer.validated_data

    def test_id_input_is_ignored(self):
        serializer = LanguageSerializer(
            data={
                "id": 123,
                "language": "English",
                "proficiency": "C1",
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data == {
            "language": "English",
            "proficiency": "C1",
        }
        assert "id" not in serializer.validated_data

    def test_partial_update_can_change_language(self, language):
        serializer = LanguageSerializer(
            language,
            data={"language": "German"},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data == {"language": "German"}

    def test_partial_update_can_change_proficiency(self, language):
        serializer = LanguageSerializer(
            language,
            data={"proficiency": "B2"},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data == {"proficiency": "B2"}

    def test_partial_update_can_change_both_fields(self, language):
        data = {
            "language": "German",
            "proficiency": "B2",
        }

        serializer = LanguageSerializer(
            language,
            data=data,
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data == data

    def test_partial_update_allows_empty_data(self, language):
        serializer = LanguageSerializer(
            language,
            data={},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data == {}

    def test_full_update_requires_language(self, language):
        serializer = LanguageSerializer(
            language,
            data={"proficiency": "B2"},
        )

        assert serializer.is_valid() is False
        assert "language" in serializer.errors

    def test_full_update_requires_proficiency(self, language):
        serializer = LanguageSerializer(
            language,
            data={"language": "German"},
        )

        assert serializer.is_valid() is False
        assert "proficiency" in serializer.errors

    def test_full_update(self, language):
        data = {
            "language": "German",
            "proficiency": "B2",
        }

        serializer = LanguageSerializer(
            language,
            data=data,
        )

        assert serializer.is_valid() is True

        updated_language = serializer.save()

        assert updated_language.language == "German"
        assert updated_language.proficiency == "B2"

    def test_update_does_not_change_profile(self, language):
        original_profile = language.profile

        serializer = LanguageSerializer(
            language,
            data={
                "language": "German",
                "proficiency": "B2",
            },
        )

        assert serializer.is_valid() is True

        updated_language = serializer.save()

        assert updated_language.profile == original_profile

    def test_update_cannot_change_id(self, language):
        original_id = language.pk

        serializer = LanguageSerializer(
            language,
            data={
                "id": original_id + 100,
                "language": "German",
                "proficiency": "B2",
            },
        )

        assert serializer.is_valid() is True
        assert "id" not in serializer.validated_data

        updated_language = serializer.save()

        assert updated_language.pk == original_id
        assert updated_language.language == "German"
        assert updated_language.proficiency == "B2"

    def test_update_ignores_profile_input(self, language, profile):
        original_profile_id = language.profile_id

        serializer = LanguageSerializer(
            language,
            data={
                "language": "German",
                "proficiency": "B2",
                "profile": profile.pk,
            },
        )

        assert serializer.is_valid() is True
        assert "profile" not in serializer.validated_data

        updated_language = serializer.save()

        assert updated_language.profile_id == original_profile_id
        assert updated_language.language == "German"
        assert updated_language.proficiency == "B2"

    def test_representation(self, language):
        serializer = LanguageSerializer(language)

        assert serializer.data == {
            "id": language.pk,
            "language": "English",
            "proficiency": "C1",
        }

    def test_representation_does_not_expose_profile(self, language):
        serializer = LanguageSerializer(language)

        assert "profile" not in serializer.data

    def test_serialization_does_not_modify_instance(self, language):
        original_values = {
            "pk": language.pk,
            "profile_id": language.profile_id,
            "language": language.language,
            "proficiency": language.proficiency,
        }

        serializer = LanguageSerializer(language)

        _ = serializer.data

        assert language.pk == original_values["pk"]
        assert language.profile_id == original_values["profile_id"]
        assert language.language == original_values["language"]
        assert language.proficiency == original_values["proficiency"]
