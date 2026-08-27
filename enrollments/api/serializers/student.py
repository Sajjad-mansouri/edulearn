from rest_framework import serializers

from courses.models import Course


class StudentCourseSerializer(serializers.ModelSerializer):
    difficulty = serializers.CharField(source="level")
    category = serializers.CharField(source="category.name", default="", read_only=True)
    instructor = serializers.CharField(
        source="owner", read_only=True
    )  # adjust as needed
    # The rest come from annotations
    enrollment_id = serializers.IntegerField(read_only=True)
    progress = serializers.FloatField(read_only=True)  # or IntegerField
    status = serializers.CharField(read_only=True)
    last_accessed = serializers.DateTimeField(read_only=True)
    enrolled_at = serializers.DateTimeField(read_only=True)
    rating = serializers.FloatField(read_only=True, allow_null=True)

    class Meta:
        model = Course
        fields = [
            "id",
            "enrollment_id",
            "title",
            "instructor",
            "thumbnail",
            "status",
            "progress",
            "difficulty",
            "category",
            "duration",
            "last_accessed",
            "enrolled_at",
            "rating",
            "slug",
        ]
