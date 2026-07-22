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

    def is_valid(self, *, raise_exception=False):
        super().is_valid(raise_exception=False)
        print(self._errors)
        return bool(self._errors)
