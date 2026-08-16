from rest_framework import serializers

from curriculums.models import Section

from .lessons import EnrollmentLessonSerializer


class EnrollmentSectionSerializer(serializers.ModelSerializer):
    lessons = EnrollmentLessonSerializer(many=True)

    class Meta:
        model = Section
        fields = ["id", "title", "order", "lessons"]
