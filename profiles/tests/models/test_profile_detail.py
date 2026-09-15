from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from profiles.models import (
    Education,
    Experience,
    Language,
    Skill,
    SocialLink,
)


class TestSkill:
    def test_creates_skill(
        self,
        db,
        profile,
    ):
        skill = Skill.objects.create(
            profile=profile,
            name="Django",
            slug="django",
        )

        assert skill.profile == profile
        assert skill.name == "Django"
        assert skill.slug == "django"

    def test_str_returns_name(
        self,
        db,
        profile,
    ):
        skill = Skill.objects.create(
            profile=profile,
            name="Django",
            slug="django",
        )

        assert str(skill) == "Django"

    def test_profile_reverse_relation_returns_skills(
        self,
        db,
        profile,
    ):
        skill = Skill.objects.create(
            profile=profile,
            name="Django",
            slug="django",
        )

        assert list(profile.skills.all()) == [skill]

    def test_multiple_skills_can_belong_to_same_profile(
        self,
        db,
        profile,
    ):
        first = Skill.objects.create(
            profile=profile,
            name="Django",
            slug="django",
        )
        second = Skill.objects.create(
            profile=profile,
            name="Python",
            slug="python",
        )

        skills = list(profile.skills.all())

        assert len(skills) == 2
        assert {skill.pk for skill in skills} == {
            first.pk,
            second.pk,
        }

    def test_slug_is_generated_from_name_when_empty(
        self,
        db,
        profile,
    ):
        skill = Skill.objects.create(
            profile=profile,
            name="Django REST Framework",
        )

        assert skill.slug == "django-rest-framework"

    def test_existing_slug_is_not_overwritten(
        self,
        db,
        profile,
    ):
        skill = Skill.objects.create(
            profile=profile,
            name="Django REST Framework",
            slug="custom-slug",
        )

        assert skill.slug == "custom-slug"

    def test_slug_is_unique(
        self,
        db,
        profile,
    ):
        Skill.objects.create(
            profile=profile,
            name="Django",
            slug="django",
        )

        with pytest.raises(IntegrityError):
            Skill.objects.create(
                profile=profile,
                name="Django Framework",
                slug="django",
            )

    def test_name_is_required(
        self,
        db,
        profile,
    ):
        skill = Skill(
            profile=profile,
            slug="django",
        )

        with pytest.raises(ValidationError) as exc_info:
            Skill._meta.get_field("name").validate(
                skill.name,
                skill,
            )

        assert exc_info.value.messages

    def test_profile_is_required(
        self,
        db,
    ):
        skill = Skill(
            name="Django",
            slug="django",
        )

        with pytest.raises(ValidationError) as exc_info:
            Skill._meta.get_field("profile").validate(
                skill.profile_id,
                skill,
            )

        assert exc_info.value.messages

    def test_description_defaults_to_empty_string(
        self,
        db,
        profile,
    ):
        skill = Skill.objects.create(
            profile=profile,
            name="Django",
            slug="django",
        )

        assert skill.description == ""

    def test_description_is_persisted(
        self,
        db,
        profile,
    ):
        skill = Skill.objects.create(
            profile=profile,
            name="Django",
            slug="django",
            description="Web framework for Python.",
        )

        skill.refresh_from_db()

        assert skill.description == "Web framework for Python."

    def test_skills_are_ordered_by_name(
        self,
        db,
        profile,
    ):
        python = Skill.objects.create(
            profile=profile,
            name="Python",
            slug="python",
        )
        django = Skill.objects.create(
            profile=profile,
            name="Django",
            slug="django",
        )

        skills = list(Skill.objects.all())

        assert skills == [django, python]

    def test_deleting_profile_deletes_skills(
        self,
        db,
        profile,
    ):
        skill = Skill.objects.create(
            profile=profile,
            name="Django",
            slug="django",
        )

        skill_id = skill.pk

        profile.delete()

        assert not Skill.objects.filter(pk=skill_id).exists()


