from io import BytesIO

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework import serializers

from profiles.api.serializers.profile import StudentProfileUpdateSerializer
from profiles.models import Profile, StudentProfile

User = get_user_model()


@pytest.fixture
def student_user(db):
    return User.objects.create_user(
        username="student_profile_update_user",
        email="student-profile-update@example.com",
        password="test-password",
    )


@pytest.fixture
def profile(db, student_user):
    return Profile.objects.create(
        user=student_user,
        country="Azerbaijan",
        timezone="Asia/Baku",
        company="Example Company",
        job_title="Developer",
    )


@pytest.fixture
def student_profile(db, profile):
    return StudentProfile.objects.create(
        profile=profile,
        headline="Original headline",
        biography="Original biography",
        learning_goal="Original learning goal",
        current_streak=5,
        longest_streak=10,
    )


@pytest.fixture
def valid_cover_image():
    image = Image.new("RGB", (100, 100), "white")

    image_file = BytesIO()
    image.save(image_file, format="JPEG")
    image_file.seek(0)

    return SimpleUploadedFile(
        "student-cover.jpg",
        image_file.read(),
        content_type="image/jpeg",
    )


class TestStudentProfileUpdateSerializerConfiguration:
    def test_serializer_is_model_serializer(self):
        serializer = StudentProfileUpdateSerializer()

        assert isinstance(serializer, serializers.ModelSerializer)

    def test_serializer_model_is_student_profile(self):
        serializer = StudentProfileUpdateSerializer()

        assert serializer.Meta.model is StudentProfile

    def test_serializer_fields_are_exact(self):
        serializer = StudentProfileUpdateSerializer()

        assert list(serializer.fields) == [
            "cover",
            "biography",
            "headline",
        ]

    def test_cover_field_is_writable(self):
        serializer = StudentProfileUpdateSerializer()

        field = serializer.fields["cover"]

        assert field.read_only is False
        assert field.write_only is False

    def test_biography_field_is_writable(self):
        serializer = StudentProfileUpdateSerializer()

        field = serializer.fields["biography"]

        assert field.read_only is False
        assert field.write_only is False

    def test_headline_field_is_writable(self):
        serializer = StudentProfileUpdateSerializer()

        field = serializer.fields["headline"]

        assert field.read_only is False
        assert field.write_only is False

    def test_cover_is_not_required(self):
        serializer = StudentProfileUpdateSerializer()

        assert serializer.fields["cover"].required is False

    def test_biography_is_not_required(self):
        serializer = StudentProfileUpdateSerializer()

        assert serializer.fields["biography"].required is False

    def test_headline_is_not_required(self):
        serializer = StudentProfileUpdateSerializer()

        assert serializer.fields["headline"].required is False

    def test_profile_field_is_not_exposed(self):
        serializer = StudentProfileUpdateSerializer()

        assert "profile" not in serializer.fields

    def test_learning_goal_is_not_exposed(self):
        serializer = StudentProfileUpdateSerializer()

        assert "learning_goal" not in serializer.fields

    def test_current_streak_is_not_exposed(self):
        serializer = StudentProfileUpdateSerializer()

        assert "current_streak" not in serializer.fields

    def test_longest_streak_is_not_exposed(self):
        serializer = StudentProfileUpdateSerializer()

        assert "longest_streak" not in serializer.fields

    def test_profile_model_fields_are_not_exposed(self):
        serializer = StudentProfileUpdateSerializer()

        profile_fields = {
            "website",
            "country",
            "timezone",
            "language",
            "linkedin",
            "github",
            "date_of_birth",
            "company",
            "job_title",
        }

        assert profile_fields.isdisjoint(serializer.fields)


