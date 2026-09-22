from uuid import uuid4

import pytest
from django.urls import reverse

from profiles.models import Language


class TestProfileLanguageViewSetCreate:
    def test_authenticated_user_can_create_language(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        url = reverse("profile-api:language-list")
        data = {
            "language": "English",
            "proficiency": "C1",
        }

        # Act
        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        # Assert
        assert response.status_code == 201
        assert response.data["language"] == "English"
        assert response.data["proficiency"] == "C1"

        language = Language.objects.get(pk=response.data["id"])

        assert language.profile == profile
        assert language.language == "English"
        assert language.proficiency == "C1"

    def test_create_assigns_authenticated_users_profile(
        self,
        authenticated_client,
        profile,
        another_profile,
    ):
        # Arrange
        url = reverse("profile-api:language-list")
        data = {
            "language": "French",
            "proficiency": "B2",
            "profile": another_profile.pk,
        }

        # Act
        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        # Assert
        assert response.status_code == 201

        language = Language.objects.get(pk=response.data["id"])

        assert language.profile == profile
        assert language.profile != another_profile

    def test_create_cannot_assign_language_to_another_profile(
        self,
        authenticated_client,
        profile,
        another_profile,
    ):
        # Arrange
        url = reverse("profile-api:language-list")
        data = {
            "language": "German",
            "proficiency": "B1",
            "profile": another_profile.pk,
        }

        # Act
        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        # Assert
        assert response.status_code == 201

        language = Language.objects.get(pk=response.data["id"])

        assert language.profile == profile
        assert language.profile != another_profile

        assert not Language.objects.filter(
            profile=another_profile,
            language="German",
        ).exists()

    def test_create_requires_language(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        url = reverse("profile-api:language-list")
        data = {
            "proficiency": "C1",
        }

        # Act
        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        # Assert
        assert response.status_code == 400
        assert "language" in response.data
        assert not Language.objects.filter(profile=profile).exists()

    def test_create_requires_proficiency(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        url = reverse("profile-api:language-list")
        data = {
            "language": "English",
        }

        # Act
        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        # Assert
        assert response.status_code == 400
        assert "proficiency" in response.data
        assert not Language.objects.filter(profile=profile).exists()

    def test_create_rejects_blank_language(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        url = reverse("profile-api:language-list")
        data = {
            "language": "",
            "proficiency": "C1",
        }

        # Act
        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        # Assert
        assert response.status_code == 400
        assert "language" in response.data
        assert not Language.objects.filter(profile=profile).exists()

    @pytest.mark.parametrize(
        "proficiency",
        [
            "Native",
            "C2",
            "C1",
            "B2",
            "B1",
            "A2",
            "A1",
        ],
    )
    def test_create_accepts_all_supported_proficiencies(
        self,
        authenticated_client,
        profile,
        proficiency,
    ):
        # Arrange
        url = reverse("profile-api:language-list")
        data = {
            "language": f"Language {proficiency}",
            "proficiency": proficiency,
        }

        # Act
        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        # Assert
        assert response.status_code == 201
        assert response.data["proficiency"] == proficiency

        language = Language.objects.get(pk=response.data["id"])

        assert language.profile == profile
        assert language.proficiency == proficiency

    @pytest.mark.parametrize(
        "proficiency",
        [
            "native",
            "native-level",
            "C3",
            "D1",
            "beginner",
            "",
            "invalid",
        ],
    )
    def test_create_rejects_invalid_proficiency(
        self,
        authenticated_client,
        profile,
        proficiency,
    ):
        # Arrange
        url = reverse("profile-api:language-list")
        data = {
            "language": "English",
            "proficiency": proficiency,
        }

        # Act
        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        # Assert
        assert response.status_code == 400
        assert "proficiency" in response.data
        assert not Language.objects.filter(profile=profile).exists()

    def test_create_ignores_unknown_fields(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        url = reverse("profile-api:language-list")
        data = {
            "language": "Spanish",
            "proficiency": "B2",
            "unexpected_field": "unexpected value",
        }

        # Act
        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        # Assert
        assert response.status_code == 201

        language = Language.objects.get(pk=response.data["id"])

        assert language.language == "Spanish"
        assert language.proficiency == "B2"
        assert language.profile == profile
        assert not hasattr(language, "unexpected_field")

    def test_create_allows_duplicate_language_for_same_profile(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        url = reverse("profile-api:language-list")
        data = {
            "language": "English",
            "proficiency": "C1",
        }

        # Act
        first_response = authenticated_client.post(
            url,
            data,
            format="json",
        )
        second_response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        # Assert
        assert first_response.status_code == 201
        assert second_response.status_code == 201

        assert (
            Language.objects.filter(
                profile=profile,
                language="English",
                proficiency="C1",
            ).count()
            == 2
        )


class TestProfileLanguageViewSetUpdate:
    def test_owner_can_fully_update_language(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        language = Language.objects.create(
            profile=profile,
            language="English",
            proficiency="B2",
        )
        url = reverse(
            "profile-api:language-detail",
            kwargs={"pk": language.pk},
        )
        data = {
            "language": "German",
            "proficiency": "C1",
        }

        # Act
        response = authenticated_client.put(
            url,
            data,
            format="json",
        )

        # Assert
        assert response.status_code == 200
        assert response.data["id"] == language.pk
        assert response.data["language"] == "German"
        assert response.data["proficiency"] == "C1"

        language.refresh_from_db()

        assert language.profile == profile
        assert language.language == "German"
        assert language.proficiency == "C1"

    def test_full_update_requires_language(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        language = Language.objects.create(
            profile=profile,
            language="English",
            proficiency="B2",
        )
        url = reverse(
            "profile-api:language-detail",
            kwargs={"pk": language.pk},
        )
        data = {
            "proficiency": "C1",
        }

        # Act
        response = authenticated_client.put(
            url,
            data,
            format="json",
        )

        # Assert
        assert response.status_code == 400
        assert "language" in response.data

        language.refresh_from_db()

        assert language.language == "English"
        assert language.proficiency == "B2"

    def test_full_update_requires_proficiency(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        language = Language.objects.create(
            profile=profile,
            language="English",
            proficiency="B2",
        )
        url = reverse(
            "profile-api:language-detail",
            kwargs={"pk": language.pk},
        )
        data = {
            "language": "German",
        }

        # Act
        response = authenticated_client.put(
            url,
            data,
            format="json",
        )

        # Assert
        assert response.status_code == 400
        assert "proficiency" in response.data

        language.refresh_from_db()

        assert language.language == "English"
        assert language.proficiency == "B2"

    def test_owner_can_partially_update_proficiency(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        language = Language.objects.create(
            profile=profile,
            language="English",
            proficiency="B2",
        )
        url = reverse(
            "profile-api:language-detail",
            kwargs={"pk": language.pk},
        )
        data = {
            "proficiency": "C1",
        }

        # Act
        response = authenticated_client.patch(
            url,
            data,
            format="json",
        )

        # Assert
        assert response.status_code == 200
        assert response.data["language"] == "English"
        assert response.data["proficiency"] == "C1"

        language.refresh_from_db()

        assert language.language == "English"
        assert language.proficiency == "C1"

    def test_owner_can_partially_update_language(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        language = Language.objects.create(
            profile=profile,
            language="English",
            proficiency="B2",
        )
        url = reverse(
            "profile-api:language-detail",
            kwargs={"pk": language.pk},
        )
        data = {
            "language": "French",
        }

        # Act
        response = authenticated_client.patch(
            url,
            data,
            format="json",
        )

        # Assert
        assert response.status_code == 200
        assert response.data["language"] == "French"
        assert response.data["proficiency"] == "B2"

        language.refresh_from_db()

        assert language.language == "French"
        assert language.proficiency == "B2"

    @pytest.mark.parametrize(
        "proficiency",
        [
            "native",
            "C3",
            "D1",
            "invalid",
            "",
        ],
    )
    def test_partial_update_rejects_invalid_proficiency(
        self,
        authenticated_client,
        profile,
        proficiency,
    ):
        # Arrange
        language = Language.objects.create(
            profile=profile,
            language="English",
            proficiency="B2",
        )
        url = reverse(
            "profile-api:language-detail",
            kwargs={"pk": language.pk},
        )
        data = {
            "proficiency": proficiency,
        }

        # Act
        response = authenticated_client.patch(
            url,
            data,
            format="json",
        )

        # Assert
        assert response.status_code == 400
        assert "proficiency" in response.data

        language.refresh_from_db()

        assert language.proficiency == "B2"

    def test_partial_update_rejects_blank_language(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        language = Language.objects.create(
            profile=profile,
            language="English",
            proficiency="B2",
        )
        url = reverse(
            "profile-api:language-detail",
            kwargs={"pk": language.pk},
        )
        data = {
            "language": "",
        }

        # Act
        response = authenticated_client.patch(
            url,
            data,
            format="json",
        )

        # Assert
        assert response.status_code == 400
        assert "language" in response.data

        language.refresh_from_db()

        assert language.language == "English"

    def test_update_cannot_change_profile(
        self,
        authenticated_client,
        profile,
        another_profile,
    ):
        # Arrange
        language = Language.objects.create(
            profile=profile,
            language="English",
            proficiency="B2",
        )
        url = reverse(
            "profile-api:language-detail",
            kwargs={"pk": language.pk},
        )
        data = {
            "language": "German",
            "proficiency": "C1",
            "profile": another_profile.pk,
        }

        # Act
        response = authenticated_client.put(
            url,
            data,
            format="json",
        )

        # Assert
        assert response.status_code == 200

        language.refresh_from_db()

        assert language.profile == profile
        assert language.profile != another_profile
        assert language.language == "German"
        assert language.proficiency == "C1"

    def test_update_ignores_unknown_fields(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        language = Language.objects.create(
            profile=profile,
            language="English",
            proficiency="B2",
        )
        url = reverse(
            "profile-api:language-detail",
            kwargs={"pk": language.pk},
        )
        data = {
            "language": "French",
            "proficiency": "C1",
            "unknown_field": "unexpected",
        }

        # Act
        response = authenticated_client.put(
            url,
            data,
            format="json",
        )

        # Assert
        assert response.status_code == 200

        language.refresh_from_db()

        assert language.language == "French"
        assert language.proficiency == "C1"
        assert not hasattr(language, "unknown_field")


class TestProfileLanguageViewSetOwnership:
    def test_user_cannot_update_another_users_language(
        self,
        authenticated_client,
        another_user,
        profile,
        another_profile,
    ):
        # Arrange
        language = Language.objects.create(
            profile=profile,
            language="English",
            proficiency="B2",
        )

        authenticated_client.force_authenticate(user=another_user)

        url = reverse(
            "profile-api:language-detail",
            kwargs={"pk": language.pk},
        )
        data = {
            "language": "German",
            "proficiency": "C1",
        }

        # Act
        response = authenticated_client.put(
            url,
            data,
            format="json",
        )

        # Assert
        assert response.status_code == 404

        language.refresh_from_db()

        assert language.profile == profile
        assert language.language == "English"
        assert language.proficiency == "B2"

    def test_user_cannot_patch_another_users_language(
        self,
        authenticated_client,
        another_user,
        profile,
        another_profile,
    ):
        # Arrange
        language = Language.objects.create(
            profile=profile,
            language="English",
            proficiency="B2",
        )

        authenticated_client.force_authenticate(user=another_user)

        url = reverse(
            "profile-api:language-detail",
            kwargs={"pk": language.pk},
        )
        data = {
            "proficiency": "C1",
        }

        # Act
        response = authenticated_client.patch(
            url,
            data,
            format="json",
        )

        # Assert
        assert response.status_code == 404

        language.refresh_from_db()

        assert language.profile == profile
        assert language.proficiency == "B2"

    def test_user_cannot_delete_another_users_language(
        self,
        authenticated_client,
        another_user,
        profile,
        another_profile,
    ):
        # Arrange
        language = Language.objects.create(
            profile=profile,
            language="English",
            proficiency="B2",
        )
        language_id = language.pk

        authenticated_client.force_authenticate(user=another_user)

        url = reverse(
            "profile-api:language-detail",
            kwargs={"pk": language_id},
        )

        # Act
        response = authenticated_client.delete(url)

        # Assert
        assert response.status_code == 404
        assert Language.objects.filter(pk=language_id).exists()

    def test_user_cannot_access_another_users_language_by_primary_key(
        self,
        authenticated_client,
        another_user,
        profile,
        another_profile,
    ):
        # Arrange
        language = Language.objects.create(
            profile=profile,
            language="English",
            proficiency="B2",
        )

        authenticated_client.force_authenticate(user=another_user)

        url = reverse(
            "profile-api:language-detail",
            kwargs={"pk": language.pk},
        )

        # Act
        response = authenticated_client.get(url)

        # Assert
        assert response.status_code == 405


class TestProfileLanguageViewSetDelete:
    def test_owner_can_delete_language(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        language = Language.objects.create(
            profile=profile,
            language="English",
            proficiency="C1",
        )
        language_id = language.pk

        url = reverse(
            "profile-api:language-detail",
            kwargs={"pk": language_id},
        )

        # Act
        response = authenticated_client.delete(url)

        # Assert
        assert response.status_code == 204
        assert not Language.objects.filter(pk=language_id).exists()

    def test_delete_does_not_delete_other_languages(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        language_to_delete = Language.objects.create(
            profile=profile,
            language="English",
            proficiency="C1",
        )
        language_to_keep = Language.objects.create(
            profile=profile,
            language="French",
            proficiency="B2",
        )

        url = reverse(
            "profile-api:language-detail",
            kwargs={"pk": language_to_delete.pk},
        )

        # Act
        response = authenticated_client.delete(url)

        # Assert
        assert response.status_code == 204

        assert not Language.objects.filter(
            pk=language_to_delete.pk,
        ).exists()

        assert Language.objects.filter(
            pk=language_to_keep.pk,
        ).exists()

    def test_deleting_nonexistent_language_returns_404(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        nonexistent_id = uuid4()
        url = reverse(
            "profile-api:language-detail",
            kwargs={"pk": nonexistent_id},
        )

        # Act
        response = authenticated_client.delete(url)

        # Assert
        assert response.status_code == 404

    def test_deleting_same_language_twice_returns_404(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        language = Language.objects.create(
            profile=profile,
            language="English",
            proficiency="C1",
        )

        url = reverse(
            "profile-api:language-detail",
            kwargs={"pk": language.pk},
        )

        # Act
        first_response = authenticated_client.delete(url)
        second_response = authenticated_client.delete(url)

        # Assert
        assert first_response.status_code == 204
        assert second_response.status_code == 404


class TestProfileLanguageViewSetObjectLookup:
    def test_updating_nonexistent_language_returns_404(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        nonexistent_id = uuid4()
        url = reverse(
            "profile-api:language-detail",
            kwargs={"pk": nonexistent_id},
        )
        data = {
            "language": "English",
            "proficiency": "C1",
        }

        # Act
        response = authenticated_client.put(
            url,
            data,
            format="json",
        )

        # Assert
        assert response.status_code == 404

    def test_patching_nonexistent_language_returns_404(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        nonexistent_id = uuid4()
        url = reverse(
            "profile-api:language-detail",
            kwargs={"pk": nonexistent_id},
        )
        data = {
            "proficiency": "C1",
        }

        # Act
        response = authenticated_client.patch(
            url,
            data,
            format="json",
        )

        # Assert
        assert response.status_code == 404


class TestProfileLanguageViewSetAllowedMethods:
    def test_list_request_is_not_supported(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        url = reverse("profile-api:language-list")

        # Act
        response = authenticated_client.get(url)

        # Assert
        assert response.status_code == 405

    def test_detail_get_request_is_not_supported(
        self,
        authenticated_client,
        profile,
    ):
        # Arrange
        language = Language.objects.create(
            profile=profile,
            language="English",
            proficiency="C1",
        )
        url = reverse(
            "profile-api:language-detail",
            kwargs={"pk": language.pk},
        )

        # Act
        response = authenticated_client.get(url)

        # Assert
        assert response.status_code == 405


class TestProfileLanguageViewSetAuthentication:
    def test_unauthenticated_user_cannot_create_language(
        self,
        api_client,
    ):
        # Arrange
        url = reverse("profile-api:language-list")
        data = {
            "language": "English",
            "proficiency": "C1",
        }

        # Act
        response = api_client.post(
            url,
            data,
            format="json",
        )

        # Assert
        assert response.status_code in (401, 403)

    def test_unauthenticated_user_cannot_update_language(
        self,
        api_client,
        profile,
    ):
        # Arrange
        language = Language.objects.create(
            profile=profile,
            language="English",
            proficiency="C1",
        )
        url = reverse(
            "profile-api:language-detail",
            kwargs={"pk": language.pk},
        )
        data = {
            "language": "German",
            "proficiency": "B2",
        }

        # Act
        response = api_client.put(
            url,
            data,
            format="json",
        )

        # Assert
        assert response.status_code in (401, 403)

        language.refresh_from_db()

        assert language.language == "English"
        assert language.proficiency == "C1"

    def test_unauthenticated_user_cannot_patch_language(
        self,
        api_client,
        profile,
    ):
        # Arrange
        language = Language.objects.create(
            profile=profile,
            language="English",
            proficiency="C1",
        )
        url = reverse(
            "profile-api:language-detail",
            kwargs={"pk": language.pk},
        )
        data = {
            "proficiency": "C2",
        }

        # Act
        response = api_client.patch(
            url,
            data,
            format="json",
        )

        # Assert
        assert response.status_code in (401, 403)

        language.refresh_from_db()

        assert language.proficiency == "C1"

    def test_unauthenticated_user_cannot_delete_language(
        self,
        api_client,
        profile,
    ):
        # Arrange
        language = Language.objects.create(
            profile=profile,
            language="English",
            proficiency="C1",
        )
        language_id = language.pk

        url = reverse(
            "profile-api:language-detail",
            kwargs={"pk": language_id},
        )

        # Act
        response = api_client.delete(url)

        # Assert
        assert response.status_code in (401, 403)
        assert Language.objects.filter(pk=language_id).exists()
