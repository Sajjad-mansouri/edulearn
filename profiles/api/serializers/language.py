from rest_framework import serializers

from profiles.models import Language


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = (
            "id",
            "language",
            "proficiency",
        )