class TestStudentProfileUpdateSerializerValidation:
    def test_valid_headline(self, student_profile):
        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={"headline": "Senior Python Instructor"},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["headline"] == ("Senior Python Instructor")

    def test_valid_biography(self, student_profile):
        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={"biography": "Experienced software instructor."},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["biography"] == (
            "Experienced software instructor."
        )

    def test_empty_headline_is_allowed(self, student_profile):
        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={"headline": ""},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["headline"] == ""

    def test_empty_biography_is_allowed(self, student_profile):
        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={"biography": ""},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["biography"] == ""

    def test_whitespace_headline_is_trimmed(self, student_profile):
        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={"headline": "  Python Instructor  "},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["headline"] == "Python Instructor"

    def test_whitespace_biography_is_trimmed(self, student_profile):
        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={"biography": "  Experienced instructor.  "},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["biography"] == ("Experienced instructor.")

    def test_headline_at_maximum_length_is_valid(self, student_profile):
        headline = "a" * 255

        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={"headline": headline},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["headline"] == headline

    def test_headline_longer_than_maximum_length_is_rejected(
        self,
        student_profile,
    ):
        headline = "a" * 256

        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={"headline": headline},
            partial=True,
        )

        assert serializer.is_valid() is False
        assert "headline" in serializer.errors

    def test_non_string_headline_is_coerced_to_string(self, student_profile):
        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={"headline": 123},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["headline"] == "123"

    def test_non_string_biography_is_coerced_to_string(
        self,
        student_profile,
    ):
        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={"biography": 123},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["biography"] == "123"

    def test_null_headline_is_rejected(self, student_profile):
        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={"headline": None},
            partial=True,
        )

        assert serializer.is_valid() is False
        assert "headline" in serializer.errors

    def test_null_biography_is_rejected(self, student_profile):
        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={"biography": None},
            partial=True,
        )

        assert serializer.is_valid() is False
        assert "biography" in serializer.errors

    def test_missing_fields_are_valid_during_partial_update(
        self,
        student_profile,
    ):
        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data == {}


class TestStudentProfileUpdateSerializerCover:
    def test_valid_cover_is_accepted(
        self,
        student_profile,
        valid_cover_image,
    ):
        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={"cover": valid_cover_image},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert "cover" in serializer.validated_data

    def test_invalid_image_content_is_rejected(self, student_profile):
        invalid_image = SimpleUploadedFile(
            "invalid.jpg",
            b"this is not a real image",
            content_type="image/jpeg",
        )

        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={"cover": invalid_image},
            partial=True,
        )

        assert serializer.is_valid() is False
        assert "cover" in serializer.errors

    def test_null_cover_is_rejected(self, student_profile):
        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={"cover": None},
            partial=True,
        )

        assert serializer.is_valid() is False
        assert "cover" in serializer.errors

    def test_empty_cover_string_is_rejected(self, student_profile):
        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={"cover": ""},
            partial=True,
        )

        assert serializer.is_valid() is False
        assert "cover" in serializer.errors

    def test_cover_can_be_omitted(self, student_profile):
        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={"headline": "Updated headline"},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert "cover" not in serializer.validated_data

    def test_cover_extension_is_preserved(
        self,
        student_profile,
        valid_cover_image,
    ):
        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={"cover": valid_cover_image},
            partial=True,
        )

        assert serializer.is_valid() is True

        cover = serializer.validated_data["cover"]

        assert cover.name.lower().endswith(".jpg")

    def test_cover_can_be_saved(
        self,
        student_profile,
        valid_cover_image,
    ):
        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={"cover": valid_cover_image},
            partial=True,
        )

        assert serializer.is_valid() is True

        updated_profile = serializer.save()

        assert updated_profile.cover
        assert updated_profile.cover.name
        assert updated_profile.cover.name.startswith("profiles/students/cover/")

    def test_saved_cover_exists_on_disk(
        self,
        student_profile,
        valid_cover_image,
    ):
        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={"cover": valid_cover_image},
            partial=True,
        )

        assert serializer.is_valid() is True

        serializer.save()

        student_profile.refresh_from_db()

        assert student_profile.cover
        assert student_profile.cover.storage.exists(
            student_profile.cover.name,
        )


class TestStudentProfileUpdateSerializerRepresentation:
    def test_representation_contains_only_exposed_fields(
        self,
        student_profile,
    ):
        serializer = StudentProfileUpdateSerializer(student_profile)

        assert set(serializer.data.keys()) == {
            "cover",
            "biography",
            "headline",
        }

    def test_representation_contains_headline(
        self,
        student_profile,
    ):
        serializer = StudentProfileUpdateSerializer(student_profile)

        assert serializer.data["headline"] == "Original headline"

    def test_representation_contains_biography(
        self,
        student_profile,
    ):
        serializer = StudentProfileUpdateSerializer(student_profile)

        assert serializer.data["biography"] == "Original biography"

    def test_representation_contains_cover(
        self,
        student_profile,
        valid_cover_image,
    ):
        student_profile.cover = valid_cover_image
        student_profile.save(update_fields=["cover"])

        serializer = StudentProfileUpdateSerializer(student_profile)

        assert serializer.data["cover"]
        assert student_profile.cover.url in serializer.data["cover"]

    def test_profile_is_not_in_representation(
        self,
        student_profile,
    ):
        serializer = StudentProfileUpdateSerializer(student_profile)

        assert "profile" not in serializer.data

    def test_learning_goal_is_not_in_representation(
        self,
        student_profile,
    ):
        serializer = StudentProfileUpdateSerializer(student_profile)

        assert "learning_goal" not in serializer.data

    def test_streak_fields_are_not_in_representation(
        self,
        student_profile,
    ):
        serializer = StudentProfileUpdateSerializer(student_profile)

        assert "current_streak" not in serializer.data
        assert "longest_streak" not in serializer.data


