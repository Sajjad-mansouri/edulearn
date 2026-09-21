from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.serializers import ModelSerializer

from profiles.api.serializers import StudentProfileSerializer
from profiles.api.serializers.profile import ProfileSerializer
from profiles.models import Profile, StudentProfile


@pytest.fixture
def profile(django_user_model):
    user = django_user_model.objects.create_user(
        username="student-user",
        email="student@example.com",
        password="strong-password",
        first_name="Student",
        last_name="User",
    )

    return Profile.objects.create(
        user=user,
        website="https://example.com",
        country="Azerbaijan",
        timezone="Asia/Baku",
        language="English",
        linkedin="https://linkedin.com/in/student",
        github="https://github.com/student",
        company="Example Company",
        job_title="Software Developer",
    )


@pytest.fixture
def student_profile(profile):
    return StudentProfile.objects.create(
        profile=profile,
        cover="",
        headline="Software Engineering Student",
        biography="Student biography.",
        learning_goal="Become a backend developer",
        current_streak=7,
        longest_streak=30,
    )


@pytest.fixture
def serializer():
    return StudentProfileSerializer()


class TestStudentProfileSerializerConfiguration:
    def test_serializer_is_model_serializer(self):
        assert issubclass(StudentProfileSerializer, ModelSerializer)

    def test_model_is_student_profile(self):
        assert StudentProfileSerializer.Meta.model is StudentProfile

    def test_serializer_inherits_from_profile_serializer(self):
        assert issubclass(StudentProfileSerializer, ProfileSerializer)

    def test_expected_fields_are_exposed(self):
        serializer = StudentProfileSerializer()

        expected_fields = {
            "profile",
            "cover",
            "biography",
            "headline",
        }

        assert set(serializer.fields) == expected_fields

    def test_profile_field_uses_profile_serializer(self):
        serializer = StudentProfileSerializer()

        profile_field = serializer.fields["profile"]

        assert isinstance(profile_field, ProfileSerializer)
        assert profile_field.read_only is True

    def test_profile_field_is_not_many(self):
        serializer = StudentProfileSerializer()

        assert isinstance(serializer.fields["profile"], ProfileSerializer)

    def test_cover_is_writable(self):
        serializer = StudentProfileSerializer()

        assert serializer.fields["cover"].read_only is False

    def test_biography_is_writable(self):
        serializer = StudentProfileSerializer()

        assert serializer.fields["biography"].read_only is False

    def test_headline_is_writable(self):
        serializer = StudentProfileSerializer()

        assert serializer.fields["headline"].read_only is False

    def test_profile_is_read_only(self):
        serializer = StudentProfileSerializer()

        assert serializer.fields["profile"].read_only is True

    def test_student_specific_fields_are_not_exposed(self):
        serializer = StudentProfileSerializer()

        assert "learning_goal" not in serializer.fields
        assert "current_streak" not in serializer.fields
        assert "longest_streak" not in serializer.fields

    def test_profile_model_fields_are_not_directly_exposed(self):
        serializer = StudentProfileSerializer()

        assert "website" not in serializer.fields
        assert "country" not in serializer.fields
        assert "timezone" not in serializer.fields
        assert "language" not in serializer.fields
        assert "linkedin" not in serializer.fields
        assert "github" not in serializer.fields
        assert "date_of_birth" not in serializer.fields
        assert "company" not in serializer.fields
        assert "job_title" not in serializer.fields
        assert "avatar" not in serializer.fields
        assert "user" not in serializer.fields


