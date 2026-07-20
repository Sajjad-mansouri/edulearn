from rest_framework import serializers

from profiles.models import Education


class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = (
            "id",
            "institution",
            "field_of_study",
            "description",
            "start_year",
            "end_year",
        )
