import pytest
from django.contrib.auth import get_user_model
from rest_framework import serializers

from accounts.api.serializers import (
    InstructorProfileSerializer,
    StudentRegistrationSerializer,
    UserRegisterationSerializer,
    UserRegisterProfileSerializer,
)
from profiles.models import InstructorProfile, Profile

User = get_user_model()


@pytest.mark.django_db
class TestUserRegisterationSerializer:
    def test_fields_are_limited_to_registration_fields(self):
        serializer = UserRegisterationSerializer()

        assert set(serializer.fields) == {
            "username",
            "email",
            "first_name",
            "last_name",
        }

    def test_serializes_user(self, test_user):
        serializer = UserRegisterationSerializer(test_user)

        assert serializer.data == {
            "username": test_user.username,
            "email": test_user.email,
            "first_name": test_user.first_name,
            "last_name": test_user.last_name,
        }

    def test_valid_data_is_valid(self):
        data = {
            "username": "new_user",
            "email": "new_user@example.com",
            "first_name": "Test",
            "last_name": "User",
        }

        serializer = UserRegisterationSerializer(data=data)

        assert serializer.is_valid(), serializer.errors

    def test_valid_data_can_create_user(self):
        data = {
            "username": "new_user",
            "email": "new_user@example.com",
            "first_name": "Test",
            "last_name": "User",
        }

        serializer = UserRegisterationSerializer(data=data)

        assert serializer.is_valid(), serializer.errors

        user = serializer.save()

        assert isinstance(user, User)
        assert user.username == "new_user"
        assert user.email == "new_user@example.com"
        assert user.first_name == "Test"
        assert user.last_name == "User"

    def test_username_is_required(self):
        data = {
            "email": "new_user@example.com",
            "first_name": "Test",
            "last_name": "User",
        }

        serializer = UserRegisterationSerializer(data=data)

        assert serializer.is_valid() is False
        assert "username" in serializer.errors

    def test_email_is_required(self):
        data = {
            "username": "new_user",
            "first_name": "Test",
            "last_name": "User",
        }

        serializer = UserRegisterationSerializer(data=data)

        assert serializer.is_valid() is False
        assert "email" in serializer.errors

    def test_invalid_email_is_rejected(self):
        data = {
            "username": "new_user",
            "email": "invalid-email",
            "first_name": "Test",
            "last_name": "User",
        }

        serializer = UserRegisterationSerializer(data=data)

        assert serializer.is_valid() is False
        assert "email" in serializer.errors

    def test_duplicate_username_is_rejected(
        self,
        test_user,
    ):
        data = {
            "username": test_user.username,
            "email": "another@example.com",
            "first_name": "Test",
            "last_name": "User",
        }

        serializer = UserRegisterationSerializer(data=data)

        assert serializer.is_valid() is False
        assert "username" in serializer.errors

    def test_duplicate_email_is_rejected(
        self,
        test_user,
    ):
        data = {
            "username": "another_user",
            "email": test_user.email,
            "first_name": "Test",
            "last_name": "User",
        }

        serializer = UserRegisterationSerializer(data=data)

        assert serializer.is_valid() is False
        assert "email" in serializer.errors

    def test_first_name_is_optional(self):
        data = {
            "username": "new_user",
            "email": "new_user@example.com",
            "last_name": "User",
        }

        serializer = UserRegisterationSerializer(data=data)

        assert serializer.is_valid(), serializer.errors

    def test_last_name_is_optional(self):
        data = {
            "username": "new_user",
            "email": "new_user@example.com",
            "first_name": "Test",
        }

        serializer = UserRegisterationSerializer(data=data)

        assert serializer.is_valid(), serializer.errors

    def test_password_is_not_in_validated_data(self):
        data = {
            "username": "new_user",
            "email": "new_user@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "test-password",
        }

        serializer = UserRegisterationSerializer(data=data)

        assert serializer.is_valid(), serializer.errors
        assert "password" not in serializer.validated_data


