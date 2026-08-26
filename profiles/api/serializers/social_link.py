from rest_framework import serializers

from profiles.models import SocialLink


class SocialLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialLink
        fields = (
            "id",
            "platform",
            "address",
        )
