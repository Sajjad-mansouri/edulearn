from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.utils import timezone

from profiles.models import (
    InstructorProfile,
    Profile,
    StudentProfile,
)

User = get_user_model()


class TestProfile:
    def test_creates_profile_with_user(
        self,
        db,
        test_user,
    ):
        profile = Profile.objects.create(
            user=test_user,
        )

        assert profile.user == test_user
        assert profile.user_id == test_user.pk

    def test_user_reverse_relation_returns_profile(
        self,
        db,
        test_user,
    ):
        profile = Profile.objects.create(
            user=test_user,
        )

        assert test_user.profile == profile

    def test_profile_user_is_one_to_one(
        self,
        db,
        test_user,
    ):
        Profile.objects.create(
            user=test_user,
        )

        with pytest.raises(IntegrityError):
            Profile.objects.create(
                user=test_user,
            )

    def test_str_returns_username_and_profile(
        self,
        db,
        test_user,
    ):
        profile = Profile.objects.create(
            user=test_user,
        )

        assert str(profile) == f"{test_user.username}'s Profile"

    def test_optional_fields_default_to_empty_values(
        self,
        db,
        test_user,
    ):
        profile = Profile.objects.create(
            user=test_user,
        )

        assert profile.avatar.name == ""
        assert profile.website == ""
        assert profile.country == ""
        assert profile.timezone == ""
        assert profile.language == ""
        assert profile.linkedin == ""
        assert profile.github == ""
        assert profile.date_of_birth is None
        assert profile.company == ""
        assert profile.job_title == ""

    def test_profile_fields_are_persisted(
        self,
        db,
        test_user,
    ):
        birthday = date(1995, 5, 20)

        profile = Profile.objects.create(
            user=test_user,
            website="https://example.com",
            country="Country",
            timezone="UTC",
            language="en",
            linkedin="https://linkedin.com/in/example",
            github="https://github.com/example",
            date_of_birth=birthday,
            company="Example Company",
            job_title="Developer",
        )

        profile.refresh_from_db()

        assert profile.website == "https://example.com"
        assert profile.country == "Country"
        assert profile.timezone == "UTC"
        assert profile.language == "en"
        assert profile.linkedin == "https://linkedin.com/in/example"
        assert profile.github == "https://github.com/example"
        assert profile.date_of_birth == birthday
        assert profile.company == "Example Company"
        assert profile.job_title == "Developer"

    def test_user_is_required(
        self,
        db,
    ):
        profile = Profile()

        with pytest.raises(ValidationError) as exc_info:
            Profile._meta.get_field("user").validate(
                profile.user_id,
                profile,
            )

        assert exc_info.value.messages

    def test_website_accepts_valid_url(
        self,
        db,
        test_user,
    ):
        profile = Profile(
            user=test_user,
            website="https://example.com",
        )

        Profile._meta.get_field("website").clean(
            profile.website,
            profile,
        )

    def test_invalid_website_is_rejected(
        self,
        db,
        test_user,
    ):
        profile = Profile(
            user=test_user,
            website="not-a-url",
        )

        with pytest.raises(ValidationError):
            Profile._meta.get_field("website").clean(
                profile.website,
                profile,
            )

    def test_linkedin_accepts_valid_url(
        self,
        db,
        test_user,
    ):
        profile = Profile(
            user=test_user,
            linkedin="https://linkedin.com/in/example",
        )

        Profile._meta.get_field("linkedin").clean(
            profile.linkedin,
            profile,
        )

    def test_github_accepts_valid_url(
        self,
        db,
        test_user,
    ):
        profile = Profile(
            user=test_user,
            github="https://github.com/example",
        )

        Profile._meta.get_field("github").clean(
            profile.github,
            profile,
        )

    def test_get_avatar_returns_empty_string_without_avatar(
        self,
        db,
        test_user,
    ):
        profile = Profile.objects.create(
            user=test_user,
        )

        assert profile.get_avatar() == ""

    def test_get_avatar_returns_file_url_when_avatar_exists(
        self,
        db,
        test_user,
    ):
        avatar = SimpleUploadedFile(
            "avatar.png",
            b"fake-image-content",
            content_type="image/png",
        )

        profile = Profile.objects.create(
            user=test_user,
            avatar=avatar,
        )

        assert profile.get_avatar() == profile.avatar.url
        assert profile.get_avatar() != ""

    def test_created_at_is_set_automatically(
        self,
        db,
        test_user,
    ):
        before = timezone.now()

        profile = Profile.objects.create(
            user=test_user,
        )

        after = timezone.now()

        assert before <= profile.created_at <= after

    def test_updated_at_is_set_automatically(
        self,
        db,
        test_user,
    ):
        before = timezone.now()

        profile = Profile.objects.create(
            user=test_user,
        )

        after = timezone.now()

        assert before <= profile.updated_at <= after

    def test_updated_at_changes_after_update(
        self,
        db,
        test_user,
    ):
        profile = Profile.objects.create(
            user=test_user,
        )

        original_updated_at = profile.updated_at

        profile.company = "Updated Company"
        profile.save()
        profile.refresh_from_db()

        assert profile.updated_at >= original_updated_at

    def test_profile_ordering_uses_user(
        self,
        db,
    ):
        first_user = User.objects.create_user(
            username="aaa_user",
            email="aaa@example.com",
            password="test-password",
        )
        second_user = User.objects.create_user(
            username="bbb_user",
            email="bbb@example.com",
            password="test-password",
        )

        first_profile = Profile.objects.create(
            user=first_user,
        )
        second_profile = Profile.objects.create(
            user=second_user,
        )

        profiles = list(Profile.objects.all())

        assert profiles == [first_profile, second_profile]

    def test_deleting_user_deletes_profile(
        self,
        db,
        test_user,
    ):
        profile = Profile.objects.create(
            user=test_user,
        )

        profile_id = profile.pk

        test_user.delete()

        assert not Profile.objects.filter(pk=profile_id).exists()