class TestStudentProfileUpdateSerializerPartialUpdates:
    def test_partial_update_preserves_headline_when_omitted(
        self,
        student_profile,
    ):
        original_headline = student_profile.headline

        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={"biography": "Updated biography"},
            partial=True,
        )

        assert serializer.is_valid() is True

        serializer.save()
        student_profile.refresh_from_db()

        assert student_profile.headline == original_headline
        assert student_profile.biography == "Updated biography"

    def test_partial_update_preserves_biography_when_omitted(
        self,
        student_profile,
    ):
        original_biography = student_profile.biography

        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={"headline": "Updated headline"},
            partial=True,
        )

        assert serializer.is_valid() is True

        serializer.save()
        student_profile.refresh_from_db()

        assert student_profile.headline == "Updated headline"
        assert student_profile.biography == original_biography

    def test_partial_update_preserves_cover_when_omitted(
        self,
        student_profile,
        valid_cover_image,
    ):
        student_profile.cover = valid_cover_image
        student_profile.save(update_fields=["cover"])

        original_cover_name = student_profile.cover.name

        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={"headline": "Updated headline"},
            partial=True,
        )

        assert serializer.is_valid() is True

        serializer.save()
        student_profile.refresh_from_db()

        assert student_profile.cover.name == original_cover_name

    def test_empty_partial_update_is_valid(self, student_profile):
        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data == {}

        instance = serializer.save()

        assert instance.pk == student_profile.pk


class TestStudentProfileUpdateSerializerFullUpdates:
    def test_full_update_does_not_require_headline(
        self,
        student_profile,
    ):
        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={"biography": "Updated biography"},
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data == {
            "biography": "Updated biography",
        }

    def test_full_update_does_not_require_biography(
        self,
        student_profile,
    ):
        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={"headline": "Updated headline"},
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data == {
            "headline": "Updated headline",
        }

    def test_full_update_with_empty_data_is_valid(
        self,
        student_profile,
    ):
        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={},
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data == {}

    def test_full_update_accepts_all_fields(
        self,
        student_profile,
        valid_cover_image,
    ):
        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={
                "cover": valid_cover_image,
                "headline": "Updated headline",
                "biography": "Updated biography",
            },
        )

        assert serializer.is_valid() is True

        assert serializer.validated_data["headline"] == ("Updated headline")
        assert serializer.validated_data["biography"] == ("Updated biography")
        assert serializer.validated_data["cover"] is not None

    def test_full_update_can_clear_text_fields(
        self,
        student_profile,
    ):
        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={
                "headline": "",
                "biography": "",
            },
        )

        assert serializer.is_valid() is True

        serializer.save()
        student_profile.refresh_from_db()

        assert student_profile.headline == ""
        assert student_profile.biography == ""


class TestStudentProfileUpdateSerializerIgnoredFields:
    def test_profile_input_is_ignored(
        self,
        student_profile,
    ):
        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={
                "profile": student_profile.profile.pk,
                "headline": "Updated headline",
            },
            partial=True,
        )

        assert serializer.is_valid() is True
        assert "profile" not in serializer.validated_data

    def test_learning_goal_input_is_ignored(
        self,
        student_profile,
    ):
        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={
                "learning_goal": "Should be ignored",
                "headline": "Updated headline",
            },
            partial=True,
        )

        assert serializer.is_valid() is True
        assert "learning_goal" not in serializer.validated_data

    def test_current_streak_input_is_ignored(
        self,
        student_profile,
    ):
        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={
                "current_streak": 999,
                "headline": "Updated headline",
            },
            partial=True,
        )

        assert serializer.is_valid() is True
        assert "current_streak" not in serializer.validated_data

    def test_longest_streak_input_is_ignored(
        self,
        student_profile,
    ):
        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={
                "longest_streak": 999,
                "headline": "Updated headline",
            },
            partial=True,
        )

        assert serializer.is_valid() is True
        assert "longest_streak" not in serializer.validated_data

    def test_profile_model_fields_are_ignored(
        self,
        student_profile,
    ):
        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={
                "website": "https://example.com",
                "country": "Azerbaijan",
                "timezone": "Asia/Baku",
                "company": "Should be ignored",
                "job_title": "Should be ignored",
                "headline": "Updated headline",
            },
            partial=True,
        )

        assert serializer.is_valid() is True

        assert "website" not in serializer.validated_data
        assert "country" not in serializer.validated_data
        assert "timezone" not in serializer.validated_data
        assert "company" not in serializer.validated_data
        assert "job_title" not in serializer.validated_data

    def test_unknown_field_is_ignored(
        self,
        student_profile,
    ):
        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={
                "unknown_field": "ignored",
                "headline": "Updated headline",
            },
            partial=True,
        )

        assert serializer.is_valid() is True
        assert "unknown_field" not in serializer.validated_data


