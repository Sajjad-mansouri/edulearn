# tests/accounts/test_profile_model.py
from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from accounts.tests.factories import UserFactory
from profiles.models import (
    Education,
    Experience,
    InstructorProfile,
    Language,
    Profile,
    Skill,
    SocialLink,
    StudentProfile,
)

from .factories import (
    EducationFactory,
    ExperienceFactory,
    InstructorProfileFactory,
    ProfileFactory,
    SkillFactory,
    SocialLinkFactory,
    StudentProfileFactory,
)


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
        assert profile.cover.name == ""
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
            organization="test_company Academy",
            years_of_experience=8,
        )

        assert instructor.profile == profile
        assert instructor.professional_title == "Senior Python Instructor"
        assert instructor.organization == "test_company Academy"
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


@pytest.mark.django_db
class TestSkillModel:
    """Tests for the Skill model."""

    @pytest.fixture
    def profile(self):
        return ProfileFactory()

    @pytest.fixture
    def skill(self, profile):
        return SkillFactory(profile=profile)

    def test_create_skill(self, profile):
        """A skill can be created."""
        skill = Skill.objects.create(
            profile=profile,
            name="Python",
            slug="python",
            description="Programming language",
        )

        assert skill.profile == profile
        assert skill.name == "Python"
        assert skill.slug == "python"
        assert skill.description == "Programming language"

    def test_string_representation(self, skill):
        """The string representation returns the skill name."""
        assert str(skill) == skill.name

    def test_description_is_optional(self, profile):
        """A skill may be created without a description."""
        skill = Skill.objects.create(
            profile=profile,
            name="Django",
            slug="django",
        )

        assert skill.description == ""

    def test_slug_must_be_unique(self, profile):
        """Two skills cannot share the same slug."""
        SkillFactory(
            profile=profile,
            slug="python",
        )

        with pytest.raises(IntegrityError):
            SkillFactory(
                profile=profile,
                slug="python",
            )

    def test_profile_can_have_multiple_skills(self, profile):
        """A profile can own multiple skills."""
        python = SkillFactory(
            profile=profile,
            name="Python",
            slug="python",
        )
        django = SkillFactory(
            profile=profile,
            name="Django",
            slug="django",
        )

        assert profile.skills.count() == 2
        assert set(profile.skills.all()) == {python, django}

    def test_profile_returns_related_skills(self, profile):
        """A profile exposes its related skills."""
        skill = SkillFactory(profile=profile)

        assert skill in profile.skills.all()

    def test_skill_belongs_to_profile(self, profile):
        """A skill belongs to exactly one profile."""
        skill = SkillFactory(profile=profile)

        assert skill.profile == profile

    def test_deleting_profile_deletes_related_skills(self, profile):
        """Deleting a profile cascades to its skills."""
        skill = SkillFactory(profile=profile)

        profile.delete()

        assert not Skill.objects.filter(pk=skill.pk).exists()

    def test_generates_slug_when_slug_is_not_provided(self, profile):
        """Slug is automatically generated from the name."""
        skill = Skill.objects.create(
            profile=profile,
            name="Machine Learning",
        )

        assert skill.slug == "machine-learning"

    def test_does_not_override_existing_slug(self, profile):
        """An explicitly provided slug is preserved."""
        skill = Skill.objects.create(
            profile=profile,
            name="Machine Learning",
            slug="ml",
        )

        assert skill.slug == "ml"

    def test_slug_does_not_change_when_name_is_updated(self, skill):
        """Updating the name does not modify an existing slug."""
        original_slug = skill.slug

        skill.name = "Advanced Python"
        skill.save()
        skill.refresh_from_db()

        assert skill.slug == original_slug


