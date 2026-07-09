# tests/accounts/test_profile_model.py

import pytest
from django.db import IntegrityError
from django.utils import timezone

from accounts.tests.factories import UserFactory
from profiles.models import InstructorProfile, Profile, StudentProfile

from .factories import InstructorProfileFactory, ProfileFactory, StudentProfileFactory


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


@pytest.mark.django_db
class TestInstructorProfileModel:
    @pytest.fixture
    def profile(self):
        return ProfileFactory()

    @pytest.fixture
    def instructor_profile(self, profile):
        return InstructorProfileFactory(profile=profile)

    def test_create_instructor_profile(self, profile):
        """An instructor profile can be created."""
        instructor = InstructorProfile.objects.create(
            profile=profile,
            professional_title="Senior Python Instructor",
            organization="OpenAI Academy",
            years_of_experience=8,
        )

        assert instructor.profile == profile
        assert instructor.professional_title == "Senior Python Instructor"
        assert instructor.organization == "OpenAI Academy"
        assert instructor.years_of_experience == 8
        assert instructor.is_verified is False

    def test_string_representation(self, instructor_profile):
        """The string representation should include the username and title."""
        expected = (
            f"{instructor_profile.profile.user.username} - "
            f"{instructor_profile.professional_title}"
        )

        assert str(instructor_profile) == expected

    def test_profile_can_access_instructor_profile(self, instructor_profile):
        """A profile should access its instructor profile through the reverse relation."""
        assert instructor_profile.profile.instructor_profile == instructor_profile

    def test_profile_can_have_only_one_instructor_profile(self, profile):
        """A profile cannot have more than one instructor profile."""
        InstructorProfileFactory(profile=profile)

        with pytest.raises(IntegrityError):
            InstructorProfileFactory(profile=profile)

    def test_is_verified_defaults_to_false(self, instructor_profile):
        """New instructor profiles should not be verified by default."""
        assert instructor_profile.is_verified is False

    def test_optional_fields_can_be_blank(self, profile):
        """Optional fields may be omitted when creating a profile."""
        instructor = InstructorProfile.objects.create(
            profile=profile,
            professional_title="Backend Instructor",
        )

        assert instructor.organization == ""
        assert instructor.introduction_video.name == ""
        assert instructor.years_of_experience == 0

    def test_deleting_profile_deletes_instructor_profile(self):
        """Deleting a profile should delete its instructor profile."""
        profile = ProfileFactory()
        InstructorProfileFactory(profile=profile)

        profile.delete()

        assert InstructorProfile.objects.count() == 0


@pytest.mark.django_db
class TestStudentProfileModel:
    @pytest.fixture
    def profile(self):
        return ProfileFactory()

    @pytest.fixture
    def student_profile(self, profile):
        return StudentProfileFactory(profile=profile)

    def test_create_student_profile(self, profile):
        """A student profile can be created."""
        student_profile = StudentProfile.objects.create(
            profile=profile,
            learning_goal="Become a Django developer",
            current_streak=15,
            longest_streak=42,
        )

        assert student_profile.profile == profile
        assert student_profile.learning_goal == "Become a Django developer"
        assert student_profile.current_streak == 15
        assert student_profile.longest_streak == 42

    def test_string_representation(self, student_profile):
        """Returns a human-readable representation."""
        expected = f"{student_profile.profile.user.username}'s Student Profile"

        assert str(student_profile) == expected

    def test_profile_can_access_student_profile(self, student_profile):
        """A profile should access its student profile through the reverse relation."""
        assert student_profile.profile.student_profile == student_profile

    def test_profile_cannot_have_multiple_student_profiles(self, profile):
        """A profile can own only one student profile."""
        StudentProfileFactory(profile=profile)

        with pytest.raises(IntegrityError):
            StudentProfileFactory(profile=profile)

    def test_learning_goal_is_optional(self, profile):
        """A learning goal is not required."""
        student_profile = StudentProfile.objects.create(profile=profile)

        assert student_profile.learning_goal == ""

    def test_streaks_default_to_zero(self, profile):
        """New student profiles should start with zero streaks."""
        student_profile = StudentProfile.objects.create(profile=profile)

        assert student_profile.current_streak == 0
        assert student_profile.longest_streak == 0

    def test_deleting_profile_deletes_student_profile(self):
        """Deleting a profile should delete the related student profile."""
        profile = ProfileFactory()
        StudentProfileFactory(profile=profile)

        profile.delete()

        assert StudentProfile.objects.count() == 0
