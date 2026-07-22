import pytest
from rest_framework.test import APIRequestFactory

from accounts.tests.factories import UserFactory
from profiles.api.serializers import (
    EducationSerializer,
    ExperienceSerializer,
    LanguageSerializer,
    ProfileSerializer,
    SkillSerializer,
    SocialLinkSerializer,
    TopNavUserSerializer,
)
from profiles.tests.factories import (
    EducationFactory,
    ExperienceFactory,
    InstructorProfileFactory,
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
            degree="Master of Science",
            description="Master's degree",
            start_date="2022-12-01",
            end_date="2022-12-10",
        )

        serializer = EducationSerializer(education)

        assert serializer.data == {
            "id": education.id,
            "institution": "Massachusetts Institute of Technology",
            "field_of_study": "Computer Science",
            "degree": "Master of Science",
            "description": "Master's degree",
            "start_date": "2022-12-01",
            "end_date": "2022-12-10",
        }

    def test_contains_expected_fields(self):
        """Serializer exposes the expected fields."""
        serializer = EducationSerializer()

        assert set(serializer.fields.keys()) == {
            "id",
            "institution",
            "field_of_study",
            "degree",
            "description",
            "start_date",
            "end_date",
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
            profile=profile,
            description="Programming language",
        )

        education = EducationFactory(
            profile=profile,
            degree="Master of Science",
            institution="MIT",
        )

        experience = ExperienceFactory(
            profile=profile,
            company="test_company",
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
                "degree": education.degree,
                "description": education.description,
                "start_date": education.start_date,
                "end_date": education.end_date,
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
        print(serializer.fields.keys())
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


@pytest.mark.django_db
class TestTopNavUserSerializer:
    """Tests for TopNavUserSerializer."""

    def test_serializes_user(self):
        """Serializer returns the expected user data."""
        user = UserFactory(
            username="test_user",
            first_name="test_user",
            last_name="test_last",
            email="test_user@example.com",
        )

        ProfileFactory(user=user)

        serializer = TopNavUserSerializer(user)

        assert serializer.data == {
            "id": user.id,
            "first_name": "test_user",
            "last_name": "test_last",
            "full_name": "test_user test_last",
            "email": "test_user@example.com",
            "avatar_url": None,
            "role": "student",
        }

    def test_uses_username_when_full_name_is_empty(self):
        """Username is returned when the user has no first/last name."""
        user = UserFactory(
            username="test_user",
            first_name="",
            last_name="",
        )

        ProfileFactory(user=user)

        serializer = TopNavUserSerializer(user)

        assert serializer.data["full_name"] == "test_user"

    def test_returns_relative_avatar_url_without_request(self):
        """Relative avatar URL is returned when no request is provided."""
        user = UserFactory()
        profile = ProfileFactory(
            user=user,
            avatar=image_file("avatar.jpg"),
        )

        serializer = TopNavUserSerializer(user)

        assert serializer.data["avatar_url"] == profile.avatar.url

    def test_returns_absolute_avatar_url_with_request(self):
        """Absolute avatar URL is returned when request exists."""
        user = UserFactory()
        profile = ProfileFactory(
            user=user,
            avatar=image_file("avatar.jpg"),
        )

        request = APIRequestFactory().get("/")

        serializer = TopNavUserSerializer(
            user,
            context={"request": request},
        )

        assert serializer.data["avatar_url"] == request.build_absolute_uri(
            profile.avatar.url
        )

    def test_returns_none_when_avatar_is_missing(self):
        """None is returned when the profile has no avatar."""
        user = UserFactory()
        ProfileFactory(user=user)

        serializer = TopNavUserSerializer(user)

        assert serializer.data["avatar_url"] is None

    def test_returns_student_role(self):
        """Users without an instructor profile are students."""
        user = UserFactory()
        ProfileFactory(user=user)

        serializer = TopNavUserSerializer(user)

        assert serializer.data["role"] == "student"

    def test_returns_instructor_role(self):
        """Users with an instructor profile are instructors."""
        user = UserFactory()
        profile = ProfileFactory(user=user)
        InstructorProfileFactory(profile=profile)
        serializer = TopNavUserSerializer(user)
        assert serializer.data["role"] == "instructor"

    def test_contains_expected_fields(self):
        """Serializer exposes the expected fields."""
        serializer = TopNavUserSerializer()

        assert set(serializer.fields.keys()) == {
            "id",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "avatar_url",
            "role",
        }


@pytest.mark.django_db
class TestProfileSerializerUpdate:
    """Tests for ProfileSerializer.update()."""

    def test_updates_profile_and_user_fields(self):
        """Serializer updates both the related User and Profile."""
        profile = ProfileFactory(
            biography="Old biography",
            headline="Old headline",
            company="Old Company",
        )

        serializer = ProfileSerializer(
            instance=profile,
            data={
                "first_name": "Test",
                "last_name": "User",
                "biography": "Updated biography",
                "headline": "Backend Developer",
                "company": "Test Company",
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        serializer.save()

        profile.refresh_from_db()
        profile.user.refresh_from_db()

        assert profile.user.first_name == "Test"
        assert profile.user.last_name == "User"

        assert profile.biography == "Updated biography"
        assert profile.headline == "Backend Developer"
        assert profile.company == "Test Company"

    def test_partial_update_preserves_unspecified_fields(self):
        """Fields not included in the update remain unchanged."""
        profile = ProfileFactory(
            biography="Original biography",
            headline="Original headline",
        )

        original_first_name = profile.user.first_name
        original_last_name = profile.user.last_name

        serializer = ProfileSerializer(
            instance=profile,
            data={
                "headline": "Updated headline",
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        serializer.save()

        profile.refresh_from_db()
        profile.user.refresh_from_db()

        assert profile.headline == "Updated headline"
        assert profile.biography == "Original biography"

        assert profile.user.first_name == original_first_name
        assert profile.user.last_name == original_last_name

    def test_email_is_read_only(self):
        """Email cannot be updated through the serializer."""
        profile = ProfileFactory()

        original_email = profile.user.email

        serializer = ProfileSerializer(
            instance=profile,
            data={
                "email": "new@example.com",
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        serializer.save()

        profile.user.refresh_from_db()

        assert profile.user.email == original_email
