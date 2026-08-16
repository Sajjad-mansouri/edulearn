from rest_framework import serializers

from courses.models import Course

from .sections import EnrollmentSectionSerializer


class EnrollmentCourseSerializer(serializers.ModelSerializer):
    courseId = serializers.IntegerField(source="id", read_only=True)
    courseTitle = serializers.CharField(source="title", read_only=True)

    totalLessons = serializers.IntegerField(source="total_lessons", read_only=True)
    sections = EnrollmentSectionSerializer(many=True, read_only=True)
    enrollmentId = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "courseId",
            "courseTitle",
            "totalLessons",
            "enrollmentId",
            "sections",
        ]

    def get_enrollmentId(self, obj):
        enrollment_id = self.context["enrollment_id"]
        return enrollment_id
