import pytest
from rest_framework.test import APIRequestFactory

from profiles.api.serializers import (
    EducationSerializer,
    ExperienceSerializer,
    LanguageSerializer,
    ProfileSerializer,
    SkillSerializer,
    SocialLinkSerializer,
)
from profiles.tests.factories import (
    EducationFactory,
    ExperienceFactory,
    LanguageFactory,
    ProfileFactory,
    SkillFactory,
    SocialLinkFactory,
)
from profiles.tests.utils import image_file


@pytest.mark.django_db
class TestEducationSerializer:
    """Tests for EducationSerializer."""

    def test_serializes_education(self):
        """Serializer returns the expected education data."""
        education = EducationFactory(
            institution="Massachusetts Institute of Technology",
            field_of_study="Computer Science",
            description="Master's degree",
            start_year=2022,
            end_year=2024,
        )

        serializer = EducationSerializer(education)

        assert serializer.data == {
            "id": education.id,
            "institution": "Massachusetts Institute of Technology",
            "field_of_study": "Computer Science",
            "description": "Master's degree",
            "start_year": 2022,
            "end_year": 2024,
        }

    def test_contains_expected_fields(self):
        """Serializer exposes the expected fields."""
        serializer = EducationSerializer()

        assert set(serializer.fields.keys()) == {
            "id",
            "institution",
            "field_of_study",
            "description",
            "start_year",
            "end_year",
        }


@pytest.mark.django_db
class TestExperienceSerializer:
    """Tests for ExperienceSerializer."""

    def test_serializes_experience(self):
        """Serializer returns the expected experience data."""
        experience = ExperienceFactory(
            company="Example Company",
            position="Backend Developer",
            location="Remote",
            description="Developed REST APIs using Django REST Framework.",
            start_date="2024-01-01",
            end_date="2025-01-01",
        )

        serializer = ExperienceSerializer(experience)

        assert serializer.data == {
            "id": experience.id,
            "company": "Example Company",
            "position": "Backend Developer",
            "location": "Remote",
            "description": "Developed REST APIs using Django REST Framework.",
            "start_date": "2024-01-01",
            "end_date": "2025-01-01",
        }

    def test_contains_expected_fields(self):
        """Serializer exposes the expected fields."""
        serializer = ExperienceSerializer()

        assert set(serializer.fields.keys()) == {
            "id",
            "company",
            "position",
            "location",
            "description",
            "start_date",
            "end_date",
        }


@pytest.mark.django_db
class TestLanguageSerializer:
    """Tests for LanguageSerializer."""

    def test_serializes_language(self):
        """Serializer returns the expected language data."""
        language = LanguageFactory(
            language="English",
            proficiency="native",
        )

        serializer = LanguageSerializer(language)

        assert serializer.data == {
            "id": language.id,
            "language": "English",
            "proficiency": "native",
        }

    def test_contains_expected_fields(self):
        """Serializer exposes the expected fields."""
        serializer = LanguageSerializer()

        assert set(serializer.fields.keys()) == {
            "id",
            "language",
            "proficiency",
        }


@pytest.mark.django_db
class TestSkillSerializer:
    """Tests for SkillSerializer."""

    def test_serializes_skill(self):
        """Serializer returns the expected skill data."""
        skill = SkillFactory(
            name="Python",
            description="Programming language for backend development.",
        )

        serializer = SkillSerializer(skill)

        assert serializer.data == {
            "id": skill.id,
            "name": "Python",
            "description": "Programming language for backend development.",
        }

    def test_contains_expected_fields(self):
        """Serializer exposes the expected fields."""
        serializer = SkillSerializer()

        assert set(serializer.fields.keys()) == {
            "id",
            "name",
            "description",
        }


@pytest.mark.django_db
class TestSocialLinkSerializer:
    """Tests for SocialLinkSerializer."""

    def test_serializes_social_link(self):
        """Serializer returns the expected social link data."""
        social_link = SocialLinkFactory(
            platform="github",
            url="https://github.com/test_user",
        )

        serializer = SocialLinkSerializer(social_link)

        assert serializer.data == {
            "id": social_link.id,
            "platform": "github",
            "url": "https://github.com/test_user",
        }

    def test_contains_expected_fields(self):
        """Serializer exposes the expected fields."""
        serializer = SocialLinkSerializer()

        assert set(serializer.fields.keys()) == {
            "id",
            "platform",
            "url",
        }