class TestInstructorProfile:
    def test_creates_instructor_profile(
        self,
        db,
        profile,
    ):
        instructor_profile = InstructorProfile.objects.create(
            profile=profile,
            professional_title="Software Developer",
        )

        assert instructor_profile.profile == profile
        assert instructor_profile.professional_title == "Software Developer"

    def test_profile_reverse_relation_returns_instructor_profile(
        self,
        db,
        profile,
    ):
        instructor_profile = InstructorProfile.objects.create(
            profile=profile,
            professional_title="Software Developer",
        )

        assert profile.instructor_profile == instructor_profile

    def test_instructor_profile_is_one_to_one(
        self,
        db,
        profile,
    ):
        InstructorProfile.objects.create(
            profile=profile,
            professional_title="Software Developer",
        )

        with pytest.raises(IntegrityError):
            InstructorProfile.objects.create(
                profile=profile,
                professional_title="Another Title",
            )

    def test_str_returns_username_and_professional_title(
        self,
        db,
        profile,
    ):
        instructor_profile = InstructorProfile.objects.create(
            profile=profile,
            professional_title="Software Developer",
        )

        assert str(instructor_profile) == (
            f"{profile.user.username} - Software Developer"
        )

    def test_application_status_defaults_to_pending(
        self,
        db,
        profile,
    ):
        instructor_profile = InstructorProfile.objects.create(
            profile=profile,
            professional_title="Software Developer",
        )

        assert instructor_profile.application_status == "pending"

    @pytest.mark.parametrize(
        "status",
        [
            "draft",
            "pending",
            "approved",
            "rejected",
        ],
    )
    def test_accepts_defined_application_statuses(
        self,
        db,
        profile,
        status,
    ):
        instructor_profile = InstructorProfile.objects.create(
            profile=profile,
            professional_title="Software Developer",
            application_status=status,
        )

        assert instructor_profile.application_status == status

    def test_is_verified_defaults_to_false(
        self,
        db,
        profile,
    ):
        instructor_profile = InstructorProfile.objects.create(
            profile=profile,
            professional_title="Software Developer",
        )

        assert instructor_profile.is_verified is False

    def test_verification_date_defaults_to_none(
        self,
        db,
        profile,
    ):
        instructor_profile = InstructorProfile.objects.create(
            profile=profile,
            professional_title="Software Developer",
        )

        assert instructor_profile.verification_date is None

    def test_rejection_reason_defaults_to_empty_string(
        self,
        db,
        profile,
    ):
        instructor_profile = InstructorProfile.objects.create(
            profile=profile,
            professional_title="Software Developer",
        )

        assert instructor_profile.rejection_reason == ""

    def test_introduction_video_defaults_to_empty_string(
        self,
        db,
        profile,
    ):
        instructor_profile = InstructorProfile.objects.create(
            profile=profile,
            professional_title="Software Developer",
        )

        assert instructor_profile.introduction_video == ""

    def test_resume_defaults_to_empty_file(
        self,
        db,
        profile,
    ):
        instructor_profile = InstructorProfile.objects.create(
            profile=profile,
            professional_title="Software Developer",
        )

        assert instructor_profile.resume.name == ""

    def test_years_of_experience_defaults_to_zero(
        self,
        db,
        profile,
    ):
        instructor_profile = InstructorProfile.objects.create(
            profile=profile,
            professional_title="Software Developer",
        )

        assert instructor_profile.years_of_experience == 0

    def test_instructor_fields_are_persisted(
        self,
        db,
        profile,
    ):
        verification_date = timezone.now()

        instructor_profile = InstructorProfile.objects.create(
            profile=profile,
            headline="Professional Django Developer",
            biography="Professional biography.",
            professional_title="Senior Developer",
            organization="Example Organization",
            application_status="approved",
            is_verified=True,
            verification_date=verification_date,
            rejection_reason="",
            introduction_video="https://example.com/video",
            years_of_experience=8,
        )

        instructor_profile.refresh_from_db()

        assert instructor_profile.headline == "Professional Django Developer"
        assert instructor_profile.biography == "Professional biography."
        assert instructor_profile.professional_title == "Senior Developer"
        assert instructor_profile.organization == "Example Organization"
        assert instructor_profile.application_status == "approved"
        assert instructor_profile.is_verified is True
        assert instructor_profile.verification_date == verification_date
        assert instructor_profile.introduction_video == ("https://example.com/video")
        assert instructor_profile.years_of_experience == 8

    def test_professional_title_is_required(
        self,
        db,
        profile,
    ):
        instructor_profile = InstructorProfile(
            profile=profile,
        )

        with pytest.raises(ValidationError) as exc_info:
            InstructorProfile._meta.get_field("professional_title").validate(
                instructor_profile.professional_title,
                instructor_profile,
            )

        assert exc_info.value.messages

    def test_profile_is_required(
        self,
        db,
    ):
        instructor_profile = InstructorProfile(
            professional_title="Software Developer",
        )

        with pytest.raises(ValidationError) as exc_info:
            InstructorProfile._meta.get_field("profile").validate(
                instructor_profile.profile_id,
                instructor_profile,
            )

        assert exc_info.value.messages

    def test_years_of_experience_rejects_negative_value(
        self,
        db,
        profile,
    ):
        instructor_profile = InstructorProfile(
            profile=profile,
            professional_title="Software Developer",
            years_of_experience=-1,
        )

        with pytest.raises(ValidationError):
            InstructorProfile._meta.get_field("years_of_experience").clean(
                instructor_profile.years_of_experience,
                instructor_profile,
            )

    def test_introduction_video_rejects_invalid_url(
        self,
        db,
        profile,
    ):
        instructor_profile = InstructorProfile(
            profile=profile,
            professional_title="Software Developer",
            introduction_video="not-a-url",
        )

        with pytest.raises(ValidationError):
            InstructorProfile._meta.get_field("introduction_video").clean(
                instructor_profile.introduction_video,
                instructor_profile,
            )

    def test_deleting_profile_deletes_instructor_profile(
        self,
        db,
        profile,
    ):
        instructor_profile = InstructorProfile.objects.create(
            profile=profile,
            professional_title="Software Developer",
        )

        instructor_profile_id = instructor_profile.pk

        profile.delete()

        assert not InstructorProfile.objects.filter(pk=instructor_profile_id).exists()

    def test_instructor_ordering_uses_username(
        self,
        db,
    ):
        first_user = User.objects.create_user(
            username="aaa_instructor",
            email="aaa_instructor@example.com",
            password="test-password",
        )
        second_user = User.objects.create_user(
            username="bbb_instructor",
            email="bbb_instructor@example.com",
            password="test-password",
        )

        first_profile = Profile.objects.create(
            user=first_user,
        )
        second_profile = Profile.objects.create(
            user=second_user,
        )

        first_instructor = InstructorProfile.objects.create(
            profile=first_profile,
            professional_title="Developer",
        )
        second_instructor = InstructorProfile.objects.create(
            profile=second_profile,
            professional_title="Developer",
        )

        instructors = list(InstructorProfile.objects.all())

        assert instructors == [first_instructor, second_instructor]


