from rest_framework import serializers

from profiles.models import Profile

from .education import EducationSerializer
from .experience import ExperienceSerializer
from .language import LanguageSerializer
from .skill import SkillSerializer
from .social_link import SocialLinkSerializer


class ProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    avatar = serializers.SerializerMethodField()
    cover = serializers.SerializerMethodField()

    skills = SkillSerializer(many=True, read_only=True)
    educations = EducationSerializer(many=True, read_only=True)
    experiences = ExperienceSerializer(many=True, read_only=True)
    social_links = SocialLinkSerializer(many=True, read_only=True)
    languages = LanguageSerializer(many=True, read_only=True)

    class Meta:
        model = Profile
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "cover",
            "avatar",
            "biography",
            "headline",
            "website",
            "country",
            "timezone",
            "date_of_birth",
            "company",
            "job_title",
            "skills",
            "educations",
            "experiences",
            "social_links",
            "languages",
        )

    def get_avatar(self, obj):
        if not obj.avatar:
            return None

        request = self.context.get("request")
        if request is not None:
            return request.build_absolute_uri(obj.avatar.url)

        return obj.avatar.url

    def get_cover(self, obj):
        if not obj.cover:
            return None

        request = self.context.get("request")
        if request is not None:
            return request.build_absolute_uri(obj.cover.url)

        return obj.cover.url