@pytest.mark.django_db
class TestProfileSerializer:
    """Tests for ProfileSerializer."""

    def test_serializes_profile_with_nested_relations(self):
        """Serializer returns the expected profile representation."""
        profile = ProfileFactory(
            biography="Backend developer",
            headline="Senior Django Developer",
            website="https://example.com",
            country="Germany",
            timezone="UTC",
            company="OpenAI",
            job_title="Software Engineer",
        )

        skill = SkillFactory(
            name="Python",
            description="Programming language",
        )
        profile.skills.add(skill)

        education = EducationFactory(
            profile=profile,
            institution="MIT",
        )

        experience = ExperienceFactory(
            profile=profile,
            company="OpenAI",
        )

        language = LanguageFactory(
            profile=profile,
            language="English",
            proficiency="native",
        )

        social_link = SocialLinkFactory(
            profile=profile,
            platform="github",
            url="https://github.com/testuser",
        )

        serializer = ProfileSerializer(profile)
        data = serializer.data

        assert data["id"] == profile.id

        assert data["first_name"] == profile.user.first_name
        assert data["last_name"] == profile.user.last_name
        assert data["email"] == profile.user.email

        assert data["biography"] == profile.biography
        assert data["headline"] == profile.headline
        assert data["website"] == profile.website
        assert data["country"] == profile.country
        assert data["timezone"] == profile.timezone
        assert data["company"] == profile.company
        assert data["job_title"] == profile.job_title

        assert data["avatar"] is None
        assert data["cover"] is None

        assert data["skills"] == [
            {
                "id": skill.id,
                "name": skill.name,
                "description": skill.description,
            }
        ]

        assert data["educations"] == [
            {
                "id": education.id,
                "institution": education.institution,
                "field_of_study": education.field_of_study,
                "description": education.description,
                "start_year": education.start_year,
                "end_year": education.end_year,
            }
        ]

        assert data["experiences"] == [
            {
                "id": experience.id,
                "company": experience.company,
                "position": experience.position,
                "location": experience.location,
                "description": experience.description,
                "start_date": str(experience.start_date),
                "end_date": (str(experience.end_date) if experience.end_date else None),
            }
        ]

        assert data["languages"] == [
            {
                "id": language.id,
                "language": language.language,
                "proficiency": language.proficiency,
            }
        ]

        assert data["social_links"] == [
            {
                "id": social_link.id,
                "platform": social_link.platform,
                "url": social_link.url,
            }
        ]

    def test_returns_relative_media_urls_without_request(self):
        """Serializer returns relative media URLs without a request."""
        profile = ProfileFactory(
            avatar=image_file("avatar.jpg"),
            cover=image_file("cover.jpg"),
        )

        serializer = ProfileSerializer(profile)

        assert serializer.data["avatar"] == profile.avatar.url
        assert serializer.data["cover"] == profile.cover.url

    def test_returns_absolute_media_urls_with_request(self):
        """Serializer returns absolute media URLs when request is provided."""
        profile = ProfileFactory(
            avatar=image_file("avatar.jpg"),
            cover=image_file("cover.jpg"),
        )

        request = APIRequestFactory().get("/")

        serializer = ProfileSerializer(
            profile,
            context={"request": request},
        )

        assert serializer.data["avatar"] == request.build_absolute_uri(
            profile.avatar.url
        )
        assert serializer.data["cover"] == request.build_absolute_uri(profile.cover.url)

    def test_returns_none_when_avatar_and_cover_are_missing(self):
        """Serializer returns None when avatar and cover are not set."""
        profile = ProfileFactory()

        serializer = ProfileSerializer(profile)

        assert serializer.data["avatar"] is None
        assert serializer.data["cover"] is None

    def test_contains_expected_fields(self):
        """Serializer exposes the expected public fields."""
        serializer = ProfileSerializer()

        assert set(serializer.fields.keys()) == {
            "id",
            "first_name",
            "last_name",
            "email",
            "cover",
            "avatar",
            "biography",
            "headline",
            "website",
            "country",
            "timezone",
            "date_of_birth",
            "company",
            "job_title",
            "skills",
            "educations",
            "experiences",
            "social_links",
            "languages",
        }