class TestStudentProfile:
    def test_creates_student_profile(
        self,
        db,
        profile,
    ):
        student_profile = StudentProfile.objects.create(
            profile=profile,
        )

        assert student_profile.profile == profile

    def test_profile_reverse_relation_returns_student_profile(
        self,
        db,
        profile,
    ):
        student_profile = StudentProfile.objects.create(
            profile=profile,
        )

        assert profile.student_profile == student_profile

    def test_student_profile_is_one_to_one(
        self,
        db,
        profile,
    ):
        StudentProfile.objects.create(
            profile=profile,
        )

        with pytest.raises(IntegrityError):
            StudentProfile.objects.create(
                profile=profile,
            )

    def test_str_returns_username_and_student_profile(
        self,
        db,
        profile,
    ):
        student_profile = StudentProfile.objects.create(
            profile=profile,
        )

        assert str(student_profile) == (f"{profile.user.username}'s Student Profile")

    def test_learning_goal_defaults_to_empty_string(
        self,
        db,
        profile,
    ):
        student_profile = StudentProfile.objects.create(
            profile=profile,
        )

        assert student_profile.learning_goal == ""

    def test_current_streak_defaults_to_zero(
        self,
        db,
        profile,
    ):
        student_profile = StudentProfile.objects.create(
            profile=profile,
        )

        assert student_profile.current_streak == 0

    def test_longest_streak_defaults_to_zero(
        self,
        db,
        profile,
    ):
        student_profile = StudentProfile.objects.create(
            profile=profile,
        )

        assert student_profile.longest_streak == 0

    def test_student_fields_are_persisted(
        self,
        db,
        profile,
    ):
        student_profile = StudentProfile.objects.create(
            profile=profile,
            headline="Learning software development",
            biography="Student biography.",
            learning_goal="Become a backend developer",
            current_streak=7,
            longest_streak=30,
        )

        student_profile.refresh_from_db()

        assert student_profile.headline == ("Learning software development")
        assert student_profile.biography == "Student biography."
        assert student_profile.learning_goal == ("Become a backend developer")
        assert student_profile.current_streak == 7
        assert student_profile.longest_streak == 30

    def test_profile_is_required(
        self,
        db,
    ):
        student_profile = StudentProfile()

        with pytest.raises(ValidationError) as exc_info:
            StudentProfile._meta.get_field("profile").validate(
                student_profile.profile_id,
                student_profile,
            )

        assert exc_info.value.messages

    def test_current_streak_rejects_negative_value(
        self,
        db,
        profile,
    ):
        student_profile = StudentProfile(
            profile=profile,
            current_streak=-1,
        )

        with pytest.raises(ValidationError):
            StudentProfile._meta.get_field("current_streak").clean(
                student_profile.current_streak,
                student_profile,
            )

    def test_longest_streak_rejects_negative_value(
        self,
        db,
        profile,
    ):
        student_profile = StudentProfile(
            profile=profile,
            longest_streak=-1,
        )

        with pytest.raises(ValidationError):
            StudentProfile._meta.get_field("longest_streak").clean(
                student_profile.longest_streak,
                student_profile,
            )

    def test_deleting_profile_deletes_student_profile(
        self,
        db,
        profile,
    ):
        student_profile = StudentProfile.objects.create(
            profile=profile,
        )

        student_profile_id = student_profile.pk

        profile.delete()

        assert not StudentProfile.objects.filter(pk=student_profile_id).exists()

    def test_student_ordering_uses_username(
        self,
        db,
    ):
        first_user = User.objects.create_user(
            username="aaa_student",
            email="aaa_student@example.com",
            password="test-password",
        )
        second_user = User.objects.create_user(
            username="bbb_student",
            email="bbb_student@example.com",
            password="test-password",
        )

        first_profile = Profile.objects.create(
            user=first_user,
        )
        second_profile = Profile.objects.create(
            user=second_user,
        )

        first_student = StudentProfile.objects.create(
            profile=first_profile,
        )
        second_student = StudentProfile.objects.create(
            profile=second_profile,
        )

        students = list(StudentProfile.objects.all())

        assert students == [first_student, second_student]