class TestStudentProfileSerializerRepresentation:
    def test_serializes_student_profile(self, student_profile):
        serializer = StudentProfileSerializer(student_profile)

        assert serializer.data["cover"] is None
        assert serializer.data["headline"] == student_profile.headline
        assert serializer.data["biography"] == student_profile.biography

    def test_serializes_nested_profile(self, student_profile):
        serializer = StudentProfileSerializer(student_profile)

        profile_data = serializer.data["profile"]

        assert profile_data["id"] == student_profile.profile.pk
        assert profile_data["first_name"] == student_profile.profile.user.first_name
        assert profile_data["last_name"] == student_profile.profile.user.last_name
        assert profile_data["email"] == student_profile.profile.user.email
        assert profile_data["website"] == student_profile.profile.website
        assert profile_data["country"] == student_profile.profile.country
        assert profile_data["timezone"] == student_profile.profile.timezone
        assert profile_data["company"] == student_profile.profile.company
        assert profile_data["job_title"] == student_profile.profile.job_title

    def test_nested_profile_uses_profile_serializer_fields(
        self,
        student_profile,
    ):
        serializer = StudentProfileSerializer(student_profile)

        profile_data = serializer.data["profile"]

        expected_profile_fields = {
            "id",
            "first_name",
            "last_name",
            "email",
            "avatar",
            "website",
            "country",
            "timezone",
            "date_of_birth",
            "company",
            "job_title",
            "skills",
            "educations",
            "experiences",
            "languages",
            "social_links",
        }

        assert set(profile_data) == expected_profile_fields

    def test_nested_profile_is_serialized_from_related_profile(
        self,
        student_profile,
    ):
        profile = student_profile.profile
        profile.website = "https://updated.example.com"
        profile.country = "Germany"
        profile.timezone = "Europe/Berlin"
        profile.save(
            update_fields=[
                "website",
                "country",
                "timezone",
            ],
        )

        serializer = StudentProfileSerializer(student_profile)

        assert serializer.data["profile"]["website"] == ("https://updated.example.com")
        assert serializer.data["profile"]["country"] == "Germany"
        assert serializer.data["profile"]["timezone"] == "Europe/Berlin"

    def test_student_profile_fields_are_not_nested_inside_profile(
        self,
        student_profile,
    ):
        serializer = StudentProfileSerializer(student_profile)

        profile_data = serializer.data["profile"]

        assert "headline" not in profile_data
        assert "biography" not in profile_data
        assert "learning_goal" not in profile_data
        assert "current_streak" not in profile_data
        assert "longest_streak" not in profile_data
        assert "cover" not in profile_data

    def test_learning_goal_is_not_serialized(self, student_profile):
        serializer = StudentProfileSerializer(student_profile)

        assert "learning_goal" not in serializer.data

    def test_current_streak_is_not_serialized(self, student_profile):
        serializer = StudentProfileSerializer(student_profile)

        assert "current_streak" not in serializer.data

    def test_longest_streak_is_not_serialized(self, student_profile):
        serializer = StudentProfileSerializer(student_profile)

        assert "longest_streak" not in serializer.data

    def test_cover_without_file_is_none(self, student_profile):
        student_profile.cover = ""
        student_profile.save(update_fields=["cover"])

        serializer = StudentProfileSerializer(student_profile)

        assert serializer.data["cover"] is None

    @staticmethod
    def create_valid_image(
        filename="student-cover.jpg",
        image_format="JPEG",
    ):
        image = Image.new("RGB", (100, 100), "white")
        image_file = BytesIO()
        image.save(image_file, format=image_format)
        image_file.seek(0)

        return SimpleUploadedFile(
            filename,
            image_file.read(),
            content_type="image/jpeg",
        )

    def test_cover_url_is_serialized_when_cover_exists(
        self,
        student_profile,
    ):
        image = self.create_valid_image()

        student_profile.cover = image
        student_profile.save()

        serializer = StudentProfileSerializer(student_profile)

        assert serializer.data["cover"]
        assert serializer.data["cover"].endswith(".jpg")


