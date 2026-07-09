# tests/accounts/test_profile_model.py

import pytest
from django.db import IntegrityError
from django.utils import timezone

from accounts.tests.factories import UserFactory
from profiles.models import Profile

from .factories import ProfileFactory


@pytest.mark.django_db
class TestProfileModel:
    @pytest.fixture
    def user(self):
        return UserFactory()

    @pytest.fixture
    def profile(self, user):
        return ProfileFactory(user=user)

    def test_create_profile(self, user):
        """A profile can be created for a user."""
        profile = Profile.objects.create(
            user=user,
            biography="Software engineer.",
            headline="Backend Developer",
            website="https://example.com",
        )

        assert profile.user == user
        assert profile.biography == "Software engineer."
        assert profile.headline == "Backend Developer"
        assert profile.website == "https://example.com"

    def test_string_representation(self, profile):
        """The string representation should include the username."""
        assert str(profile) == f"{profile.user.username}'s Profile"

    def test_user_can_access_profile(self, profile):
        """A user should access its profile through the reverse relation."""
        assert profile.user.profile == profile

    def test_user_can_have_only_one_profile(self, user):
        """A user cannot have more than one profile."""
        ProfileFactory(user=user)

        with pytest.raises(IntegrityError):
            ProfileFactory(user=user)

    def test_optional_fields_can_be_blank(self, user):
        """A profile can be created with only the required field."""
        profile = Profile.objects.create(user=user)

        assert profile.biography == ""
        assert profile.headline == ""
        assert profile.website == ""
        assert profile.country == ""
        assert profile.timezone == ""
        assert profile.language == ""
        assert profile.linkedin == ""
        assert profile.github == ""
        assert profile.company == ""
        assert profile.job_title == ""
        assert profile.avatar.name == ""
        assert profile.date_of_birth is None

    def test_created_at_is_set_on_creation(self, profile):
        """Creating a profile should populate created_at."""
        assert profile.created_at is not None
        assert profile.created_at <= timezone.now()

    def test_updated_at_is_set_on_creation(self, profile):
        """Creating a profile should populate updated_at."""
        assert profile.updated_at is not None
        assert profile.updated_at <= timezone.now()

    def test_updated_at_changes_after_save(self, profile):
        """Saving a profile should update updated_at."""
        original = profile.updated_at

        profile.headline = "Senior Backend Developer"
        profile.save()

        profile.refresh_from_db()

        assert profile.updated_at >= original

    def test_deleting_user_deletes_profile(self):
        """Deleting a user should delete the related profile."""
        user = UserFactory()
        ProfileFactory(user=user)

        user.delete()

        assert Profile.objects.count() == 0
