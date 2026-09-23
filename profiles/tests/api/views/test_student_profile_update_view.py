import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from profiles.models import Profile, StudentProfile


@pytest.mark.django_db
class TestStudentProfileUpdateView:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def user(self, django_user_model):
        return django_user_model.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="TestPassword123!",
        )

    @pytest.fixture
    def student_profile(self, user):
        profile = Profile.objects.create(
            user=user,
            website="https://example.com",
            country="Test Country",
            timezone="UTC",
            company="Test Company",
            job_title="Test Job",
        )

        return StudentProfile.objects.create(
            profile=profile,
            cover="students/cover/old-cover.jpg",
            biography="Original biography.",
            headline="Original headline",
        )

    @pytest.fixture
    def authenticated_client(self, api_client, user):
        api_client.force_authenticate(user=user)
        return api_client

    @pytest.fixture
    def url(self):
        return reverse("profile-api:update_student_profile")

    # ------------------------------------------------------------------
    # Successful updates
    # ------------------------------------------------------------------

    def test_update_student_profile_updates_student_profile_fields(
        self,
        authenticated_client,
        student_profile,
        url,
    ):
        data = {
            "biography": "Updated biography.",
            "headline": "Updated headline",
        }

        response = authenticated_client.put(url, data, format="multipart")

        assert response.status_code == status.HTTP_200_OK

        student_profile.refresh_from_db()

        assert student_profile.biography == "Updated biography."
        assert student_profile.headline == "Updated headline"

    def test_update_student_profile_updates_user_fields(
        self,
        authenticated_client,
        student_profile,
        user,
        url,
    ):
        data = {
            "username": "updated_user",
            "email": "updated_user@example.com",
        }

        response = authenticated_client.put(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK

        user.refresh_from_db()

        assert user.username == "updated_user"
        assert user.email == "updated_user@example.com"

    def test_update_student_profile_updates_profile_fields(
        self,
        authenticated_client,
        student_profile,
        url,
    ):
        data = {
            "website": "https://updated.example.com",
            "country": "Updated Country",
            "timezone": "Europe/Berlin",
            "company": "Updated Company",
            "job_title": "Updated Job",
            "date_of_birth": "2000-01-15",
        }

        response = authenticated_client.put(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK

        student_profile.profile.refresh_from_db()

        assert student_profile.profile.website == "https://updated.example.com"
        assert student_profile.profile.country == "Updated Country"
        assert student_profile.profile.timezone == "Europe/Berlin"
        assert student_profile.profile.company == "Updated Company"
        assert student_profile.profile.job_title == "Updated Job"

    def test_update_student_profile_can_update_all_supported_models_in_one_request(
        self,
        authenticated_client,
        student_profile,
        user,
        url,
    ):
        data = {
            "username": "combined_update_user",
            "email": "combined_update@example.com",
            "website": "https://combined.example.com",
            "country": "Combined Country",
            "timezone": "Asia/Tokyo",
            "company": "Combined Company",
            "job_title": "Combined Job",
            "date_of_birth": "1998-06-20",
            "biography": "Combined biography.",
            "headline": "Combined headline",
        }

        response = authenticated_client.put(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK

        user.refresh_from_db()
        student_profile.refresh_from_db()
        student_profile.profile.refresh_from_db()

        assert user.username == "combined_update_user"
        assert user.email == "combined_update@example.com"

        assert student_profile.profile.website == "https://combined.example.com"
        assert student_profile.profile.country == "Combined Country"
        assert student_profile.profile.timezone == "Asia/Tokyo"
        assert student_profile.profile.company == "Combined Company"
        assert student_profile.profile.job_title == "Combined Job"
        assert str(student_profile.profile.date_of_birth) == "1998-06-20"

        assert student_profile.biography == "Combined biography."
        assert student_profile.headline == "Combined headline"

    # ------------------------------------------------------------------
    # Partial-update behavior
    # ------------------------------------------------------------------

    def test_update_student_profile_allows_partial_update(
        self,
        authenticated_client,
        student_profile,
        user,
        url,
    ):
        original_email = user.email
        original_website = student_profile.profile.website
        original_headline = student_profile.headline

        data = {
            "headline": "Only headline changed.",
        }

        response = authenticated_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK

        user.refresh_from_db()
        student_profile.refresh_from_db()
        student_profile.profile.refresh_from_db()

        assert student_profile.headline == "Only headline changed."

        assert user.email == original_email
        assert student_profile.profile.website == original_website
        assert student_profile.biography == student_profile.biography
        assert student_profile.headline != original_headline

    def test_partial_update_of_user_does_not_clear_profile_fields(
        self,
        authenticated_client,
        student_profile,
        user,
        url,
    ):
        original_website = student_profile.profile.website
        original_biography = student_profile.biography

        response = authenticated_client.patch(
            url,
            {"username": "new_username"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        user.refresh_from_db()
        student_profile.refresh_from_db()
        student_profile.profile.refresh_from_db()

        assert user.username == "new_username"
        assert student_profile.profile.website == original_website
        assert student_profile.biography == original_biography

    def test_empty_request_is_successful_without_clearing_existing_values(
        self,
        authenticated_client,
        student_profile,
        user,
        url,
    ):
        original_username = user.username
        original_email = user.email
        original_website = student_profile.profile.website
        original_biography = student_profile.biography
        original_headline = student_profile.headline

        response = authenticated_client.patch(
            url,
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        user.refresh_from_db()
        student_profile.refresh_from_db()
        student_profile.profile.refresh_from_db()

        assert user.username == original_username
        assert user.email == original_email
        assert student_profile.profile.website == original_website
        assert student_profile.biography == original_biography
        assert student_profile.headline == original_headline

    # ------------------------------------------------------------------
    # Response behavior
    # ------------------------------------------------------------------

    def test_update_returns_student_profile_serializer_representation(
        self,
        authenticated_client,
        student_profile,
        url,
    ):
        response = authenticated_client.patch(
            url,
            {
                "headline": "Updated response headline",
                "biography": "Updated response biography",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        assert set(response.data) == {
            "profile",
            "cover",
            "biography",
            "headline",
        }

        assert response.data["headline"] == "Updated response headline"
        assert response.data["biography"] == "Updated response biography"

    def test_update_response_contains_nested_profile_data(
        self,
        authenticated_client,
        student_profile,
        user,
        url,
    ):
        response = authenticated_client.patch(
            url,
            {
                "username": "response_user",
                "email": "response@example.com",
                "website": "https://response.example.com",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        profile_data = response.data["profile"]

        assert profile_data["first_name"] == user.first_name
        assert profile_data["last_name"] == user.last_name
        assert profile_data["email"] == "response@example.com"
        assert profile_data["website"] == "https://response.example.com"

    def test_response_reflects_updated_user_data(
        self,
        authenticated_client,
        student_profile,
        url,
    ):
        response = authenticated_client.patch(
            url,
            {
                "username": "updated_response_user",
                "email": "updated_response@example.com",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        assert response.data["profile"]["email"] == "updated_response@example.com"

    # ------------------------------------------------------------------
    # Field ownership / serializer boundaries
    # ------------------------------------------------------------------

    def test_user_fields_are_not_written_to_student_profile(
        self,
        authenticated_client,
        student_profile,
        url,
    ):
        original_headline = student_profile.headline
        original_biography = student_profile.biography

        response = authenticated_client.patch(
            url,
            {
                "username": "boundary_user",
                "email": "boundary@example.com",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        student_profile.refresh_from_db()

        assert student_profile.headline == original_headline
        assert student_profile.biography == original_biography

    def test_profile_fields_are_not_written_to_student_profile(
        self,
        authenticated_client,
        student_profile,
        url,
    ):
        original_headline = student_profile.headline
        original_biography = student_profile.biography

        response = authenticated_client.patch(
            url,
            {
                "website": "https://boundary.example.com",
                "company": "Boundary Company",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        student_profile.refresh_from_db()

        assert student_profile.headline == original_headline
        assert student_profile.biography == original_biography

    def test_student_profile_fields_are_not_written_to_user(
        self,
        authenticated_client,
        student_profile,
        user,
        url,
    ):
        original_username = user.username
        original_email = user.email

        response = authenticated_client.patch(
            url,
            {
                "headline": "Student headline",
                "biography": "Student biography",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        user.refresh_from_db()

        assert user.username == original_username
        assert user.email == original_email

    # ------------------------------------------------------------------
    # Validation errors
    # ------------------------------------------------------------------

    def test_invalid_email_returns_400_and_does_not_update_any_model(
        self,
        authenticated_client,
        student_profile,
        user,
        url,
    ):
        original_username = user.username
        original_email = user.email
        original_website = student_profile.profile.website
        original_headline = student_profile.headline

        response = authenticated_client.patch(
            url,
            {
                "email": "not-an-email",
                "website": "https://new.example.com",
                "headline": "New headline",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

        user.refresh_from_db()
        student_profile.refresh_from_db()
        student_profile.profile.refresh_from_db()

        assert user.username == original_username
        assert user.email == original_email
        assert student_profile.profile.website == original_website
        assert student_profile.headline == original_headline

    def test_duplicate_email_returns_400_and_does_not_update_other_models(
        self,
        authenticated_client,
        student_profile,
        user,
        django_user_model,
        url,
    ):
        django_user_model.objects.create_user(
            username="existing_user",
            email="existing@example.com",
            password="TestPassword123!",
        )

        original_username = user.username
        original_website = student_profile.profile.website
        original_headline = student_profile.headline

        response = authenticated_client.patch(
            url,
            {
                "email": "existing@example.com",
                "website": "https://should-not-save.example.com",
                "headline": "Should not save",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

        user.refresh_from_db()
        student_profile.refresh_from_db()
        student_profile.profile.refresh_from_db()

        assert user.username == original_username
        assert user.email != "existing@example.com"
        assert student_profile.profile.website == original_website
        assert student_profile.headline == original_headline

    def test_duplicate_username_returns_400_and_does_not_update_other_models(
        self,
        authenticated_client,
        student_profile,
        user,
        django_user_model,
        url,
    ):
        django_user_model.objects.create_user(
            username="existing_user",
            email="existing@example.com",
            password="TestPassword123!",
        )

        original_email = user.email
        original_website = student_profile.profile.website
        original_headline = student_profile.headline

        response = authenticated_client.patch(
            url,
            {
                "username": "existing_user",
                "website": "https://should-not-save.example.com",
                "headline": "Should not save",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "username" in response.data

        user.refresh_from_db()
        student_profile.refresh_from_db()
        student_profile.profile.refresh_from_db()

        assert user.username != "existing_user"
        assert user.email == original_email
        assert student_profile.profile.website == original_website
        assert student_profile.headline == original_headline

    def test_unknown_fields_are_ignored(
        self,
        authenticated_client,
        student_profile,
        user,
        url,
    ):
        original_username = user.username
        original_website = student_profile.profile.website
        original_headline = student_profile.headline

        response = authenticated_client.patch(
            url,
            {
                "unknown_field": "value",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        user.refresh_from_db()
        student_profile.refresh_from_db()
        student_profile.profile.refresh_from_db()

        assert user.username == original_username
        assert student_profile.profile.website == original_website
        assert student_profile.headline == original_headline

        assert "unknown_field" not in response.data

    def test_headline_longer_than_model_max_length_returns_400(
        self,
        authenticated_client,
        student_profile,
        url,
    ):
        response = authenticated_client.patch(
            url,
            {"headline": "x" * 256},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "headline" in response.data

        student_profile.refresh_from_db()

        assert student_profile.headline == "Original headline"

    # ------------------------------------------------------------------
    # Security / ownership
    # ------------------------------------------------------------------

    def test_authenticated_user_can_only_update_their_own_student_profile(
        self,
        api_client,
        student_profile,
        django_user_model,
        url,
    ):
        other_user = django_user_model.objects.create_user(
            username="test_other_user",
            email="test_other_user@example.com",
            password="TestPassword123!",
        )

        other_profile = Profile.objects.create(user=other_user)

        other_student_profile = StudentProfile.objects.create(
            profile=other_profile,
            biography="Other user's biography.",
            headline="Other user's headline",
        )

        api_client.force_authenticate(user=other_user)

        response = api_client.patch(
            url,
            {
                "headline": "Attempted unauthorized update",
                "biography": "Attempted unauthorized biography",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        other_student_profile.refresh_from_db()
        student_profile.refresh_from_db()

        assert other_student_profile.headline == "Attempted unauthorized update"
        assert student_profile.headline == "Original headline"
        assert student_profile.biography == "Original biography."

    def test_user_cannot_update_another_users_student_profile_by_submitting_profile_id(
        self,
        api_client,
        student_profile,
        django_user_model,
        url,
    ):
        other_user = django_user_model.objects.create_user(
            username="test_other_user",
            email="test_other_user@example.com",
            password="TestPassword123!",
        )

        other_profile = Profile.objects.create(user=other_user)

        other_student_profile = StudentProfile.objects.create(
            profile=other_profile,
            biography="Other biography.",
            headline="Other headline",
        )

        api_client.force_authenticate(user=other_user)

        response = api_client.patch(
            url,
            {
                "profile": student_profile.profile.pk,
                "headline": "Malicious update",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        student_profile.refresh_from_db()
        other_student_profile.refresh_from_db()

        assert student_profile.headline == "Original headline"
        assert other_student_profile.headline == "Malicious update"

    # ------------------------------------------------------------------
    # Invalid field handling
    # ------------------------------------------------------------------

    def test_read_only_profile_fields_are_ignored(
        self,
        authenticated_client,
        student_profile,
        user,
        url,
    ):
        original_first_name = user.first_name
        original_last_name = user.last_name

        response = authenticated_client.patch(
            url,
            {
                "first_name": "Attempted change",
                "last_name": "Attempted change",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        user.refresh_from_db()

        assert user.first_name == original_first_name
        assert user.last_name == original_last_name

        assert response.data["profile"]["first_name"] == original_first_name
        assert response.data["profile"]["last_name"] == original_last_name

    # ------------------------------------------------------------------
    # get_object behavior
    # ------------------------------------------------------------------

    def test_update_targets_student_profile_belonging_to_authenticated_user(
        self,
        authenticated_client,
        student_profile,
        user,
        django_user_model,
        url,
    ):
        other_user = django_user_model.objects.create_user(
            username="test_other_user",
            email="test_other_user@example.com",
            password="TestPassword123!",
        )

        other_profile = Profile.objects.create(user=other_user)

        other_student_profile = StudentProfile.objects.create(
            profile=other_profile,
            biography="Other biography.",
            headline="Other headline",
        )

        response = authenticated_client.patch(
            url,
            {"headline": "Authenticated user's headline"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        student_profile.refresh_from_db()
        other_student_profile.refresh_from_db()

        assert student_profile.profile.user_id == user.pk
        assert student_profile.headline == "Authenticated user's headline"
        assert other_student_profile.headline == "Other headline"

    # ------------------------------------------------------------------
    # Transaction/sequencing regression protection
    # ------------------------------------------------------------------

    def test_invalid_profile_data_does_not_save_user_update(
        self,
        authenticated_client,
        student_profile,
        user,
        url,
    ):
        original_username = user.username
        original_website = student_profile.profile.website

        response = authenticated_client.patch(
            url,
            {
                "username": "should_not_be_saved",
                "website": "not-a-valid-url",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        user.refresh_from_db()
        student_profile.profile.refresh_from_db()

        assert user.username == original_username
        assert student_profile.profile.website == original_website

    def test_invalid_student_profile_data_does_not_save_user_update(
        self,
        authenticated_client,
        student_profile,
        user,
        url,
    ):
        original_username = user.username
        original_biography = student_profile.biography

        # StudentProfileSerializer is validated first in update().
        # An invalid headline therefore prevents perform_update() from
        # updating User or Profile.
        response = authenticated_client.patch(
            url,
            {
                "username": "should_not_be_saved",
                "headline": "x" * 256,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        user.refresh_from_db()
        student_profile.refresh_from_db()

        assert user.username == original_username
        assert student_profile.biography == original_biography

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def test_unauthenticated_request_is_rejected(
        self,
        api_client,
        url,
    ):
        response = api_client.patch(
            url,
            {"headline": "Unauthenticated update"},
            format="json",
        )

        assert response.status_code in {
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        }
