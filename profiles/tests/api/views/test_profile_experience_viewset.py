from datetime import date

from django.urls import reverse
from rest_framework import status

from profiles.models import Experience


class TestProfileExperienceViewSet:
    def test_create_experience_successfully(
        self,
        authenticated_client,
        profile,
    ):
        url = reverse("profile-api:experience-list")
        data = {
            "company": "Acme",
            "position": "Software Engineer",
            "location": "Remote",
            "description": "Backend development.",
            "start_date": "2024-01-01",
            "end_date": "2025-01-01",
        }

        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        experience = Experience.objects.get()

        assert experience.profile == profile
        assert experience.company == "Acme"
        assert experience.position == "Software Engineer"
        assert experience.location == "Remote"
        assert experience.description == "Backend development."
        assert experience.start_date == date(2024, 1, 1)
        assert experience.end_date == date(2025, 1, 1)

        assert response.data["id"] == experience.id
        assert response.data["company"] == "Acme"
        assert response.data["position"] == "Software Engineer"
        assert response.data["location"] == "Remote"
        assert response.data["description"] == "Backend development."
        assert response.data["start_date"] == "2024-01-01"
        assert response.data["end_date"] == "2025-01-01"

    def test_create_experience_with_only_required_fields(
        self,
        authenticated_client,
        profile,
    ):
        url = reverse("profile-api:experience-list")
        data = {
            "company": "Acme",
            "position": "Developer",
        }

        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        experience = Experience.objects.get()

        assert experience.profile == profile
        assert experience.company == "Acme"
        assert experience.position == "Developer"
        assert experience.location == ""
        assert experience.description == ""
        assert experience.start_date is None
        assert experience.end_date is None

    def test_create_experience_allows_null_dates(
        self,
        authenticated_client,
        profile,
    ):
        url = reverse("profile-api:experience-list")
        data = {
            "company": "Acme",
            "position": "Developer",
            "location": "Remote",
            "description": "Current role.",
            "start_date": None,
            "end_date": None,
        }

        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        experience = Experience.objects.get()

        assert experience.start_date is None
        assert experience.end_date is None

    def test_create_experience_allows_current_date_without_end_date(
        self,
        authenticated_client,
        profile,
    ):
        url = reverse("profile-api:experience-list")
        data = {
            "company": "Acme",
            "position": "Developer",
            "start_date": "2024-01-01",
            "end_date": None,
        }

        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        experience = Experience.objects.get()

        assert experience.start_date == date(2024, 1, 1)
        assert experience.end_date is None

    def test_create_experience_requires_company(
        self,
        authenticated_client,
        profile,
    ):
        url = reverse("profile-api:experience-list")
        data = {
            "position": "Developer",
        }

        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "company" in response.data
        assert not Experience.objects.exists()

    def test_create_experience_requires_position(
        self,
        authenticated_client,
        profile,
    ):
        url = reverse("profile-api:experience-list")
        data = {
            "company": "Acme",
        }

        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "position" in response.data
        assert not Experience.objects.exists()

    def test_create_experience_rejects_company_longer_than_max_length(
        self,
        authenticated_client,
        profile,
    ):
        url = reverse("profile-api:experience-list")
        data = {
            "company": "a" * 256,
            "position": "Developer",
        }

        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "company" in response.data
        assert not Experience.objects.exists()

    def test_create_experience_accepts_company_at_max_length(
        self,
        authenticated_client,
        profile,
    ):
        url = reverse("profile-api:experience-list")
        data = {
            "company": "a" * 255,
            "position": "Developer",
        }

        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        experience = Experience.objects.get()

        assert len(experience.company) == 255

    def test_create_experience_rejects_position_longer_than_max_length(
        self,
        authenticated_client,
        profile,
    ):
        url = reverse("profile-api:experience-list")
        data = {
            "company": "Acme",
            "position": "a" * 256,
        }

        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "position" in response.data
        assert not Experience.objects.exists()

    def test_create_experience_accepts_position_at_max_length(
        self,
        authenticated_client,
        profile,
    ):
        url = reverse("profile-api:experience-list")
        data = {
            "company": "Acme",
            "position": "a" * 255,
        }

        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        experience = Experience.objects.get()

        assert len(experience.position) == 255

    def test_create_experience_rejects_location_longer_than_max_length(
        self,
        authenticated_client,
        profile,
    ):
        url = reverse("profile-api:experience-list")
        data = {
            "company": "Acme",
            "position": "Developer",
            "location": "a" * 251,
        }

        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "location" in response.data
        assert not Experience.objects.exists()

    def test_create_experience_accepts_location_at_max_length(
        self,
        authenticated_client,
        profile,
    ):
        url = reverse("profile-api:experience-list")
        data = {
            "company": "Acme",
            "position": "Developer",
            "location": "a" * 250,
        }

        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        experience = Experience.objects.get()

        assert len(experience.location) == 250

    def test_create_experience_rejects_invalid_start_date(
        self,
        authenticated_client,
        profile,
    ):
        url = reverse("profile-api:experience-list")
        data = {
            "company": "Acme",
            "position": "Developer",
            "start_date": "not-a-date",
        }

        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "start_date" in response.data
        assert not Experience.objects.exists()

    def test_create_experience_rejects_invalid_end_date(
        self,
        authenticated_client,
        profile,
    ):
        url = reverse("profile-api:experience-list")
        data = {
            "company": "Acme",
            "position": "Developer",
            "end_date": "not-a-date",
        }

        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "end_date" in response.data
        assert not Experience.objects.exists()

    def test_create_experience_accepts_equal_start_and_end_dates(
        self,
        authenticated_client,
        profile,
    ):
        url = reverse("profile-api:experience-list")
        data = {
            "company": "Acme",
            "position": "Developer",
            "start_date": "2025-01-01",
            "end_date": "2025-01-01",
        }

        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        experience = Experience.objects.get()

        assert experience.start_date == experience.end_date

    def test_create_experience_rejects_end_date_before_start_date(
        self,
        authenticated_client,
        profile,
    ):
        url = reverse("profile-api:experience-list")
        data = {
            "company": "Acme",
            "position": "Developer",
            "start_date": "2025-01-01",
            "end_date": "2024-01-01",
        }

        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "end_date" in response.data
        assert not Experience.objects.exists()

    def test_create_experience_cannot_assign_another_users_profile(
        self,
        authenticated_client,
        profile,
        another_profile,
    ):
        url = reverse("profile-api:experience-list")
        data = {
            "company": "Acme",
            "position": "Developer",
            "profile": another_profile.id,
        }

        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        experience = Experience.objects.get()

        assert experience.profile == profile
        assert experience.profile != another_profile

    def test_create_experience_ignores_is_current_field(
        self,
        authenticated_client,
        profile,
    ):
        url = reverse("profile-api:experience-list")
        data = {
            "company": "Acme",
            "position": "Developer",
            "is_current": True,
        }

        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        experience = Experience.objects.get()

        assert experience.is_current is False
        assert "is_current" not in response.data

    def test_create_experience_does_not_allow_unknown_fields_to_change_model(
        self,
        authenticated_client,
        profile,
    ):
        url = reverse("profile-api:experience-list")
        data = {
            "company": "Acme",
            "position": "Developer",
            "unexpected_field": "unexpected value",
        }

        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        experience = Experience.objects.get()

        assert experience.company == "Acme"
        assert experience.position == "Developer"
        assert not hasattr(experience, "unexpected_field")

    def test_update_experience_successfully(
        self,
        authenticated_client,
        profile,
    ):
        experience = Experience.objects.create(
            profile=profile,
            company="Old Company",
            position="Old Position",
            location="Old Location",
            description="Old description",
            start_date=date(2023, 1, 1),
            end_date=date(2024, 1, 1),
        )

        url = reverse(
            "profile-api:experience-detail",
            kwargs={"pk": experience.pk},
        )
        data = {
            "company": "New Company",
            "position": "New Position",
            "location": "New Location",
            "description": "New description",
            "start_date": "2024-01-01",
            "end_date": "2025-01-01",
        }

        response = authenticated_client.put(
            url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        experience.refresh_from_db()

        assert experience.company == "New Company"
        assert experience.position == "New Position"
        assert experience.location == "New Location"
        assert experience.description == "New description"
        assert experience.start_date == date(2024, 1, 1)
        assert experience.end_date == date(2025, 1, 1)
        assert experience.profile == profile

    def test_update_experience_returns_updated_representation(
        self,
        authenticated_client,
        profile,
    ):
        experience = Experience.objects.create(
            profile=profile,
            company="Old Company",
            position="Developer",
        )

        url = reverse(
            "profile-api:experience-detail",
            kwargs={"pk": experience.pk},
        )

        response = authenticated_client.patch(
            url,
            {
                "company": "New Company",
                "position": "Senior Developer",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == experience.id
        assert response.data["company"] == "New Company"
        assert response.data["position"] == "Senior Developer"

    def test_partial_update_preserves_omitted_fields(
        self,
        authenticated_client,
        profile,
    ):
        experience = Experience.objects.create(
            profile=profile,
            company="Acme",
            position="Developer",
            location="Remote",
            description="Original description",
            start_date=date(2023, 1, 1),
            end_date=date(2024, 1, 1),
        )

        url = reverse(
            "profile-api:experience-detail",
            kwargs={"pk": experience.pk},
        )

        response = authenticated_client.patch(
            url,
            {"position": "Senior Developer"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        experience.refresh_from_db()

        assert experience.position == "Senior Developer"
        assert experience.company == "Acme"
        assert experience.location == "Remote"
        assert experience.description == "Original description"
        assert experience.start_date == date(2023, 1, 1)
        assert experience.end_date == date(2024, 1, 1)

    def test_partial_update_can_clear_optional_string_fields(
        self,
        authenticated_client,
        profile,
    ):
        experience = Experience.objects.create(
            profile=profile,
            company="Acme",
            position="Developer",
            location="Remote",
            description="Some description",
        )

        url = reverse(
            "profile-api:experience-detail",
            kwargs={"pk": experience.pk},
        )

        response = authenticated_client.patch(
            url,
            {
                "location": "",
                "description": "",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        experience.refresh_from_db()

        assert experience.location == ""
        assert experience.description == ""

    def test_partial_update_can_clear_dates(
        self,
        authenticated_client,
        profile,
    ):
        experience = Experience.objects.create(
            profile=profile,
            company="Acme",
            position="Developer",
            start_date=date(2023, 1, 1),
            end_date=date(2024, 1, 1),
        )

        url = reverse(
            "profile-api:experience-detail",
            kwargs={"pk": experience.pk},
        )

        response = authenticated_client.patch(
            url,
            {
                "start_date": None,
                "end_date": None,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        experience.refresh_from_db()

        assert experience.start_date is None
        assert experience.end_date is None

    def test_update_experience_accepts_equal_dates(
        self,
        authenticated_client,
        profile,
    ):
        experience = Experience.objects.create(
            profile=profile,
            company="Acme",
            position="Developer",
            start_date=date(2023, 1, 1),
            end_date=date(2024, 1, 1),
        )

        url = reverse(
            "profile-api:experience-detail",
            kwargs={"pk": experience.pk},
        )

        response = authenticated_client.patch(
            url,
            {
                "start_date": "2025-01-01",
                "end_date": "2025-01-01",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        experience.refresh_from_db()

        assert experience.start_date == date(2025, 1, 1)
        assert experience.end_date == date(2025, 1, 1)

    def test_update_experience_rejects_end_date_before_start_date(
        self,
        authenticated_client,
        profile,
    ):
        experience = Experience.objects.create(
            profile=profile,
            company="Acme",
            position="Developer",
            start_date=date(2023, 1, 1),
            end_date=date(2024, 1, 1),
        )

        url = reverse(
            "profile-api:experience-detail",
            kwargs={"pk": experience.pk},
        )

        response = authenticated_client.patch(
            url,
            {
                "start_date": "2025-01-01",
                "end_date": "2024-01-01",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        experience.refresh_from_db()

        assert experience.start_date == date(2023, 1, 1)
        assert experience.end_date == date(2024, 1, 1)

    def test_update_experience_rejects_invalid_start_date(
        self,
        authenticated_client,
        profile,
    ):
        experience = Experience.objects.create(
            profile=profile,
            company="Acme",
            position="Developer",
        )

        url = reverse(
            "profile-api:experience-detail",
            kwargs={"pk": experience.pk},
        )

        response = authenticated_client.patch(
            url,
            {"start_date": "invalid-date"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "start_date" in response.data

    def test_update_experience_rejects_invalid_end_date(
        self,
        authenticated_client,
        profile,
    ):
        experience = Experience.objects.create(
            profile=profile,
            company="Acme",
            position="Developer",
        )

        url = reverse(
            "profile-api:experience-detail",
            kwargs={"pk": experience.pk},
        )

        response = authenticated_client.patch(
            url,
            {"end_date": "invalid-date"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "end_date" in response.data

    def test_update_experience_cannot_change_profile(
        self,
        authenticated_client,
        profile,
        another_profile,
    ):
        experience = Experience.objects.create(
            profile=profile,
            company="Acme",
            position="Developer",
        )

        url = reverse(
            "profile-api:experience-detail",
            kwargs={"pk": experience.pk},
        )

        response = authenticated_client.patch(
            url,
            {
                "position": "Senior Developer",
                "profile": another_profile.id,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        experience.refresh_from_db()

        assert experience.position == "Senior Developer"
        assert experience.profile == profile
        assert experience.profile != another_profile

    def test_update_experience_cannot_change_is_current(
        self,
        authenticated_client,
        profile,
    ):
        experience = Experience.objects.create(
            profile=profile,
            company="Acme",
            position="Developer",
        )

        assert experience.is_current is False

        url = reverse(
            "profile-api:experience-detail",
            kwargs={"pk": experience.pk},
        )

        response = authenticated_client.patch(
            url,
            {"is_current": True},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        experience.refresh_from_db()

        assert experience.is_current is False
        assert "is_current" not in response.data

    def test_update_cannot_access_another_users_experience(
        self,
        authenticated_client,
        profile,
        another_user,
        another_profile,
    ):
        experience = Experience.objects.create(
            profile=profile,
            company="Acme",
            position="Developer",
        )

        authenticated_client.force_authenticate(user=another_user)

        url = reverse(
            "profile-api:experience-detail",
            kwargs={"pk": experience.pk},
        )

        response = authenticated_client.patch(
            url,
            {"position": "Unauthorized Update"},
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

        experience.refresh_from_db()

        assert experience.position == "Developer"
        assert experience.profile == profile

    def test_update_own_experience_does_not_modify_another_users_experience(
        self,
        authenticated_client,
        profile,
        another_profile,
    ):
        own_experience = Experience.objects.create(
            profile=profile,
            company="Own Company",
            position="Developer",
        )
        another_experience = Experience.objects.create(
            profile=another_profile,
            company="Another Company",
            position="Developer",
        )

        url = reverse(
            "profile-api:experience-detail",
            kwargs={"pk": own_experience.pk},
        )

        response = authenticated_client.patch(
            url,
            {"company": "Updated Own Company"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        own_experience.refresh_from_db()
        another_experience.refresh_from_db()

        assert own_experience.company == "Updated Own Company"
        assert another_experience.company == "Another Company"

    def test_put_updates_experience(
        self,
        authenticated_client,
        profile,
    ):
        experience = Experience.objects.create(
            profile=profile,
            company="Old Company",
            position="Old Position",
            location="Old Location",
            description="Old description",
            start_date=date(2023, 1, 1),
            end_date=date(2024, 1, 1),
        )

        url = reverse(
            "profile-api:experience-detail",
            kwargs={"pk": experience.pk},
        )

        response = authenticated_client.put(
            url,
            {
                "company": "New Company",
                "position": "New Position",
                "location": "New Location",
                "description": "New description",
                "start_date": "2024-01-01",
                "end_date": "2025-01-01",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        experience.refresh_from_db()

        assert experience.company == "New Company"
        assert experience.position == "New Position"
        assert experience.location == "New Location"
        assert experience.description == "New description"
        assert experience.start_date == date(2024, 1, 1)
        assert experience.end_date == date(2025, 1, 1)

    def test_put_requires_required_fields(
        self,
        authenticated_client,
        profile,
    ):
        experience = Experience.objects.create(
            profile=profile,
            company="Acme",
            position="Developer",
        )

        url = reverse(
            "profile-api:experience-detail",
            kwargs={"pk": experience.pk},
        )

        response = authenticated_client.put(
            url,
            {"company": "New Company"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "position" in response.data

        experience.refresh_from_db()

        assert experience.company == "Acme"
        assert experience.position == "Developer"

    def test_delete_own_experience_successfully(
        self,
        authenticated_client,
        profile,
    ):
        experience = Experience.objects.create(
            profile=profile,
            company="Acme",
            position="Developer",
        )

        url = reverse(
            "profile-api:experience-detail",
            kwargs={"pk": experience.pk},
        )

        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Experience.objects.filter(pk=experience.pk).exists()

    def test_delete_cannot_access_another_users_experience(
        self,
        authenticated_client,
        profile,
        another_user,
        another_profile,
    ):
        experience = Experience.objects.create(
            profile=profile,
            company="Acme",
            position="Developer",
        )

        authenticated_client.force_authenticate(user=another_user)

        url = reverse(
            "profile-api:experience-detail",
            kwargs={"pk": experience.pk},
        )

        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Experience.objects.filter(pk=experience.pk).exists()

    def test_delete_own_experience_does_not_delete_another_users_experience(
        self,
        authenticated_client,
        profile,
        another_profile,
    ):
        own_experience = Experience.objects.create(
            profile=profile,
            company="Own Company",
            position="Developer",
        )
        another_experience = Experience.objects.create(
            profile=another_profile,
            company="Another Company",
            position="Developer",
        )

        url = reverse(
            "profile-api:experience-detail",
            kwargs={"pk": own_experience.pk},
        )

        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Experience.objects.filter(pk=own_experience.pk).exists()
        assert Experience.objects.filter(pk=another_experience.pk).exists()

    def test_delete_same_experience_twice_returns_not_found(
        self,
        authenticated_client,
        profile,
    ):
        experience = Experience.objects.create(
            profile=profile,
            company="Acme",
            position="Developer",
        )

        url = reverse(
            "profile-api:experience-detail",
            kwargs={"pk": experience.pk},
        )

        first_response = authenticated_client.delete(url)

        assert first_response.status_code == status.HTTP_204_NO_CONTENT

        second_response = authenticated_client.delete(url)

        assert second_response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_nonexistent_experience_returns_not_found(
        self,
        authenticated_client,
        profile,
    ):
        url = reverse(
            "profile-api:experience-detail",
            kwargs={"pk": 999999},
        )

        response = authenticated_client.patch(
            url,
            {"company": "Acme"},
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_nonexistent_experience_returns_not_found(
        self,
        authenticated_client,
        profile,
    ):
        url = reverse(
            "profile-api:experience-detail",
            kwargs={"pk": 999999},
        )

        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_list_endpoint_is_not_supported(
        self,
        authenticated_client,
        profile,
    ):
        url = reverse("profile-api:experience-list")

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_detail_get_endpoint_is_not_supported(
        self,
        authenticated_client,
        profile,
    ):
        experience = Experience.objects.create(
            profile=profile,
            company="Acme",
            position="Developer",
        )

        url = reverse(
            "profile-api:experience-detail",
            kwargs={"pk": experience.pk},
        )

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_unauthenticated_create_is_rejected(
        self,
        api_client,
    ):
        url = reverse("profile-api:experience-list")
        data = {
            "company": "Acme",
            "position": "Developer",
        }

        response = api_client.post(
            url,
            data,
            format="json",
        )

        assert response.status_code in {
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        }

    def test_unauthenticated_update_is_rejected(
        self,
        api_client,
        profile,
    ):
        experience = Experience.objects.create(
            profile=profile,
            company="Acme",
            position="Developer",
        )

        url = reverse(
            "profile-api:experience-detail",
            kwargs={"pk": experience.pk},
        )

        response = api_client.patch(
            url,
            {"company": "Unauthorized Update"},
            format="json",
        )

        assert response.status_code in {
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        }

        experience.refresh_from_db()

        assert experience.company == "Acme"

    def test_unauthenticated_delete_is_rejected(
        self,
        api_client,
        profile,
    ):
        experience = Experience.objects.create(
            profile=profile,
            company="Acme",
            position="Developer",
        )

        url = reverse(
            "profile-api:experience-detail",
            kwargs={"pk": experience.pk},
        )

        response = api_client.delete(url)

        assert response.status_code in {
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        }

        assert Experience.objects.filter(pk=experience.pk).exists()
