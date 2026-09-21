from datetime import UTC, datetime
from io import BytesIO

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework import serializers

from profiles.api.serializers.profile import InstructorProfileUpdateSerializer
from profiles.models import InstructorProfile, Profile

User = get_user_model()


@pytest.fixture
def instructor_user(db):
    return User.objects.create_user(
        username="instructor_profile_update_user",
        email="instructor-profile-update@example.com",
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
        company="Example Company",
        job_title="Senior Developer",
    )


@pytest.fixture
def instructor_profile(db, profile):
    return InstructorProfile.objects.create(
        profile=profile,
        cover="instructors/cover/existing-cover.jpg",
        biography="Original instructor biography.",
        headline="Original instructor headline",
        professional_title="Senior Software Engineer",
        organization="Original Organization",
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
        introduction_video="https://example.com/original-introduction",
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


class TestInstructorProfileUpdateSerializerConfiguration:
    def test_uses_instructor_profile_model(self):
        serializer = InstructorProfileUpdateSerializer()

        assert serializer.Meta.model is InstructorProfile

    def test_exposes_exact_expected_fields(self):
        serializer = InstructorProfileUpdateSerializer()

        assert set(serializer.fields) == {
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

    def test_profile_is_not_exposed(self):
        serializer = InstructorProfileUpdateSerializer()

        assert "profile" not in serializer.fields

    def test_application_status_is_not_exposed(self):
        serializer = InstructorProfileUpdateSerializer()

        assert "application_status" not in serializer.fields

    def test_rejection_reason_is_not_exposed(self):
        serializer = InstructorProfileUpdateSerializer()

        assert "rejection_reason" not in serializer.fields

    def test_professional_title_is_required(self):
        serializer = InstructorProfileUpdateSerializer()

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
    def test_blank_or_nullable_model_fields_are_not_required(
        self,
        field_name,
    ):
        serializer = InstructorProfileUpdateSerializer()

        assert serializer.fields[field_name].required is False

    def test_is_verified_is_not_required_because_model_has_default(self):
        serializer = InstructorProfileUpdateSerializer()

        assert serializer.fields["is_verified"].required is False

    def test_years_of_experience_is_not_required_because_model_has_default(
        self,
    ):
        serializer = InstructorProfileUpdateSerializer()

        assert serializer.fields["years_of_experience"].required is False

    def test_verification_date_allows_null(self):
        serializer = InstructorProfileUpdateSerializer()

        assert serializer.fields["verification_date"].allow_null is True

    @pytest.mark.parametrize(
        "field_name",
        [
            "biography",
            "headline",
            "organization",
            "introduction_video",
        ],
    )
    def test_text_fields_allow_blank(self, field_name):
        serializer = InstructorProfileUpdateSerializer()

        assert serializer.fields[field_name].allow_blank is True


class TestInstructorProfileUpdateSerializerMinimalValidation:
    def test_empty_data_is_invalid_for_full_update(self):
        serializer = InstructorProfileUpdateSerializer(data={})

        assert serializer.is_valid() is False
        assert "professional_title" in serializer.errors
        assert serializer.errors["professional_title"][0].code == "required"

    def test_professional_title_only_is_valid(self):
        serializer = InstructorProfileUpdateSerializer(
            data={
                "professional_title": "Python Instructor",
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data == {
            "professional_title": "Python Instructor",
        }

    def test_professional_title_is_required_even_when_optional_fields_are_omitted(
        self,
    ):
        serializer = InstructorProfileUpdateSerializer(
            data={
                "biography": "Instructor biography",
                "organization": "Example Organization",
            }
        )

        assert serializer.is_valid() is False
        assert "professional_title" in serializer.errors


class TestInstructorProfileUpdateSerializerProfessionalTitle:
    def test_professional_title_accepts_normal_value(self):
        value = "Senior Python Instructor"

        serializer = InstructorProfileUpdateSerializer(
            data={
                "professional_title": value,
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["professional_title"] == value

    def test_professional_title_accepts_255_characters(self):
        value = "A" * 255

        serializer = InstructorProfileUpdateSerializer(
            data={
                "professional_title": value,
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["professional_title"] == value

    def test_professional_title_rejects_more_than_255_characters(self):
        value = "A" * 256

        serializer = InstructorProfileUpdateSerializer(
            data={
                "professional_title": value,
            }
        )

        assert serializer.is_valid() is False
        assert "professional_title" in serializer.errors
        assert serializer.errors["professional_title"][0].code == "max_length"

    def test_empty_professional_title_is_rejected(self):
        serializer = InstructorProfileUpdateSerializer(
            data={
                "professional_title": "",
            }
        )

        assert serializer.is_valid() is False
        assert "professional_title" in serializer.errors

    def test_whitespace_professional_title_is_rejected(self):
        serializer = InstructorProfileUpdateSerializer(
            data={
                "professional_title": "   ",
            }
        )

        assert serializer.is_valid() is False
        assert "professional_title" in serializer.errors
        assert serializer.errors["professional_title"][0].code == "blank"


class TestInstructorProfileUpdateSerializerOptionalTextFields:
    @pytest.mark.parametrize(
        "field_name",
        [
            "biography",
            "headline",
            "organization",
            "introduction_video",
        ],
    )
    def test_optional_text_field_accepts_empty_string(self, field_name):
        serializer = InstructorProfileUpdateSerializer(
            data={
                "professional_title": "Python Instructor",
                field_name: "",
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data[field_name] == ""

    def test_biography_accepts_normal_text(self):
        value = "Experienced Python and Django instructor."

        serializer = InstructorProfileUpdateSerializer(
            data={
                "professional_title": "Python Instructor",
                "biography": value,
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["biography"] == value

    def test_headline_accepts_normal_text(self):
        value = "Teaching Python, Django, and REST APIs"

        serializer = InstructorProfileUpdateSerializer(
            data={
                "professional_title": "Python Instructor",
                "headline": value,
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["headline"] == value

    def test_organization_accepts_maximum_length(self):
        value = "A" * 255

        serializer = InstructorProfileUpdateSerializer(
            data={
                "professional_title": "Python Instructor",
                "organization": value,
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["organization"] == value

    def test_organization_rejects_more_than_maximum_length(self):
        value = "A" * 256

        serializer = InstructorProfileUpdateSerializer(
            data={
                "professional_title": "Python Instructor",
                "organization": value,
            }
        )

        assert serializer.is_valid() is False
        assert "organization" in serializer.errors
        assert serializer.errors["organization"][0].code == "max_length"


class TestInstructorProfileUpdateSerializerVerificationDate:
    def test_verification_date_accepts_valid_datetime(self):
        value = "2026-02-20T12:30:00Z"

        serializer = InstructorProfileUpdateSerializer(
            data={
                "professional_title": "Python Instructor",
                "verification_date": value,
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["verification_date"] is not None

    def test_verification_date_accepts_null(self):
        serializer = InstructorProfileUpdateSerializer(
            data={
                "professional_title": "Python Instructor",
                "verification_date": None,
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["verification_date"] is None

    def test_verification_date_rejects_invalid_value(self):
        serializer = InstructorProfileUpdateSerializer(
            data={
                "professional_title": "Python Instructor",
                "verification_date": "not-a-date",
            }
        )

        assert serializer.is_valid() is False
        assert "verification_date" in serializer.errors

    @pytest.mark.parametrize(
        "value",
        [
            "2026-02-20",
            "2026-02-20T12:30:00",
            "2026-02-20T12:30:00Z",
        ],
    )
    def test_supported_datetime_inputs_are_accepted(self, value):
        serializer = InstructorProfileUpdateSerializer(
            data={
                "professional_title": "Python Instructor",
                "verification_date": value,
            }
        )

        assert serializer.is_valid() is True


class TestInstructorProfileUpdateSerializerIntroductionVideo:
    def test_valid_url_is_accepted(self):
        value = "https://example.com/introduction"

        serializer = InstructorProfileUpdateSerializer(
            data={
                "professional_title": "Python Instructor",
                "introduction_video": value,
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["introduction_video"] == value

    def test_empty_url_is_accepted(self):
        serializer = InstructorProfileUpdateSerializer(
            data={
                "professional_title": "Python Instructor",
                "introduction_video": "",
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["introduction_video"] == ""

    @pytest.mark.parametrize(
        "value",
        [
            "not-a-url",
            "example.com",
            "invalid",
            "www.example.com/video",
        ],
    )
    def test_invalid_url_is_rejected(self, value):
        serializer = InstructorProfileUpdateSerializer(
            data={
                "professional_title": "Python Instructor",
                "introduction_video": value,
            }
        )

        assert serializer.is_valid() is False
        assert "introduction_video" in serializer.errors


class TestInstructorProfileUpdateSerializerYearsOfExperience:
    @pytest.mark.parametrize(
        "value",
        [
            0,
            1,
            5,
            20,
            100,
            255,
            256,
            1000,
        ],
    )
    def test_non_negative_years_of_experience_are_accepted(self, value):
        serializer = InstructorProfileUpdateSerializer(
            data={
                "professional_title": "Python Instructor",
                "years_of_experience": value,
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["years_of_experience"] == value

    def test_negative_years_of_experience_is_rejected(self):
        serializer = InstructorProfileUpdateSerializer(
            data={
                "professional_title": "Python Instructor",
                "years_of_experience": -1,
            }
        )

        assert serializer.is_valid() is False
        assert "years_of_experience" in serializer.errors

    @pytest.mark.parametrize(
        "value",
        [
            "5",
            "10",
            "20",
        ],
    )
    def test_integer_string_is_coerced_to_integer(self, value):
        serializer = InstructorProfileUpdateSerializer(
            data={
                "professional_title": "Python Instructor",
                "years_of_experience": value,
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["years_of_experience"] == int(value)


class TestInstructorProfileUpdateSerializerBoolean:
    @pytest.mark.parametrize(
        "value",
        [True, False],
    )
    def test_is_verified_accepts_boolean_values(self, value):
        serializer = InstructorProfileUpdateSerializer(
            data={
                "professional_title": "Python Instructor",
                "is_verified": value,
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["is_verified"] is value

    @pytest.mark.parametrize(
        "value",
        [
            "true",
            "false",
            "True",
            "False",
        ],
    )
    def test_is_verified_accepts_boolean_string_representations(
        self,
        value,
    ):
        serializer = InstructorProfileUpdateSerializer(
            data={
                "professional_title": "Python Instructor",
                "is_verified": value,
            }
        )

        assert serializer.is_valid() is True


class TestInstructorProfileUpdateSerializerCover:
    def test_valid_cover_image_is_accepted(self, valid_cover_image):
        serializer = InstructorProfileUpdateSerializer(
            data={
                "professional_title": "Python Instructor",
                "cover": valid_cover_image,
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["cover"].name == ("instructor-cover.jpg")

    def test_empty_cover_is_rejected(self):
        serializer = InstructorProfileUpdateSerializer(
            data={
                "professional_title": "Python Instructor",
                "cover": "",
            }
        )

        assert serializer.is_valid() is False
        assert "cover" in serializer.errors

    def test_null_cover_is_rejected(self):
        serializer = InstructorProfileUpdateSerializer(
            data={
                "professional_title": "Python Instructor",
                "cover": None,
            }
        )

        assert serializer.is_valid() is False
        assert "cover" in serializer.errors


class TestInstructorProfileUpdateSerializerResume:
    def test_valid_resume_is_accepted(self, valid_resume):
        serializer = InstructorProfileUpdateSerializer(
            data={
                "professional_title": "Python Instructor",
                "resume": valid_resume,
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["resume"].name == ("instructor-resume.pdf")

    def test_empty_resume_is_rejected(self):
        serializer = InstructorProfileUpdateSerializer(
            data={
                "professional_title": "Python Instructor",
                "resume": "",
            }
        )

        assert serializer.is_valid() is False
        assert "resume" in serializer.errors

    def test_null_resume_is_rejected(self):
        serializer = InstructorProfileUpdateSerializer(
            data={
                "professional_title": "Python Instructor",
                "resume": None,
            }
        )

        assert serializer.is_valid() is False
        assert "resume" in serializer.errors


class TestInstructorProfileUpdateSerializerExtraFields:
    @pytest.mark.parametrize(
        "field_name,value",
        [
            ("profile", 123),
            ("application_status", "rejected"),
            ("rejection_reason", "Rejected."),
            ("learning_goal", "Become a senior engineer"),
            ("current_streak", 10),
            ("longest_streak", 20),
            ("unknown_field", "ignored"),
        ],
    )
    def test_fields_not_declared_by_serializer_are_ignored(
        self,
        field_name,
        value,
    ):
        serializer = InstructorProfileUpdateSerializer(
            data={
                "professional_title": "Python Instructor",
                field_name: value,
            }
        )

        assert serializer.is_valid() is True
        assert field_name not in serializer.validated_data


class TestInstructorProfileUpdateSerializerPartialUpdates:
    def test_partial_update_accepts_only_headline(
        self,
        instructor_profile,
    ):
        serializer = InstructorProfileUpdateSerializer(
            instructor_profile,
            data={
                "headline": "Updated Headline",
            },
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data == {
            "headline": "Updated Headline",
        }

    def test_partial_update_accepts_only_organization(
        self,
        instructor_profile,
    ):
        serializer = InstructorProfileUpdateSerializer(
            instructor_profile,
            data={
                "organization": "Updated Organization",
            },
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data == {
            "organization": "Updated Organization",
        }

    def test_partial_update_accepts_only_is_verified(
        self,
        instructor_profile,
    ):
        serializer = InstructorProfileUpdateSerializer(
            instructor_profile,
            data={
                "is_verified": False,
            },
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data == {
            "is_verified": False,
        }

    def test_partial_update_accepts_only_years_of_experience(
        self,
        instructor_profile,
    ):
        serializer = InstructorProfileUpdateSerializer(
            instructor_profile,
            data={
                "years_of_experience": 12,
            },
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data == {
            "years_of_experience": 12,
        }

    def test_partial_update_can_clear_optional_text_fields(
        self,
        instructor_profile,
    ):
        serializer = InstructorProfileUpdateSerializer(
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

    def test_partial_update_can_clear_verification_date(
        self,
        instructor_profile,
    ):
        serializer = InstructorProfileUpdateSerializer(
            instructor_profile,
            data={
                "verification_date": None,
            },
            partial=True,
        )

        assert serializer.is_valid() is True

        serializer.save()

        instructor_profile.refresh_from_db()

        assert instructor_profile.verification_date is None

    def test_partial_update_does_not_require_professional_title(
        self,
        instructor_profile,
    ):
        original_title = instructor_profile.professional_title

        serializer = InstructorProfileUpdateSerializer(
            instructor_profile,
            data={
                "headline": "Updated Headline",
            },
            partial=True,
        )

        assert serializer.is_valid() is True

        serializer.save()

        instructor_profile.refresh_from_db()

        assert instructor_profile.professional_title == original_title
        assert instructor_profile.headline == "Updated Headline"


class TestInstructorProfileUpdateSerializerFullUpdates:
    def test_full_update_requires_professional_title(
        self,
        instructor_profile,
    ):
        serializer = InstructorProfileUpdateSerializer(
            instructor_profile,
            data={
                "headline": "Updated Headline",
            },
        )

        assert serializer.is_valid() is False
        assert "professional_title" in serializer.errors
        assert serializer.errors["professional_title"][0].code == "required"

    def test_full_update_accepts_professional_title_without_optional_fields(
        self,
        instructor_profile,
    ):
        serializer = InstructorProfileUpdateSerializer(
            instructor_profile,
            data={
                "professional_title": "Updated Professional Title",
            },
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data == {
            "professional_title": "Updated Professional Title",
        }

    def test_full_update_does_not_require_optional_fields(
        self,
        instructor_profile,
    ):
        serializer = InstructorProfileUpdateSerializer(
            instructor_profile,
            data={
                "professional_title": "Updated Professional Title",
            },
        )

        assert serializer.is_valid() is True


class TestInstructorProfileUpdateSerializerPersistence:
    def test_save_persists_all_writable_fields(
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

        serializer = InstructorProfileUpdateSerializer(
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

        serializer = InstructorProfileUpdateSerializer(
            instructor_profile,
            data={
                "professional_title": "Updated Professional Title",
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

    def test_excluded_application_status_is_not_modified(
        self,
        instructor_profile,
    ):
        original_status = instructor_profile.application_status

        serializer = InstructorProfileUpdateSerializer(
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

    def test_excluded_rejection_reason_is_not_modified(
        self,
        instructor_profile,
    ):
        original_reason = instructor_profile.rejection_reason

        serializer = InstructorProfileUpdateSerializer(
            instructor_profile,
            data={
                "professional_title": "Updated Professional Title",
                "rejection_reason": "Changed rejection reason",
            },
            partial=True,
        )

        assert serializer.is_valid() is True

        serializer.save()

        instructor_profile.refresh_from_db()

        assert instructor_profile.rejection_reason == original_reason

    def test_profile_relation_cannot_be_changed(
        self,
        instructor_profile,
        instructor_user,
    ):
        original_profile_id = instructor_profile.profile_id

        serializer = InstructorProfileUpdateSerializer(
            instructor_profile,
            data={
                "professional_title": "Updated Professional Title",
                "profile": 999999,
            },
            partial=True,
        )

        assert serializer.is_valid() is True
        assert "profile" not in serializer.validated_data

        serializer.save()

        instructor_profile.refresh_from_db()

        assert instructor_profile.profile_id == original_profile_id

    def test_cover_file_is_persisted(
        self,
        instructor_profile,
        valid_cover_image,
    ):
        original_cover_name = instructor_profile.cover.name

        serializer = InstructorProfileUpdateSerializer(
            instructor_profile,
            data={
                "cover": valid_cover_image,
            },
            partial=True,
        )

        assert serializer.is_valid() is True

        serializer.save()

        instructor_profile.refresh_from_db()

        assert instructor_profile.cover
        assert instructor_profile.cover.name != original_cover_name

    def test_resume_file_is_persisted(
        self,
        instructor_profile,
        valid_resume,
    ):
        original_resume_name = instructor_profile.resume.name

        serializer = InstructorProfileUpdateSerializer(
            instructor_profile,
            data={
                "resume": valid_resume,
            },
            partial=True,
        )

        assert serializer.is_valid() is True

        serializer.save()

        instructor_profile.refresh_from_db()

        assert instructor_profile.resume
        assert instructor_profile.resume.name != original_resume_name


class TestInstructorProfileUpdateSerializerValidationErrors:
    def test_raise_exception_for_missing_professional_title(self):
        serializer = InstructorProfileUpdateSerializer(data={})

        with pytest.raises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_raise_exception_for_invalid_introduction_video(self):
        serializer = InstructorProfileUpdateSerializer(
            data={
                "professional_title": "Python Instructor",
                "introduction_video": "not-a-url",
            }
        )

        with pytest.raises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_raise_exception_for_negative_experience(self):
        serializer = InstructorProfileUpdateSerializer(
            data={
                "professional_title": "Python Instructor",
                "years_of_experience": -1,
            }
        )

        with pytest.raises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)


class TestInstructorProfileUpdateSerializerNonMutation:
    def test_validation_does_not_mutate_instance(
        self,
        instructor_profile,
    ):
        original_values = {
            "biography": instructor_profile.biography,
            "headline": instructor_profile.headline,
            "professional_title": instructor_profile.professional_title,
            "organization": instructor_profile.organization,
            "is_verified": instructor_profile.is_verified,
            "years_of_experience": instructor_profile.years_of_experience,
        }

        serializer = InstructorProfileUpdateSerializer(
            instructor_profile,
            data={
                "biography": "Temporary biography",
                "headline": "Temporary headline",
                "professional_title": "Temporary title",
                "organization": "Temporary organization",
                "is_verified": False,
                "years_of_experience": 20,
            },
            partial=True,
        )

        assert serializer.is_valid() is True

        assert instructor_profile.biography == original_values["biography"]
        assert instructor_profile.headline == original_values["headline"]
        assert (
            instructor_profile.professional_title
            == (original_values["professional_title"])
        )
        assert instructor_profile.organization == original_values["organization"]
        assert instructor_profile.is_verified is original_values["is_verified"]
        assert (
            instructor_profile.years_of_experience
            == (original_values["years_of_experience"])
        )
