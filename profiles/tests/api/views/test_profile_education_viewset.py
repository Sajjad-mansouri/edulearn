from datetime import date

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from profiles.models import Education


@pytest.mark.django_db
class TestProfileEducationViewSet:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def authenticated_client(self, api_client, test_user):
        api_client.force_authenticate(user=test_user)
        return api_client

    @pytest.fixture
    def education(self, profile):
        return Education.objects.create(
            profile=profile,
            institution="Original University",
            degree="Bachelor's Degree",
            field_of_study="Computer Science",
            description="Original education description.",
            start_date=date(2018, 9, 1),
            end_date=date(2022, 6, 30),
        )

    @pytest.fixture
    def another_education(self, another_profile):
        return Education.objects.create(
            profile=another_profile,
            institution="Another University",
            degree="Master's Degree",
            field_of_study="Software Engineering",
            description="Another user's education.",
            start_date=date(2020, 9, 1),
            end_date=date(2022, 6, 30),
        )

    @pytest.fixture
    def list_url(self):
        return reverse("profile-api:education-list")

    def detail_url(self, education):
        return reverse(
            "profile-api:education-detail",
            kwargs={"pk": education.pk},
        )

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    def test_authenticated_user_can_create_education(
        self,
        authenticated_client,
        profile,
        list_url,
    ):
        response = authenticated_client.post(
            list_url,
            {
                "institution": "New University",
                "degree": "Bachelor's Degree",
                "field_of_study": "Computer Science",
                "description": "Bachelor's degree description.",
                "start_date": "2019-09-01",
                "end_date": "2023-06-30",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        education = Education.objects.get(
            institution="New University",
        )

        assert education.profile == profile
        assert education.degree == "Bachelor's Degree"
        assert education.field_of_study == "Computer Science"
        assert education.description == "Bachelor's degree description."
        assert education.start_date == date(2019, 9, 1)
        assert education.end_date == date(2023, 6, 30)

    def test_create_returns_created_education(
        self,
        authenticated_client,
        profile,
        list_url,
    ):
        response = authenticated_client.post(
            list_url,
            {
                "institution": "New University",
                "degree": "Bachelor's Degree",
                "field_of_study": "Computer Science",
                "description": "Bachelor's degree description.",
                "start_date": "2019-09-01",
                "end_date": "2023-06-30",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        education = Education.objects.get(
            institution="New University",
        )

        assert response.data["id"] == education.id
        assert response.data["institution"] == "New University"
        assert response.data["degree"] == "Bachelor's Degree"
        assert response.data["field_of_study"] == "Computer Science"
        assert response.data["description"] == "Bachelor's degree description."
        assert response.data["start_date"] == "2019-09-01"
        assert response.data["end_date"] == "2023-06-30"

    def test_create_education_without_optional_fields(
        self,
        authenticated_client,
        profile,
        list_url,
    ):
        response = authenticated_client.post(
            list_url,
            {
                "institution": "Current University",
                "degree": "Master's Degree",
                "field_of_study": "Computer Science",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        education = Education.objects.get(
            institution="Current University",
        )

        assert education.profile == profile
        assert education.description == ""
        assert education.start_date is None
        assert education.end_date is None

    def test_create_current_education_with_null_end_date(
        self,
        authenticated_client,
        profile,
        list_url,
    ):
        response = authenticated_client.post(
            list_url,
            {
                "institution": "Current University",
                "degree": "Master's Degree",
                "field_of_study": "Software Engineering",
                "start_date": "2024-09-01",
                "end_date": None,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        education = Education.objects.get(
            institution="Current University",
        )

        assert education.profile == profile
        assert education.start_date == date(2024, 9, 1)
        assert education.end_date is None

    def test_create_cannot_assign_education_to_another_profile(
        self,
        authenticated_client,
        profile,
        another_profile,
        list_url,
    ):
        response = authenticated_client.post(
            list_url,
            {
                "profile": another_profile.id,
                "institution": "Attempted Hijack University",
                "degree": "Bachelor's Degree",
                "field_of_study": "Computer Science",
                "start_date": "2019-09-01",
                "end_date": "2023-06-30",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        education = Education.objects.get(
            institution="Attempted Hijack University",
        )

        assert education.profile == profile
        assert education.profile != another_profile

    def test_create_requires_institution(
        self,
        authenticated_client,
        profile,
        list_url,
    ):
        response = authenticated_client.post(
            list_url,
            {
                "degree": "Bachelor's Degree",
                "field_of_study": "Computer Science",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "institution" in response.data

    def test_create_requires_degree(
        self,
        authenticated_client,
        profile,
        list_url,
    ):
        response = authenticated_client.post(
            list_url,
            {
                "institution": "New University",
                "field_of_study": "Computer Science",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "degree" in response.data

    def test_create_requires_field_of_study(
        self,
        authenticated_client,
        profile,
        list_url,
    ):
        response = authenticated_client.post(
            list_url,
            {
                "institution": "New University",
                "degree": "Bachelor's Degree",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "field_of_study" in response.data

    def test_create_rejects_invalid_start_date(
        self,
        authenticated_client,
        profile,
        list_url,
    ):
        response = authenticated_client.post(
            list_url,
            {
                "institution": "New University",
                "degree": "Bachelor's Degree",
                "field_of_study": "Computer Science",
                "start_date": "not-a-date",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "start_date" in response.data

        assert not Education.objects.filter(
            institution="New University",
        ).exists()

    def test_create_rejects_invalid_end_date(
        self,
        authenticated_client,
        profile,
        list_url,
    ):
        response = authenticated_client.post(
            list_url,
            {
                "institution": "New University",
                "degree": "Bachelor's Degree",
                "field_of_study": "Computer Science",
                "end_date": "not-a-date",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "end_date" in response.data

        assert not Education.objects.filter(
            institution="New University",
        ).exists()

    def test_create_accepts_equal_start_and_end_dates(
        self,
        authenticated_client,
        profile,
        list_url,
    ):
        response = authenticated_client.post(
            list_url,
            {
                "institution": "Short Course University",
                "degree": "Certificate",
                "field_of_study": "Computer Science",
                "start_date": "2024-06-01",
                "end_date": "2024-06-01",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        education = Education.objects.get(
            institution="Short Course University",
        )

        assert education.start_date == date(2024, 6, 1)
        assert education.end_date == date(2024, 6, 1)

    def test_create_rejects_institution_longer_than_max_length(
        self,
        authenticated_client,
        profile,
        list_url,
    ):
        response = authenticated_client.post(
            list_url,
            {
                "institution": "I" * 256,
                "degree": "Bachelor's Degree",
                "field_of_study": "Computer Science",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "institution" in response.data

    def test_create_rejects_degree_longer_than_max_length(
        self,
        authenticated_client,
        profile,
        list_url,
    ):
        response = authenticated_client.post(
            list_url,
            {
                "institution": "New University",
                "degree": "D" * 256,
                "field_of_study": "Computer Science",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "degree" in response.data

    def test_create_rejects_field_of_study_longer_than_max_length(
        self,
        authenticated_client,
        profile,
        list_url,
    ):
        response = authenticated_client.post(
            list_url,
            {
                "institution": "New University",
                "degree": "Bachelor's Degree",
                "field_of_study": "F" * 256,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "field_of_study" in response.data

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------

    def test_authenticated_user_can_update_education(
        self,
        authenticated_client,
        education,
    ):
        response = authenticated_client.patch(
            self.detail_url(education),
            {
                "institution": "Updated University",
                "degree": "Updated Degree",
                "field_of_study": "Updated Field",
                "description": "Updated description.",
                "start_date": "2019-01-01",
                "end_date": "2023-12-31",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        education.refresh_from_db()

        assert education.institution == "Updated University"
        assert education.degree == "Updated Degree"
        assert education.field_of_study == "Updated Field"
        assert education.description == "Updated description."
        assert education.start_date == date(2019, 1, 1)
        assert education.end_date == date(2023, 12, 31)

    def test_update_returns_updated_education(
        self,
        authenticated_client,
        education,
    ):
        response = authenticated_client.patch(
            self.detail_url(education),
            {
                "institution": "Updated University",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == education.id
        assert response.data["institution"] == "Updated University"

    def test_partial_update_preserves_omitted_fields(
        self,
        authenticated_client,
        education,
    ):
        original_degree = education.degree
        original_field_of_study = education.field_of_study
        original_description = education.description
        original_start_date = education.start_date
        original_end_date = education.end_date

        response = authenticated_client.patch(
            self.detail_url(education),
            {
                "institution": "Only Institution Changed",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        education.refresh_from_db()

        assert education.institution == "Only Institution Changed"
        assert education.degree == original_degree
        assert education.field_of_study == original_field_of_study
        assert education.description == original_description
        assert education.start_date == original_start_date
        assert education.end_date == original_end_date

    def test_update_can_clear_optional_fields(
        self,
        authenticated_client,
        education,
    ):
        response = authenticated_client.patch(
            self.detail_url(education),
            {
                "description": "",
                "start_date": None,
                "end_date": None,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        education.refresh_from_db()

        assert education.description == ""
        assert education.start_date is None
        assert education.end_date is None

    def test_update_accepts_equal_start_and_end_dates(
        self,
        authenticated_client,
        education,
    ):
        response = authenticated_client.patch(
            self.detail_url(education),
            {
                "start_date": "2024-01-01",
                "end_date": "2024-01-01",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        education.refresh_from_db()

        assert education.start_date == date(2024, 1, 1)
        assert education.end_date == date(2024, 1, 1)

    def test_update_rejects_invalid_start_date(
        self,
        authenticated_client,
        education,
    ):
        original_start_date = education.start_date

        response = authenticated_client.patch(
            self.detail_url(education),
            {
                "start_date": "invalid-date",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "start_date" in response.data

        education.refresh_from_db()

        assert education.start_date == original_start_date

    def test_update_rejects_invalid_end_date(
        self,
        authenticated_client,
        education,
    ):
        original_end_date = education.end_date

        response = authenticated_client.patch(
            self.detail_url(education),
            {
                "end_date": "invalid-date",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "end_date" in response.data

        education.refresh_from_db()

        assert education.end_date == original_end_date

    def test_update_cannot_access_another_users_education(
        self,
        authenticated_client,
        profile,
        another_user,
        another_profile,
    ):
        education = Education.objects.create(
            profile=profile,
            institution="Original Institution",
            degree="Original Degree",
            field_of_study="Original Field",
        )

        authenticated_client.force_authenticate(user=another_user)

        url = reverse(
            "profile-api:education-detail",
            kwargs={"pk": education.pk},
        )

        response = authenticated_client.patch(
            url,
            {"institution": "Unauthorized Update"},
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

        education.refresh_from_db()
        assert education.institution == "Original Institution"

    def test_update_does_not_modify_another_users_education(
        self,
        authenticated_client,
        education,
        another_education,
    ):
        original_institution = another_education.institution

        response = authenticated_client.patch(
            self.detail_url(education),
            {
                "institution": "Updated Own Education",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        another_education.refresh_from_db()

        assert another_education.institution == original_institution

    def test_update_cannot_change_education_owner(
        self,
        authenticated_client,
        profile,
        another_profile,
        education,
    ):
        original_profile_id = education.profile_id

        response = authenticated_client.patch(
            self.detail_url(education),
            {
                "profile": another_profile.id,
                "institution": "Updated Institution",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        education.refresh_from_db()

        assert education.profile_id == original_profile_id
        assert education.profile == profile
        assert education.institution == "Updated Institution"

    # ------------------------------------------------------------------
    # PUT
    # ------------------------------------------------------------------

    def test_put_updates_education(
        self,
        authenticated_client,
        education,
    ):
        response = authenticated_client.put(
            self.detail_url(education),
            {
                "institution": "Replaced University",
                "degree": "Master's Degree",
                "field_of_study": "Software Engineering",
                "description": "Replaced description.",
                "start_date": "2020-09-01",
                "end_date": "2024-06-30",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        education.refresh_from_db()

        assert education.institution == "Replaced University"
        assert education.degree == "Master's Degree"
        assert education.field_of_study == "Software Engineering"
        assert education.description == "Replaced description."
        assert education.start_date == date(2020, 9, 1)
        assert education.end_date == date(2024, 6, 30)

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------

    def test_authenticated_user_can_delete_education(
        self,
        authenticated_client,
        education,
    ):
        education_id = education.id

        response = authenticated_client.delete(
            self.detail_url(education),
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Education.objects.filter(
            id=education_id,
        ).exists()

    def test_delete_cannot_access_another_users_education(
        self,
        authenticated_client,
        profile,
        another_user,
        another_profile,
    ):
        education = Education.objects.create(
            profile=profile,
            institution="Original Institution",
            degree="Original Degree",
            field_of_study="Original Field",
        )

        authenticated_client.force_authenticate(user=another_user)

        url = reverse(
            "profile-api:education-detail",
            kwargs={"pk": education.pk},
        )

        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Education.objects.filter(pk=education.pk).exists()

    def test_delete_does_not_delete_another_education(
        self,
        authenticated_client,
        education,
        another_education,
    ):
        response = authenticated_client.delete(
            self.detail_url(education),
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        assert not Education.objects.filter(
            id=education.id,
        ).exists()

        assert Education.objects.filter(
            id=another_education.id,
        ).exists()

    def test_delete_same_education_twice_returns_404(
        self,
        authenticated_client,
        education,
    ):
        response = authenticated_client.delete(
            self.detail_url(education),
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        second_response = authenticated_client.delete(
            self.detail_url(education),
        )

        assert second_response.status_code == status.HTTP_404_NOT_FOUND

    # ------------------------------------------------------------------
    # HTTP METHOD RESTRICTIONS
    # ------------------------------------------------------------------

    def test_list_method_is_not_supported(
        self,
        authenticated_client,
        profile,
        list_url,
    ):
        response = authenticated_client.get(list_url)

        assert response.status_code == (status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_retrieve_method_is_not_supported(
        self,
        authenticated_client,
        education,
    ):
        response = authenticated_client.get(
            self.detail_url(education),
        )

        assert response.status_code == (status.HTTP_405_METHOD_NOT_ALLOWED)

    # ------------------------------------------------------------------
    # AUTHENTICATION
    # ------------------------------------------------------------------

    def test_unauthenticated_create_is_rejected(
        self,
        api_client,
        list_url,
    ):
        response = api_client.post(
            list_url,
            {
                "institution": "Unauthorized University",
                "degree": "Bachelor's Degree",
                "field_of_study": "Computer Science",
            },
            format="json",
        )

        assert response.status_code in {
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        }

        assert not Education.objects.filter(
            institution="Unauthorized University",
        ).exists()

    def test_unauthenticated_update_is_rejected(
        self,
        api_client,
        education,
    ):
        response = api_client.patch(
            self.detail_url(education),
            {
                "institution": "Unauthorized Update",
            },
            format="json",
        )

        assert response.status_code in {
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        }

        education.refresh_from_db()

        assert education.institution == "Original University"

    def test_unauthenticated_delete_is_rejected(
        self,
        api_client,
        education,
    ):
        education_id = education.id

        response = api_client.delete(
            self.detail_url(education),
        )

        assert response.status_code in {
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        }

        assert Education.objects.filter(
            id=education_id,
        ).exists()

    # ------------------------------------------------------------------
    # NOT FOUND
    # ------------------------------------------------------------------

    def test_update_nonexistent_education_returns_404(
        self,
        authenticated_client,
        profile,
    ):
        response = authenticated_client.patch(
            reverse(
                "profile-api:education-detail",
                kwargs={"pk": 999999},
            ),
            {
                "institution": "Updated University",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_nonexistent_education_returns_404(
        self,
        authenticated_client,
        profile,
    ):
        response = authenticated_client.delete(
            reverse(
                "profile-api:education-detail",
                kwargs={"pk": 999999},
            ),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