@pytest.mark.django_db
class TestEducationModel:
    @pytest.fixture
    def profile(self):
        return ProfileFactory()

    @pytest.fixture
    def education(self, profile):
        return EducationFactory(profile=profile)

    def test_create_education(self, profile):
        """An education record can be created."""
        education = Education.objects.create(
            profile=profile,
            institution="MIT",
            degree="Bachelor",
            field_of_study="Computer Science",
            description="Focused on deep learning and NLP.",
            start_date="2020-12-01",
            end_date="2020-12-12",
        )

        assert education.profile == profile
        assert education.institution == "MIT"
        assert education.degree == "Bachelor"
        assert education.description == "Focused on deep learning and NLP."
        assert education.field_of_study == "Computer Science"
        assert education.start_date == "2020-12-01"
        assert education.end_date == "2020-12-12"

    def test_string_representation(self, education):
        """Returns a human-readable representation."""
        assert (
            str(education)
            == "Master of Science in Computer Science at University of Oxford"
        )

    def test_profile_can_access_education_records(self, profile):
        """A profile should access its education records through the reverse relation."""
        education = EducationFactory(profile=profile)

        assert education in profile.educations.all()

    def test_multiple_education_records_can_belong_to_profile(self, profile):
        """A profile can have multiple education records."""
        EducationFactory.create_batch(3, profile=profile)

        assert profile.educations.count() == 3

    def test_end_date_can_be_blank(self, profile):
        """An education record may represent ongoing studies."""
        education = Education.objects.create(
            profile=profile,
            institution="MIT",
            degree="Bachelor",
            description="Focused on deep learning and NLP.",
            field_of_study="Computer Science",
            start_date="2020-12-01",
            end_date=None,
        )

        assert education.end_date is None

    def test_start_date_can_be_blank(self, profile):
        """An education record may omit the start year."""
        education = Education.objects.create(
            profile=profile,
            institution="MIT",
            degree="Bachelor",
            description="Focused on deep learning and NLP.",
            field_of_study="Computer Science",
            start_date=None,
            end_date="2020-12-12",
        )

        assert education.start_date is None

    def test_clean_allows_equal_start_and_end_date(self, education):
        """The same start and end year is valid."""
        education.start_date = "2020-12-01"
        education.end_date = "2020-12-01"

        education.full_clean()
        assert education.start_date == education.end_date

    def test_clean_raises_validation_error_when_end_date_before_start_date(
        self,
        education,
    ):
        """End year cannot be earlier than start year."""
        education.start_date = "2020-12-12"
        education.end_date = "2020-12-01"

        with pytest.raises(ValidationError) as exc_info:
            education.full_clean()

        assert "end_date" in exc_info.value.message_dict

    def test_database_constraint_prevents_invalid_years(self, profile):
        """The database should reject records with an invalid year range."""
        with pytest.raises(IntegrityError):
            Education.objects.create(
                profile=profile,
                institution="MIT",
                degree="Bachelor",
                description="Focused on deep learning and NLP.",
                field_of_study="Computer Science",
                start_date="2020-12-12",
                end_date="2020-12-01",
            )

    def test_deleting_profile_deletes_education_records(self):
        """Deleting a profile should delete its education records."""
        profile = ProfileFactory()
        EducationFactory.create_batch(2, profile=profile)

        profile.delete()

        assert not Education.objects.exists()


@pytest.mark.django_db
class TestExperienceModel:
    @pytest.fixture
    def profile(self):
        return ProfileFactory()

    @pytest.fixture
    def experience(self, profile):
        return ExperienceFactory(profile=profile)

    def test_create_experience(self, profile):
        """An experience record can be created."""
        experience = Experience.objects.create(
            profile=profile,
            company="test_company",
            location="San Francisco, US",
            position="Backend Developer",
            description="Leading data analytics team.",
            start_date=date(2022, 1, 1),
            end_date=date(2024, 1, 1),
        )

        assert experience.profile == profile
        assert experience.company == "test_company"
        assert experience.location == "San Francisco, US"
        assert experience.position == "Backend Developer"
        assert experience.description == "Leading data analytics team."
        assert experience.start_date == date(2022, 1, 1)
        assert experience.end_date == date(2024, 1, 1)
        assert experience.is_current is False

    def test_string_representation(self, experience):
        """Returns a human-readable representation."""
        assert str(experience) == "Backend Developer at test_company"

    def test_profile_can_access_experiences(self, profile):
        """A profile should access its experiences through the reverse relation."""
        experience = ExperienceFactory(profile=profile)

        assert experience in profile.experiences.all()

    def test_profile_can_have_multiple_experiences(self, profile):
        """A profile can have multiple experience records."""
        ExperienceFactory.create_batch(3, profile=profile)

        assert profile.experiences.count() == 3

    def test_current_position_can_have_no_end_date(self, experience):
        """A current position may omit the end date."""
        experience.is_current = True
        experience.end_date = None

        experience.full_clean()

        assert experience.end_date is None

    def test_end_date_can_be_blank(self, experience):
        """An experience may omit the end date."""
        experience.end_date = None

        experience.full_clean()

        assert experience.end_date is None

    def test_clean_rejects_end_date_before_start_date(self, experience):
        """End date must not be earlier than the start date."""
        experience.start_date = date(2024, 1, 1)
        experience.end_date = date(2023, 1, 1)

        with pytest.raises(ValidationError) as exc_info:
            experience.full_clean()

        assert exc_info.value.message_dict == {
            "end_date": ["End date must be greater than or equal to the start date."]
        }

    def test_clean_rejects_current_position_with_end_date(self, experience):
        """A current position cannot have an end date."""
        experience.is_current = True
        experience.end_date = date(2024, 1, 1)

        with pytest.raises(ValidationError) as exc_info:
            experience.full_clean()

        assert exc_info.value.message_dict == {
            "end_date": ["Current positions cannot have an end date."]
        }

    def test_database_constraint_rejects_invalid_date_range(self, profile):
        """The database should reject an invalid date range."""
        with pytest.raises(IntegrityError):
            Experience.objects.create(
                profile=profile,
                company="test_company",
                location="San Francisco, US",
                position="Backend Developer",
                description="Leading data analytics team.",
                start_date=date(2024, 1, 1),
                end_date=date(2023, 1, 1),
            )

    def test_database_constraint_rejects_current_position_with_end_date(
        self,
        profile,
    ):
        """The database should reject a current position that has an end date."""
        with pytest.raises(IntegrityError):
            Experience.objects.create(
                profile=profile,
                company="test_company",
                location="San Francisco, US",
                position="Backend Developer",
                description="Leading data analytics team.",
                start_date=date(2022, 1, 1),
                end_date=date(2024, 1, 1),
                is_current=True,
            )

    def test_deleting_profile_deletes_related_experiences(self):
        """Deleting a profile should delete its experience records."""
        profile = ProfileFactory()
        ExperienceFactory.create_batch(2, profile=profile)

        profile.delete()

        assert not Experience.objects.exists()


