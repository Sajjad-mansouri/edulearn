from django.contrib.auth import get_user_model
from rest_framework import serializers

from profiles.models import Profile

from .education import EducationSerializer
from .experience import ExperienceSerializer
from .language import LanguageSerializer
from .skill import SkillSerializer

User = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):
    skills = SkillSerializer(many=True, read_only=True)
    educations = EducationSerializer(many=True, read_only=True)
    experiences = ExperienceSerializer(many=True, read_only=True)
    # social_links = SocialLinkSerializer(many=True, read_only=True)
    languages = LanguageSerializer(many=True, read_only=True)

    class Meta:
        model = Profile
        fields = [
            "id",
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
            # "social_links",
            "languages",
        ]


class StudentProfileSerializer(ProfileSerializer):
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    email = serializers.EmailField(source="user.email", read_only=True)

    cover = serializers.ImageField(source="student_profile.cover")
    biography = serializers.CharField(source="student_profile.biography")
    headline = serializers.CharField(source="student_profile.headline")

    class Meta(ProfileSerializer.Meta):
        model = Profile
        fields = ProfileSerializer.Meta.fields + [
            "first_name",
            "last_name",
            "email",
            "cover",
            "biography",
            "headline",
        ]

    def update(self, instance, validated_data):
        user = instance.user
        user_info = validated_data.pop("user", {})

        for attr, val in user_info.items():
            setattr(user, attr, val)
        user.save()

        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        return instance
