from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


# ============================================
# USER SERIALIZER (for top nav avatar/name)
# ============================================
class TopNavUserSerializer(serializers.ModelSerializer):
    """
    Minimal user serializer for the top navigation bar.
    Returns only the fields needed: name, email, avatar.
    """

    full_name = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "avatar_url",
            "role",
        ]
        read_only_fields = fields

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username

    def get_avatar_url(self, obj):
        # Return uploaded avatar or None (frontend will use UI Avatars fallback)
        if hasattr(obj, "profile") and obj.profile.avatar:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.profile.avatar.url)
            return obj.profile.avatar.url
        return None

    def get_role(self, obj):
        # Determine user role
        if (
            hasattr(obj.profile, "instructor_profile")
            and obj.profile.instructor_profile
        ):
            return "instructor"
        return "student"
