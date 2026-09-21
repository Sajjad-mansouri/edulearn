from datetime import date
from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.serializers import ModelSerializer

from profiles.api.serializers import (
    EducationSerializer,
    ExperienceSerializer,
    LanguageSerializer,
    ProfileSerializer,
    SkillSerializer,
    SocialLinkSerializer,
)
from profiles.models import (
    Education,
    Experience,
    Language,
    Profile,
    Skill,
    SocialLink,
)


@pytest.fixture
def profile(django_user_model):
    user = django_user_model.objects.create_user(
        username="profile-user",
        email="profile@example.com",
        password="strong-password",
        first_name="Profile",
        last_name="User",
    )
    return Profile.objects.create(
        user=user,
        website="https://example.com",
        country="Azerbaijan",
        timezone="Asia/Baku",
        date_of_birth=date(1995, 5, 15),
        company="Example Company",
        job_title="Software Developer",
    )


@pytest.fixture
def serializer():
    return ProfileSerializer()


class TestProfileSerializerConfiguration:
    def test_serializer_is_model_serializer(self):
        assert issubclass(ProfileSerializer, ModelSerializer)

    def test_model_is_profile(self):
        assert ProfileSerializer.Meta.model is Profile

    def test_fields_are_correct(self):
        expected_fields = {
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

        serializer = ProfileSerializer()

        assert set(serializer.fields) == expected_fields

    def test_read_only_fields_are_configured_correctly(self):
        serializer = ProfileSerializer()

        assert serializer.fields["id"].read_only is True
        assert serializer.fields["first_name"].read_only is True
        assert serializer.fields["last_name"].read_only is True
        assert serializer.fields["email"].read_only is True
        assert serializer.fields["skills"].read_only is True
        assert serializer.fields["educations"].read_only is True
        assert serializer.fields["experiences"].read_only is True
        assert serializer.fields["languages"].read_only is True
        assert serializer.fields["social_links"].read_only is True

    def test_writable_profile_fields_are_not_read_only(self):
        serializer = ProfileSerializer()

        writable_fields = (
            "avatar",
            "website",
            "country",
            "timezone",
            "date_of_birth",
            "company",
            "job_title",
        )

        for field_name in writable_fields:
            assert serializer.fields[field_name].read_only is False

    def test_nested_serializers_are_configured_as_expected(self):
        serializer = ProfileSerializer()

        skills_field = serializer.fields["skills"]
        assert skills_field.many is True
        assert skills_field.read_only is True
        assert isinstance(skills_field.child, SkillSerializer)

        educations_field = serializer.fields["educations"]
        assert educations_field.many is True
        assert educations_field.read_only is True
        assert isinstance(educations_field.child, EducationSerializer)

        experiences_field = serializer.fields["experiences"]
        assert experiences_field.many is True
        assert experiences_field.read_only is True
        assert isinstance(experiences_field.child, ExperienceSerializer)

        languages_field = serializer.fields["languages"]
        assert languages_field.many is True
        assert languages_field.read_only is True
        assert isinstance(languages_field.child, LanguageSerializer)

        social_links_field = serializer.fields["social_links"]
        assert social_links_field.many is True
        assert social_links_field.read_only is True
        assert isinstance(social_links_field.child, SocialLinkSerializer)


class TestProfileSerializerRepresentation:
    def test_serializes_profile_fields(self, profile):
        serializer = ProfileSerializer(profile)

        assert serializer.data["id"] == profile.pk
        assert serializer.data["first_name"] == profile.user.first_name
        assert serializer.data["last_name"] == profile.user.last_name
        assert serializer.data["email"] == profile.user.email
        assert serializer.data["website"] == profile.website
        assert serializer.data["country"] == profile.country
        assert serializer.data["timezone"] == profile.timezone
        assert serializer.data["date_of_birth"] == (profile.date_of_birth.isoformat())
        assert serializer.data["company"] == profile.company
        assert serializer.data["job_title"] == profile.job_title

    def test_serializes_user_information_from_related_user(self, profile):
        profile.user.first_name = "Updated"
        profile.user.last_name = "Name"
        profile.user.email = "updated@example.com"
        profile.user.save(
            update_fields=["first_name", "last_name", "email"],
        )

        serializer = ProfileSerializer(profile)

        assert serializer.data["first_name"] == "Updated"
        assert serializer.data["last_name"] == "Name"
        assert serializer.data["email"] == "updated@example.com"

    def test_avatar_without_file_is_represented_as_none(self, profile):
        profile.avatar = ""
        profile.save(update_fields=["avatar"])

        serializer = ProfileSerializer(profile)

        assert serializer.data["avatar"] is None

    def test_avatar_url_is_serialized_when_avatar_exists(self, profile):
        image = SimpleUploadedFile(
            "avatar.jpg",
            b"fake-image-content",
            content_type="image/jpeg",
        )
        profile.avatar = image
        profile.save()

        serializer = ProfileSerializer(profile)

        assert serializer.data["avatar"]
        assert serializer.data["avatar"].endswith(".jpg")

    def test_empty_related_collections_are_serialized_as_empty_lists(
        self,
        profile,
    ):
        serializer = ProfileSerializer(profile)

        assert serializer.data["skills"] == []
        assert serializer.data["educations"] == []
        assert serializer.data["experiences"] == []
        assert serializer.data["languages"] == []
        assert serializer.data["social_links"] == []

    def test_serializes_multiple_skills(self, profile):
        Skill.objects.create(
            profile=profile,
            name="Python",
            description="Python programming language",
        )
        Skill.objects.create(
            profile=profile,
            name="Django",
            description="Django web framework",
        )

        serializer = ProfileSerializer(profile)

        expected = [
            {
                "id": skill.pk,
                "name": skill.name,
                "description": skill.description,
            }
            for skill in profile.skills.all()
        ]

        assert serializer.data["skills"] == expected

    def test_serializes_multiple_educations(self, profile):
        Education.objects.create(
            profile=profile,
            institution="University A",
            degree="Bachelor",
            field_of_study="Computer Science",
            description="Computer science education",
            start_date=date(2014, 9, 1),
            end_date=date(2018, 6, 30),
        )
        Education.objects.create(
            profile=profile,
            institution="University B",
            degree="Master",
            field_of_study="Software Engineering",
            description="Software engineering education",
            start_date=date(2018, 9, 1),
            end_date=date(2020, 6, 30),
        )

        serializer = ProfileSerializer(profile)

        expected = [
            {
                "id": education.pk,
                "institution": education.institution,
                "degree": education.degree,
                "field_of_study": education.field_of_study,
                "description": education.description,
                "start_date": (
                    education.start_date.isoformat() if education.start_date else None
                ),
                "end_date": (
                    education.end_date.isoformat() if education.end_date else None
                ),
            }
            for education in profile.educations.all()
        ]

        assert serializer.data["educations"] == expected

    def test_serializes_multiple_experiences(self, profile):
        Experience.objects.create(
            profile=profile,
            company="Company A",
            position="Developer",
            location="Baku",
            description="Backend development",
            start_date=date(2019, 1, 1),
            end_date=date(2021, 1, 1),
        )
        Experience.objects.create(
            profile=profile,
            company="Company B",
            position="Senior Developer",
            location="Remote",
            description="Senior backend development",
            start_date=date(2021, 2, 1),
            end_date=date(2024, 1, 1),
        )

        serializer = ProfileSerializer(profile)

        expected = [
            {
                "id": experience.pk,
                "company": experience.company,
                "position": experience.position,
                "location": experience.location,
                "description": experience.description,
                "start_date": (
                    experience.start_date.isoformat() if experience.start_date else None
                ),
                "end_date": (
                    experience.end_date.isoformat() if experience.end_date else None
                ),
            }
            for experience in profile.experiences.all()
        ]

        assert serializer.data["experiences"] == expected

    def test_serializes_multiple_languages(self, profile):
        Language.objects.create(
            profile=profile,
            language="English",
            proficiency="C1",
        )
        Language.objects.create(
            profile=profile,
            language="Azerbaijani",
            proficiency="Native",
        )

        serializer = ProfileSerializer(profile)

        expected = [
            {
                "id": language.pk,
                "language": language.language,
                "proficiency": language.proficiency,
            }
            for language in profile.languages.all()
        ]

        assert serializer.data["languages"] == expected

    def test_serializes_multiple_social_links(self, profile):
        SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.GITHUB,
            address="https://github.com/example",
        )
        SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.LINKEDIN,
            address="https://linkedin.com/in/example",
        )

        serializer = ProfileSerializer(profile)

        expected = [
            {
                "id": social_link.pk,
                "platform": social_link.platform,
                "address": social_link.address,
            }
            for social_link in profile.social_links.all()
        ]

        assert serializer.data["social_links"] == expected

    def test_nested_serializers_do_not_expose_profile_id(self, profile):
        skill = Skill.objects.create(
            profile=profile,
            name="Python",
            description="Programming language",
        )
        education = Education.objects.create(
            profile=profile,
            institution="University",
            degree="Bachelor",
            field_of_study="Computer Science",
        )
        experience = Experience.objects.create(
            profile=profile,
            company="Company",
            position="Developer",
        )
        language = Language.objects.create(
            profile=profile,
            language="English",
            proficiency="C1",
        )
        social_link = SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.GITHUB,
            address="https://github.com/example",
        )

        serializer = ProfileSerializer(profile)

        assert "profile" not in serializer.data["skills"][0]
        assert "profile" not in serializer.data["educations"][0]
        assert "profile" not in serializer.data["experiences"][0]
        assert "profile" not in serializer.data["languages"][0]
        assert "profile" not in serializer.data["social_links"][0]

        assert serializer.data["skills"][0]["id"] == skill.pk
        assert serializer.data["educations"][0]["id"] == education.pk
        assert serializer.data["experiences"][0]["id"] == experience.pk
        assert serializer.data["languages"][0]["id"] == language.pk
        assert serializer.data["social_links"][0]["id"] == social_link.pk