class TestStudentProfileUpdateSerializerPersistence:
    def test_headline_is_persisted(
        self,
        student_profile,
    ):
        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={"headline": "New headline"},
            partial=True,
        )

        assert serializer.is_valid() is True

        serializer.save()
        student_profile.refresh_from_db()

        assert student_profile.headline == "New headline"

    def test_biography_is_persisted(
        self,
        student_profile,
    ):
        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={"biography": "New biography"},
            partial=True,
        )

        assert serializer.is_valid() is True

        serializer.save()
        student_profile.refresh_from_db()

        assert student_profile.biography == "New biography"

    def test_cover_is_persisted(
        self,
        student_profile,
        valid_cover_image,
    ):
        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={"cover": valid_cover_image},
            partial=True,
        )

        assert serializer.is_valid() is True

        serializer.save()
        student_profile.refresh_from_db()

        assert student_profile.cover
        assert student_profile.cover.name.startswith("profiles/students/cover/")

    def test_multiple_fields_are_persisted(
        self,
        student_profile,
        valid_cover_image,
    ):
        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={
                "cover": valid_cover_image,
                "headline": "New headline",
                "biography": "New biography",
            },
            partial=True,
        )

        assert serializer.is_valid() is True

        serializer.save()
        student_profile.refresh_from_db()

        assert student_profile.headline == "New headline"
        assert student_profile.biography == "New biography"
        assert student_profile.cover

    def test_ignored_fields_are_not_persisted(
        self,
        student_profile,
    ):
        profile = student_profile.profile

        original_learning_goal = student_profile.learning_goal
        original_current_streak = student_profile.current_streak
        original_longest_streak = student_profile.longest_streak
        original_country = profile.country
        original_company = profile.company

        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={
                "learning_goal": "Should not change",
                "current_streak": 999,
                "longest_streak": 999,
                "country": "Should not change",
                "company": "Should not change",
                "headline": "Updated headline",
            },
            partial=True,
        )

        assert serializer.is_valid() is True

        serializer.save()

        student_profile.refresh_from_db()
        profile.refresh_from_db()

        assert student_profile.learning_goal == original_learning_goal
        assert student_profile.current_streak == original_current_streak
        assert student_profile.longest_streak == original_longest_streak
        assert profile.country == original_country
        assert profile.company == original_company
        assert student_profile.headline == "Updated headline"


class TestStudentProfileUpdateSerializerNonMutation:
    def test_validation_does_not_modify_instance(
        self,
        student_profile,
    ):
        original_headline = student_profile.headline
        original_biography = student_profile.biography

        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={
                "headline": "Temporary headline",
                "biography": "Temporary biography",
            },
            partial=True,
        )

        assert serializer.is_valid() is True

        student_profile.refresh_from_db()

        assert student_profile.headline == original_headline
        assert student_profile.biography == original_biography

    def test_invalid_validation_does_not_modify_instance(
        self,
        student_profile,
    ):
        original_headline = student_profile.headline
        original_biography = student_profile.biography

        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={
                "headline": "a" * 256,
                "biography": "Temporary biography",
            },
            partial=True,
        )

        assert serializer.is_valid() is False

        student_profile.refresh_from_db()

        assert student_profile.headline == original_headline
        assert student_profile.biography == original_biography

    def test_serializer_save_returns_same_instance(
        self,
        student_profile,
    ):
        serializer = StudentProfileUpdateSerializer(
            student_profile,
            data={"headline": "Updated headline"},
            partial=True,
        )

        assert serializer.is_valid() is True

        result = serializer.save()

        assert result is student_profile
        assert result.pk == student_profile.pk