@pytest.mark.django_db
class TestStudentRegistrationSerializer:
    def test_fields_include_registration_and_password_fields(self):
        serializer = StudentRegistrationSerializer()

        assert set(serializer.fields) == {
            "username",
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
        }

    def test_password_fields_are_write_only(self):
        serializer = StudentRegistrationSerializer()

        assert serializer.fields["password1"].write_only is True
        assert serializer.fields["password2"].write_only is True

    def test_valid_matching_passwords_are_accepted(self):
        data = {
            "username": "new_user",
            "email": "new_user@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password1": "Strong-password-123!",
            "password2": "Strong-password-123!",
        }

        serializer = StudentRegistrationSerializer(data=data)

        assert serializer.is_valid(), serializer.errors

    def test_matching_passwords_are_available_in_validated_data(self):
        data = {
            "username": "new_user",
            "email": "new_user@example.com",
            "password1": "Strong-password-123!",
            "password2": "Strong-password-123!",
        }

        serializer = StudentRegistrationSerializer(data=data)

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["password1"] == "Strong-password-123!"
        assert serializer.validated_data["password2"] == "Strong-password-123!"

    def test_mismatched_passwords_are_rejected(self):
        data = {
            "username": "new_user",
            "email": "new_user@example.com",
            "password1": "Strong-password-123!",
            "password2": "Different-password-123!",
        }

        serializer = StudentRegistrationSerializer(data=data)

        assert serializer.is_valid() is False
        assert serializer.errors == {"password2": ["Passwords do not match."]}

    def test_weak_password_is_rejected(self, monkeypatch):
        def reject_password(password):
            raise serializers.ValidationError("This password is too weak.")

        monkeypatch.setattr(
            "accounts.api.serializers.validate_password",
            reject_password,
        )

        data = {
            "username": "new_user",
            "email": "new_user@example.com",
            "password1": "weak-password",
            "password2": "weak-password",
        }

        serializer = StudentRegistrationSerializer(data=data)

        assert serializer.is_valid() is False
        assert serializer.errors == {"non_field_errors": ["This password is too weak."]}

    def test_password_validation_is_called_for_matching_passwords(
        self,
        monkeypatch,
    ):
        called_with = []

        def validate(password):
            called_with.append(password)

        monkeypatch.setattr(
            "accounts.api.serializers.validate_password",
            validate,
        )

        data = {
            "username": "new_user",
            "email": "new_user@example.com",
            "password1": "Strong-password-123!",
            "password2": "Strong-password-123!",
        }

        serializer = StudentRegistrationSerializer(data=data)

        assert serializer.is_valid(), serializer.errors
        assert called_with == ["Strong-password-123!"]

    def test_password_validation_is_not_called_when_passwords_mismatch(
        self,
        monkeypatch,
    ):
        called = False

        def validate(password):
            nonlocal called
            called = True

        monkeypatch.setattr(
            "accounts.api.serializers.validate_password",
            validate,
        )

        data = {
            "username": "new_user",
            "email": "new_user@example.com",
            "password1": "Strong-password-123!",
            "password2": "Different-password-123!",
        }

        serializer = StudentRegistrationSerializer(data=data)

        assert serializer.is_valid() is False
        assert called is False

    def test_password_fields_are_not_in_representation(self):
        user = User(
            username="test_user",
            email="test_user@example.com",
            first_name="Test",
            last_name="User",
        )

        serializer = StudentRegistrationSerializer(user)

        assert "password1" not in serializer.data
        assert "password2" not in serializer.data

    def test_password1_is_required(self):
        data = {
            "username": "new_user",
            "email": "new_user@example.com",
            "password2": "Strong-password-123!",
        }

        serializer = StudentRegistrationSerializer(data=data)

        assert serializer.is_valid() is False
        assert "password1" in serializer.errors

    def test_password2_is_required(self):
        data = {
            "username": "new_user",
            "email": "new_user@example.com",
            "password1": "Strong-password-123!",
        }

        serializer = StudentRegistrationSerializer(data=data)

        assert serializer.is_valid() is False
        assert "password2" in serializer.errors

    def test_optional_user_fields_remain_optional(self):
        data = {
            "username": "new_user",
            "email": "new_user@example.com",
            "password1": "Strong-password-123!",
            "password2": "Strong-password-123!",
        }

        serializer = StudentRegistrationSerializer(data=data)

        assert serializer.is_valid(), serializer.errors

    def test_unknown_password_field_is_not_accepted_as_password_input(self):
        data = {
            "username": "new_user",
            "email": "new_user@example.com",
            "password1": "Strong-password-123!",
            "password2": "Strong-password-123!",
            "password": "another-password",
        }

        serializer = StudentRegistrationSerializer(data=data)

        assert serializer.is_valid(), serializer.errors
        assert "password" not in serializer.validated_data