class TestProfileRoleRelationships:
    def test_same_profile_can_have_instructor_and_student_profiles(
        self,
        db,
        profile,
    ):
        instructor_profile = InstructorProfile.objects.create(
            profile=profile,
            professional_title="Developer",
        )

        student_profile = StudentProfile.objects.create(
            profile=profile,
        )

        assert profile.instructor_profile == instructor_profile
        assert profile.student_profile == student_profile

    def test_instructor_and_student_profiles_are_independent(
        self,
        db,
        profile,
    ):
        instructor_profile = InstructorProfile.objects.create(
            profile=profile,
            professional_title="Developer",
        )

        student_profile = StudentProfile.objects.create(
            profile=profile,
            learning_goal="Learn backend development",
        )

        instructor_profile.professional_title = "Senior Developer"
        instructor_profile.save()

        student_profile.refresh_from_db()

        assert student_profile.learning_goal == ("Learn backend development")

    def test_deleting_profile_cascades_to_both_role_profiles(
        self,
        db,
        profile,
    ):
        instructor_profile = InstructorProfile.objects.create(
            profile=profile,
            professional_title="Developer",
        )
        student_profile = StudentProfile.objects.create(
            profile=profile,
        )

        instructor_id = instructor_profile.pk
        student_id = student_profile.pk

        profile.delete()

        assert not InstructorProfile.objects.filter(pk=instructor_id).exists()
        assert not StudentProfile.objects.filter(pk=student_id).exists()