@pytest.mark.django_db
class TestSocialLinkModel:
    @pytest.fixture
    def profile(self):
        return ProfileFactory()

    @pytest.fixture
    def social_link(self, profile):
        return SocialLinkFactory(profile=profile)

    def test_create_social_link(self, profile):
        """A social link can be created."""
        social_link = SocialLink.objects.create(
            profile=profile,
            platform="GitHub",
            url="https://github.com/test_user",
            visibility=SocialLink.Visibility.PUBLIC,
            display_order=1,
        )

        assert social_link.profile == profile
        assert social_link.platform == "GitHub"
        assert social_link.url == "https://github.com/test_user"
        assert social_link.visibility == SocialLink.Visibility.PUBLIC
        assert social_link.display_order == 1

    def test_string_representation(self, social_link):
        """Returns a human-readable representation."""
        expected = f"{social_link.platform} ({social_link.profile.user.username})"

        assert str(social_link) == expected

    def test_visibility_defaults_to_public(self, profile):
        """New social links should be public by default."""
        social_link = SocialLink.objects.create(
            profile=profile,
            platform="LinkedIn",
            url="https://linkedin.com/in/test_user",
        )

        assert social_link.visibility == SocialLink.Visibility.PUBLIC

    def test_display_order_defaults_to_zero(self, profile):
        """New social links should have a display order of zero."""
        social_link = SocialLink.objects.create(
            profile=profile,
            platform="LinkedIn",
            url="https://linkedin.com/in/test_user",
        )

        assert social_link.display_order == 0

    def test_profile_can_access_social_links(self, profile):
        """A profile should access its social links through the reverse relation."""
        social_link = SocialLinkFactory(profile=profile)

        assert social_link in profile.social_links.all()

    def test_profile_can_have_multiple_social_links(self, profile):
        """A profile can have multiple social links."""
        SocialLinkFactory.create_batch(3, profile=profile)

        assert profile.social_links.count() == 3

    def test_deleting_profile_deletes_social_links(self):
        """Deleting a profile should delete its social links."""
        profile = ProfileFactory()
        SocialLinkFactory.create_batch(2, profile=profile)

        profile.delete()

        assert not SocialLink.objects.exists()

    def test_same_platform_can_be_used_by_different_profiles(self):
        """Different profiles can use the same platform."""
        SocialLinkFactory(
            profile=ProfileFactory(),
            platform="GitHub",
        )

        SocialLinkFactory(
            profile=ProfileFactory(),
            platform="GitHub",
        )

        assert SocialLink.objects.filter(platform="GitHub").count() == 2


@pytest.mark.django_db
class TestLanguageModel:
    """Tests for the Language model."""

    def test_creates_language(self):
        """A language can be created for a profile."""
        profile = ProfileFactory()

        language = Language.objects.create(
            profile=profile,
            language="English",
            proficiency="c1",
        )

        assert language.pk is not None
        assert language.profile == profile
        assert language.language == "English"
        assert language.proficiency == "c1"

    def test_profile_languages_related_name(self):
        """Languages are accessible through the profile related name."""
        profile = ProfileFactory()

        language = Language.objects.create(
            profile=profile,
            language="English",
            proficiency="native",
        )

        assert profile.languages.count() == 1
        assert profile.languages.first() == language

    def test_deletes_languages_when_profile_is_deleted(self):
        """Deleting a profile deletes its languages."""
        profile = ProfileFactory()

        language = Language.objects.create(
            profile=profile,
            language="English",
            proficiency="b2",
        )

        profile.delete()

        assert not Language.objects.filter(pk=language.pk).exists()

    @pytest.mark.parametrize(
        "proficiency",
        [
            "native",
            "c2",
            "c1",
            "B2",
            "B1",
            "A2",
            "A1",
        ],
    )
    def test_accepts_valid_proficiency_values(self, proficiency):
        """All defined proficiency values can be stored."""
        profile = ProfileFactory()

        language = Language.objects.create(
            profile=profile,
            language="English",
            proficiency=proficiency,
        )

        assert language.proficiency == proficiency
