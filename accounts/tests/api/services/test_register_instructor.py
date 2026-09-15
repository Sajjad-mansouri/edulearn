from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from rest_framework.exceptions import ValidationError

from accounts.api.services import register_instructor
from accounts.models import Role
from profiles.models import Education, InstructorProfile, Profile, Skill

User = get_user_model()


@pytest.fixture
def request_factory():
    return RequestFactory()


@pytest.fixture
def anonymous_request(request_factory):
    request = request_factory.post(
        "/register/instructor/",
        REMOTE_ADDR="192.0.2.10",
    )
    request.user = AnonymousUser()
    return request


@pytest.fixture
def test_user(db):
    return User.objects.create_user(
        username="test_user",
        email="test_user@example.com",
        password="test-password",
        is_active=True,
    )


@pytest.fixture
def existing_profile(db, test_user):
    return Profile.objects.create(
        user=test_user,
        website="https://old.example.com",
        country="Old Country",
        linkedin="https://linkedin.com/old",
        github="https://github.com/old",
    )


@pytest.fixture
def authenticated_request(request_factory, existing_profile):
    request = request_factory.post(
        "/register/instructor/",
        REMOTE_ADDR="192.0.2.10",
    )
    request.user = existing_profile.user
    return request


@pytest.fixture
def user_data():
    return {
        "username": "new_instructor",
        "email": "new_instructor@example.com",
        "password": "strong-password",
    }


@pytest.fixture
def profile_data():
    return {
        "website": "https://example.com",
        "country": "Azerbaijan",
        "linkedin": "https://linkedin.com/in/instructor",
        "github": "https://github.com/instructor",
    }


@pytest.fixture
def instructor_data():
    return {
        "headline": "Backend Developer",
        "biography": "Experienced software developer.",
        "professional_title": "Senior Python Developer",
        "organization": "Example Organization",
        "years_of_experience": 8,
    }


@pytest.fixture
def skills_data():
    return [
        {"name": "Python"},
        {"name": "Django"},
    ]


@pytest.fixture
def educations_data():
    return [
        {
            "institution": "Example University",
            "degree": "Bachelor",
            "field_of_study": "Computer Science",
        },
        {
            "institution": "Example Institute",
            "degree": "Master",
            "field_of_study": "Software Engineering",
        },
    ]


@pytest.fixture
def experiences_data():
    """
    Keep this empty because the exact Experience field names are not
    assumed by the service tests.

    The service's handling of experience_data is tested separately
    by mocking Experience.objects.create().
    """
    return []


@pytest.fixture
def registration_data(
    user_data,
    profile_data,
    instructor_data,
    skills_data,
    educations_data,
    experiences_data,
):
    return {
        "user_data": user_data,
        "profile_data": profile_data,
        "instructor_data": instructor_data,
        "skills_data": skills_data,
        "educations_data": educations_data,
        "experiences_data": experiences_data,
    }


