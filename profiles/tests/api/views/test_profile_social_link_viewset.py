from django.urls import reverse
from rest_framework import status

from profiles.models import SocialLink


class TestProfileSocialLinkViewSet:
    def test_create_social_link_successfully(
        self,
        authenticated_client,
        profile,
    ):
        url = reverse("profile-api:social_link-list")
        data = {
            "platform": "github",
            "address": "https://github.com/example",
        }

        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        social_link = SocialLink.objects.get()

        assert social_link.profile == profile
        assert social_link.platform == SocialLink.Platform.GITHUB
        assert social_link.address == "https://github.com/example"

        # These model fields are not exposed by the serializer, so their
        # model defaults must remain intact.
        assert social_link.visibility == SocialLink.Visibility.PUBLIC
        assert social_link.display_order == 0

        assert response.data["id"] == social_link.id
        assert response.data["platform"] == "github"
        assert response.data["address"] == "https://github.com/example"

    def test_create_social_link_requires_platform(
        self,
        authenticated_client,
        profile,
    ):
        url = reverse("profile-api:social_link-list")
        data = {
            "address": "https://github.com/example",
        }

        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "platform" in response.data
        assert not SocialLink.objects.exists()

    def test_create_social_link_requires_address(
        self,
        authenticated_client,
        profile,
    ):
        url = reverse("profile-api:social_link-list")
        data = {
            "platform": "github",
        }

        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "address" in response.data
        assert not SocialLink.objects.exists()

    def test_create_social_link_rejects_invalid_platform(
        self,
        authenticated_client,
        profile,
    ):
        url = reverse("profile-api:social_link-list")
        data = {
            "platform": "invalid-platform",
            "address": "https://example.com",
        }

        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "platform" in response.data
        assert not SocialLink.objects.exists()

    def test_create_social_link_accepts_every_supported_platform(
        self,
        authenticated_client,
        profile,
    ):
        url = reverse("profile-api:social_link-list")

        for platform, _ in SocialLink.Platform.choices:
            response = authenticated_client.post(
                url,
                {
                    "platform": platform,
                    "address": f"https://example.com/{platform}",
                },
                format="json",
            )

            assert response.status_code == status.HTTP_201_CREATED

        assert SocialLink.objects.filter(profile=profile).count() == len(
            SocialLink.Platform.choices
        )

    def test_create_social_link_rejects_invalid_url(
        self,
        authenticated_client,
        profile,
    ):
        url = reverse("profile-api:social_link-list")
        data = {
            "platform": "github",
            "address": "not-a-valid-url",
        }

        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "address" in response.data
        assert not SocialLink.objects.exists()

    def test_create_social_link_rejects_blank_address(
        self,
        authenticated_client,
        profile,
    ):
        url = reverse("profile-api:social_link-list")
        data = {
            "platform": "github",
            "address": "",
        }

        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "address" in response.data
        assert not SocialLink.objects.exists()

    def test_create_social_link_accepts_valid_url_with_path_and_query(
        self,
        authenticated_client,
        profile,
    ):
        url = reverse("profile-api:social_link-list")
        address = "https://example.com/profile/user?tab=projects"

        response = authenticated_client.post(
            url,
            {
                "platform": "github",
                "address": address,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        social_link = SocialLink.objects.get()

        assert social_link.address == address

    def test_create_social_link_cannot_assign_another_users_profile(
        self,
        authenticated_client,
        profile,
        another_profile,
    ):
        url = reverse("profile-api:social_link-list")
        data = {
            "platform": "github",
            "address": "https://github.com/example",
            "profile": another_profile.id,
        }

        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        social_link = SocialLink.objects.get()

        assert social_link.profile == profile
        assert social_link.profile != another_profile

    def test_create_social_link_ignores_visibility_field(
        self,
        authenticated_client,
        profile,
    ):
        url = reverse("profile-api:social_link-list")
        data = {
            "platform": "github",
            "address": "https://github.com/example",
            "visibility": "private",
        }

        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        social_link = SocialLink.objects.get()

        assert social_link.visibility == SocialLink.Visibility.PUBLIC
        assert "visibility" not in response.data

    def test_create_social_link_ignores_display_order_field(
        self,
        authenticated_client,
        profile,
    ):
        url = reverse("profile-api:social_link-list")
        data = {
            "platform": "github",
            "address": "https://github.com/example",
            "display_order": 10,
        }

        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        social_link = SocialLink.objects.get()

        assert social_link.display_order == 0
        assert "display_order" not in response.data

    def test_create_social_link_ignores_unknown_fields(
        self,
        authenticated_client,
        profile,
    ):
        url = reverse("profile-api:social_link-list")
        data = {
            "platform": "github",
            "address": "https://github.com/example",
            "unknown_field": "ignored",
        }

        response = authenticated_client.post(
            url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        social_link = SocialLink.objects.get()

        assert social_link.platform == "github"
        assert social_link.address == "https://github.com/example"
        assert not hasattr(social_link, "unknown_field")

    def test_create_social_link_does_not_create_for_another_profile(
        self,
        authenticated_client,
        profile,
        another_profile,
    ):
        url = reverse("profile-api:social_link-list")

        response = authenticated_client.post(
            url,
            {
                "platform": "linkedin",
                "address": "https://linkedin.com/in/example",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        assert profile.social_links.count() == 1
        assert another_profile.social_links.count() == 0

    def test_update_social_link_successfully(
        self,
        authenticated_client,
        profile,
    ):
        social_link = SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.GITHUB,
            address="https://github.com/old",
        )

        url = reverse(
            "profile-api:social_link-detail",
            kwargs={"pk": social_link.pk},
        )
        data = {
            "platform": "linkedin",
            "address": "https://linkedin.com/in/example",
        }

        response = authenticated_client.put(
            url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        social_link.refresh_from_db()

        assert social_link.platform == SocialLink.Platform.LINKEDIN
        assert social_link.address == "https://linkedin.com/in/example"
        assert social_link.profile == profile

    def test_update_social_link_returns_updated_representation(
        self,
        authenticated_client,
        profile,
    ):
        social_link = SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.GITHUB,
            address="https://github.com/old",
        )

        url = reverse(
            "profile-api:social_link-detail",
            kwargs={"pk": social_link.pk},
        )

        response = authenticated_client.patch(
            url,
            {
                "platform": "linkedin",
                "address": "https://linkedin.com/in/example",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == social_link.id
        assert response.data["platform"] == "linkedin"
        assert response.data["address"] == "https://linkedin.com/in/example"

    def test_partial_update_platform_only_preserves_address(
        self,
        authenticated_client,
        profile,
    ):
        social_link = SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.GITHUB,
            address="https://github.com/example",
        )

        url = reverse(
            "profile-api:social_link-detail",
            kwargs={"pk": social_link.pk},
        )

        response = authenticated_client.patch(
            url,
            {"platform": "linkedin"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        social_link.refresh_from_db()

        assert social_link.platform == SocialLink.Platform.LINKEDIN
        assert social_link.address == "https://github.com/example"

    def test_partial_update_address_only_preserves_platform(
        self,
        authenticated_client,
        profile,
    ):
        social_link = SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.GITHUB,
            address="https://github.com/example",
        )

        url = reverse(
            "profile-api:social_link-detail",
            kwargs={"pk": social_link.pk},
        )

        response = authenticated_client.patch(
            url,
            {"address": "https://github.com/new-example"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        social_link.refresh_from_db()

        assert social_link.platform == SocialLink.Platform.GITHUB
        assert social_link.address == "https://github.com/new-example"

    def test_partial_update_rejects_invalid_platform(
        self,
        authenticated_client,
        profile,
    ):
        social_link = SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.GITHUB,
            address="https://github.com/example",
        )

        url = reverse(
            "profile-api:social_link-detail",
            kwargs={"pk": social_link.pk},
        )

        response = authenticated_client.patch(
            url,
            {"platform": "invalid-platform"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "platform" in response.data

        social_link.refresh_from_db()

        assert social_link.platform == SocialLink.Platform.GITHUB
        assert social_link.address == "https://github.com/example"

    def test_partial_update_rejects_invalid_address(
        self,
        authenticated_client,
        profile,
    ):
        social_link = SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.GITHUB,
            address="https://github.com/example",
        )

        url = reverse(
            "profile-api:social_link-detail",
            kwargs={"pk": social_link.pk},
        )

        response = authenticated_client.patch(
            url,
            {"address": "invalid-url"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "address" in response.data

        social_link.refresh_from_db()

        assert social_link.address == "https://github.com/example"

    def test_put_requires_platform(
        self,
        authenticated_client,
        profile,
    ):
        social_link = SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.GITHUB,
            address="https://github.com/example",
        )

        url = reverse(
            "profile-api:social_link-detail",
            kwargs={"pk": social_link.pk},
        )

        response = authenticated_client.put(
            url,
            {"address": "https://example.com"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "platform" in response.data

        social_link.refresh_from_db()

        assert social_link.platform == SocialLink.Platform.GITHUB
        assert social_link.address == "https://github.com/example"

    def test_put_requires_address(
        self,
        authenticated_client,
        profile,
    ):
        social_link = SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.GITHUB,
            address="https://github.com/example",
        )

        url = reverse(
            "profile-api:social_link-detail",
            kwargs={"pk": social_link.pk},
        )

        response = authenticated_client.put(
            url,
            {"platform": "linkedin"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "address" in response.data

        social_link.refresh_from_db()

        assert social_link.platform == SocialLink.Platform.GITHUB
        assert social_link.address == "https://github.com/example"

    def test_update_social_link_cannot_change_profile(
        self,
        authenticated_client,
        profile,
        another_profile,
    ):
        social_link = SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.GITHUB,
            address="https://github.com/example",
        )

        url = reverse(
            "profile-api:social_link-detail",
            kwargs={"pk": social_link.pk},
        )

        response = authenticated_client.patch(
            url,
            {
                "address": "https://github.com/updated",
                "profile": another_profile.id,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        social_link.refresh_from_db()

        assert social_link.address == "https://github.com/updated"
        assert social_link.profile == profile
        assert social_link.profile != another_profile

    def test_update_social_link_cannot_change_visibility(
        self,
        authenticated_client,
        profile,
    ):
        social_link = SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.GITHUB,
            address="https://github.com/example",
        )

        url = reverse(
            "profile-api:social_link-detail",
            kwargs={"pk": social_link.pk},
        )

        response = authenticated_client.patch(
            url,
            {
                "address": "https://github.com/updated",
                "visibility": "private",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        social_link.refresh_from_db()

        assert social_link.address == "https://github.com/updated"
        assert social_link.visibility == SocialLink.Visibility.PUBLIC

    def test_update_social_link_cannot_change_display_order(
        self,
        authenticated_client,
        profile,
    ):
        social_link = SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.GITHUB,
            address="https://github.com/example",
            display_order=5,
        )

        url = reverse(
            "profile-api:social_link-detail",
            kwargs={"pk": social_link.pk},
        )

        response = authenticated_client.patch(
            url,
            {
                "address": "https://github.com/updated",
                "display_order": 100,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        social_link.refresh_from_db()

        assert social_link.address == "https://github.com/updated"
        assert social_link.display_order == 5

    def test_update_cannot_access_another_users_social_link(
        self,
        authenticated_client,
        profile,
        another_user,
        another_profile,
    ):
        social_link = SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.GITHUB,
            address="https://github.com/example",
        )

        authenticated_client.force_authenticate(user=another_user)

        url = reverse(
            "profile-api:social_link-detail",
            kwargs={"pk": social_link.pk},
        )

        response = authenticated_client.patch(
            url,
            {"address": "https://github.com/unauthorized"},
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

        social_link.refresh_from_db()

        assert social_link.address == "https://github.com/example"
        assert social_link.profile == profile

    def test_update_own_social_link_does_not_modify_another_users_social_link(
        self,
        authenticated_client,
        profile,
        another_profile,
    ):
        own_link = SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.GITHUB,
            address="https://github.com/own",
        )
        another_link = SocialLink.objects.create(
            profile=another_profile,
            platform=SocialLink.Platform.GITHUB,
            address="https://github.com/another",
        )

        url = reverse(
            "profile-api:social_link-detail",
            kwargs={"pk": own_link.pk},
        )

        response = authenticated_client.patch(
            url,
            {"address": "https://github.com/updated"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        own_link.refresh_from_db()
        another_link.refresh_from_db()

        assert own_link.address == "https://github.com/updated"
        assert another_link.address == "https://github.com/another"

    def test_delete_own_social_link_successfully(
        self,
        authenticated_client,
        profile,
    ):
        social_link = SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.GITHUB,
            address="https://github.com/example",
        )

        url = reverse(
            "profile-api:social_link-detail",
            kwargs={"pk": social_link.pk},
        )

        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not SocialLink.objects.filter(pk=social_link.pk).exists()

    def test_delete_cannot_access_another_users_social_link(
        self,
        authenticated_client,
        profile,
        another_user,
        another_profile,
    ):
        social_link = SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.GITHUB,
            address="https://github.com/example",
        )

        authenticated_client.force_authenticate(user=another_user)

        url = reverse(
            "profile-api:social_link-detail",
            kwargs={"pk": social_link.pk},
        )

        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert SocialLink.objects.filter(pk=social_link.pk).exists()

    def test_delete_own_social_link_does_not_delete_another_users_social_link(
        self,
        authenticated_client,
        profile,
        another_profile,
    ):
        own_link = SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.GITHUB,
            address="https://github.com/own",
        )
        another_link = SocialLink.objects.create(
            profile=another_profile,
            platform=SocialLink.Platform.GITHUB,
            address="https://github.com/another",
        )

        url = reverse(
            "profile-api:social_link-detail",
            kwargs={"pk": own_link.pk},
        )

        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        assert not SocialLink.objects.filter(pk=own_link.pk).exists()
        assert SocialLink.objects.filter(pk=another_link.pk).exists()

    def test_delete_same_social_link_twice_returns_not_found(
        self,
        authenticated_client,
        profile,
    ):
        social_link = SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.GITHUB,
            address="https://github.com/example",
        )

        url = reverse(
            "profile-api:social_link-detail",
            kwargs={"pk": social_link.pk},
        )

        first_response = authenticated_client.delete(url)

        assert first_response.status_code == status.HTTP_204_NO_CONTENT

        second_response = authenticated_client.delete(url)

        assert second_response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_nonexistent_social_link_returns_not_found(
        self,
        authenticated_client,
        profile,
    ):
        url = reverse(
            "profile-api:social_link-detail",
            kwargs={"pk": 999999},
        )

        response = authenticated_client.patch(
            url,
            {
                "platform": "github",
                "address": "https://github.com/example",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_nonexistent_social_link_returns_not_found(
        self,
        authenticated_client,
        profile,
    ):
        url = reverse(
            "profile-api:social_link-detail",
            kwargs={"pk": 999999},
        )

        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_list_endpoint_is_not_supported(
        self,
        authenticated_client,
        profile,
    ):
        url = reverse("profile-api:social_link-list")

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_detail_get_endpoint_is_not_supported(
        self,
        authenticated_client,
        profile,
    ):
        social_link = SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.GITHUB,
            address="https://github.com/example",
        )

        url = reverse(
            "profile-api:social_link-detail",
            kwargs={"pk": social_link.pk},
        )

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_unauthenticated_create_is_rejected(
        self,
        api_client,
    ):
        url = reverse("profile-api:social_link-list")
        data = {
            "platform": "github",
            "address": "https://github.com/example",
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
        social_link = SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.GITHUB,
            address="https://github.com/example",
        )

        url = reverse(
            "profile-api:social_link-detail",
            kwargs={"pk": social_link.pk},
        )

        response = api_client.patch(
            url,
            {"address": "https://github.com/unauthorized"},
            format="json",
        )

        assert response.status_code in {
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        }

        social_link.refresh_from_db()

        assert social_link.address == "https://github.com/example"

    def test_unauthenticated_delete_is_rejected(
        self,
        api_client,
        profile,
    ):
        social_link = SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.GITHUB,
            address="https://github.com/example",
        )

        url = reverse(
            "profile-api:social_link-detail",
            kwargs={"pk": social_link.pk},
        )

        response = api_client.delete(url)

        assert response.status_code in {
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        }

        assert SocialLink.objects.filter(pk=social_link.pk).exists()