class TestEducation:
    def test_creates_education(
        self,
        db,
        profile,
    ):
        education = Education.objects.create(
            profile=profile,
            institution="Example University",
            degree="Master",
            field_of_study="Computer Science",
        )

        assert education.profile == profile
        assert education.institution == "Example University"
        assert education.degree == "Master"
        assert education.field_of_study == "Computer Science"

    def test_str_returns_degree_field_and_institution(
        self,
        db,
        profile,
    ):
        education = Education.objects.create(
            profile=profile,
            institution="Example University",
            degree="Master",
            field_of_study="Computer Science",
        )

        assert str(education) == ("Master in Computer Science at Example University")

    def test_profile_reverse_relation_returns_educations(
        self,
        db,
        profile,
    ):
        education = Education.objects.create(
            profile=profile,
            institution="Example University",
            degree="Master",
            field_of_study="Computer Science",
        )

        assert list(profile.educations.all()) == [education]

    def test_multiple_educations_can_belong_to_same_profile(
        self,
        db,
        profile,
    ):
        first = Education.objects.create(
            profile=profile,
            institution="University A",
            degree="Bachelor",
            field_of_study="Computer Science",
        )
        second = Education.objects.create(
            profile=profile,
            institution="University B",
            degree="Master",
            field_of_study="Software Engineering",
        )

        educations = list(profile.educations.all())

        assert len(educations) == 2
        assert {education.pk for education in educations} == {
            first.pk,
            second.pk,
        }

    def test_optional_dates_default_to_none(
        self,
        db,
        profile,
    ):
        education = Education.objects.create(
            profile=profile,
            institution="Example University",
            degree="Master",
            field_of_study="Computer Science",
        )

        assert education.start_date is None
        assert education.end_date is None

    def test_description_defaults_to_empty_string(
        self,
        db,
        profile,
    ):
        education = Education.objects.create(
            profile=profile,
            institution="Example University",
            degree="Master",
            field_of_study="Computer Science",
        )

        assert education.description == ""

    def test_education_fields_are_persisted(
        self,
        db,
        profile,
    ):
        start_date = date(2020, 9, 1)
        end_date = date(2024, 6, 30)

        education = Education.objects.create(
            profile=profile,
            institution="Example University",
            degree="Master",
            field_of_study="Computer Science",
            description="Graduate studies.",
            start_date=start_date,
            end_date=end_date,
        )

        education.refresh_from_db()

        assert education.institution == "Example University"
        assert education.degree == "Master"
        assert education.field_of_study == "Computer Science"
        assert education.description == "Graduate studies."
        assert education.start_date == start_date
        assert education.end_date == end_date

    def test_required_fields_are_validated(
        self,
        db,
        profile,
    ):
        education = Education(
            profile=profile,
        )

        required_fields = (
            "institution",
            "degree",
            "field_of_study",
        )

        for field_name in required_fields:
            with pytest.raises(ValidationError) as exc_info:
                Education._meta.get_field(field_name).validate(
                    getattr(education, field_name),
                    education,
                )

            assert exc_info.value.messages

    def test_profile_is_required(
        self,
        db,
    ):
        education = Education(
            institution="Example University",
            degree="Master",
            field_of_study="Computer Science",
        )

        with pytest.raises(ValidationError) as exc_info:
            Education._meta.get_field("profile").validate(
                education.profile_id,
                education,
            )

        assert exc_info.value.messages

    def test_end_date_can_equal_start_date(
        self,
        db,
        profile,
    ):
        start_date = date(2024, 1, 1)

        education = Education(
            profile=profile,
            institution="Example University",
            degree="Master",
            field_of_study="Computer Science",
            start_date=start_date,
            end_date=start_date,
        )

        education.full_clean()

    def test_end_date_cannot_be_before_start_date(
        self,
        db,
        profile,
    ):
        education = Education(
            profile=profile,
            institution="Example University",
            degree="Master",
            field_of_study="Computer Science",
            start_date=date(2024, 1, 1),
            end_date=date(2023, 12, 31),
        )

        with pytest.raises(ValidationError) as exc_info:
            education.full_clean()

        assert "end_date" in exc_info.value.message_dict

    def test_end_date_can_be_null(
        self,
        db,
        profile,
    ):
        education = Education(
            profile=profile,
            institution="Example University",
            degree="Master",
            field_of_study="Computer Science",
            start_date=date(2024, 1, 1),
            end_date=None,
        )

        education.full_clean()

    def test_ordering_uses_latest_start_date_first(
        self,
        db,
        profile,
    ):
        older = Education.objects.create(
            profile=profile,
            institution="University A",
            degree="Bachelor",
            field_of_study="Computer Science",
            start_date=date(2018, 1, 1),
        )
        newer = Education.objects.create(
            profile=profile,
            institution="University B",
            degree="Master",
            field_of_study="Software Engineering",
            start_date=date(2022, 1, 1),
        )

        educations = list(Education.objects.all())

        assert educations == [newer, older]

    def test_deleting_profile_deletes_education(
        self,
        db,
        profile,
    ):
        education = Education.objects.create(
            profile=profile,
            institution="Example University",
            degree="Master",
            field_of_study="Computer Science",
        )

        education_id = education.pk

        profile.delete()

        assert not Education.objects.filter(pk=education_id).exists()