class TestStudentProfileSerializerValidation:
    def test_valid_student_profile_data_is_accepted(
        self,
        student_profile,
    ):
        data = {
            "headline": "Backend Development Student",
            "biography": "Learning Django and backend development.",
        }

        serializer = StudentProfileSerializer(
            student_profile,
            data=data,
            partial=True,
        )

        assert serializer.is_valid() is True

        assert serializer.validated_data["headline"] == ("Backend Development Student")
        assert serializer.validated_data["biography"] == (
            "Learning Django and backend development."
        )

    def test_headline_can_be_updated(self, student_profile):
        serializer = StudentProfileSerializer(
            student_profile,
            data={
                "headline": "Advanced Backend Developer",
            },
            partial=True,
        )

        assert serializer.is_valid() is True

        updated_profile = serializer.save()

        assert updated_profile.headline == "Advanced Backend Developer"

    def test_biography_can_be_updated(self, student_profile):
        serializer = StudentProfileSerializer(
            student_profile,
            data={
                "biography": "Updated student biography.",
            },
            partial=True,
        )

        assert serializer.is_valid() is True

        updated_profile = serializer.save()

        assert updated_profile.biography == "Updated student biography."

    def test_headline_and_biography_can_be_updated_together(
        self,
        student_profile,
    ):
        serializer = StudentProfileSerializer(
            student_profile,
            data={
                "headline": "Backend Developer",
                "biography": "Updated biography.",
            },
            partial=True,
        )

        assert serializer.is_valid() is True

        updated_profile = serializer.save()

        assert updated_profile.headline == "Backend Developer"
        assert updated_profile.biography == "Updated biography."

    def test_blank_headline_is_allowed(self, student_profile):
        serializer = StudentProfileSerializer(
            student_profile,
            data={"headline": ""},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["headline"] == ""

    def test_blank_biography_is_allowed(self, student_profile):
        serializer = StudentProfileSerializer(
            student_profile,
            data={"biography": ""},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["biography"] == ""

    def test_headline_is_trimmed(self, student_profile):
        serializer = StudentProfileSerializer(
            student_profile,
            data={
                "headline": "  Backend Developer  ",
            },
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["headline"] == "Backend Developer"

    def test_biography_is_trimmed(self, student_profile):
        serializer = StudentProfileSerializer(
            student_profile,
            data={
                "biography": "  Backend developer biography  ",
            },
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["biography"] == "Backend developer biography"

    def test_headline_longer_than_maximum_length_is_rejected(
        self,
        student_profile,
    ):
        serializer = StudentProfileSerializer(
            student_profile,
            data={
                "headline": "x" * 256,
            },
            partial=True,
        )

        assert serializer.is_valid() is False
        assert "headline" in serializer.errors

    def test_profile_input_is_ignored(self, student_profile):
        serializer = StudentProfileSerializer(
            student_profile,
            data={
                "profile": {
                    "website": "https://changed.example.com",
                    "country": "Germany",
                },
            },
            partial=True,
        )

        assert serializer.is_valid() is True
        assert "profile" not in serializer.validated_data

    def test_learning_goal_input_is_ignored(self, student_profile):
        serializer = StudentProfileSerializer(
            student_profile,
            data={
                "learning_goal": "Changed learning goal",
            },
            partial=True,
        )

        assert serializer.is_valid() is True
        assert "learning_goal" not in serializer.validated_data

    def test_current_streak_input_is_ignored(self, student_profile):
        serializer = StudentProfileSerializer(
            student_profile,
            data={
                "current_streak": 100,
            },
            partial=True,
        )

        assert serializer.is_valid() is True
        assert "current_streak" not in serializer.validated_data

    def test_longest_streak_input_is_ignored(self, student_profile):
        serializer = StudentProfileSerializer(
            student_profile,
            data={
                "longest_streak": 100,
            },
            partial=True,
        )

        assert serializer.is_valid() is True
        assert "longest_streak" not in serializer.validated_data


class TestStudentProfileSerializerReadOnlyProfile:
    def test_profile_cannot_be_replaced(self, student_profile, django_user_model):
        original_profile = student_profile.profile

        another_user = django_user_model.objects.create_user(
            username="another-student",
            email="another@example.com",
            password="strong-password",
        )
        another_profile = Profile.objects.create(
            user=another_user,
        )

        serializer = StudentProfileSerializer(
            student_profile,
            data={
                "profile": another_profile.pk,
            },
            partial=True,
        )

        assert serializer.is_valid() is True
        assert "profile" not in serializer.validated_data

        serializer.save()

        student_profile.refresh_from_db()

        assert student_profile.profile_id == original_profile.pk

    def test_profile_nested_data_cannot_update_profile(
        self,
        student_profile,
    ):
        original_website = student_profile.profile.website
        original_country = student_profile.profile.country

        serializer = StudentProfileSerializer(
            student_profile,
            data={
                "profile": {
                    "website": "https://changed.example.com",
                    "country": "Germany",
                },
            },
            partial=True,
        )

        assert serializer.is_valid() is True
        assert "profile" not in serializer.validated_data

        serializer.save()

        student_profile.profile.refresh_from_db()

        assert student_profile.profile.website == original_website
        assert student_profile.profile.country == original_country

    def test_profile_is_not_created_or_modified_by_save(
        self,
        student_profile,
    ):
        profile = student_profile.profile

        serializer = StudentProfileSerializer(
            student_profile,
            data={
                "headline": "Updated headline",
            },
            partial=True,
        )

        assert serializer.is_valid() is True
        serializer.save()

        profile.refresh_from_db()

        assert profile.pk == student_profile.profile_id
        assert profile.website == "https://example.com"
        assert profile.country == "Azerbaijan"


class TestStudentProfileSerializerIgnoredFields:
    def test_ignored_student_fields_do_not_modify_instance(
        self,
        student_profile,
    ):
        original_goal = student_profile.learning_goal
        original_current_streak = student_profile.current_streak
        original_longest_streak = student_profile.longest_streak

        serializer = StudentProfileSerializer(
            student_profile,
            data={
                "learning_goal": "New goal",
                "current_streak": 999,
                "longest_streak": 999,
            },
            partial=True,
        )

        assert serializer.is_valid() is True
        serializer.save()

        student_profile.refresh_from_db()

        assert student_profile.learning_goal == original_goal
        assert student_profile.current_streak == original_current_streak
        assert student_profile.longest_streak == original_longest_streak

    def test_profile_model_fields_are_not_accepted_directly(
        self,
        student_profile,
    ):
        serializer = StudentProfileSerializer(
            student_profile,
            data={
                "website": "https://changed.example.com",
                "country": "Germany",
                "timezone": "Europe/Berlin",
                "language": "German",
                "linkedin": "https://linkedin.com/in/changed",
                "github": "https://github.com/changed",
                "company": "Changed Company",
                "job_title": "Changed Job",
                "date_of_birth": "1990-01-01",
            },
            partial=True,
        )

        assert serializer.is_valid() is True

        for field_name in (
            "website",
            "country",
            "timezone",
            "language",
            "linkedin",
            "github",
            "company",
            "job_title",
            "date_of_birth",
        ):
            assert field_name not in serializer.validated_data

        serializer.save()

        student_profile.profile.refresh_from_db()

        assert student_profile.profile.website == "https://example.com"
        assert student_profile.profile.country == "Azerbaijan"
        assert student_profile.profile.timezone == "Asia/Baku"
        assert student_profile.profile.language == "English"
        assert student_profile.profile.linkedin == "https://linkedin.com/in/student"
        assert student_profile.profile.github == "https://github.com/student"
        assert student_profile.profile.company == "Example Company"
        assert student_profile.profile.job_title == "Software Developer"


class TestStudentProfileSerializerCover:
    @staticmethod
    def create_valid_image(
        filename="student-cover.jpg",
        image_format="JPEG",
    ):
        image = Image.new("RGB", (100, 100), "white")
        image_file = BytesIO()
        image.save(image_file, format=image_format)
        image_file.seek(0)

        return SimpleUploadedFile(
            filename,
            image_file.read(),
            content_type="image/jpeg",
        )

    def test_valid_cover_image_is_accepted(self, student_profile):
        image = self.create_valid_image()

        serializer = StudentProfileSerializer(
            student_profile,
            data={"cover": image},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["cover"] is image

    def test_cover_can_be_saved(self, student_profile):
        image = self.create_valid_image()

        serializer = StudentProfileSerializer(
            student_profile,
            data={"cover": image},
            partial=True,
        )

        assert serializer.is_valid() is True

        updated_profile = serializer.save()

        assert updated_profile.cover
        assert updated_profile.cover.name.endswith(".jpg")

    def test_cover_is_stored_under_student_cover_directory(
        self,
        student_profile,
    ):
        image = self.create_valid_image()

        serializer = StudentProfileSerializer(
            student_profile,
            data={"cover": image},
            partial=True,
        )

        assert serializer.is_valid() is True

        updated_profile = serializer.save()

        assert updated_profile.cover.name.startswith("profiles/students/cover/")

    def test_null_cover_is_rejected(self, student_profile):
        serializer = StudentProfileSerializer(
            student_profile,
            data={"cover": None},
            partial=True,
        )

        assert serializer.is_valid() is False
        assert "cover" in serializer.errors

    def test_invalid_image_content_is_rejected(self, student_profile):
        invalid_image = SimpleUploadedFile(
            "not-an-image.jpg",
            b"not-an-image",
            content_type="image/jpeg",
        )

        serializer = StudentProfileSerializer(
            student_profile,
            data={"cover": invalid_image},
            partial=True,
        )

        assert serializer.is_valid() is False
        assert "cover" in serializer.errors


class TestStudentProfileSerializerPartialUpdates:
    def test_partial_update_with_headline_preserves_other_fields(
        self,
        student_profile,
    ):
        original_biography = student_profile.biography
        original_goal = student_profile.learning_goal
        original_current_streak = student_profile.current_streak
        original_longest_streak = student_profile.longest_streak

        serializer = StudentProfileSerializer(
            student_profile,
            data={
                "headline": "New headline",
            },
            partial=True,
        )

        assert serializer.is_valid() is True
        serializer.save()

        student_profile.refresh_from_db()

        assert student_profile.headline == "New headline"
        assert student_profile.biography == original_biography
        assert student_profile.learning_goal == original_goal
        assert student_profile.current_streak == original_current_streak
        assert student_profile.longest_streak == original_longest_streak

    def test_partial_update_with_biography_preserves_other_fields(
        self,
        student_profile,
    ):
        original_headline = student_profile.headline
        original_goal = student_profile.learning_goal
        original_current_streak = student_profile.current_streak
        original_longest_streak = student_profile.longest_streak

        serializer = StudentProfileSerializer(
            student_profile,
            data={
                "biography": "New biography.",
            },
            partial=True,
        )

        assert serializer.is_valid() is True
        serializer.save()

        student_profile.refresh_from_db()

        assert student_profile.biography == "New biography."
        assert student_profile.headline == original_headline
        assert student_profile.learning_goal == original_goal
        assert student_profile.current_streak == original_current_streak
        assert student_profile.longest_streak == original_longest_streak

    def test_partial_update_with_no_data_is_valid(
        self,
        student_profile,
    ):
        serializer = StudentProfileSerializer(
            student_profile,
            data={},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data == {}

        updated_profile = serializer.save()

        assert updated_profile.pk == student_profile.pk


class TestStudentProfileSerializerNestedProfile:
    def test_nested_profile_contains_profile_collections(
        self,
        student_profile,
    ):
        serializer = StudentProfileSerializer(student_profile)

        profile_data = serializer.data["profile"]

        assert "skills" in profile_data
        assert "educations" in profile_data
        assert "experiences" in profile_data
        assert "languages" in profile_data
        assert "social_links" in profile_data

    def test_nested_profile_contains_empty_collections_when_none_exist(
        self,
        student_profile,
    ):
        serializer = StudentProfileSerializer(student_profile)

        profile_data = serializer.data["profile"]

        assert profile_data["skills"] == []
        assert profile_data["educations"] == []
        assert profile_data["experiences"] == []
        assert profile_data["languages"] == []
        assert profile_data["social_links"] == []

    def test_nested_profile_serializes_existing_avatar(
        self,
        student_profile,
    ):
        image = Image.new("RGB", (100, 100), "white")
        image_file = BytesIO()
        image.save(image_file, format="JPEG")
        image_file.seek(0)

        avatar = SimpleUploadedFile(
            "avatar.jpg",
            image_file.read(),
            content_type="image/jpeg",
        )

        student_profile.profile.avatar = avatar
        student_profile.profile.save()

        serializer = StudentProfileSerializer(student_profile)

        assert serializer.data["profile"]["avatar"]
        assert serializer.data["profile"]["avatar"].endswith(".jpg")


class TestStudentProfileSerializerNonMutation:
    def test_serialization_does_not_modify_student_profile(
        self,
        student_profile,
    ):
        original_values = {
            "profile_id": student_profile.profile_id,
            "cover": student_profile.cover.name if student_profile.cover else "",
            "headline": student_profile.headline,
            "biography": student_profile.biography,
            "learning_goal": student_profile.learning_goal,
            "current_streak": student_profile.current_streak,
            "longest_streak": student_profile.longest_streak,
        }

        serializer = StudentProfileSerializer(student_profile)

        _ = serializer.data

        student_profile.refresh_from_db()

        assert student_profile.profile_id == original_values["profile_id"]
        assert (
            student_profile.cover.name if student_profile.cover else ""
        ) == original_values["cover"]
        assert student_profile.headline == original_values["headline"]
        assert student_profile.biography == original_values["biography"]
        assert student_profile.learning_goal == original_values["learning_goal"]
        assert student_profile.current_streak == original_values["current_streak"]
        assert student_profile.longest_streak == original_values["longest_streak"]