class TestProfileSerializerValidation:
    def test_valid_profile_data_is_accepted(self, profile):
        data = {
            "website": "https://new-example.com",
            "country": "Azerbaijan",
            "timezone": "Asia/Baku",
            "date_of_birth": "1996-06-20",
            "company": "New Company",
            "job_title": "Senior Developer",
        }

        serializer = ProfileSerializer(
            profile,
            data=data,
            partial=True,
        )

        assert serializer.is_valid() is True

        assert serializer.validated_data["website"] == ("https://new-example.com")
        assert serializer.validated_data["country"] == "Azerbaijan"
        assert serializer.validated_data["timezone"] == "Asia/Baku"
        assert serializer.validated_data["date_of_birth"] == date(1996, 6, 20)
        assert serializer.validated_data["company"] == "New Company"
        assert serializer.validated_data["job_title"] == "Senior Developer"

    def test_profile_fields_can_be_updated(self, profile):
        data = {
            "website": "https://updated.example.com",
            "country": "Azerbaijan",
            "timezone": "Europe/Berlin",
            "date_of_birth": "1997-01-10",
            "company": "Updated Company",
            "job_title": "Lead Developer",
        }

        serializer = ProfileSerializer(
            profile,
            data=data,
            partial=True,
        )

        assert serializer.is_valid() is True

        updated_profile = serializer.save()

        assert updated_profile.website == "https://updated.example.com"
        assert updated_profile.country == "Azerbaijan"
        assert updated_profile.timezone == "Europe/Berlin"
        assert updated_profile.date_of_birth == date(1997, 1, 10)
        assert updated_profile.company == "Updated Company"
        assert updated_profile.job_title == "Lead Developer"

    def test_optional_fields_can_be_omitted(self, profile):
        serializer = ProfileSerializer(
            profile,
            data={
                "company": "Updated Company",
            },
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["company"] == "Updated Company"

        assert "website" not in serializer.validated_data
        assert "country" not in serializer.validated_data
        assert "timezone" not in serializer.validated_data
        assert "date_of_birth" not in serializer.validated_data
        assert "job_title" not in serializer.validated_data

    def test_date_of_birth_accepts_null(self, profile):
        serializer = ProfileSerializer(
            profile,
            data={"date_of_birth": None},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["date_of_birth"] is None

    def test_blank_string_is_allowed_for_blank_model_fields(self, profile):
        data = {
            "website": "",
            "country": "",
            "timezone": "",
            "company": "",
            "job_title": "",
        }

        serializer = ProfileSerializer(
            profile,
            data=data,
            partial=True,
        )

        assert serializer.is_valid() is True

        assert serializer.validated_data["website"] == ""
        assert serializer.validated_data["country"] == ""
        assert serializer.validated_data["timezone"] == ""
        assert serializer.validated_data["company"] == ""
        assert serializer.validated_data["job_title"] == ""

    def test_invalid_website_is_rejected(self, profile):
        serializer = ProfileSerializer(
            profile,
            data={"website": "not-a-url"},
            partial=True,
        )

        assert serializer.is_valid() is False
        assert "website" in serializer.errors

    def test_invalid_date_of_birth_is_rejected(self, profile):
        serializer = ProfileSerializer(
            profile,
            data={"date_of_birth": "not-a-date"},
            partial=True,
        )

        assert serializer.is_valid() is False
        assert "date_of_birth" in serializer.errors


class TestProfileSerializerReadOnlyFields:
    def test_id_input_is_ignored(self, profile):
        original_id = profile.pk

        serializer = ProfileSerializer(
            profile,
            data={"id": 999999},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert "id" not in serializer.validated_data

        serializer.save()

        profile.refresh_from_db()

        assert profile.pk == original_id

    def test_first_name_input_is_ignored(self, profile):
        original_name = profile.user.first_name

        serializer = ProfileSerializer(
            profile,
            data={"first_name": "Changed"},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert "first_name" not in serializer.validated_data

        serializer.save()

        profile.user.refresh_from_db()

        assert profile.user.first_name == original_name

    def test_last_name_input_is_ignored(self, profile):
        original_name = profile.user.last_name

        serializer = ProfileSerializer(
            profile,
            data={"last_name": "Changed"},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert "last_name" not in serializer.validated_data

        serializer.save()

        profile.user.refresh_from_db()

        assert profile.user.last_name == original_name

    def test_email_input_is_ignored(self, profile):
        original_email = profile.user.email

        serializer = ProfileSerializer(
            profile,
            data={"email": "changed@example.com"},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert "email" not in serializer.validated_data

        serializer.save()

        profile.user.refresh_from_db()

        assert profile.user.email == original_email

    def test_nested_read_only_fields_are_ignored(self, profile):
        serializer = ProfileSerializer(
            profile,
            data={
                "skills": [
                    {
                        "name": "Python",
                        "description": "Programming",
                    },
                ],
                "educations": [
                    {
                        "institution": "University",
                        "degree": "Bachelor",
                        "field_of_study": "Computer Science",
                    },
                ],
                "experiences": [
                    {
                        "company": "Company",
                        "position": "Developer",
                    },
                ],
                "languages": [
                    {
                        "language": "English",
                        "proficiency": "C1",
                    },
                ],
                "social_links": [
                    {
                        "platform": "github",
                        "address": "https://github.com/example",
                    },
                ],
            },
            partial=True,
        )

        assert serializer.is_valid() is True

        assert "skills" not in serializer.validated_data
        assert "educations" not in serializer.validated_data
        assert "experiences" not in serializer.validated_data
        assert "languages" not in serializer.validated_data
        assert "social_links" not in serializer.validated_data

    def test_read_only_fields_do_not_modify_profile(self, profile):
        original_values = {
            "first_name": profile.user.first_name,
            "last_name": profile.user.last_name,
            "email": profile.user.email,
        }

        serializer = ProfileSerializer(
            profile,
            data={
                "first_name": "Changed",
                "last_name": "Changed",
                "email": "changed@example.com",
            },
            partial=True,
        )

        assert serializer.is_valid() is True
        serializer.save()

        profile.user.refresh_from_db()

        assert profile.user.first_name == original_values["first_name"]
        assert profile.user.last_name == original_values["last_name"]
        assert profile.user.email == original_values["email"]


class TestProfileSerializerPartialUpdates:
    def test_partial_update_accepts_single_field(self, profile):
        serializer = ProfileSerializer(
            profile,
            data={"job_title": "Senior Developer"},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data == {
            "job_title": "Senior Developer",
        }

    def test_partial_update_does_not_clear_unprovided_fields(self, profile):
        original_website = profile.website
        original_country = profile.country
        original_timezone = profile.timezone
        original_company = profile.company

        serializer = ProfileSerializer(
            profile,
            data={"job_title": "Senior Developer"},
            partial=True,
        )

        assert serializer.is_valid() is True
        serializer.save()

        profile.refresh_from_db()

        assert profile.website == original_website
        assert profile.country == original_country
        assert profile.timezone == original_timezone
        assert profile.company == original_company
        assert profile.job_title == "Senior Developer"


class TestProfileSerializerAvatar:
    @staticmethod
    def create_valid_image():
        image = Image.new("RGB", (100, 100), "white")
        image_file = BytesIO()
        image.save(image_file, format="JPEG")
        image_file.seek(0)

        return SimpleUploadedFile(
            "profile-avatar.jpg",
            image_file.read(),
            content_type="image/jpeg",
        )

    def test_valid_image_file_is_accepted(self, profile):
        image = self.create_valid_image()

        serializer = ProfileSerializer(
            profile,
            data={"avatar": image},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["avatar"] is image

    def test_avatar_can_be_replaced(self, profile):
        first_image = self.create_valid_image()

        profile.avatar = first_image
        profile.save()

        original_name = profile.avatar.name

        second_image = self.create_valid_image()

        serializer = ProfileSerializer(
            profile,
            data={"avatar": second_image},
            partial=True,
        )

        assert serializer.is_valid() is True

        updated_profile = serializer.save()

        assert updated_profile.avatar
        assert updated_profile.avatar.name != original_name
        assert updated_profile.avatar.name.endswith(".jpg")

    def test_null_avatar_is_rejected(self, profile):
        serializer = ProfileSerializer(
            profile,
            data={"avatar": None},
            partial=True,
        )

        assert serializer.is_valid() is False
        assert "avatar" in serializer.errors


class TestProfileSerializerNestedDataIsReadOnly:
    def test_updating_nested_skill_data_does_not_change_skill(
        self,
        profile,
    ):
        skill = Skill.objects.create(
            profile=profile,
            name="Python",
            description="Original description",
        )

        serializer = ProfileSerializer(
            profile,
            data={
                "skills": [
                    {
                        "id": skill.pk,
                        "name": "Django",
                        "description": "Changed description",
                    },
                ],
            },
            partial=True,
        )

        assert serializer.is_valid() is True
        serializer.save()

        skill.refresh_from_db()

        assert skill.name == "Python"
        assert skill.description == "Original description"

    def test_updating_nested_education_data_does_not_change_education(
        self,
        profile,
    ):
        education = Education.objects.create(
            profile=profile,
            institution="Original University",
            degree="Bachelor",
            field_of_study="Computer Science",
        )

        serializer = ProfileSerializer(
            profile,
            data={
                "educations": [
                    {
                        "id": education.pk,
                        "institution": "Changed University",
                        "degree": "Master",
                        "field_of_study": "Engineering",
                    },
                ],
            },
            partial=True,
        )

        assert serializer.is_valid() is True
        serializer.save()

        education.refresh_from_db()

        assert education.institution == "Original University"
        assert education.degree == "Bachelor"
        assert education.field_of_study == "Computer Science"

    def test_updating_nested_experience_data_does_not_change_experience(
        self,
        profile,
    ):
        experience = Experience.objects.create(
            profile=profile,
            company="Original Company",
            position="Developer",
        )

        serializer = ProfileSerializer(
            profile,
            data={
                "experiences": [
                    {
                        "id": experience.pk,
                        "company": "Changed Company",
                        "position": "Senior Developer",
                    },
                ],
            },
            partial=True,
        )

        assert serializer.is_valid() is True
        serializer.save()

        experience.refresh_from_db()

        assert experience.company == "Original Company"
        assert experience.position == "Developer"

    def test_updating_nested_language_data_does_not_change_language(
        self,
        profile,
    ):
        language = Language.objects.create(
            profile=profile,
            language="English",
            proficiency="C1",
        )

        serializer = ProfileSerializer(
            profile,
            data={
                "languages": [
                    {
                        "id": language.pk,
                        "language": "German",
                        "proficiency": "B2",
                    },
                ],
            },
            partial=True,
        )

        assert serializer.is_valid() is True
        serializer.save()

        language.refresh_from_db()

        assert language.language == "English"
        assert language.proficiency == "C1"

    def test_updating_nested_social_link_data_does_not_change_social_link(
        self,
        profile,
    ):
        social_link = SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.GITHUB,
            address="https://github.com/example",
        )

        serializer = ProfileSerializer(
            profile,
            data={
                "social_links": [
                    {
                        "id": social_link.pk,
                        "platform": SocialLink.Platform.LINKEDIN,
                        "address": "https://linkedin.com/in/example",
                    },
                ],
            },
            partial=True,
        )

        assert serializer.is_valid() is True
        serializer.save()

        social_link.refresh_from_db()

        assert social_link.platform == SocialLink.Platform.GITHUB
        assert social_link.address == "https://github.com/example"
