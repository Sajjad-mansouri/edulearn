import pytest
from django.contrib.auth import get_user_model

from profiles.api.serializers.social_link import SocialLinkSerializer
from profiles.models import Profile, SocialLink

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="social_link_test_user",
        email="social_link_test@example.com",
        password="test-password",
    )


@pytest.fixture
def profile(db, user):
    return Profile.objects.create(user=user)


@pytest.fixture
def social_link(db, profile):
    return SocialLink.objects.create(
        profile=profile,
        platform=SocialLink.Platform.GITHUB,
        address="https://github.com/example",
    )


@pytest.fixture
def serializer():
    return SocialLinkSerializer()


class TestSocialLinkSerializer:
    def test_fields_are_exactly_expected(self, serializer):
        assert set(serializer.fields) == {
            "id",
            "platform",
            "address",
        }

    def test_id_is_read_only(self, serializer):
        assert serializer.fields["id"].read_only is True

    def test_platform_is_required(self, serializer):
        assert serializer.fields["platform"].required is True

    def test_platform_does_not_allow_null(self, serializer):
        assert serializer.fields["platform"].allow_null is False

    def test_platform_does_not_allow_blank(self, serializer):
        assert serializer.fields["platform"].allow_blank is False

    def test_address_is_required(self, serializer):
        assert serializer.fields["address"].required is True

    def test_address_does_not_allow_null(self, serializer):
        assert serializer.fields["address"].allow_null is False

    def test_address_does_not_allow_blank(self, serializer):
        assert serializer.fields["address"].allow_blank is False

    def test_profile_is_not_exposed(self, serializer):
        assert "profile" not in serializer.fields

    def test_visibility_is_not_exposed(self, serializer):
        assert "visibility" not in serializer.fields

    def test_display_order_is_not_exposed(self, serializer):
        assert "display_order" not in serializer.fields

    @pytest.mark.parametrize(
        "platform",
        [
            SocialLink.Platform.TELEGRAM,
            SocialLink.Platform.INSTAGRAM,
            SocialLink.Platform.TWITTER,
            SocialLink.Platform.LINKEDIN,
            SocialLink.Platform.YOUTUBE,
            SocialLink.Platform.GITHUB,
            SocialLink.Platform.FACEBOOK,
            SocialLink.Platform.EMAIL,
        ],
    )
    def test_all_supported_platforms_are_valid(self, platform):
        serializer = SocialLinkSerializer(
            data={
                "platform": platform,
                "address": "https://example.com/profile",
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["platform"] == platform

    def test_invalid_platform_is_rejected(self):
        serializer = SocialLinkSerializer(
            data={
                "platform": "discord",
                "address": "https://example.com/profile",
            }
        )

        assert serializer.is_valid() is False
        assert "platform" in serializer.errors

    def test_missing_platform_is_rejected(self):
        serializer = SocialLinkSerializer(
            data={
                "address": "https://example.com/profile",
            }
        )

        assert serializer.is_valid() is False
        assert "platform" in serializer.errors

    def test_empty_platform_is_rejected(self):
        serializer = SocialLinkSerializer(
            data={
                "platform": "",
                "address": "https://example.com/profile",
            }
        )

        assert serializer.is_valid() is False
        assert "platform" in serializer.errors

    def test_null_platform_is_rejected(self):
        serializer = SocialLinkSerializer(
            data={
                "platform": None,
                "address": "https://example.com/profile",
            }
        )

        assert serializer.is_valid() is False
        assert "platform" in serializer.errors

    def test_missing_address_is_rejected(self):
        serializer = SocialLinkSerializer(
            data={
                "platform": SocialLink.Platform.GITHUB,
            }
        )

        assert serializer.is_valid() is False
        assert "address" in serializer.errors

    def test_empty_address_is_rejected(self):
        serializer = SocialLinkSerializer(
            data={
                "platform": SocialLink.Platform.GITHUB,
                "address": "",
            }
        )

        assert serializer.is_valid() is False
        assert "address" in serializer.errors

    def test_null_address_is_rejected(self):
        serializer = SocialLinkSerializer(
            data={
                "platform": SocialLink.Platform.GITHUB,
                "address": None,
            }
        )

        assert serializer.is_valid() is False
        assert "address" in serializer.errors

    @pytest.mark.parametrize(
        "address",
        [
            "https://github.com/example",
            "http://github.com/example",
            "https://www.instagram.com/example/",
            "https://t.me/example",
            "https://www.linkedin.com/in/example",
            "https://www.youtube.com/@example",
            "https://www.facebook.com/example",
        ],
    )
    def test_valid_url_addresses_are_accepted(self, address):
        serializer = SocialLinkSerializer(
            data={
                "platform": SocialLink.Platform.GITHUB,
                "address": address,
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["address"] == address

    @pytest.mark.parametrize(
        "address",
        [
            "not-a-url",
            "github.com/example",
            "example",
            "://github.com/example",
            "https://",
        ],
    )
    def test_invalid_url_addresses_are_rejected(self, address):
        serializer = SocialLinkSerializer(
            data={
                "platform": SocialLink.Platform.GITHUB,
                "address": address,
            }
        )

        assert serializer.is_valid() is False
        assert "address" in serializer.errors

    def test_address_whitespace_is_trimmed(self):
        serializer = SocialLinkSerializer(
            data={
                "platform": SocialLink.Platform.GITHUB,
                "address": "  https://github.com/example  ",
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["address"] == ("https://github.com/example")

    def test_platform_with_surrounding_whitespace_is_rejected(self):
        serializer = SocialLinkSerializer(
            data={
                "platform": "  github  ",
                "address": "https://github.com/example",
            }
        )

        assert serializer.is_valid() is False
        assert "platform" in serializer.errors

    def test_complete_valid_data_is_valid(self):
        data = {
            "platform": SocialLink.Platform.GITHUB,
            "address": "https://github.com/example",
        }

        serializer = SocialLinkSerializer(data=data)

        assert serializer.is_valid() is True
        assert serializer.validated_data == data

    def test_id_input_is_ignored(self):
        serializer = SocialLinkSerializer(
            data={
                "id": 999,
                "platform": SocialLink.Platform.GITHUB,
                "address": "https://github.com/example",
            }
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data == {
            "platform": SocialLink.Platform.GITHUB,
            "address": "https://github.com/example",
        }

    def test_profile_input_is_ignored(self, profile):
        serializer = SocialLinkSerializer(
            data={
                "profile": profile.pk,
                "platform": SocialLink.Platform.GITHUB,
                "address": "https://github.com/example",
            }
        )

        assert serializer.is_valid() is True
        assert "profile" not in serializer.validated_data

    def test_visibility_input_is_ignored(self):
        serializer = SocialLinkSerializer(
            data={
                "platform": SocialLink.Platform.GITHUB,
                "address": "https://github.com/example",
                "visibility": SocialLink.Visibility.PRIVATE,
            }
        )

        assert serializer.is_valid() is True
        assert "visibility" not in serializer.validated_data

    def test_display_order_input_is_ignored(self):
        serializer = SocialLinkSerializer(
            data={
                "platform": SocialLink.Platform.GITHUB,
                "address": "https://github.com/example",
                "display_order": 10,
            }
        )

        assert serializer.is_valid() is True
        assert "display_order" not in serializer.validated_data

    def test_partial_update_allows_platform_to_be_omitted(
        self,
        social_link,
    ):
        serializer = SocialLinkSerializer(
            social_link,
            data={"address": "https://github.com/new-profile"},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data == {
            "address": "https://github.com/new-profile",
        }

    def test_partial_update_allows_address_to_be_omitted(
        self,
        social_link,
    ):
        serializer = SocialLinkSerializer(
            social_link,
            data={"platform": SocialLink.Platform.LINKEDIN},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data == {
            "platform": SocialLink.Platform.LINKEDIN,
        }

    def test_partial_update_can_change_platform(self, social_link):
        serializer = SocialLinkSerializer(
            social_link,
            data={"platform": SocialLink.Platform.LINKEDIN},
            partial=True,
        )

        assert serializer.is_valid() is True

        updated_link = serializer.save()

        assert updated_link.platform == SocialLink.Platform.LINKEDIN
        assert updated_link.address == "https://github.com/example"

    def test_partial_update_can_change_address(self, social_link):
        serializer = SocialLinkSerializer(
            social_link,
            data={"address": "https://gitlab.com/example"},
            partial=True,
        )

        assert serializer.is_valid() is True

        updated_link = serializer.save()

        assert updated_link.platform == SocialLink.Platform.GITHUB
        assert updated_link.address == "https://gitlab.com/example"

    def test_partial_update_can_change_platform_and_address(
        self,
        social_link,
    ):
        serializer = SocialLinkSerializer(
            social_link,
            data={
                "platform": SocialLink.Platform.LINKEDIN,
                "address": "https://linkedin.com/in/example",
            },
            partial=True,
        )

        assert serializer.is_valid() is True

        updated_link = serializer.save()

        assert updated_link.platform == SocialLink.Platform.LINKEDIN
        assert updated_link.address == ("https://linkedin.com/in/example")

    def test_partial_update_with_empty_data_is_valid(self, social_link):
        serializer = SocialLinkSerializer(
            social_link,
            data={},
            partial=True,
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data == {}

    def test_full_update_requires_platform(self, social_link):
        serializer = SocialLinkSerializer(
            social_link,
            data={
                "address": "https://github.com/new-profile",
            },
        )

        assert serializer.is_valid() is False
        assert "platform" in serializer.errors

    def test_full_update_requires_address(self, social_link):
        serializer = SocialLinkSerializer(
            social_link,
            data={
                "platform": SocialLink.Platform.LINKEDIN,
            },
        )

        assert serializer.is_valid() is False
        assert "address" in serializer.errors

    def test_full_update_does_not_require_unexposed_model_fields(
        self,
        social_link,
    ):
        serializer = SocialLinkSerializer(
            social_link,
            data={
                "platform": SocialLink.Platform.LINKEDIN,
                "address": "https://linkedin.com/in/example",
            },
        )

        assert serializer.is_valid() is True

    def test_full_update_saves_platform_and_address(self, social_link):
        serializer = SocialLinkSerializer(
            social_link,
            data={
                "platform": SocialLink.Platform.LINKEDIN,
                "address": "https://linkedin.com/in/example",
            },
        )

        assert serializer.is_valid() is True

        updated_link = serializer.save()

        assert updated_link.pk == social_link.pk
        assert updated_link.platform == SocialLink.Platform.LINKEDIN
        assert updated_link.address == ("https://linkedin.com/in/example")

    def test_profile_is_not_changed_by_update(
        self,
        social_link,
        profile,
    ):
        serializer = SocialLinkSerializer(
            social_link,
            data={
                "platform": SocialLink.Platform.LINKEDIN,
                "address": "https://linkedin.com/in/example",
                "profile": profile.pk + 1,
            },
        )

        assert serializer.is_valid() is True

        updated_link = serializer.save()

        assert updated_link.profile_id == profile.pk

    def test_id_cannot_be_changed_by_update(self, social_link):
        original_pk = social_link.pk

        serializer = SocialLinkSerializer(
            social_link,
            data={
                "id": original_pk + 100,
                "platform": SocialLink.Platform.LINKEDIN,
                "address": "https://linkedin.com/in/example",
            },
        )

        assert serializer.is_valid() is True

        updated_link = serializer.save()

        assert updated_link.pk == original_pk

    def test_visibility_is_not_changed_by_update(self, social_link):
        original_visibility = social_link.visibility

        serializer = SocialLinkSerializer(
            social_link,
            data={
                "platform": SocialLink.Platform.LINKEDIN,
                "address": "https://linkedin.com/in/example",
                "visibility": SocialLink.Visibility.PRIVATE,
            },
        )

        assert serializer.is_valid() is True

        updated_link = serializer.save()

        assert updated_link.visibility == original_visibility

    def test_display_order_is_not_changed_by_update(self, social_link):
        original_display_order = social_link.display_order

        serializer = SocialLinkSerializer(
            social_link,
            data={
                "platform": SocialLink.Platform.LINKEDIN,
                "address": "https://linkedin.com/in/example",
                "display_order": 50,
            },
        )

        assert serializer.is_valid() is True

        updated_link = serializer.save()

        assert updated_link.display_order == original_display_order

    def test_representation_contains_only_serializer_fields(
        self,
        social_link,
    ):
        serializer = SocialLinkSerializer(social_link)

        assert set(serializer.data) == {
            "id",
            "platform",
            "address",
        }

    def test_representation_contains_expected_values(self, social_link):
        serializer = SocialLinkSerializer(social_link)

        assert serializer.data == {
            "id": social_link.pk,
            "platform": SocialLink.Platform.GITHUB,
            "address": "https://github.com/example",
        }

    def test_representation_returns_platform_value_not_display_label(
        self,
        social_link,
    ):
        serializer = SocialLinkSerializer(social_link)

        assert serializer.data["platform"] == "github"
        assert serializer.data["platform"] != "GitHub"

    def test_representation_returns_url_as_string(self, social_link):
        serializer = SocialLinkSerializer(social_link)

        assert serializer.data["address"] == ("https://github.com/example")

    def test_serialization_does_not_mutate_instance(self, social_link):
        original_values = {
            "pk": social_link.pk,
            "platform": social_link.platform,
            "address": social_link.address,
            "profile_id": social_link.profile_id,
            "visibility": social_link.visibility,
            "display_order": social_link.display_order,
        }

        serializer = SocialLinkSerializer(social_link)

        assert serializer.data

        assert social_link.pk == original_values["pk"]
        assert social_link.platform == original_values["platform"]
        assert social_link.address == original_values["address"]
        assert social_link.profile_id == original_values["profile_id"]
        assert social_link.visibility == original_values["visibility"]
        assert social_link.display_order == original_values["display_order"]

    def test_serializer_does_not_expose_visibility_even_when_private(
        self,
        social_link,
    ):
        social_link.visibility = SocialLink.Visibility.PRIVATE
        social_link.save(update_fields=["visibility"])

        serializer = SocialLinkSerializer(social_link)

        assert "visibility" not in serializer.data

    def test_serializer_does_not_expose_display_order(
        self,
        social_link,
    ):
        social_link.display_order = 25
        social_link.save(update_fields=["display_order"])

        serializer = SocialLinkSerializer(social_link)

        assert "display_order" not in serializer.data
