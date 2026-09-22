from datetime import datetime
from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient

from profiles.models import InstructorProfile


@pytest.mark.django_db
class TestInstructorProfileUpdateView:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def instructor_profile(self, profile):
        return InstructorProfile.objects.create(
            profile=profile,
            cover="instructors/cover/original-cover.jpg",
            biography="Original instructor biography.",
            headline="Original instructor headline.",
            professional_title="Senior Software Engineer",
            organization="Original Organization",
            is_verified=False,
            verification_date=timezone.make_aware(datetime(2026, 1, 15, 10, 30)),
            introduction_video="instructors/videos/original-video.mp4",
            resume="instructors/resumes/original-resume.pdf",
            years_of_experience=5,
        )

    @pytest.fixture
    def another_instructor_profile(self, another_profile):
        return InstructorProfile.objects.create(
            profile=another_profile,
            biography="Another instructor biography.",
            headline="Another instructor headline.",
            professional_title="Another Professional Title",
            organization="Another Organization",
            is_verified=False,
            years_of_experience=2,
        )

    @pytest.fixture
    def authenticated_client(self, api_client, test_user):
        api_client.force_authenticate(user=test_user)
        return api_client

    @pytest.fixture
    def url(self):
        return reverse("profile-api:update_instructor_profile")

    def test_authenticated_user_can_update_instructor_profile(
        self,
        authenticated_client,
        instructor_profile,
        url,
    ):
        response = authenticated_client.patch(
            url,
            {
                "headline": "Updated instructor headline",
                "biography": "Updated instructor biography.",
                "professional_title": "Lead Software Engineer",
                "organization": "Updated Organization",
                "is_verified": True,
                "years_of_experience": 10,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        instructor_profile.refresh_from_db()

        assert instructor_profile.headline == "Updated instructor headline"
        assert instructor_profile.biography == "Updated instructor biography."
        assert instructor_profile.professional_title == "Lead Software Engineer"
        assert instructor_profile.organization == "Updated Organization"
        assert instructor_profile.is_verified is True
        assert instructor_profile.years_of_experience == 10

    def test_update_returns_updated_instructor_profile(
        self,
        authenticated_client,
        instructor_profile,
        url,
    ):
        response = authenticated_client.patch(
            url,
            {
                "headline": "Updated headline",
                "organization": "Updated Organization",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        assert response.data["headline"] == "Updated headline"
        assert response.data["organization"] == "Updated Organization"

    def test_update_returns_nested_profile(
        self,
        authenticated_client,
        instructor_profile,
        test_user,
        url,
    ):
        response = authenticated_client.patch(
            url,
            {
                "headline": "Updated headline",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        assert "profile" in response.data

        profile_data = response.data["profile"]

        assert profile_data["id"] == instructor_profile.profile.id
        assert profile_data["first_name"] == test_user.first_name
        assert profile_data["last_name"] == test_user.last_name
        assert profile_data["email"] == test_user.email

    def test_update_user_username(
        self,
        authenticated_client,
        instructor_profile,
        test_user,
        url,
    ):
        original_username = test_user.username

        response = authenticated_client.patch(
            url,
            {
                "username": "updated_username",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        test_user.refresh_from_db()

        assert test_user.username == "updated_username"
        assert test_user.username != original_username

    def test_update_user_email(
        self,
        authenticated_client,
        instructor_profile,
        test_user,
        url,
    ):
        response = authenticated_client.patch(
            url,
            {
                "email": "updated@example.com",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        test_user.refresh_from_db()

        assert test_user.email == "updated@example.com"

    def test_update_profile_website(
        self,
        authenticated_client,
        instructor_profile,
        profile,
        url,
    ):
        response = authenticated_client.patch(
            url,
            {
                "website": "https://updated.example.com",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        profile.refresh_from_db()

        assert profile.website == "https://updated.example.com"

    def test_update_profile_country(
        self,
        authenticated_client,
        instructor_profile,
        profile,
        url,
    ):
        response = authenticated_client.patch(
            url,
            {
                "country": "Updated Country",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        profile.refresh_from_db()

        assert profile.country == "Updated Country"

    def test_update_profile_timezone(
        self,
        authenticated_client,
        instructor_profile,
        profile,
        url,
    ):
        response = authenticated_client.patch(
            url,
            {
                "timezone": "Asia/Baku",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        profile.refresh_from_db()

        assert profile.timezone == "Asia/Baku"

    def test_update_profile_date_of_birth(
        self,
        authenticated_client,
        instructor_profile,
        profile,
        url,
    ):
        response = authenticated_client.patch(
            url,
            {
                "date_of_birth": "1995-05-20",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        profile.refresh_from_db()

        assert str(profile.date_of_birth) == "1995-05-20"

    def test_update_profile_company(
        self,
        authenticated_client,
        instructor_profile,
        profile,
        url,
    ):
        response = authenticated_client.patch(
            url,
            {
                "company": "Updated Company",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        profile.refresh_from_db()

        assert profile.company == "Updated Company"

    def test_update_profile_job_title(
        self,
        authenticated_client,
        instructor_profile,
        profile,
        url,
    ):
        response = authenticated_client.patch(
            url,
            {
                "job_title": "Updated Job Title",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        profile.refresh_from_db()

        assert profile.job_title == "Updated Job Title"

    def test_update_verification_date(
        self,
        authenticated_client,
        instructor_profile,
        url,
    ):
        new_verification_date = timezone.make_aware(datetime(2026, 8, 20, 14, 30))

        response = authenticated_client.patch(
            url,
            {
                "verification_date": (new_verification_date.isoformat()),
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        instructor_profile.refresh_from_db()

        assert instructor_profile.verification_date == new_verification_date

    def test_update_all_instructor_profile_fields(
        self,
        authenticated_client,
        instructor_profile,
        url,
    ):
        # Arrange
        new_verification_date = timezone.make_aware(datetime(2026, 8, 20, 14, 30))

        image = Image.new("RGB", (100, 100), "white")
        image_buffer = BytesIO()
        image.save(image_buffer, format="JPEG")
        image_buffer.seek(0)

        cover = SimpleUploadedFile(
            "new-cover.jpg",
            image_buffer.getvalue(),
            content_type="image/jpeg",
        )

        resume = SimpleUploadedFile(
            "new-resume.pdf",
            b"fake-pdf-content",
            content_type="application/pdf",
        )

        original_cover_name = instructor_profile.cover.name
        original_resume_name = instructor_profile.resume.name

        # Act
        response = authenticated_client.patch(
            url,
            {
                "cover": cover,
                "biography": "Completely updated biography.",
                "headline": "Completely updated headline",
                "professional_title": "Principal Engineer",
                "organization": "New Organization",
                "is_verified": True,
                "verification_date": new_verification_date.isoformat(),
                "introduction_video": ("https://example.com/videos/new-video.mp4"),
                "resume": resume,
                "years_of_experience": 15,
            },
            format="multipart",
        )

        # Assert
        assert response.status_code == 200

        instructor_profile.refresh_from_db()

        assert instructor_profile.cover.name != original_cover_name
        assert instructor_profile.cover.name.endswith(".jpg")

        assert instructor_profile.biography == "Completely updated biography."
        assert instructor_profile.headline == "Completely updated headline"
        assert instructor_profile.professional_title == "Principal Engineer"
        assert instructor_profile.organization == "New Organization"
        assert instructor_profile.is_verified is True

        assert instructor_profile.verification_date == new_verification_date

        assert instructor_profile.introduction_video == (
            "https://example.com/videos/new-video.mp4"
        )

        assert instructor_profile.resume.name != original_resume_name
        assert instructor_profile.resume.name.endswith(".pdf")

        assert instructor_profile.years_of_experience == 15

    def test_combined_update_changes_user_profile_and_instructor_profile(
        self,
        authenticated_client,
        instructor_profile,
        test_user,
        profile,
        url,
    ):
        response = authenticated_client.patch(
            url,
            {
                "username": "new_username",
                "email": "new@example.com",
                "website": "https://new.example.com",
                "country": "New Country",
                "company": "New Company",
                "job_title": "New Job Title",
                "headline": "New Headline",
                "organization": "New Organization",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        test_user.refresh_from_db()
        profile.refresh_from_db()
        instructor_profile.refresh_from_db()

        assert test_user.username == "new_username"
        assert test_user.email == "new@example.com"

        assert profile.website == "https://new.example.com"
        assert profile.country == "New Country"
        assert profile.company == "New Company"
        assert profile.job_title == "New Job Title"

        assert instructor_profile.headline == "New Headline"
        assert instructor_profile.organization == "New Organization"

    def test_partial_update_preserves_omitted_instructor_fields(
        self,
        authenticated_client,
        instructor_profile,
        url,
    ):
        original_biography = instructor_profile.biography
        original_organization = instructor_profile.organization
        original_years = instructor_profile.years_of_experience

        response = authenticated_client.patch(
            url,
            {
                "headline": "Only headline changed",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        instructor_profile.refresh_from_db()

        assert instructor_profile.headline == "Only headline changed"
        assert instructor_profile.biography == original_biography
        assert instructor_profile.organization == original_organization
        assert instructor_profile.years_of_experience == original_years

    def test_empty_patch_does_not_change_existing_values(
        self,
        authenticated_client,
        instructor_profile,
        profile,
        test_user,
        url,
    ):
        original_username = test_user.username
        original_email = test_user.email
        original_website = profile.website
        original_headline = instructor_profile.headline
        original_organization = instructor_profile.organization

        response = authenticated_client.patch(
            url,
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        test_user.refresh_from_db()
        profile.refresh_from_db()
        instructor_profile.refresh_from_db()

        assert test_user.username == original_username
        assert test_user.email == original_email
        assert profile.website == original_website
        assert instructor_profile.headline == original_headline
        assert instructor_profile.organization == original_organization

    def test_invalid_email_returns_400(
        self,
        authenticated_client,
        instructor_profile,
        test_user,
        url,
    ):
        original_email = test_user.email

        response = authenticated_client.patch(
            url,
            {
                "email": "not-an-email",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

        test_user.refresh_from_db()

        assert test_user.email == original_email

    def test_duplicate_username_returns_400(
        self,
        authenticated_client,
        instructor_profile,
        test_user,
        another_user,
        url,
    ):
        original_username = test_user.username

        response = authenticated_client.patch(
            url,
            {
                "username": another_user.username,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "username" in response.data

        test_user.refresh_from_db()

        assert test_user.username == original_username

    def test_duplicate_email_returns_400(
        self,
        authenticated_client,
        instructor_profile,
        test_user,
        another_user,
        url,
    ):
        original_email = test_user.email

        response = authenticated_client.patch(
            url,
            {
                "email": another_user.email,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

        test_user.refresh_from_db()

        assert test_user.email == original_email

    def test_invalid_website_returns_400(
        self,
        authenticated_client,
        instructor_profile,
        profile,
        url,
    ):
        original_website = profile.website

        response = authenticated_client.patch(
            url,
            {
                "website": "invalid-url",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "website" in response.data

        profile.refresh_from_db()

        assert profile.website == original_website

    def test_invalid_instructor_profile_data_returns_400(
        self,
        authenticated_client,
        instructor_profile,
        url,
    ):
        original_headline = instructor_profile.headline

        response = authenticated_client.patch(
            url,
            {
                "years_of_experience": -1,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "years_of_experience" in response.data

        instructor_profile.refresh_from_db()

        assert instructor_profile.headline == original_headline

    def test_invalid_verification_date_returns_400(
        self,
        authenticated_client,
        instructor_profile,
        url,
    ):
        original_date = instructor_profile.verification_date

        response = authenticated_client.patch(
            url,
            {
                "verification_date": "not-a-datetime",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "verification_date" in response.data

        instructor_profile.refresh_from_db()

        assert instructor_profile.verification_date == original_date

    def test_invalid_user_data_does_not_update_instructor_profile(
        self,
        authenticated_client,
        instructor_profile,
        url,
    ):
        original_headline = instructor_profile.headline

        response = authenticated_client.patch(
            url,
            {
                "email": "invalid-email",
                "headline": "Should not be saved",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

        instructor_profile.refresh_from_db()

        assert instructor_profile.headline == original_headline

    def test_invalid_profile_data_does_not_update_user(
        self,
        authenticated_client,
        instructor_profile,
        profile,
        test_user,
        url,
    ):
        original_username = test_user.username
        original_website = profile.website

        response = authenticated_client.patch(
            url,
            {
                "username": "should_not_be_saved",
                "website": "invalid-url",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "website" in response.data

        test_user.refresh_from_db()
        profile.refresh_from_db()

        assert test_user.username == original_username
        assert profile.website == original_website

    def test_invalid_profile_data_does_not_update_instructor_profile(
        self,
        authenticated_client,
        instructor_profile,
        profile,
        url,
    ):
        original_headline = instructor_profile.headline
        original_website = profile.website

        response = authenticated_client.patch(
            url,
            {
                "headline": "Should not be saved",
                "website": "invalid-url",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "website" in response.data

        profile.refresh_from_db()
        instructor_profile.refresh_from_db()

        assert profile.website == original_website
        assert instructor_profile.headline == original_headline

    def test_read_only_first_name_and_last_name_are_not_changed(
        self,
        authenticated_client,
        instructor_profile,
        test_user,
        url,
    ):
        original_first_name = test_user.first_name
        original_last_name = test_user.last_name

        response = authenticated_client.patch(
            url,
            {
                "first_name": "Attempted change",
                "last_name": "Attempted change",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        test_user.refresh_from_db()

        assert test_user.first_name == original_first_name
        assert test_user.last_name == original_last_name

    def test_unknown_fields_are_ignored(
        self,
        authenticated_client,
        instructor_profile,
        url,
    ):
        response = authenticated_client.patch(
            url,
            {
                "headline": "Valid headline",
                "unknown_field": "Unexpected value",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        instructor_profile.refresh_from_db()

        assert instructor_profile.headline == "Valid headline"
        assert "unknown_field" not in response.data

    def test_update_does_not_modify_another_users_profile(
        self,
        authenticated_client,
        instructor_profile,
        another_instructor_profile,
        url,
    ):
        original_headline = another_instructor_profile.headline

        response = authenticated_client.patch(
            url,
            {
                "headline": "Updated own headline",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        another_instructor_profile.refresh_from_db()

        assert another_instructor_profile.headline == original_headline

    def test_update_targets_authenticated_users_instructor_profile(
        self,
        authenticated_client,
        instructor_profile,
        another_instructor_profile,
        url,
    ):
        response = authenticated_client.patch(
            url,
            {
                "headline": "Authenticated user's headline",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        instructor_profile.refresh_from_db()
        another_instructor_profile.refresh_from_db()

        assert instructor_profile.headline == "Authenticated user's headline"
        assert another_instructor_profile.headline == "Another instructor headline."

    def test_query_parameters_cannot_change_target_profile(
        self,
        authenticated_client,
        instructor_profile,
        another_instructor_profile,
        url,
    ):
        # Arrange
        url_with_query_params = (
            f"{url}"
            f"?id={another_instructor_profile.id}"
            f"&profile={another_instructor_profile.profile.id}"
        )

        # Act
        response = authenticated_client.patch(
            url_with_query_params,
            {
                "headline": "Authenticated user's headline",
            },
            format="json",
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        instructor_profile.refresh_from_db()
        another_instructor_profile.refresh_from_db()

        assert instructor_profile.headline == "Authenticated user's headline"
        assert another_instructor_profile.headline == "Another instructor headline."

    def test_unauthenticated_request_is_rejected(
        self,
        api_client,
        instructor_profile,
        url,
    ):
        response = api_client.patch(
            url,
            {
                "headline": "Unauthorized update",
            },
            format="json",
        )

        assert response.status_code in {
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        }

    def test_get_method_is_not_supported(
        self,
        authenticated_client,
        instructor_profile,
        url,
    ):
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_delete_method_is_not_supported(
        self,
        authenticated_client,
        instructor_profile,
        url,
    ):
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
