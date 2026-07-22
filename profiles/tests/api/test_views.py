import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from profiles.api.serializers import ProfileSerializer, TopNavUserSerializer
from profiles.models import Education, Experience, Language, SocialLink
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
class TestProfileApiView:
    """Tests for ProfileApiView."""

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def url(self):
        return reverse("profile-api:student_profile")

    def test_returns_authenticated_user_profile(
        self,
        api_client,
        url,
    ):
        """Authenticated users receive their profile."""
        profile = ProfileFactory()

        api_client.force_authenticate(user=profile.user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == ProfileSerializer(profile).data

    def test_returns_unauthorized_for_anonymous_user(
        self,
        api_client,
        url,
    ):
        """Anonymous users cannot access the endpoint."""
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestCurrentUserApiView:
    """Tests for CurrentUserApiView."""

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def url(self):
        return reverse("profile-api:current_user")

    def test_returns_authenticated_user(
        self,
        api_client,
        url,
    ):
        """Authenticated users receive their own information."""
        profile = ProfileFactory()

        api_client.force_authenticate(user=profile.user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == TopNavUserSerializer(profile.user).data

    def test_returns_unauthorized_for_anonymous_user(
        self,
        api_client,
        url,
    ):
        """Anonymous users cannot access the endpoint."""
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestSkillViewSet:
    """Tests for SkillViewSet."""

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def user(self):
        return ProfileFactory().user

    @pytest.fixture
    def delete_url(self):
        return reverse("profile-api:skill-delete")

    @pytest.fixture
    def create_url(self):
        return reverse("profile-api:skill-list")

    def test_creates_skill(
        self,
        api_client,
        user,
        create_url,
    ):
        """Authenticated users can create a skill."""
        api_client.force_authenticate(user=user)

        payload = {
            "name": "Python",
            "description": "Programming language",
        }

        response = api_client.post(create_url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED

        skill = user.profile.skills.get(name="Python")
        assert skill.description == "Programming language"

    def test_created_skill_belongs_to_authenticated_user(
        self,
        api_client,
        user,
        create_url,
    ):
        """perform_create() associates the skill with the authenticated profile."""
        api_client.force_authenticate(user=user)

        response = api_client.post(
            create_url,
            {
                "name": "Django",
                "description": "",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        skill = user.profile.skills.get(name="Django")
        assert skill.profile == user.profile

    def test_deletes_existing_skill(
        self,
        api_client,
        user,
        delete_url,
    ):
        """Users can delete one of their own skills."""
        skill = SkillFactory(
            profile=user.profile,
            name="Python",
        )

        api_client.force_authenticate(user=user)

        response = api_client.delete(
            delete_url,
            {"name": skill.name},
            format="json",
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not user.profile.skills.filter(pk=skill.pk).exists()

    def test_returns_bad_request_when_name_is_missing(
        self,
        api_client,
        user,
        delete_url,
    ):
        """Skill name is required."""
        api_client.force_authenticate(user=user)

        response = api_client.delete(
            delete_url,
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            "error": "Skill name is required",
        }

    def test_returns_not_found_for_unknown_skill(
        self,
        api_client,
        user,
        delete_url,
    ):
        """Deleting a nonexistent skill returns 404."""
        api_client.force_authenticate(user=user)

        response = api_client.delete(
            delete_url,
            {"name": "Unknown"},
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cannot_delete_another_users_skill(
        self,
        api_client,
        delete_url,
    ):
        """Users cannot delete another user's skill."""
        owner = ProfileFactory().user
        attacker = ProfileFactory().user

        skill = SkillFactory(
            profile=owner.profile,
            name="Python",
        )

        api_client.force_authenticate(user=attacker)

        response = api_client.delete(
            delete_url,
            {"name": skill.name},
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert owner.profile.skills.filter(pk=skill.pk).exists()

    def test_requires_authentication_for_create(
        self,
        api_client,
        create_url,
    ):
        """Anonymous users cannot create skills."""
        response = api_client.post(
            create_url,
            {
                "name": "Python",
                "description": "",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_requires_authentication_for_delete(
        self,
        api_client,
        delete_url,
    ):
        """Anonymous users cannot delete skills."""
        response = api_client.delete(
            delete_url,
            {"name": "Python"},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestUserInfoUpdateApiView:
    """Tests for UserInfoUpdateApiView."""

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def url(self):
        return reverse("profile-api:update_user")

    def test_updates_authenticated_user_profile(
        self,
        api_client,
        url,
    ):
        """Authenticated users can update their own profile."""
        profile = ProfileFactory(
            biography="Old biography",
            headline="Old headline",
            company="Old Company",
        )

        api_client.force_authenticate(user=profile.user)

        payload = {
            "first_name": "Test",
            "last_name": "User",
            "biography": "Updated biography",
            "headline": "Backend Developer",
            "company": "Test Company",
        }

        response = api_client.patch(
            url,
            payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        profile.refresh_from_db()
        profile.user.refresh_from_db()

        assert profile.user.first_name == "Test"
        assert profile.user.last_name == "User"
        assert profile.biography == "Updated biography"
        assert profile.headline == "Backend Developer"
        assert profile.company == "Test Company"

    def test_partial_update_only_updates_supplied_fields(
        self,
        api_client,
        url,
    ):
        """PATCH updates only the provided fields."""
        profile = ProfileFactory(
            biography="Original biography",
            headline="Original headline",
        )

        original_first_name = profile.user.first_name

        api_client.force_authenticate(user=profile.user)

        response = api_client.patch(
            url,
            {
                "headline": "Updated headline",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        profile.refresh_from_db()
        profile.user.refresh_from_db()

        assert profile.headline == "Updated headline"
        assert profile.biography == "Original biography"
        assert profile.user.first_name == original_first_name

    def test_email_cannot_be_updated(
        self,
        api_client,
        url,
    ):
        """Email is read-only."""
        profile = ProfileFactory()

        original_email = profile.user.email

        api_client.force_authenticate(user=profile.user)

        response = api_client.patch(
            url,
            {
                "email": "new@example.com",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        profile.user.refresh_from_db()

        assert profile.user.email == original_email

    def test_requires_authentication(
        self,
        api_client,
        url,
    ):
        """Anonymous users cannot update profile information."""
        response = api_client.patch(
            url,
            {
                "headline": "Backend Developer",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_updates_avatar(
        self,
        api_client,
        url,
    ):
        """Users can upload a new avatar."""
        profile = ProfileFactory()

        api_client.force_authenticate(user=profile.user)

        response = api_client.patch(
            url,
            {
                "avatar": image_file("avatar.jpg"),
            },
            format="multipart",
        )

        assert response.status_code == status.HTTP_200_OK

        profile.refresh_from_db()

        assert profile.avatar
        assert profile.avatar.name.endswith("avatar.jpg")

    def test_updates_cover(
        self,
        api_client,
        url,
    ):
        """Users can upload a new cover image."""
        profile = ProfileFactory()

        api_client.force_authenticate(user=profile.user)

        response = api_client.patch(
            url,
            {
                "cover": image_file("cover.jpg"),
            },
            format="multipart",
        )

        assert response.status_code == status.HTTP_200_OK

        profile.refresh_from_db()

        assert profile.cover
        assert profile.cover.name.endswith("cover.jpg")

    def test_updates_avatar_and_cover_together(
        self,
        api_client,
        url,
    ):
        """Users can upload avatar and cover in one request."""
        profile = ProfileFactory()

        api_client.force_authenticate(user=profile.user)

        response = api_client.patch(
            url,
            {
                "avatar": image_file("avatar.jpg"),
                "cover": image_file("cover.jpg"),
            },
            format="multipart",
        )

        assert response.status_code == status.HTTP_200_OK

        profile.refresh_from_db()

        assert profile.avatar
        assert profile.cover

        assert profile.avatar.name.endswith("avatar.jpg")
        assert profile.cover.name.endswith("cover.jpg")


@pytest.mark.django_db
class TestProfileEducationViewSet:
    """Tests for ProfileEducationViewSet."""

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def profile(self):
        return ProfileFactory()

    @pytest.fixture
    def create_url(self):
        return reverse("profile-api:education-list")

    @pytest.fixture
    def education(self, profile):
        return EducationFactory(profile=profile)

    def test_create_education(
        self,
        api_client,
        profile,
        create_url,
    ):
        """Authenticated users can add an education entry."""
        api_client.force_authenticate(profile.user)

        payload = {
            "institution": "Test University",
            "degree": "Bachelor",
            "field_of_study": "Computer Science",
            "description": "Test description",
            "start_date": "2020-09-01",
            "end_date": "2024-06-30",
        }

        response = api_client.post(create_url, payload)

        assert response.status_code == status.HTTP_201_CREATED

        education = Education.objects.get()

        assert education.profile == profile
        assert education.institution == payload["institution"]
        assert education.degree == payload["degree"]
        assert education.field_of_study == payload["field_of_study"]
        assert education.description == payload["description"]

    def test_update_education(
        self,
        api_client,
        profile,
        education,
    ):
        """Users can update their own education."""
        api_client.force_authenticate(profile.user)

        url = reverse(
            "profile-api:education-detail",
            kwargs={"pk": education.pk},
        )

        payload = {
            "institution": "Updated University",
            "degree": education.degree,
            "field_of_study": education.field_of_study,
            "description": "Updated description",
            "start_date": str(education.start_date),
            "end_date": (str(education.end_date) if education.end_date else None),
        }

        response = api_client.patch(url, payload)

        assert response.status_code == status.HTTP_200_OK

        education.refresh_from_db()

        assert education.institution == "Updated University"
        assert education.description == "Updated description"

    def test_delete_education(
        self,
        api_client,
        profile,
        education,
    ):
        """Users can delete their own education."""
        api_client.force_authenticate(profile.user)

        url = reverse(
            "profile-api:education-detail",
            kwargs={"pk": education.pk},
        )

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        assert not Education.objects.filter(pk=education.pk).exists()

    def test_cannot_access_other_users_education(
        self,
        api_client,
    ):
        """Users cannot update another user's education."""
        owner = ProfileFactory()
        other = ProfileFactory()

        education = EducationFactory(profile=owner)

        api_client.force_authenticate(other.user)

        url = reverse(
            "profile-api:education-detail",
            kwargs={"pk": education.pk},
        )

        response = api_client.patch(
            url,
            {"institution": "Hacked"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_requires_authentication_for_create(
        self,
        api_client,
        create_url,
    ):
        """Anonymous users cannot create education."""
        response = api_client.post(
            create_url,
            {},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_requires_authentication_for_update(
        self,
        api_client,
        education,
    ):
        """Anonymous users cannot update education."""
        url = reverse(
            "profile-api:education-detail",
            kwargs={"pk": education.pk},
        )

        response = api_client.patch(
            url,
            {},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_requires_authentication_for_delete(
        self,
        api_client,
        education,
    ):
        """Anonymous users cannot delete education."""
        url = reverse(
            "profile-api:education-detail",
            kwargs={"pk": education.pk},
        )

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestProfileExperienceViewSet:
    """Tests for ProfileExperienceViewSet."""

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def profile(self):
        return ProfileFactory()

    @pytest.fixture
    def create_url(self):
        return reverse("profile-api:experience-list")

    @pytest.fixture
    def experience(self, profile):
        return ExperienceFactory(profile=profile)

    def test_create_experience(
        self,
        api_client,
        profile,
        create_url,
    ):
        """Authenticated users can create an experience."""
        api_client.force_authenticate(profile.user)

        payload = {
            "company": "Test Company",
            "position": "Backend Developer",
            "location": "Remote",
            "description": "Working on Django APIs.",
            "start_date": "2024-01-01",
            "end_date": None,
        }

        response = api_client.post(create_url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED

        experience = Experience.objects.get(company="Test Company")

        assert experience.profile == profile
        assert experience.company == payload["company"]
        assert experience.position == payload["position"]
        assert experience.location == payload["location"]
        assert experience.description == payload["description"]

    def test_update_experience(
        self,
        api_client,
        profile,
        experience,
    ):
        """Users can update their own experience."""
        api_client.force_authenticate(profile.user)

        url = reverse(
            "profile-api:experience-detail",
            kwargs={"pk": experience.pk},
        )

        payload = {
            "company": "Updated Company",
            "position": experience.position,
            "location": experience.location,
            "description": "Updated description",
            "start_date": str(experience.start_date),
            "end_date": (str(experience.end_date) if experience.end_date else None),
        }

        response = api_client.patch(
            url,
            payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        experience.refresh_from_db()

        assert experience.company == "Updated Company"
        assert experience.description == "Updated description"

    def test_delete_experience(
        self,
        api_client,
        profile,
        experience,
    ):
        """Users can delete their own experience."""
        api_client.force_authenticate(profile.user)

        url = reverse(
            "profile-api:experience-detail",
            kwargs={"pk": experience.pk},
        )

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Experience.objects.filter(pk=experience.pk).exists()

    def test_cannot_update_other_users_experience(
        self,
        api_client,
    ):
        """Users cannot update another user's experience."""
        owner = ProfileFactory()
        other = ProfileFactory()

        experience = ExperienceFactory(profile=owner)

        api_client.force_authenticate(other.user)

        url = reverse(
            "profile-api:experience-detail",
            kwargs={"pk": experience.pk},
        )

        response = api_client.patch(
            url,
            {"company": "Hacked"},
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_requires_authentication_for_create(
        self,
        api_client,
        create_url,
    ):
        """Anonymous users cannot create an experience."""
        response = api_client.post(create_url, {}, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_requires_authentication_for_update(
        self,
        api_client,
        experience,
    ):
        """Anonymous users cannot update an experience."""
        url = reverse(
            "profile-api:experience-detail",
            kwargs={"pk": experience.pk},
        )

        response = api_client.patch(
            url,
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_requires_authentication_for_delete(
        self,
        api_client,
        experience,
    ):
        """Anonymous users cannot delete an experience."""
        url = reverse(
            "profile-api:experience-detail",
            kwargs={"pk": experience.pk},
        )

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestProfileSocialLinkViewSet:
    """Tests for ProfileSocialLinkViewSet."""

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def profile(self):
        return ProfileFactory()

    @pytest.fixture
    def create_url(self):
        return reverse("profile-api:social_link-list")

    @pytest.fixture
    def social_link(self, profile):
        return SocialLinkFactory(profile=profile)

    def test_create_social_link(
        self,
        api_client,
        profile,
        create_url,
    ):
        """Authenticated users can create a social link."""
        api_client.force_authenticate(profile.user)

        payload = {
            "platform": "github",
            "url": "https://github.com/test_user",
        }

        response = api_client.post(
            create_url,
            payload,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        social_link = SocialLink.objects.get(
            platform="github",
        )

        assert social_link.profile == profile
        assert social_link.platform == payload["platform"]
        assert social_link.url == payload["url"]

    def test_update_social_link(
        self,
        api_client,
        profile,
        social_link,
    ):
        """Users can update their own social link."""
        api_client.force_authenticate(profile.user)

        url = reverse(
            "profile-api:social_link-detail",
            kwargs={"pk": social_link.pk},
        )

        payload = {
            "platform": "linkedin",
            "url": "https://linkedin.com/in/test_user",
        }

        response = api_client.patch(
            url,
            payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        social_link.refresh_from_db()

        assert social_link.platform == payload["platform"]
        assert social_link.url == payload["url"]

    def test_delete_social_link(
        self,
        api_client,
        profile,
        social_link,
    ):
        """Users can delete their own social link."""
        api_client.force_authenticate(profile.user)

        url = reverse(
            "profile-api:social_link-detail",
            kwargs={"pk": social_link.pk},
        )

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        assert not SocialLink.objects.filter(
            pk=social_link.pk,
        ).exists()

    def test_cannot_update_other_users_social_link(
        self,
        api_client,
    ):
        """Users cannot update another user's social link."""
        owner = ProfileFactory()
        other = ProfileFactory()

        social_link = SocialLinkFactory(
            profile=owner,
        )

        api_client.force_authenticate(
            other.user,
        )

        url = reverse(
            "profile-api:social_link-detail",
            kwargs={"pk": social_link.pk},
        )

        response = api_client.patch(
            url,
            {
                "platform": "github",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_requires_authentication_for_create(
        self,
        api_client,
        create_url,
    ):
        """Anonymous users cannot create a social link."""
        response = api_client.post(
            create_url,
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_requires_authentication_for_update(
        self,
        api_client,
        social_link,
    ):
        """Anonymous users cannot update a social link."""
        url = reverse(
            "profile-api:social_link-detail",
            kwargs={"pk": social_link.pk},
        )

        response = api_client.patch(
            url,
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_requires_authentication_for_delete(
        self,
        api_client,
        social_link,
    ):
        """Anonymous users cannot delete a social link."""
        url = reverse(
            "profile-api:social_link-detail",
            kwargs={"pk": social_link.pk},
        )

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestProfileLanguageViewSet:
    """Tests for ProfileLanguageViewSet."""

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def profile(self):
        return ProfileFactory()

    @pytest.fixture
    def create_url(self):
        return reverse("profile-api:language-list")

    @pytest.fixture
    def language(self, profile):
        return LanguageFactory(profile=profile)

    def test_create_language(
        self,
        api_client,
        profile,
        create_url,
    ):
        """Authenticated users can add a language."""
        api_client.force_authenticate(profile.user)

        payload = {
            "language": "English",
            "proficiency": "Native",
        }

        response = api_client.post(
            create_url,
            payload,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        language = Language.objects.get(
            language="English",
        )

        assert language.profile == profile
        assert language.language == payload["language"]
        assert language.proficiency == payload["proficiency"]

    def test_update_language(
        self,
        api_client,
        profile,
        language,
    ):
        """Users can update their own language."""
        api_client.force_authenticate(profile.user)

        url = reverse(
            "profile-api:language-detail",
            kwargs={"pk": language.pk},
        )

        payload = {
            "language": "Spanish",
            "proficiency": "B2",
        }

        response = api_client.patch(
            url,
            payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        language.refresh_from_db()

        assert language.language == payload["language"]
        assert language.proficiency == payload["proficiency"]

    def test_delete_language(
        self,
        api_client,
        profile,
        language,
    ):
        """Users can delete their own language."""
        api_client.force_authenticate(profile.user)

        url = reverse(
            "profile-api:language-detail",
            kwargs={"pk": language.pk},
        )

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Language.objects.filter(pk=language.pk).exists()

    def test_cannot_update_other_users_language(
        self,
        api_client,
    ):
        """Users cannot update another user's language."""
        owner = ProfileFactory()
        other = ProfileFactory()

        language = LanguageFactory(profile=owner)

        api_client.force_authenticate(other.user)

        url = reverse(
            "profile-api:language-detail",
            kwargs={"pk": language.pk},
        )

        response = api_client.patch(
            url,
            {
                "language": "German",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_requires_authentication_for_create(
        self,
        api_client,
        create_url,
    ):
        """Anonymous users cannot create a language."""
        response = api_client.post(
            create_url,
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_requires_authentication_for_update(
        self,
        api_client,
        language,
    ):
        """Anonymous users cannot update a language."""
        url = reverse(
            "profile-api:language-detail",
            kwargs={"pk": language.pk},
        )

        response = api_client.patch(
            url,
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_requires_authentication_for_delete(
        self,
        api_client,
        language,
    ):
        """Anonymous users cannot delete a language."""
        url = reverse(
            "profile-api:language-detail",
            kwargs={"pk": language.pk},
        )

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
