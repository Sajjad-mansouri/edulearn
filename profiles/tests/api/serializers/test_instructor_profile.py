from datetime import UTC, date, datetime
from io import BytesIO

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework import serializers

from profiles.api.serializers.profile import (
    InstructorProfileSerializer,
    ProfileSerializer,
)
from profiles.models import InstructorProfile, Profile

User = get_user_model()


@pytest.fixture
def instructor_user(db):
    return User.objects.create_user(
        username="instructor_profile_serializer_user",
        email="instructor-profile-serializer@example.com",
        password="test-password",
        first_name="Instructor",
        last_name="User",
    )


@pytest.fixture
def profile(db, instructor_user):
    return Profile.objects.create(
        user=instructor_user,
        website="https://example.com",
        country="Azerbaijan",
        timezone="Asia/Baku",
        language="en",
        linkedin="https://www.linkedin.com/in/instructor",
        github="https://github.com/instructor",
        date_of_birth=date(1990, 5, 15),
        company="Example Company",
        job_title="Senior Developer",
    )


@pytest.fixture
def instructor_profile(db, profile):
    return InstructorProfile.objects.create(
        profile=profile,
        cover="instructors/cover/existing-cover.jpg",
        biography="Experienced software developer and instructor.",
        headline="Senior Python Instructor",
        professional_title="Senior Software Engineer",
        organization="Example Organization",
        application_status="approved",
        is_verified=True,
        verification_date=datetime(
            2026,
            1,
            15,
            10,
            30,
            tzinfo=UTC,
        ),
        introduction_video="https://example.com/introduction",
        resume="instructors/resumes/existing-resume.pdf",
        years_of_experience=8,
    )


@pytest.fixture
def valid_cover_image():
    image = Image.new("RGB", (100, 100), "white")
    image_file = BytesIO()
    image.save(image_file, format="JPEG")
    image_file.seek(0)

    return SimpleUploadedFile(
        "instructor-cover.jpg",
        image_file.read(),
        content_type="image/jpeg",
    )


@pytest.fixture
def valid_resume():
    return SimpleUploadedFile(
        "instructor-resume.pdf",
        b"%PDF-1.4\ninstructor resume content",
        content_type="application/pdf",
    )