@pytest.mark.django_db
class TestUserRegisterProfileSerializer:
    def test_fields_are_defined_correctly(self):
        serializer = UserRegisterProfileSerializer()

        assert set(serializer.fields) == {
            "website",
            "country",
            "linkedin",
            "github",
        }

    def test_serializes_profile(self, profile):
        profile.website = "https://example.com"
        profile.country = "Example Country"
        profile.linkedin = "https://linkedin.com/in/test-user"
        profile.github = "https://github.com/test-user"
        profile.save()

        serializer = UserRegisterProfileSerializer(profile)

        assert serializer.data == {
            "website": "https://example.com",
            "country": "Example Country",
            "linkedin": "https://linkedin.com/in/test-user",
            "github": "https://github.com/test-user",
        }

    def test_all_fields_are_optional(self):
        serializer = UserRegisterProfileSerializer(data={})

        assert serializer.is_valid(), serializer.errors

    def test_valid_profile_data_is_accepted(self):
        data = {
            "website": "https://example.com",
            "country": "Example Country",
            "linkedin": "https://linkedin.com/in/test-user",
            "github": "https://github.com/test-user",
        }

        serializer = UserRegisterProfileSerializer(data=data)

        assert serializer.is_valid(), serializer.errors

    def test_invalid_website_is_rejected(self):
        data = {
            "website": "not-a-url",
            "country": "Example Country",
            "linkedin": "https://linkedin.com/in/test-user",
            "github": "https://github.com/test-user",
        }

        serializer = UserRegisterProfileSerializer(data=data)

        assert serializer.is_valid() is False
        assert "website" in serializer.errors

    def test_invalid_linkedin_is_rejected(self):
        data = {
            "website": "https://example.com",
            "country": "Example Country",
            "linkedin": "not-a-url",
            "github": "https://github.com/test-user",
        }

        serializer = UserRegisterProfileSerializer(data=data)

        assert serializer.is_valid() is False
        assert "linkedin" in serializer.errors

    def test_invalid_github_is_rejected(self):
        data = {
            "website": "https://example.com",
            "country": "Example Country",
            "linkedin": "https://linkedin.com/in/test-user",
            "github": "not-a-url",
        }

        serializer = UserRegisterProfileSerializer(data=data)

        assert serializer.is_valid() is False
        assert "github" in serializer.errors

    def test_empty_optional_fields_are_accepted(self):
        data = {
            "website": "",
            "country": "",
            "linkedin": "",
            "github": "",
        }

        serializer = UserRegisterProfileSerializer(data=data)

        assert serializer.is_valid(), serializer.errors

    def test_creates_profile(self, test_user):
        data = {
            "website": "https://example.com",
            "country": "Example Country",
            "linkedin": "https://linkedin.com/in/test-user",
            "github": "https://github.com/test-user",
        }

        serializer = UserRegisterProfileSerializer(data=data)

        assert serializer.is_valid(), serializer.errors

        profile = serializer.save(user=test_user)

        assert isinstance(profile, Profile)
        assert profile.user == test_user
        assert profile.website == "https://example.com"
        assert profile.country == "Example Country"
        assert profile.linkedin == "https://linkedin.com/in/test-user"
        assert profile.github == "https://github.com/test-user"

    def test_updates_existing_profile(self, profile):
        data = {
            "website": "https://new-example.com",
            "country": "New Country",
            "linkedin": "https://linkedin.com/in/new-user",
            "github": "https://github.com/new-user",
        }

        serializer = UserRegisterProfileSerializer(
            profile,
            data=data,
        )

        assert serializer.is_valid(), serializer.errors

        updated_profile = serializer.save()

        assert updated_profile.pk == profile.pk
        assert updated_profile.website == "https://new-example.com"
        assert updated_profile.country == "New Country"
        assert updated_profile.linkedin == ("https://linkedin.com/in/new-user")
        assert updated_profile.github == ("https://github.com/new-user")

    def test_partial_update_only_changes_supplied_fields(
        self,
        profile,
    ):
        profile.website = "https://old-example.com"
        profile.country = "Old Country"
        profile.linkedin = "https://linkedin.com/in/old-user"
        profile.github = "https://github.com/old-user"
        profile.save()

        serializer = UserRegisterProfileSerializer(
            profile,
            data={
                "country": "New Country",
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        updated_profile = serializer.save()

        assert updated_profile.country == "New Country"
        assert updated_profile.website == ("https://old-example.com")
        assert updated_profile.linkedin == ("https://linkedin.com/in/old-user")
        assert updated_profile.github == ("https://github.com/old-user")

    def test_password_is_not_exposed(self, profile):
        serializer = UserRegisterProfileSerializer(profile)

        assert "password" not in serializer.data

    def test_only_declared_fields_are_in_output(self, profile):
        serializer = UserRegisterProfileSerializer(profile)

        assert set(serializer.data.keys()) == {
            "website",
            "country",
            "linkedin",
            "github",
        }


@pytest.mark.django_db
class TestInstructorProfileSerializer:
    def test_fields_are_defined_correctly(self):
        serializer = InstructorProfileSerializer()

        assert set(serializer.fields) == {
            "headline",
            "biography",
            "professional_title",
            "organization",
            "years_of_experience",
        }

    def test_serializes_instructor_profile(self, instructor_profile):
        instructor_profile.headline = "Senior Backend Developer"
        instructor_profile.biography = "Experienced software developer."
        instructor_profile.professional_title = "Software Engineer"
        instructor_profile.organization = "Example Organization"
        instructor_profile.years_of_experience = 8
        instructor_profile.save()

        serializer = InstructorProfileSerializer(instructor_profile)

        assert serializer.data == {
            "headline": "Senior Backend Developer",
            "biography": "Experienced software developer.",
            "professional_title": "Software Engineer",
            "organization": "Example Organization",
            "years_of_experience": 8,
        }

    def test_valid_data_is_accepted(self):
        data = {
            "headline": "Senior Backend Developer",
            "biography": "Experienced software developer.",
            "professional_title": "Software Engineer",
            "organization": "Example Organization",
            "years_of_experience": 8,
        }

        serializer = InstructorProfileSerializer(data=data)

        assert serializer.is_valid(), serializer.errors

    def test_headline_is_optional(self):
        data = {
            "biography": "Experienced software developer.",
            "professional_title": "Software Engineer",
            "organization": "Example Organization",
            "years_of_experience": 8,
        }

        serializer = InstructorProfileSerializer(data=data)

        assert serializer.is_valid(), serializer.errors

    def test_biography_is_optional(self):
        data = {
            "headline": "Senior Backend Developer",
            "professional_title": "Software Engineer",
            "organization": "Example Organization",
            "years_of_experience": 8,
        }

        serializer = InstructorProfileSerializer(data=data)

        assert serializer.is_valid(), serializer.errors

    def test_organization_is_optional(self):
        data = {
            "headline": "Senior Backend Developer",
            "biography": "Experienced software developer.",
            "professional_title": "Software Engineer",
            "years_of_experience": 8,
        }

        serializer = InstructorProfileSerializer(data=data)

        assert serializer.is_valid(), serializer.errors

    def test_years_of_experience_is_optional(self):
        data = {
            "headline": "Senior Backend Developer",
            "biography": "Experienced software developer.",
            "professional_title": "Software Engineer",
            "organization": "Example Organization",
        }

        serializer = InstructorProfileSerializer(data=data)

        assert serializer.is_valid(), serializer.errors

    def test_negative_years_of_experience_is_rejected(self):
        data = {
            "headline": "Instructor",
            "years_of_experience": -1,
        }

        serializer = InstructorProfileSerializer(data=data)

        assert serializer.is_valid() is False
        assert "years_of_experience" in serializer.errors

    def test_creates_instructor_profile(self, profile):
        data = {
            "headline": "Senior Backend Developer",
            "biography": "Experienced software developer.",
            "professional_title": "Software Engineer",
            "organization": "Example Organization",
            "years_of_experience": 8,
        }

        serializer = InstructorProfileSerializer(data=data)

        assert serializer.is_valid(), serializer.errors

        instructor_profile = serializer.save(profile=profile)

        assert isinstance(instructor_profile, InstructorProfile)
        assert instructor_profile.profile == profile
        assert instructor_profile.headline == "Senior Backend Developer"
        assert instructor_profile.biography == ("Experienced software developer.")
        assert instructor_profile.professional_title == "Software Engineer"
        assert instructor_profile.organization == "Example Organization"
        assert instructor_profile.years_of_experience == 8

    def test_updates_existing_instructor_profile(
        self,
        instructor_profile,
    ):
        data = {
            "headline": "Updated Instructor",
            "biography": "Updated biography.",
            "professional_title": "Lead Engineer",
            "organization": "Updated Organization",
            "years_of_experience": 10,
        }

        serializer = InstructorProfileSerializer(
            instructor_profile,
            data=data,
        )

        assert serializer.is_valid(), serializer.errors

        updated_profile = serializer.save()

        assert updated_profile.pk == instructor_profile.pk
        assert updated_profile.headline == "Updated Instructor"
        assert updated_profile.biography == "Updated biography."
        assert updated_profile.professional_title == "Lead Engineer"
        assert updated_profile.organization == "Updated Organization"
        assert updated_profile.years_of_experience == 10

    def test_partial_update_changes_only_supplied_fields(
        self,
        instructor_profile,
    ):
        instructor_profile.headline = "Original Headline"
        instructor_profile.biography = "Original biography."
        instructor_profile.professional_title = "Original Title"
        instructor_profile.organization = "Original Organization"
        instructor_profile.years_of_experience = 5
        instructor_profile.save()

        serializer = InstructorProfileSerializer(
            instructor_profile,
            data={
                "headline": "Updated Headline",
                "years_of_experience": 7,
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        updated_profile = serializer.save()

        assert updated_profile.headline == "Updated Headline"
        assert updated_profile.years_of_experience == 7
        assert updated_profile.biography == "Original biography."
        assert updated_profile.professional_title == "Original Title"
        assert updated_profile.organization == "Original Organization"

    def test_unrelated_profile_fields_are_not_exposed(
        self,
        instructor_profile,
    ):
        serializer = InstructorProfileSerializer(instructor_profile)

        assert "profile" not in serializer.data
        assert "avatar" not in serializer.data
        assert "website" not in serializer.data
        assert "country" not in serializer.data
        assert "company" not in serializer.data
        assert "job_title" not in serializer.data

    def test_only_declared_fields_are_in_output(
        self,
        instructor_profile,
    ):
        serializer = InstructorProfileSerializer(instructor_profile)

        assert set(serializer.data.keys()) == {
            "headline",
            "biography",
            "professional_title",
            "organization",
            "years_of_experience",
        }

    def test_empty_data_is_invalid_when_professional_title_is_required(self):
        serializer = InstructorProfileSerializer(data={})

        assert serializer.is_valid() is False
        assert "professional_title" in serializer.errors

    def test_professional_title_is_required(self):
        serializer = InstructorProfileSerializer(data={})

        assert serializer.is_valid() is False
        assert serializer.errors["professional_title"][0] == "This field is required."

    def test_years_of_experience_accepts_zero(self):
        data = {
            "professional_title": "Senior Developer",
            "years_of_experience": 0,
        }

        serializer = InstructorProfileSerializer(data=data)

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["years_of_experience"] == 0