@pytest.mark.django_db
class TestRegisterInstructor:
    def test_creates_new_inactive_user(
        self,
        anonymous_request,
        registration_data,
    ):
        profile, instructor_profile, created = register_instructor(
            request=anonymous_request,
            **registration_data,
        )

        user = profile.user

        assert created is True
        assert user.username == "new_instructor"
        assert user.email == "new_instructor@example.com"
        assert user.is_active is False
        assert user.check_password("strong-password")

        assert instructor_profile.profile == profile

    def test_creates_profile_for_new_user(
        self,
        anonymous_request,
        registration_data,
    ):
        profile, _, _ = register_instructor(
            request=anonymous_request,
            **registration_data,
        )

        assert Profile.objects.filter(
            pk=profile.pk,
            user=profile.user,
        ).exists()

        assert profile.user.username == "new_instructor"

    def test_applies_profile_data_to_new_user(
        self,
        anonymous_request,
        registration_data,
    ):
        profile, _, _ = register_instructor(
            request=anonymous_request,
            **registration_data,
        )

        assert profile.website == "https://example.com"
        assert profile.country == "Azerbaijan"
        assert profile.linkedin == ("https://linkedin.com/in/instructor")
        assert profile.github == ("https://github.com/instructor")

    def test_assigns_instructor_role_to_new_user(
        self,
        anonymous_request,
        registration_data,
    ):
        profile, _, _ = register_instructor(
            request=anonymous_request,
            **registration_data,
        )

        assert profile.user.roles.filter(name=Role.Roles.INSTRUCTOR).exists()

    def test_creates_skills(
        self,
        anonymous_request,
        registration_data,
    ):
        profile, _, _ = register_instructor(
            request=anonymous_request,
            **registration_data,
        )

        skills = Skill.objects.filter(profile=profile)

        assert skills.count() == 2
        assert set(skills.values_list("name", flat=True)) == {"Python", "Django"}

    def test_creates_educations(
        self,
        anonymous_request,
        registration_data,
    ):
        profile, _, _ = register_instructor(
            request=anonymous_request,
            **registration_data,
        )

        educations = Education.objects.filter(
            profile=profile,
        )

        assert educations.count() == 2

        assert educations.filter(
            institution="Example University",
            degree="Bachelor",
            field_of_study="Computer Science",
        ).exists()

        assert educations.filter(
            institution="Example Institute",
            degree="Master",
            field_of_study="Software Engineering",
        ).exists()

    def test_creates_experiences_using_supplied_data(
        self,
        anonymous_request,
        registration_data,
    ):
        experience_data = {
            "company": "Example Company",
            "position": "Backend Developer",
        }

        registration_data["experiences_data"] = [
            experience_data,
        ]

        with patch("accounts.api.services.Experience.objects.create") as mock_create:
            register_instructor(
                request=anonymous_request,
                **registration_data,
            )

        mock_create.assert_called_once()

        assert mock_create.call_args.kwargs["profile"].user.username == (
            "new_instructor"
        )

        assert {
            key: value
            for key, value in mock_create.call_args.kwargs.items()
            if key != "profile"
        } == experience_data

    def test_creates_each_supplied_experience(
        self,
        anonymous_request,
        registration_data,
    ):
        first_experience = {
            "company": "First Company",
            "position": "Developer",
        }
        second_experience = {
            "company": "Second Company",
            "position": "Senior Developer",
        }

        registration_data["experiences_data"] = [
            first_experience,
            second_experience,
        ]

        with patch("accounts.api.services.Experience.objects.create") as mock_create:
            register_instructor(
                request=anonymous_request,
                **registration_data,
            )

        assert mock_create.call_count == 2

        calls = [call.kwargs for call in mock_create.call_args_list]

        assert {
            key: value for key, value in calls[0].items() if key != "profile"
        } == first_experience

        assert {
            key: value for key, value in calls[1].items() if key != "profile"
        } == second_experience

    def test_creates_instructor_profile(
        self,
        anonymous_request,
        registration_data,
    ):
        profile, instructor_profile, created = register_instructor(
            request=anonymous_request,
            **registration_data,
        )

        assert created is True
        assert instructor_profile.profile == profile

        assert InstructorProfile.objects.filter(
            pk=instructor_profile.pk,
            profile=profile,
        ).exists()

    def test_applies_instructor_data(
        self,
        anonymous_request,
        registration_data,
    ):
        _, instructor_profile, _ = register_instructor(
            request=anonymous_request,
            **registration_data,
        )

        assert instructor_profile.headline == ("Backend Developer")
        assert instructor_profile.biography == ("Experienced software developer.")
        assert instructor_profile.professional_title == ("Senior Python Developer")
        assert instructor_profile.organization == ("Example Organization")
        assert instructor_profile.years_of_experience == 8

    def test_new_application_is_pending(
        self,
        anonymous_request,
        registration_data,
    ):
        _, instructor_profile, _ = register_instructor(
            request=anonymous_request,
            **registration_data,
        )

        assert instructor_profile.application_status == "pending"

    def test_new_application_is_not_verified(
        self,
        anonymous_request,
        registration_data,
    ):
        _, instructor_profile, _ = register_instructor(
            request=anonymous_request,
            **registration_data,
        )

        assert instructor_profile.is_verified is False

    def test_new_application_has_empty_rejection_reason(
        self,
        anonymous_request,
        registration_data,
    ):
        _, instructor_profile, _ = register_instructor(
            request=anonymous_request,
            **registration_data,
        )

        assert instructor_profile.rejection_reason == ""

    def test_forces_application_state(
        self,
        anonymous_request,
        registration_data,
    ):
        registration_data["instructor_data"].update(
            {
                "application_status": "approved",
                "is_verified": True,
                "rejection_reason": "Old reason",
            }
        )

        _, instructor_profile, _ = register_instructor(
            request=anonymous_request,
            **registration_data,
        )

        assert instructor_profile.application_status == "pending"
        assert instructor_profile.is_verified is False
        assert instructor_profile.rejection_reason == ""

    def test_returns_created_true_for_new_instructor_profile(
        self,
        anonymous_request,
        registration_data,
    ):
        _, _, created = register_instructor(
            request=anonymous_request,
            **registration_data,
        )

        assert created is True

    def test_reuses_authenticated_user(
        self,
        authenticated_request,
        registration_data,
        test_user,
    ):
        profile, _, _ = register_instructor(
            request=authenticated_request,
            **registration_data,
        )

        assert profile.user_id == test_user.pk
        assert User.objects.count() == 1

    def test_reuses_existing_profile(
        self,
        authenticated_request,
        registration_data,
        existing_profile,
    ):
        profile, _, _ = register_instructor(
            request=authenticated_request,
            **registration_data,
        )

        assert profile.pk == existing_profile.pk
        assert Profile.objects.count() == 1

    def test_updates_existing_profile(
        self,
        authenticated_request,
        registration_data,
        existing_profile,
    ):
        profile, _, _ = register_instructor(
            request=authenticated_request,
            **registration_data,
        )

        existing_profile.refresh_from_db()

        assert profile.pk == existing_profile.pk
        assert existing_profile.website == ("https://example.com")
        assert existing_profile.country == "Azerbaijan"
        assert existing_profile.linkedin == ("https://linkedin.com/in/instructor")
        assert existing_profile.github == ("https://github.com/instructor")

    def test_does_not_change_existing_user(
        self,
        authenticated_request,
        registration_data,
        test_user,
    ):
        original_password = test_user.password

        register_instructor(
            request=authenticated_request,
            **registration_data,
        )

        test_user.refresh_from_db()

        assert test_user.password == original_password
        assert test_user.username == "test_user"
        assert test_user.email == "test_user@example.com"
        assert test_user.is_active is True

    def test_assigns_instructor_role_to_existing_user(
        self,
        authenticated_request,
        registration_data,
        test_user,
    ):
        register_instructor(
            request=authenticated_request,
            **registration_data,
        )

        assert test_user.roles.filter(name=Role.Roles.INSTRUCTOR).exists()

    def test_replaces_existing_skills(
        self,
        authenticated_request,
        registration_data,
        existing_profile,
    ):
        Skill.objects.create(
            profile=existing_profile,
            name="Old Skill",
        )

        register_instructor(
            request=authenticated_request,
            **registration_data,
        )

        skills = Skill.objects.filter(
            profile=existing_profile,
        )

        assert skills.count() == 2
        assert set(skills.values_list("name", flat=True)) == {"Python", "Django"}

        assert not skills.filter(name="Old Skill").exists()

    def test_replaces_existing_educations(
        self,
        authenticated_request,
        registration_data,
        existing_profile,
    ):
        Education.objects.create(
            profile=existing_profile,
            institution="Old University",
            degree="Old Degree",
            field_of_study="Old Field",
        )

        register_instructor(
            request=authenticated_request,
            **registration_data,
        )

        educations = Education.objects.filter(
            profile=existing_profile,
        )

        assert educations.count() == 2

        assert not educations.filter(institution="Old University").exists()

    def test_raises_error_for_approved_instructor(
        self,
        authenticated_request,
        registration_data,
        existing_profile,
    ):
        InstructorProfile.objects.create(
            profile=existing_profile,
            professional_title="Existing Instructor",
            application_status="approved",
            is_verified=True,
        )

        with pytest.raises(
            ValidationError,
            match="You are already an approved instructor.",
        ):
            register_instructor(
                request=authenticated_request,
                **registration_data,
            )

    def test_raises_error_for_pending_instructor(
        self,
        authenticated_request,
        registration_data,
        existing_profile,
    ):
        InstructorProfile.objects.create(
            profile=existing_profile,
            professional_title="Existing Instructor",
            application_status="pending",
            is_verified=False,
        )

        with pytest.raises(
            ValidationError,
            match=("You are already registered. If approved, we will notify you."),
        ):
            register_instructor(
                request=authenticated_request,
                **registration_data,
            )

    def test_approved_application_is_not_modified(
        self,
        authenticated_request,
        registration_data,
        existing_profile,
    ):
        instructor_profile = InstructorProfile.objects.create(
            profile=existing_profile,
            professional_title="Existing Instructor",
            application_status="approved",
            is_verified=True,
        )

        original_title = instructor_profile.professional_title

        with pytest.raises(
            ValidationError,
            match="You are already an approved instructor.",
        ):
            register_instructor(
                request=authenticated_request,
                **registration_data,
            )

        instructor_profile.refresh_from_db()

        assert instructor_profile.application_status == "approved"
        assert instructor_profile.is_verified is True
        assert instructor_profile.professional_title == (original_title)

    def test_pending_application_is_not_modified(
        self,
        authenticated_request,
        registration_data,
        existing_profile,
    ):
        instructor_profile = InstructorProfile.objects.create(
            profile=existing_profile,
            professional_title="Existing Instructor",
            application_status="pending",
            is_verified=False,
        )

        with pytest.raises(
            ValidationError,
            match="You are already registered",
        ):
            register_instructor(
                request=authenticated_request,
                **registration_data,
            )

        instructor_profile.refresh_from_db()

        assert instructor_profile.application_status == "pending"

    def test_pending_application_does_not_replace_profile_data(
        self,
        authenticated_request,
        registration_data,
        existing_profile,
    ):
        InstructorProfile.objects.create(
            profile=existing_profile,
            professional_title="Existing Instructor",
            application_status="pending",
        )

        original_website = existing_profile.website
        original_country = existing_profile.country

        with pytest.raises(
            ValidationError,
            match="You are already registered",
        ):
            register_instructor(
                request=authenticated_request,
                **registration_data,
            )

        existing_profile.refresh_from_db()

        assert existing_profile.website == original_website
        assert existing_profile.country == original_country

    def test_allows_reapplication_after_rejection(
        self,
        authenticated_request,
        registration_data,
        existing_profile,
    ):
        instructor_profile = InstructorProfile.objects.create(
            profile=existing_profile,
            professional_title="Existing Instructor",
            application_status="rejected",
            is_verified=False,
            rejection_reason="Needs improvement",
        )

        profile, updated_profile, created = register_instructor(
            request=authenticated_request,
            **registration_data,
        )

        assert profile.pk == existing_profile.pk
        assert updated_profile.pk == instructor_profile.pk
        assert created is False

        updated_profile.refresh_from_db()

        assert updated_profile.application_status == "pending"
        assert updated_profile.is_verified is False
        assert updated_profile.rejection_reason == ""

    def test_updates_existing_instructor_profile(
        self,
        authenticated_request,
        registration_data,
        existing_profile,
    ):
        instructor_profile = InstructorProfile.objects.create(
            profile=existing_profile,
            professional_title="Old Title",
            application_status="rejected",
            is_verified=False,
            rejection_reason="Old reason",
        )

        _, updated_profile, created = register_instructor(
            request=authenticated_request,
            **registration_data,
        )

        assert updated_profile.pk == instructor_profile.pk
        assert created is False

        assert updated_profile.professional_title == ("Senior Python Developer")
        assert updated_profile.application_status == "pending"
        assert updated_profile.is_verified is False
        assert updated_profile.rejection_reason == ""

    def test_does_not_create_duplicate_instructor_profile(
        self,
        authenticated_request,
        registration_data,
        existing_profile,
    ):
        InstructorProfile.objects.create(
            profile=existing_profile,
            professional_title="Old Title",
            application_status="rejected",
        )

        register_instructor(
            request=authenticated_request,
            **registration_data,
        )

        assert (
            InstructorProfile.objects.filter(
                profile=existing_profile,
            ).count()
            == 1
        )

    def test_reuses_existing_instructor_role(
        self,
        authenticated_request,
        registration_data,
        test_user,
    ):
        role = Role.objects.create(
            name=Role.Roles.INSTRUCTOR,
        )

        register_instructor(
            request=authenticated_request,
            **registration_data,
        )

        assert (
            Role.objects.filter(
                name=Role.Roles.INSTRUCTOR,
            ).count()
            == 1
        )

        assert role.users.filter(
            pk=test_user.pk,
        ).exists()

    def test_does_not_create_duplicate_instructor_role(
        self,
        authenticated_request,
        registration_data,
    ):
        Role.objects.create(
            name=Role.Roles.INSTRUCTOR,
        )

        register_instructor(
            request=authenticated_request,
            **registration_data,
        )

        assert (
            Role.objects.filter(
                name=Role.Roles.INSTRUCTOR,
            ).count()
            == 1
        )

    def test_returns_expected_values_for_new_application(
        self,
        anonymous_request,
        registration_data,
    ):
        profile, instructor_profile, created = register_instructor(
            request=anonymous_request,
            **registration_data,
        )

        assert isinstance(profile, Profile)
        assert isinstance(
            instructor_profile,
            InstructorProfile,
        )
        assert created is True

    def test_returns_expected_values_for_existing_application(
        self,
        authenticated_request,
        registration_data,
        existing_profile,
    ):
        existing_instructor_profile = InstructorProfile.objects.create(
            profile=existing_profile,
            professional_title="Old Title",
            application_status="rejected",
        )

        profile, instructor_profile, created = register_instructor(
            request=authenticated_request,
            **registration_data,
        )

        assert profile.pk == existing_profile.pk
        assert instructor_profile.pk == existing_instructor_profile.pk
        assert created is False

    def test_transaction_rolls_back_new_user_when_skill_creation_fails(
        self,
        anonymous_request,
        registration_data,
    ):
        with patch(
            "accounts.api.services.Skill.objects.create",
            side_effect=RuntimeError("skill creation failed"),
        ):
            with pytest.raises(
                RuntimeError,
                match="skill creation failed",
            ):
                register_instructor(
                    request=anonymous_request,
                    **registration_data,
                )

        assert not User.objects.filter(
            username="new_instructor",
        ).exists()

        assert not Profile.objects.filter(
            user__username="new_instructor",
        ).exists()

        assert not Role.objects.filter(
            name=Role.Roles.INSTRUCTOR,
        ).exists()

        assert not Skill.objects.filter(
            profile__user__username="new_instructor",
        ).exists()

        assert not Education.objects.filter(
            profile__user__username="new_instructor",
        ).exists()

        assert not InstructorProfile.objects.filter(
            profile__user__username="new_instructor",
        ).exists()

    def test_transaction_rolls_back_when_education_creation_fails(
        self,
        anonymous_request,
        registration_data,
    ):
        with patch(
            "accounts.api.services.Education.objects.create",
            side_effect=RuntimeError("education creation failed"),
        ):
            with pytest.raises(
                RuntimeError,
                match="education creation failed",
            ):
                register_instructor(
                    request=anonymous_request,
                    **registration_data,
                )

        assert not User.objects.filter(
            username="new_instructor",
        ).exists()

        assert not Profile.objects.filter(
            user__username="new_instructor",
        ).exists()

        assert not Skill.objects.filter(
            profile__user__username="new_instructor",
        ).exists()

        assert not Education.objects.filter(
            profile__user__username="new_instructor",
        ).exists()

        assert not InstructorProfile.objects.filter(
            profile__user__username="new_instructor",
        ).exists()

    def test_transaction_rolls_back_when_instructor_profile_creation_fails(
        self,
        anonymous_request,
        registration_data,
    ):
        with patch(
            "accounts.api.services.InstructorProfile.objects.update_or_create",
            side_effect=RuntimeError("instructor profile creation failed"),
        ):
            with pytest.raises(
                RuntimeError,
                match="instructor profile creation failed",
            ):
                register_instructor(
                    request=anonymous_request,
                    **registration_data,
                )

        assert not User.objects.filter(
            username="new_instructor",
        ).exists()

        assert not Profile.objects.filter(
            user__username="new_instructor",
        ).exists()

        assert not Skill.objects.filter(
            profile__user__username="new_instructor",
        ).exists()

        assert not Education.objects.filter(
            profile__user__username="new_instructor",
        ).exists()

        assert not InstructorProfile.objects.filter(
            profile__user__username="new_instructor",
        ).exists()

    def test_transaction_rolls_back_profile_update_for_existing_user(
        self,
        authenticated_request,
        registration_data,
        existing_profile,
    ):
        original_website = existing_profile.website
        original_country = existing_profile.country

        with patch(
            "accounts.api.services.Skill.objects.create",
            side_effect=RuntimeError("skill creation failed"),
        ):
            with pytest.raises(
                RuntimeError,
                match="skill creation failed",
            ):
                register_instructor(
                    request=authenticated_request,
                    **registration_data,
                )

        existing_profile.refresh_from_db()

        assert existing_profile.website == original_website
        assert existing_profile.country == original_country

        assert not existing_profile.skills.filter(
            name="Python",
        ).exists()

        assert not existing_profile.skills.filter(
            name="Django",
        ).exists()
