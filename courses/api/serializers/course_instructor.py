from django.contrib.auth import get_user_model
from rest_framework import serializers

from profiles.models import InstructorProfile

User = get_user_model()


class CourseInstructorSerializer(serializers.ModelSerializer):
    bio = serializers.CharField(source="biography")
    avatar = serializers.ImageField(source="profile.avatar")
    rating = serializers.SerializerMethodField()
    total_students = serializers.IntegerField(read_only=True)
    total_courses = serializers.IntegerField(read_only=True)

    name = serializers.SerializerMethodField()
    social_links = serializers.SerializerMethodField()

    class Meta:
        model = InstructorProfile
        fields = [
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
        ]

    def get_name(self, obj):
        return obj.profile.user.get_full_name()

    def get_social_links(self, obj):
        return [
            {social_link.platform: social_link.address}
            for social_link in obj.profile.social_links.all()
        ]

    def get_rating(self, obj):
        if obj.rating is None:
            return ""
        return round(obj.rating, 1)
