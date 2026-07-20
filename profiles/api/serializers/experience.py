from rest_framework import serializers

from profiles.models import Experience


class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = (
            "id",
            "company",
            "position",
            "location",
            "description",
            "start_date",
            "end_date",
        )
