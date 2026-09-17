from decimal import Decimal

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import Avg, Count

from courses.api.serializers.course_instructor import (
    CourseInstructorSerializer,
)
from profiles.models import InstructorProfile, Profile, SocialLink

pytestmark = pytest.mark.django_db


class TestCourseInstructorSerializer:
    @pytest.fixture
    def profile(self, test_user):
        return Profile.objects.create(
            user=test_user,
        )

    @pytest.fixture
    def instructor_profile(self, profile):
        return InstructorProfile.objects.create(
            profile=profile,
            headline="Django Instructor",
            biography="Django and Python instructor.",
            professional_title="Django Instructor",
            organization="Programming Academy",
            is_verified=True,
        )

    @pytest.fixture
    def annotated_instructor(self, instructor_profile):
        return (
            InstructorProfile.objects.filter(
                pk=instructor_profile.pk,
            )
            .annotate(
                rating=Avg(
                    "profile__user__owned_courses__enrollments__feedback__rating",
                ),
                total_students=Count(
                    "profile__user__owned_courses__enrollments__user",
                    distinct=True,
                ),
                total_courses=Count(
                    "profile__user__owned_courses",
                    distinct=True,
                ),
            )
            .get()
        )

    @pytest.fixture
    def serializer(self, annotated_instructor):
        return CourseInstructorSerializer(
            annotated_instructor,
        )

    @pytest.fixture
    def social_links(self, profile):
        return [
            SocialLink.objects.create(
                profile=profile,
                platform=SocialLink.Platform.LINKEDIN,
                address="https://linkedin.com/in/test_user",
                visibility=SocialLink.Visibility.PUBLIC,
                display_order=1,
            ),
            SocialLink.objects.create(
                profile=profile,
                platform=SocialLink.Platform.GITHUB,
                address="https://github.com/test_user",
                visibility=SocialLink.Visibility.PUBLIC,
                display_order=2,
            ),
        ]

    @pytest.fixture
    def avatar(self):
        return SimpleUploadedFile(
            "test-avatar.jpg",
            b"fake image content",
            content_type="image/jpeg",
        )

    # ------------------------------------------------------------------
    # Serializer structure
    # ------------------------------------------------------------------

    def test_serializes_expected_fields(self, serializer):
        assert set(serializer.data.keys()) == {
            "id",
            "name",
            "headline",
            "avatar",
            "bio",
            "rating",
            "total_students",
            "total_courses",
            "is_verified",
            "organization",
            "social_links",
        }

    def test_id_field_is_serialized(
        self,
        serializer,
        instructor_profile,
    ):
        assert serializer.data["id"] == instructor_profile.id

    def test_name_field_uses_user_full_name(
        self,
        serializer,
        test_user,
    ):
        assert serializer.data["name"] == test_user.get_full_name()

    def test_name_field_uses_profile_user(
        self,
        instructor_profile,
    ):
        serializer = CourseInstructorSerializer(
            instructor_profile,
        )

        assert serializer.fields["name"].source == "*"

    def test_headline_is_serialized(
        self,
        serializer,
        instructor_profile,
    ):
        assert serializer.data["headline"] == instructor_profile.headline

    def test_bio_field_uses_instructor_biography(
        self,
        instructor_profile,
    ):
        serializer = CourseInstructorSerializer(
            instructor_profile,
        )

        assert serializer.fields["bio"].source == "biography"

    def test_bio_is_serialized_from_instructor_biography(
        self,
        serializer,
        instructor_profile,
    ):
        assert serializer.data["bio"] == instructor_profile.biography

    def test_avatar_field_uses_profile_avatar(
        self,
        instructor_profile,
    ):
        serializer = CourseInstructorSerializer(
            instructor_profile,
        )

        assert serializer.fields["avatar"].source == "profile.avatar"

    def test_avatar_is_serialized_from_profile(
        self,
        annotated_instructor,
        avatar,
    ):
        profile = annotated_instructor.profile

        profile.avatar = avatar
        profile.save(update_fields=["avatar"])

        serializer = CourseInstructorSerializer(
            annotated_instructor,
        )

        assert serializer.data["avatar"].endswith(
            profile.avatar.name,
        )

    def test_is_verified_is_serialized(
        self,
        serializer,
        instructor_profile,
    ):
        assert serializer.data["is_verified"] == instructor_profile.is_verified

    def test_organization_is_serialized(
        self,
        serializer,
        instructor_profile,
    ):
        assert serializer.data["organization"] == instructor_profile.organization

    # ------------------------------------------------------------------
    # Social links
    # ------------------------------------------------------------------

    def test_social_links_are_empty_when_profile_has_no_links(
        self,
        serializer,
    ):
        assert serializer.data["social_links"] == []

    def test_social_links_are_serialized(
        self,
        serializer,
        social_links,
    ):
        assert serializer.data["social_links"] == [
            {
                social_links[0].platform: social_links[0].address,
            },
            {
                social_links[1].platform: social_links[1].address,
            },
        ]

    def test_social_links_follow_model_ordering(
        self,
        serializer,
        profile,
    ):
        github = SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.GITHUB,
            address="https://github.com/test_user",
            display_order=2,
        )

        linkedin = SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.LINKEDIN,
            address="https://linkedin.com/in/test_user",
            display_order=1,
        )

        assert serializer.data["social_links"] == [
            {linkedin.platform: linkedin.address},
            {github.platform: github.address},
        ]

    def test_social_links_are_ordered_by_display_order_then_platform(
        self,
        serializer,
        profile,
    ):
        github = SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.GITHUB,
            address="https://github.com/test_user",
            display_order=1,
        )

        linkedin = SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.LINKEDIN,
            address="https://linkedin.com/in/test_user",
            display_order=1,
        )

        assert serializer.data["social_links"] == [
            {github.platform: github.address},
            {linkedin.platform: linkedin.address},
        ]

    def test_serializes_all_social_link_platforms(
        self,
        serializer,
        profile,
    ):
        social_links = []

        for index, platform in enumerate(
            SocialLink.Platform.values,
            start=1,
        ):
            social_links.append(
                SocialLink.objects.create(
                    profile=profile,
                    platform=platform,
                    address=f"https://example.com/{platform}",
                    display_order=index,
                )
            )

        assert serializer.data["social_links"] == [
            {
                social_link.platform: social_link.address,
            }
            for social_link in social_links
        ]

    def test_social_link_visibility_does_not_change_serializer_output(
        self,
        serializer,
        profile,
    ):
        social_link = SocialLink.objects.create(
            profile=profile,
            platform=SocialLink.Platform.GITHUB,
            address="https://github.com/test_user",
            visibility=SocialLink.Visibility.PRIVATE,
        )

        assert serializer.data["social_links"] == [
            {
                social_link.platform: social_link.address,
            }
        ]

    # ------------------------------------------------------------------
    # Rating
    # ------------------------------------------------------------------

    def test_rating_returns_empty_string_when_rating_is_none(
        self,
        instructor_profile,
    ):
        instructor_profile.rating = None

        serializer = CourseInstructorSerializer(
            instructor_profile,
        )

        assert serializer.get_rating(instructor_profile) == ""

    @pytest.mark.parametrize(
        ("rating", "expected"),
        [
            (4.0, 4.0),
            (4.1, 4.1),
            (4.14, 4.1),
            (4.15, 4.2),
            (4.56, 4.6),
            (4.99, 5.0),
            (5.0, 5.0),
        ],
    )
    def test_rating_is_rounded_to_one_decimal_place(
        self,
        instructor_profile,
        rating,
        expected,
    ):
        instructor_profile.rating = rating

        serializer = CourseInstructorSerializer(
            instructor_profile,
        )

        assert serializer.get_rating(instructor_profile) == expected

    def test_rating_is_serialized_from_annotation(
        self,
        annotated_instructor,
    ):
        annotated_instructor.rating = Decimal("4.56")

        serializer = CourseInstructorSerializer(
            annotated_instructor,
        )

        assert serializer.data["rating"] == Decimal("4.6")

    def test_zero_rating_is_preserved(
        self,
        instructor_profile,
    ):
        instructor_profile.rating = 0

        serializer = CourseInstructorSerializer(
            instructor_profile,
        )

        assert serializer.get_rating(instructor_profile) == 0

    # ------------------------------------------------------------------
    # Annotated statistics
    # ------------------------------------------------------------------

    def test_total_students_is_serialized(
        self,
        annotated_instructor,
    ):
        annotated_instructor.total_students = 25

        serializer = CourseInstructorSerializer(
            annotated_instructor,
        )

        assert serializer.data["total_students"] == 25

    def test_total_courses_is_serialized(
        self,
        annotated_instructor,
    ):
        annotated_instructor.total_courses = 3

        serializer = CourseInstructorSerializer(
            annotated_instructor,
        )

        assert serializer.data["total_courses"] == 3

    # ------------------------------------------------------------------
    # Read-only fields
    # ------------------------------------------------------------------

    def test_rating_is_read_only(
        self,
        annotated_instructor,
    ):
        serializer = CourseInstructorSerializer(
            annotated_instructor,
            data={
                "rating": 1.0,
            },
            partial=True,
        )

        assert serializer.is_valid()

        assert "rating" not in serializer.validated_data

    def test_total_students_is_read_only(
        self,
        annotated_instructor,
    ):
        serializer = CourseInstructorSerializer(
            annotated_instructor,
            data={
                "total_students": 999,
            },
            partial=True,
        )

        assert serializer.is_valid()

        assert "total_students" not in serializer.validated_data

    def test_total_courses_is_read_only(
        self,
        annotated_instructor,
    ):
        serializer = CourseInstructorSerializer(
            annotated_instructor,
            data={
                "total_courses": 999,
            },
            partial=True,
        )

        assert serializer.is_valid()

        assert "total_courses" not in serializer.validated_data

    def test_all_annotated_fields_are_read_only(
        self,
        annotated_instructor,
    ):
        serializer = CourseInstructorSerializer(
            annotated_instructor,
            data={
                "rating": 1.0,
                "total_students": 999,
                "total_courses": 999,
            },
            partial=True,
        )

        assert serializer.is_valid()

        assert "rating" not in serializer.validated_data
        assert "total_students" not in serializer.validated_data
        assert "total_courses" not in serializer.validated_data

    # ------------------------------------------------------------------
    # Field configuration
    # ------------------------------------------------------------------

    def test_rating_is_serializer_method_field(self):
        serializer = CourseInstructorSerializer()

        assert serializer.fields["rating"].__class__.__name__ == (
            "SerializerMethodField"
        )

    def test_bio_field_is_not_read_only(self):
        serializer = CourseInstructorSerializer()

        assert serializer.fields["bio"].read_only is False

    def test_avatar_field_is_not_read_only(self):
        serializer = CourseInstructorSerializer()

        assert serializer.fields["avatar"].read_only is False

    # ------------------------------------------------------------------
    # Non-mutation
    # ------------------------------------------------------------------

    def test_serializer_does_not_modify_instructor_profile(
        self,
        serializer,
        instructor_profile,
    ):
        original_headline = instructor_profile.headline
        original_biography = instructor_profile.biography
        original_is_verified = instructor_profile.is_verified
        original_organization = instructor_profile.organization

        instructor_profile.refresh_from_db()

        assert instructor_profile.headline == original_headline
        assert instructor_profile.biography == original_biography
        assert instructor_profile.is_verified == original_is_verified
        assert instructor_profile.organization == original_organization

    def test_serializer_does_not_modify_profile(
        self,
        serializer,
        profile,
    ):
        original_avatar = profile.avatar.name
        original_website = profile.website
        original_linkedin = profile.linkedin
        original_github = profile.github

        profile.refresh_from_db()

        assert profile.avatar.name == original_avatar
        assert profile.website == original_website
        assert profile.linkedin == original_linkedin
        assert profile.github == original_github
