from datetime import datetime

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from profiles.models import InstructorProfile, Profile


@pytest.mark.django_db
class TestInstructorProfileApiView:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def user(self, django_user_model):
        return django_user_model.objects.create_user(
            username="instructor_user",
            email="instructor@example.com",
            password="TestPassword123!",
            first_name="Instructor",
            last_name="User",
        )

    @pytest.fixture
    def instructor_profile(self, user):
        profile = Profile.objects.create(
            user=user,
            website="https://example.com",
            country="Test Country",
            timezone="UTC",
            date_of_birth="1990-01-10",
            company="Test Company",
            job_title="Senior Instructor",
        )

        return InstructorProfile.objects.create(
            profile=profile,
            cover="instructors/cover/original-cover.jpg",
            biography="Original instructor biography.",
            headline="Original instructor headline.",
            professional_title="Senior Software Engineer",
            organization="Test Organization",
            is_verified=True,
            verification_date=timezone.make_aware(datetime(2026, 1, 15, 0, 0, 0)),
            introduction_video="instructors/videos/introduction.mp4",
            resume="instructors/resumes/resume.pdf",
            years_of_experience=8,
        )

    @pytest.fixture
    def another_user(self, django_user_model):
        return django_user_model.objects.create_user(
            username="another_instructor",
            email="another@example.com",
            password="TestPassword123!",
            first_name="Another",
            last_name="Instructor",
        )

    @pytest.fixture
    def another_instructor_profile(self, another_user):
        profile = Profile.objects.create(
            user=another_user,
            website="https://another.example.com",
            country="Another Country",
            timezone="UTC",
            company="Another Company",
            job_title="Instructor",
        )

        return InstructorProfile.objects.create(
            profile=profile,
            biography="Another instructor biography.",
            headline="Another instructor headline.",
            professional_title="Another Professional Title",
            organization="Another Organization",
            is_verified=False,
            years_of_experience=3,
        )

    @pytest.fixture
    def authenticated_client(self, api_client, user):
        api_client.force_authenticate(user=user)
        return api_client

    @pytest.fixture
    def url(self):
        return reverse("profile-api:instructor_profile")

    def test_authenticated_user_can_retrieve_own_instructor_profile(
        self,
        authenticated_client,
        instructor_profile,
        url,
    ):
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        assert response.data["cover"].endswith(instructor_profile.cover.name)
        assert response.data["biography"] == instructor_profile.biography
        assert response.data["headline"] == instructor_profile.headline
        assert (
            response.data["professional_title"] == instructor_profile.professional_title
        )
        assert response.data["organization"] == instructor_profile.organization
        assert response.data["is_verified"] is True
        assert (
            response.data["verification_date"]
            == instructor_profile.verification_date.isoformat()
        )
        assert response.data["introduction_video"].endswith(
            str(instructor_profile.introduction_video)
        )
        assert response.data["resume"].endswith(str(instructor_profile.resume))
        assert (
            response.data["years_of_experience"]
            == instructor_profile.years_of_experience
        )

    def test_response_contains_expected_top_level_fields(
        self,
        authenticated_client,
        instructor_profile,
        url,
    ):
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        assert set(response.data.keys()) == {
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

    def test_response_contains_expected_nested_profile_fields(
        self,
        authenticated_client,
        instructor_profile,
        url,
    ):
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        assert set(response.data["profile"].keys()) == {
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

    def test_nested_profile_contains_user_information(
        self,
        authenticated_client,
        instructor_profile,
        user,
        url,
    ):
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        profile_data = response.data["profile"]

        assert profile_data["id"] == instructor_profile.profile.id
        assert profile_data["first_name"] == user.first_name
        assert profile_data["last_name"] == user.last_name
        assert profile_data["email"] == user.email

    def test_get_returns_current_database_values(
        self,
        authenticated_client,
        instructor_profile,
        user,
        url,
    ):
        instructor_profile.headline = "Updated instructor headline"
        instructor_profile.organization = "Updated Organization"
        instructor_profile.years_of_experience = 12
        instructor_profile.save()

        user.first_name = "Updated"
        user.last_name = "Name"
        user.save()

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        assert response.data["headline"] == "Updated instructor headline"
        assert response.data["organization"] == "Updated Organization"
        assert response.data["years_of_experience"] == 12

        assert response.data["profile"]["first_name"] == "Updated"
        assert response.data["profile"]["last_name"] == "Name"

    def test_get_does_not_modify_instructor_profile(
        self,
        authenticated_client,
        instructor_profile,
        url,
    ):
        original_headline = instructor_profile.headline
        original_biography = instructor_profile.biography
        original_organization = instructor_profile.organization
        original_years_of_experience = instructor_profile.years_of_experience

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        instructor_profile.refresh_from_db()

        assert instructor_profile.headline == original_headline
        assert instructor_profile.biography == original_biography
        assert instructor_profile.organization == original_organization
        assert instructor_profile.years_of_experience == original_years_of_experience

    def test_get_does_not_modify_user(
        self,
        authenticated_client,
        instructor_profile,
        user,
        url,
    ):
        original_username = user.username
        original_email = user.email
        original_first_name = user.first_name
        original_last_name = user.last_name

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        user.refresh_from_db()

        assert user.username == original_username
        assert user.email == original_email
        assert user.first_name == original_first_name
        assert user.last_name == original_last_name

    def test_authenticated_user_gets_only_own_profile(
        self,
        authenticated_client,
        instructor_profile,
        another_instructor_profile,
        url,
    ):
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        assert response.data["profile"]["id"] == instructor_profile.profile.id

        assert response.data["profile"]["id"] != another_instructor_profile.profile.id

        assert response.data["headline"] == instructor_profile.headline

        assert response.data["headline"] != another_instructor_profile.headline

    def test_query_parameters_cannot_change_selected_profile(
        self,
        authenticated_client,
        instructor_profile,
        another_instructor_profile,
        url,
    ):
        response = authenticated_client.get(
            url,
            {
                "id": another_instructor_profile.id,
                "profile": another_instructor_profile.profile.id,
                "user": another_instructor_profile.profile.user_id,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        assert response.data["profile"]["id"] == instructor_profile.profile.id

        assert response.data["profile"]["id"] != another_instructor_profile.profile.id

    def test_get_with_no_query_parameters_returns_own_profile(
        self,
        authenticated_client,
        instructor_profile,
        url,
    ):
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["profile"]["id"] == instructor_profile.profile.id

    def test_profile_with_minimal_data_is_retrieved_successfully(
        self,
        api_client,
        user,
        url,
    ):
        profile = Profile.objects.create(user=user)

        instructor_profile = InstructorProfile.objects.create(
            profile=profile,
        )

        api_client.force_authenticate(user=user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        assert response.data["profile"]["id"] == profile.id

        assert response.data["biography"] == instructor_profile.biography
        assert response.data["headline"] == instructor_profile.headline
        assert (
            response.data["professional_title"] == instructor_profile.professional_title
        )
        assert response.data["organization"] == instructor_profile.organization
        assert response.data["is_verified"] == instructor_profile.is_verified
        assert (
            response.data["verification_date"] == instructor_profile.verification_date
        )
        assert (
            response.data["years_of_experience"]
            == instructor_profile.years_of_experience
        )

    def test_unauthenticated_request_is_rejected(
        self,
        api_client,
        instructor_profile,
        url,
    ):
        response = api_client.get(url)

        assert response.status_code in {
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        }