class TestExperience:
    def test_creates_experience(
        self,
        db,
        profile,
    ):
        experience = Experience.objects.create(
            profile=profile,
            company="Example Company",
            position="Developer",
        )

        assert experience.profile == profile
        assert experience.company == "Example Company"
        assert experience.position == "Developer"

    def test_str_returns_position_and_company(
        self,
        db,
        profile,
    ):
        experience = Experience.objects.create(
            profile=profile,
            company="Example Company",
            position="Developer",
        )

        assert str(experience) == "Developer at Example Company"

    def test_profile_reverse_relation_returns_experiences(
        self,
        db,
        profile,
    ):
        experience = Experience.objects.create(
            profile=profile,
            company="Example Company",
            position="Developer",
        )

        assert list(profile.experiences.all()) == [experience]

    def test_optional_fields_have_expected_defaults(
        self,
        db,
        profile,
    ):
        experience = Experience.objects.create(
            profile=profile,
            company="Example Company",
            position="Developer",
        )

        assert experience.location == ""
        assert experience.description == ""
        assert experience.start_date is None
        assert experience.end_date is None
        assert experience.is_current is False

    def test_experience_fields_are_persisted(
        self,
        db,
        profile,
    ):
        start_date = date(2020, 1, 1)
        end_date = date(2024, 1, 1)

        experience = Experience.objects.create(
            profile=profile,
            company="Example Company",
            position="Developer",
            location="Remote",
            description="Backend development.",
            start_date=start_date,
            end_date=end_date,
            is_current=False,
        )

        experience.refresh_from_db()

        assert experience.company == "Example Company"
        assert experience.position == "Developer"
        assert experience.location == "Remote"
        assert experience.description == "Backend development."
        assert experience.start_date == start_date
        assert experience.end_date == end_date
        assert experience.is_current is False

    def test_required_fields_are_validated(
        self,
        db,
        profile,
    ):
        experience = Experience(
            profile=profile,
        )

        required_fields = (
            "company",
            "position",
        )

        for field_name in required_fields:
            with pytest.raises(ValidationError) as exc_info:
                Experience._meta.get_field(field_name).validate(
                    getattr(experience, field_name),
                    experience,
                )

            assert exc_info.value.messages

    def test_profile_is_required(
        self,
        db,
    ):
        experience = Experience(
            company="Example Company",
            position="Developer",
        )

        with pytest.raises(ValidationError) as exc_info:
            Experience._meta.get_field("profile").validate(
                experience.profile_id,
                experience,
            )

        assert exc_info.value.messages

    def test_end_date_can_equal_start_date(
        self,
        db,
        profile,
    ):
        start_date = date(2024, 1, 1)

        experience = Experience(
            profile=profile,
            company="Example Company",
            position="Developer",
            start_date=start_date,
            end_date=start_date,
        )

        experience.full_clean()

    def test_end_date_cannot_be_before_start_date(
        self,
        db,
        profile,
    ):
        experience = Experience(
            profile=profile,
            company="Example Company",
            position="Developer",
            start_date=date(2024, 1, 1),
            end_date=date(2023, 12, 31),
        )

        with pytest.raises(ValidationError) as exc_info:
            experience.full_clean()

        assert "end_date" in exc_info.value.message_dict

    def test_current_experience_can_have_no_end_date(
        self,
        db,
        profile,
    ):
        experience = Experience(
            profile=profile,
            company="Example Company",
            position="Developer",
            start_date=date(2024, 1, 1),
            end_date=None,
            is_current=True,
        )

        experience.full_clean()

    def test_current_experience_cannot_have_end_date(
        self,
        db,
        profile,
    ):
        experience = Experience(
            profile=profile,
            company="Example Company",
            position="Developer",
            start_date=date(2020, 1, 1),
            end_date=date(2024, 1, 1),
            is_current=True,
        )

        with pytest.raises(ValidationError) as exc_info:
            experience.full_clean()

        assert "end_date" in exc_info.value.message_dict

    def test_non_current_experience_can_have_end_date(
        self,
        db,
        profile,
    ):
        experience = Experience(
            profile=profile,
            company="Example Company",
            position="Developer",
            start_date=date(2020, 1, 1),
            end_date=date(2024, 1, 1),
            is_current=False,
        )

        experience.full_clean()

    def test_ordering_uses_latest_start_date_first(
        self,
        db,
        profile,
    ):
        older = Experience.objects.create(
            profile=profile,
            company="Company A",
            position="Developer",
            start_date=date(2018, 1, 1),
        )
        newer = Experience.objects.create(
            profile=profile,
            company="Company B",
            position="Developer",
            start_date=date(2022, 1, 1),
        )

        experiences = list(Experience.objects.all())

        assert experiences == [newer, older]

    def test_deleting_profile_deletes_experience(
        self,
        db,
        profile,
    ):
        experience = Experience.objects.create(
            profile=profile,
            company="Example Company",
            position="Developer",
        )

        experience_id = experience.pk

        profile.delete()

        assert not Experience.objects.filter(pk=experience_id).exists()