class TestInstructorProfileSerializerConfiguration:
    def test_serializer_uses_instructor_profile_model(self):
        serializer = InstructorProfileSerializer()

        assert serializer.Meta.model is InstructorProfile

    def test_exposes_exact_expected_fields(self):
        serializer = InstructorProfileSerializer()

        assert set(serializer.fields) == {
            "profile",
            "cover",
            "biography",
            "headline",
            "professional_title",
            "organization",
            "is_verified",
            "verification_date",
            "introduction_video",
            "resume",
            "years_of_experience",
        }

    def test_profile_is_nested_profile_serializer(self):
        serializer = InstructorProfileSerializer()

        profile_field = serializer.fields["profile"]

        assert isinstance(profile_field, ProfileSerializer)

    def test_profile_is_read_only(self):
        serializer = InstructorProfileSerializer()

        profile_field = serializer.fields["profile"]

        assert profile_field.read_only is True

    def test_application_status_is_not_exposed(self):
        serializer = InstructorProfileSerializer()

        assert "application_status" not in serializer.fields

    def test_rejection_reason_is_not_exposed(self):
        serializer = InstructorProfileSerializer()

        assert "rejection_reason" not in serializer.fields

    def test_model_management_fields_are_not_exposed(self):
        serializer = InstructorProfileSerializer()

        assert "id" not in serializer.fields
        assert "created_at" not in serializer.fields
        assert "updated_at" not in serializer.fields

    def test_profile_nested_serializer_uses_expected_fields(self):
        serializer = InstructorProfileSerializer()

        profile_serializer = serializer.fields["profile"]

        assert set(profile_serializer.fields) == {
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

    def test_professional_title_is_required(self):
        serializer = InstructorProfileSerializer()

        assert serializer.fields["professional_title"].required is True

    @pytest.mark.parametrize(
        "field_name",
        [
            "cover",
            "biography",
            "headline",
            "organization",
            "verification_date",
            "introduction_video",
            "resume",
        ],
    )
    def test_blank_or_optional_model_fields_are_not_required(
        self,
        field_name,
    ):
        serializer = InstructorProfileSerializer()

        assert serializer.fields[field_name].required is False

    def test_is_verified_is_not_required_because_model_has_default(self):
        serializer = InstructorProfileSerializer()

        assert serializer.fields["is_verified"].required is False

    def test_years_of_experience_is_not_required_because_model_has_default(
        self,
    ):
        serializer = InstructorProfileSerializer()

        assert serializer.fields["years_of_experience"].required is False

    def test_verification_date_allows_null(self):
        serializer = InstructorProfileSerializer()

        field = serializer.fields["verification_date"]

        assert field.allow_null is True

    def test_introduction_video_allows_blank(self):
        serializer = InstructorProfileSerializer()

        field = serializer.fields["introduction_video"]

        assert field.allow_blank is True

    def test_organization_allows_blank(self):
        serializer = InstructorProfileSerializer()

        field = serializer.fields["organization"]

        assert field.allow_blank is True

    def test_biography_allows_blank(self):
        serializer = InstructorProfileSerializer()

        field = serializer.fields["biography"]

        assert field.allow_blank is True

    def test_headline_allows_blank(self):
        serializer = InstructorProfileSerializer()

        field = serializer.fields["headline"]

        assert field.allow_blank is True


class TestInstructorProfileSerializerRepresentation:
    def test_serializes_instructor_profile(self, instructor_profile):
        serializer = InstructorProfileSerializer(instance=instructor_profile)

        data = serializer.data

        assert data["cover"] == instructor_profile.cover.url
        assert data["biography"] == instructor_profile.biography
        assert data["headline"] == instructor_profile.headline
        assert data["professional_title"] == (instructor_profile.professional_title)
        assert data["organization"] == instructor_profile.organization
        assert data["is_verified"] is True
        assert data["verification_date"] is not None
        assert data["introduction_video"] == (instructor_profile.introduction_video)
        assert data["resume"] == instructor_profile.resume.url
        assert data["years_of_experience"] == 8

    def test_serializes_nested_profile(self, instructor_profile):
        serializer = InstructorProfileSerializer(instance=instructor_profile)

        profile_data = serializer.data["profile"]

        assert profile_data["id"] == instructor_profile.profile.id
        assert profile_data["first_name"] == "Instructor"
        assert profile_data["last_name"] == "User"
        assert profile_data["email"] == "instructor-profile-serializer@example.com"
        assert profile_data["website"] == "https://example.com"
        assert profile_data["country"] == "Azerbaijan"
        assert profile_data["timezone"] == "Asia/Baku"

    def test_nested_profile_contains_profile_user_information(
        self,
        instructor_profile,
    ):
        serializer = InstructorProfileSerializer(instance=instructor_profile)

        profile_data = serializer.data["profile"]

        assert profile_data["first_name"] == (
            instructor_profile.profile.user.first_name
        )
        assert profile_data["last_name"] == (instructor_profile.profile.user.last_name)
        assert profile_data["email"] == instructor_profile.profile.user.email

    def test_read_only_profile_is_present_in_representation(
        self,
        instructor_profile,
    ):
        serializer = InstructorProfileSerializer(instance=instructor_profile)

        assert "profile" in serializer.data
        assert serializer.data["profile"]["id"] == instructor_profile.profile_id


class TestInstructorProfileSerializerValidation:
    def test_valid_minimal_data_is_valid(self, profile):
        data = {
            "professional_title": "Python Instructor",
        }

        serializer = InstructorProfileSerializer(data=data)

        assert serializer.is_valid() is True
        assert serializer.validated_data == {
            "professional_title": "Python Instructor",
        }

    def test_professional_title_is_required(self):
        serializer = InstructorProfileSerializer(data={})

        assert serializer.is_valid() is False
        assert "professional_title" in serializer.errors
        assert serializer.errors["professional_title"][0].code == "required"

    def test_empty_professional_title_is_rejected(self):
        serializer = InstructorProfileSerializer(
            data={
                "professional_title": "",
            }
        )

        assert serializer.is_valid() is False
        assert "professional_title" in serializer.errors

    def test_professional_title_accepts_maximum_length(self):
        professional_title = "A" * 255

        serializer = InstructorProfileSerializer(
            data={
                "professional_title": professional_title,
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["professional_title"] == (professional_title)

    def test_professional_title_rejects_more_than_maximum_length(self):
        serializer = InstructorProfileSerializer(
            data={
                "professional_title": "A" * 256,
            }
        )

        assert serializer.is_valid() is False
        assert "professional_title" in serializer.errors
        assert serializer.errors["professional_title"][0].code == "max_length"

    def test_blank_optional_fields_are_accepted(self):
        data = {
            "professional_title": "Python Instructor",
            "biography": "",
            "headline": "",
            "organization": "",
            "introduction_video": "",
        }

        serializer = InstructorProfileSerializer(data=data)

        assert serializer.is_valid() is True

        assert serializer.validated_data["biography"] == ""
        assert serializer.validated_data["headline"] == ""
        assert serializer.validated_data["organization"] == ""
        assert serializer.validated_data["introduction_video"] == ""

    def test_null_verification_date_is_accepted(self):
        serializer = InstructorProfileSerializer(
            data={
                "professional_title": "Python Instructor",
                "verification_date": None,
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["verification_date"] is None

    def test_valid_verification_date_is_accepted(self):
        verification_date = "2026-02-20T12:30:00Z"

        serializer = InstructorProfileSerializer(
            data={
                "professional_title": "Python Instructor",
                "verification_date": verification_date,
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["verification_date"] is not None

    def test_invalid_verification_date_is_rejected(self):
        serializer = InstructorProfileSerializer(
            data={
                "professional_title": "Python Instructor",
                "verification_date": "not-a-date",
            }
        )

        assert serializer.is_valid() is False
        assert "verification_date" in serializer.errors

    def test_valid_introduction_video_url_is_accepted(self):
        url = "https://example.com/instructor-introduction"

        serializer = InstructorProfileSerializer(
            data={
                "professional_title": "Python Instructor",
                "introduction_video": url,
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["introduction_video"] == url

    @pytest.mark.parametrize(
        "url",
        [
            "not-a-url",
            "example.com",
            "invalid",
        ],
    )
    def test_invalid_introduction_video_url_is_rejected(self, url):
        serializer = InstructorProfileSerializer(
            data={
                "professional_title": "Python Instructor",
                "introduction_video": url,
            }
        )

        assert serializer.is_valid() is False
        assert "introduction_video" in serializer.errors

    @pytest.mark.parametrize(
        "years_of_experience",
        [0, 1, 5, 20, 255],
    )
    def test_valid_years_of_experience_are_accepted(
        self,
        years_of_experience,
    ):
        serializer = InstructorProfileSerializer(
            data={
                "professional_title": "Python Instructor",
                "years_of_experience": years_of_experience,
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["years_of_experience"] == (years_of_experience)

    def test_negative_years_of_experience_is_rejected(self):
        serializer = InstructorProfileSerializer(
            data={
                "professional_title": "Python Instructor",
                "years_of_experience": -1,
            }
        )

        assert serializer.is_valid() is False
        assert "years_of_experience" in serializer.errors

    def test_boolean_is_verified_is_accepted(self):
        serializer = InstructorProfileSerializer(
            data={
                "professional_title": "Python Instructor",
                "is_verified": True,
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["is_verified"] is True

    def test_false_is_verified_is_accepted(self):
        serializer = InstructorProfileSerializer(
            data={
                "professional_title": "Python Instructor",
                "is_verified": False,
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["is_verified"] is False


class TestInstructorProfileSerializerReadOnlyFields:
    def test_profile_input_is_ignored(self, profile):
        data = {
            "profile": {
                "country": "Changed Country",
                "company": "Changed Company",
            },
            "professional_title": "Updated Instructor",
        }

        serializer = InstructorProfileSerializer(
            instance=profile.instructor_profile
            if hasattr(profile, "instructor_profile")
            else None,
            data=data,
        )

        assert serializer.is_valid() is True
        assert "profile" not in serializer.validated_data

    def test_nested_profile_fields_cannot_be_updated_through_serializer(
        self,
        instructor_profile,
    ):
        original_country = instructor_profile.profile.country
        original_company = instructor_profile.profile.company

        data = {
            "professional_title": "Updated Instructor",
            "profile": {
                "country": "Changed Country",
                "company": "Changed Company",
            },
        }

        serializer = InstructorProfileSerializer(
            instance=instructor_profile,
            data=data,
        )

        assert serializer.is_valid() is True

        serializer.save()

        instructor_profile.profile.refresh_from_db()

        assert instructor_profile.profile.country == original_country
        assert instructor_profile.profile.company == original_company

    @pytest.mark.parametrize(
        "field_name,value",
        [
            ("application_status", "rejected"),
            ("rejection_reason", "Rejected by reviewer."),
        ],
    )
    def test_excluded_instructor_fields_are_ignored(
        self,
        instructor_profile,
        field_name,
        value,
    ):
        data = {
            "professional_title": "Updated Instructor",
            field_name: value,
        }

        serializer = InstructorProfileSerializer(
            instance=instructor_profile,
            data=data,
        )

        assert serializer.is_valid() is True
        assert field_name not in serializer.validated_data

    @pytest.mark.parametrize(
        "field_name,value",
        [
            ("profile", 123),
            ("learning_goal", "Become a senior developer"),
            ("current_streak", 20),
            ("longest_streak", 50),
            ("unknown_field", "ignored"),
        ],
    )
    def test_fields_not_exposed_by_serializer_are_ignored(
        self,
        instructor_profile,
        field_name,
        value,
    ):
        data = {
            "professional_title": "Updated Instructor",
            field_name: value,
        }

        serializer = InstructorProfileSerializer(
            instance=instructor_profile,
            data=data,
        )

        assert serializer.is_valid() is True
        assert field_name not in serializer.validated_data


class TestInstructorProfileSerializerFileFields:
    def test_valid_cover_image_is_accepted(
        self,
        valid_cover_image,
    ):
        serializer = InstructorProfileSerializer(
            data={
                "professional_title": "Python Instructor",
                "cover": valid_cover_image,
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["cover"].name == ("instructor-cover.jpg")

    def test_empty_cover_value_is_rejected(self):
        serializer = InstructorProfileSerializer(
            data={
                "professional_title": "Python Instructor",
                "cover": "",
            }
        )

        assert serializer.is_valid() is False
        assert "cover" in serializer.errors

    def test_null_cover_value_is_rejected(self):
        serializer = InstructorProfileSerializer(
            data={
                "professional_title": "Python Instructor",
                "cover": None,
            }
        )

        assert serializer.is_valid() is False
        assert "cover" in serializer.errors

    def test_valid_resume_file_is_accepted(self, valid_resume):
        serializer = InstructorProfileSerializer(
            data={
                "professional_title": "Python Instructor",
                "resume": valid_resume,
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["resume"].name == ("instructor-resume.pdf")

    def test_empty_resume_value_is_rejected(self):
        serializer = InstructorProfileSerializer(
            data={
                "professional_title": "Python Instructor",
                "resume": "",
            }
        )

        assert serializer.is_valid() is False
        assert "resume" in serializer.errors

    def test_null_resume_value_is_rejected(self):
        serializer = InstructorProfileSerializer(
            data={
                "professional_title": "Python Instructor",
                "resume": None,
            }
        )

        assert serializer.is_valid() is False
        assert "resume" in serializer.errors


class TestInstructorProfileSerializerUpdates:
    def test_partial_update_accepts_only_headline(
        self,
        instructor_profile,
    ):
        serializer = InstructorProfileSerializer(
            instructor_profile,
            data={"headline": "Updated Headline"},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data == {
            "headline": "Updated Headline",
        }

    def test_partial_update_accepts_only_professional_title(
        self,
        instructor_profile,
    ):
        serializer = InstructorProfileSerializer(
            instructor_profile,
            data={"professional_title": "Lead Python Instructor"},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data == {
            "professional_title": "Lead Python Instructor",
        }

    def test_partial_update_can_clear_optional_text_fields(
        self,
        instructor_profile,
    ):
        serializer = InstructorProfileSerializer(
            instructor_profile,
            data={
                "biography": "",
                "headline": "",
                "organization": "",
                "introduction_video": "",
            },
            partial=True,
        )

        assert serializer.is_valid() is True

        serializer.save()

        instructor_profile.refresh_from_db()

        assert instructor_profile.biography == ""
        assert instructor_profile.headline == ""
        assert instructor_profile.organization == ""
        assert instructor_profile.introduction_video == ""

    def test_partial_update_can_set_verification_date_to_null(
        self,
        instructor_profile,
    ):
        serializer = InstructorProfileSerializer(
            instructor_profile,
            data={"verification_date": None},
            partial=True,
        )

        assert serializer.is_valid() is True

        serializer.save()

        instructor_profile.refresh_from_db()

        assert instructor_profile.verification_date is None

    def test_partial_update_can_change_verification_status(
        self,
        instructor_profile,
    ):
        serializer = InstructorProfileSerializer(
            instructor_profile,
            data={"is_verified": False},
            partial=True,
        )

        assert serializer.is_valid() is True

        serializer.save()

        instructor_profile.refresh_from_db()

        assert instructor_profile.is_verified is False

    def test_partial_update_can_change_years_of_experience(
        self,
        instructor_profile,
    ):
        serializer = InstructorProfileSerializer(
            instructor_profile,
            data={"years_of_experience": 12},
            partial=True,
        )

        assert serializer.is_valid() is True

        serializer.save()

        instructor_profile.refresh_from_db()

        assert instructor_profile.years_of_experience == 12

    def test_full_update_requires_only_required_fields(
        self,
        instructor_profile,
    ):
        serializer = InstructorProfileSerializer(
            instructor_profile,
            data={
                "professional_title": "Updated Professional Title",
            },
        )

        assert serializer.is_valid() is True

        serializer.save()

        instructor_profile.refresh_from_db()

        assert instructor_profile.professional_title == ("Updated Professional Title")


class TestInstructorProfileSerializerPersistence:
    def test_save_persists_writable_fields(
        self,
        instructor_profile,
    ):
        data = {
            "biography": "Updated biography.",
            "headline": "Updated headline",
            "professional_title": "Principal Python Engineer",
            "organization": "Updated Organization",
            "is_verified": False,
            "verification_date": None,
            "introduction_video": "https://example.com/new-introduction",
            "years_of_experience": 12,
        }

        serializer = InstructorProfileSerializer(
            instructor_profile,
            data=data,
            partial=True,
        )

        assert serializer.is_valid() is True

        serializer.save()

        instructor_profile.refresh_from_db()

        assert instructor_profile.biography == "Updated biography."
        assert instructor_profile.headline == "Updated headline"
        assert instructor_profile.professional_title == ("Principal Python Engineer")
        assert instructor_profile.organization == "Updated Organization"
        assert instructor_profile.is_verified is False
        assert instructor_profile.verification_date is None
        assert instructor_profile.introduction_video == (
            "https://example.com/new-introduction"
        )
        assert instructor_profile.years_of_experience == 12

    def test_save_does_not_modify_profile(
        self,
        instructor_profile,
    ):
        profile = instructor_profile.profile
        original_values = {
            "website": profile.website,
            "country": profile.country,
            "timezone": profile.timezone,
            "company": profile.company,
            "job_title": profile.job_title,
        }

        serializer = InstructorProfileSerializer(
            instructor_profile,
            data={
                "professional_title": "Updated Professional Title",
                "profile": {
                    "country": "Changed Country",
                    "company": "Changed Company",
                },
            },
            partial=True,
        )

        assert serializer.is_valid() is True

        serializer.save()

        profile.refresh_from_db()

        assert profile.website == original_values["website"]
        assert profile.country == original_values["country"]
        assert profile.timezone == original_values["timezone"]
        assert profile.company == original_values["company"]
        assert profile.job_title == original_values["job_title"]

    def test_save_does_not_modify_excluded_application_status(
        self,
        instructor_profile,
    ):
        original_status = instructor_profile.application_status

        serializer = InstructorProfileSerializer(
            instructor_profile,
            data={
                "professional_title": "Updated Professional Title",
                "application_status": "rejected",
            },
            partial=True,
        )

        assert serializer.is_valid() is True

        serializer.save()

        instructor_profile.refresh_from_db()

        assert instructor_profile.application_status == original_status

    def test_save_does_not_modify_excluded_rejection_reason(
        self,
        instructor_profile,
    ):
        original_reason = instructor_profile.rejection_reason

        serializer = InstructorProfileSerializer(
            instructor_profile,
            data={
                "professional_title": "Updated Professional Title",
                "rejection_reason": "Changed reason",
            },
            partial=True,
        )

        assert serializer.is_valid() is True

        serializer.save()

        instructor_profile.refresh_from_db()

        assert instructor_profile.rejection_reason == original_reason

    def test_cover_file_is_persisted(
        self,
        instructor_profile,
        valid_cover_image,
    ):
        serializer = InstructorProfileSerializer(
            instructor_profile,
            data={"cover": valid_cover_image},
            partial=True,
        )

        assert serializer.is_valid() is True

        serializer.save()

        instructor_profile.refresh_from_db()

        assert instructor_profile.cover
        assert instructor_profile.cover.name
        assert instructor_profile.cover.name != ("instructors/cover/existing-cover.jpg")

    def test_resume_file_is_persisted(
        self,
        instructor_profile,
        valid_resume,
    ):
        serializer = InstructorProfileSerializer(
            instructor_profile,
            data={"resume": valid_resume},
            partial=True,
        )

        assert serializer.is_valid() is True

        serializer.save()

        instructor_profile.refresh_from_db()

        assert instructor_profile.resume
        assert instructor_profile.resume.name
        assert instructor_profile.resume.name != (
            "instructors/resumes/existing-resume.pdf"
        )


class TestInstructorProfileSerializerEdgeCases:
    def test_zero_years_of_experience_is_valid(
        self,
    ):
        serializer = InstructorProfileSerializer(
            data={
                "professional_title": "New Instructor",
                "years_of_experience": 0,
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["years_of_experience"] == 0

    def test_maximum_positive_small_integer_value_is_valid(
        self,
    ):
        serializer = InstructorProfileSerializer(
            data={
                "professional_title": "Experienced Instructor",
                "years_of_experience": 255,
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["years_of_experience"] == 255

    def test_excluded_fields_are_not_returned_in_representation(
        self,
        instructor_profile,
    ):
        serializer = InstructorProfileSerializer(instance=instructor_profile)

        data = serializer.data

        assert "application_status" not in data
        assert "rejection_reason" not in data

    def test_serializer_does_not_mutate_instance_during_validation(
        self,
        instructor_profile,
    ):
        original_values = {
            "headline": instructor_profile.headline,
            "biography": instructor_profile.biography,
            "professional_title": instructor_profile.professional_title,
            "organization": instructor_profile.organization,
            "years_of_experience": instructor_profile.years_of_experience,
        }

        serializer = InstructorProfileSerializer(
            instructor_profile,
            data={
                "headline": "Temporary Headline",
                "biography": "Temporary Biography",
                "professional_title": "Temporary Title",
                "organization": "Temporary Organization",
                "years_of_experience": 20,
            },
            partial=True,
        )

        assert serializer.is_valid() is True

        assert instructor_profile.headline == original_values["headline"]
        assert instructor_profile.biography == original_values["biography"]
        assert (
            instructor_profile.professional_title
            == (original_values["professional_title"])
        )
        assert instructor_profile.organization == (original_values["organization"])
        assert (
            instructor_profile.years_of_experience
            == (original_values["years_of_experience"])
        )

    def test_raise_exception_validation_works_for_invalid_data(self):
        serializer = InstructorProfileSerializer(
            data={
                "professional_title": "",
            }
        )

        with pytest.raises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)
