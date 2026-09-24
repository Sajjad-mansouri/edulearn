from rest_framework import serializers

from curriculums.models import Lesson, Section
from utils.datetime.format_duration import format_duration


class CoursesSectionLessonSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    is_previewable = serializers.BooleanField(
        source="is_preview",
        read_only=True,
    )
    video_url = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = [
            "id",
            "title",
            "type",
            "duration",
            "is_previewable",
            "video_url",
        ]

    def get_type(self, obj):
        if hasattr(obj, "content"):
            return obj.content.content_type
        return None

    def get_duration(self, obj):
        return format_duration(obj.duration)

    def get_video_url(self, obj):
        if not hasattr(obj, "content"):
            return None
        content = obj.content
        if content.content_type != "video":
            return None

        return content.video.video_file.url


class CourseCurriculumSerializer(serializers.ModelSerializer):
    total_duration = serializers.SerializerMethodField()
    lessons_count = serializers.IntegerField(read_only=True)
    lessons = CoursesSectionLessonSerializer(many=True)

    class Meta:
        model = Section
        fields = ["id", "title", "total_duration", "lessons_count", "lessons"]

    def get_total_duration(self, obj):
        return format_duration(obj.section_duration)