class TestSocialLink:
    def test_creates_social_link(
        self,
        db,
        profile,
    ):
        social_link = SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.GITHUB,
            address="https://github.com/example",
        )

        assert social_link.profile == profile
        assert social_link.platform == SocialLink.Platform.GITHUB
        assert social_link.address == "https://github.com/example"

    def test_str_returns_platform_and_username(
        self,
        db,
        profile,
    ):
        social_link = SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.GITHUB,
            address="https://github.com/example",
        )

        assert str(social_link) == (f"github ({profile.user.username})")

    def test_profile_reverse_relation_returns_social_links(
        self,
        db,
        profile,
    ):
        social_link = SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.GITHUB,
            address="https://github.com/example",
        )

        assert list(profile.social_links.all()) == [social_link]

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
    def test_accepts_defined_platforms(
        self,
        db,
        profile,
        platform,
    ):
        social_link = SocialLink.objects.create(
            profile=profile,
            platform=platform,
            address="https://example.com",
        )

        assert social_link.platform == platform

    @pytest.mark.parametrize(
        "visibility",
        [
            SocialLink.Visibility.PUBLIC,
            SocialLink.Visibility.PRIVATE,
        ],
    )
    def test_accepts_defined_visibility_values(
        self,
        db,
        profile,
        visibility,
    ):
        social_link = SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.GITHUB,
            address="https://github.com/example",
            visibility=visibility,
        )

        assert social_link.visibility == visibility

    def test_visibility_defaults_to_public(
        self,
        db,
        profile,
    ):
        social_link = SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.GITHUB,
            address="https://github.com/example",
        )

        assert social_link.visibility == SocialLink.Visibility.PUBLIC

    def test_display_order_defaults_to_zero(
        self,
        db,
        profile,
    ):
        social_link = SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.GITHUB,
            address="https://github.com/example",
        )

        assert social_link.display_order == 0

    def test_profile_is_required(
        self,
        db,
    ):
        social_link = SocialLink(
            platform=SocialLink.Platform.GITHUB,
            address="https://github.com/example",
        )

        with pytest.raises(ValidationError) as exc_info:
            SocialLink._meta.get_field("profile").validate(
                social_link.profile_id,
                social_link,
            )

        assert exc_info.value.messages

    def test_platform_is_required(
        self,
        db,
        profile,
    ):
        social_link = SocialLink(
            profile=profile,
            address="https://github.com/example",
        )

        with pytest.raises(ValidationError) as exc_info:
            SocialLink._meta.get_field("platform").validate(
                social_link.platform,
                social_link,
            )

        assert exc_info.value.messages

    def test_address_is_required(
        self,
        db,
        profile,
    ):
        social_link = SocialLink(
            profile=profile,
            platform=SocialLink.Platform.GITHUB,
        )

        with pytest.raises(ValidationError) as exc_info:
            SocialLink._meta.get_field("address").validate(
                social_link.address,
                social_link,
            )

        assert exc_info.value.messages

    def test_invalid_address_is_rejected(
        self,
        db,
        profile,
    ):
        social_link = SocialLink(
            profile=profile,
            platform=SocialLink.Platform.GITHUB,
            address="not-a-url",
        )

        with pytest.raises(ValidationError):
            SocialLink._meta.get_field("address").clean(
                social_link.address,
                social_link,
            )

    def test_social_links_are_ordered_by_display_order_then_platform(
        self,
        db,
        profile,
    ):
        github = SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.GITHUB,
            address="https://github.com/example",
            display_order=1,
        )

        linkedin = SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.LINKEDIN,
            address="https://linkedin.com/in/example",
            display_order=1,
        )

        youtube = SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.YOUTUBE,
            address="https://youtube.com/example",
            display_order=2,
        )

        social_links = list(SocialLink.objects.all())

        assert social_links == [
            github,
            linkedin,
            youtube,
        ]

    def test_multiple_social_links_can_use_same_platform(
        self,
        db,
        profile,
    ):
        first = SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.GITHUB,
            address="https://github.com/example-one",
        )

        second = SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.GITHUB,
            address="https://github.com/example-two",
        )

        assert first.pk != second.pk
        assert profile.social_links.count() == 2

    def test_deleting_profile_deletes_social_links(
        self,
        db,
        profile,
    ):
        social_link = SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.GITHUB,
            address="https://github.com/example",
        )

        social_link_id = social_link.pk

        profile.delete()

        assert not SocialLink.objects.filter(pk=social_link_id).exists()


