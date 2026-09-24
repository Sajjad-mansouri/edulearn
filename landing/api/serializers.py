from rest_framework import serializers

from landing.models import (
    Contact,
    EmailInbox,
    FeatureItem,
    HighlightEdpoint,
    SiteFeature,
    SiteHighlight,
    SocialLink,
    Statistics,
)


class EmailInboxSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailInbox
        fields = ["name", "email", "message", "subject"]


class FeatureItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureItem
        fields = ["title", "description", "icon", "color", "image"]


class FeatureSerializer(serializers.ModelSerializer):
    items = FeatureItemSerializer(read_only=True, many=True)

    class Meta:
        model = SiteFeature
        fields = ["title", "items"]


class EndpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = HighlightEdpoint
        fields = [
            "end_point",
        ]


class HighlightSerializer(serializers.ModelSerializer):
    endpoints = EndpointSerializer(read_only=True, many=True)

    class Meta:
        model = SiteHighlight
        fields = ["title", "description", "icon", "color", "endpoints"]


class SocialLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialLink
        fields = [
            "platform",
            "url",
            "icon",
            "username",
        ]


class ContactSerializer(serializers.ModelSerializer):
    social_links = SocialLinkSerializer(read_only=True, many=True)

    class Meta:
        model = Contact
        fields = ["name", "title", "description", "email", "social_links"]


class StatisticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Statistics
        fields = ["api_endpoints", "automated_tests"]
