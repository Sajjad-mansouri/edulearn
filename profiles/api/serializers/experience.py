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

    def validate(self, attrs):
        start_date = attrs.get(
            "start_date",
            self.instance.start_date if self.instance else None,
        )
        end_date = attrs.get(
            "end_date",
            self.instance.end_date if self.instance else None,
        )

        if start_date is not None and end_date is not None and end_date < start_date:
            raise serializers.ValidationError(
                {
                    "end_date": (
                        "End date must be greater than or equal to the start date."
                    )
                }
            )

        return attrs