class TestLanguage:
    def test_creates_language(
        self,
        db,
        profile,
    ):
        language = Language.objects.create(
            profile=profile,
            language="English",
            proficiency="C1",
        )

        assert language.profile == profile
        assert language.language == "English"
        assert language.proficiency == "C1"

    def test_profile_reverse_relation_returns_languages(
        self,
        db,
        profile,
    ):
        language = Language.objects.create(
            profile=profile,
            language="English",
            proficiency="C1",
        )

        assert list(profile.languages.all()) == [language]

    def test_accepts_all_defined_proficiencies(
        self,
        db,
        profile,
    ):
        proficiencies = [choice[0] for choice in Language.PROFICIENCIES]

        for index, proficiency in enumerate(proficiencies):
            language = Language.objects.create(
                profile=profile,
                language=f"Language {index}",
                proficiency=proficiency,
            )

            assert language.proficiency == proficiency

    def test_language_is_required(
        self,
        db,
        profile,
    ):
        language = Language(
            profile=profile,
            proficiency="C1",
        )

        with pytest.raises(ValidationError) as exc_info:
            Language._meta.get_field("language").validate(
                language.language,
                language,
            )

        assert exc_info.value.messages

    def test_proficiency_is_required(
        self,
        db,
        profile,
    ):
        language = Language(
            profile=profile,
            language="English",
        )

        with pytest.raises(ValidationError) as exc_info:
            Language._meta.get_field("proficiency").validate(
                language.proficiency,
                language,
            )

        assert exc_info.value.messages

    def test_profile_is_required(
        self,
        db,
    ):
        language = Language(
            language="English",
            proficiency="C1",
        )

        with pytest.raises(ValidationError) as exc_info:
            Language._meta.get_field("profile").validate(
                language.profile_id,
                language,
            )

        assert exc_info.value.messages

    def test_language_and_proficiency_are_persisted(
        self,
        db,
        profile,
    ):
        language = Language.objects.create(
            profile=profile,
            language="English",
            proficiency="C2",
        )

        language.refresh_from_db()

        assert language.language == "English"
        assert language.proficiency == "C2"

    def test_multiple_languages_can_belong_to_same_profile(
        self,
        db,
        profile,
    ):
        first = Language.objects.create(
            profile=profile,
            language="English",
            proficiency="C1",
        )

        second = Language.objects.create(
            profile=profile,
            language="German",
            proficiency="B2",
        )

        languages = list(profile.languages.all())

        assert len(languages) == 2
        assert {language.pk for language in languages} == {
            first.pk,
            second.pk,
        }

    def test_deleting_profile_deletes_languages(
        self,
        db,
        profile,
    ):
        language = Language.objects.create(
            profile=profile,
            language="English",
            proficiency="C1",
        )

        language_id = language.pk

        profile.delete()

        assert not Language.objects.filter(pk=language_id).exists()
