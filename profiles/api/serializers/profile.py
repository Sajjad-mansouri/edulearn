from django.contrib.auth import get_user_model
from rest_framework import serializers

from profiles.models import InstructorProfile, Profile, StudentProfile

from .education import EducationSerializer
from .experience import ExperienceSerializer
from .language import LanguageSerializer
from .skill import SkillSerializer
from .social_link import SocialLinkSerializer

User = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    skills = SkillSerializer(many=True, read_only=True)
    educations = EducationSerializer(many=True, read_only=True)
    experiences = ExperienceSerializer(many=True, read_only=True)
    languages = LanguageSerializer(many=True, read_only=True)
    social_links = SocialLinkSerializer(many=True, read_only=True)

    class Meta:
        model = Profile
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "avatar",
            "website",
            "country",
            "timezone",
            "date_of_birth",
            "company",
            "job_title",
            "skills",
            "educations",
            "experiences",
            "languages",
            "social_links",
        ]


class StudentProfileSerializer(ProfileSerializer):
    cover = serializers.ImageField(source="student_profile.cover")
    biography = serializers.CharField(source="student_profile.biography")
    headline = serializers.CharField(source="student_profile.headline")

    class Meta(ProfileSerializer.Meta):
        model = StudentProfile
        fields = ProfileSerializer.Meta.fields + [
            "cover",
            "biography",
            "headline",
        ]


class StudentProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = [
            "cover",
            "biography",
            "headline",
        ]


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "email"]


class InstructorProfileSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta(ProfileSerializer.Meta):
        model = InstructorProfile
        fields = [
            "profile",
            "cover",
            "biography",
            "headline",
            "professional_title",
            "organization",
            "is_verified",
            "verification_date",
            "introduction_video",
            "resume",
            "years_of_experience",
        ]


class InstructorProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstructorProfile
        fields = [
            "cover",
            "biography",
            "headline",
            "professional_title",
            "organization",
            "is_verified",
            "verification_date",
            "introduction_video",
            "resume",
            "years_of_experience",
        ]
