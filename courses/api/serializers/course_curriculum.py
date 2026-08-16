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
        content = obj.main_contents[0] if obj.main_contents else None
        return content.content_type

    def get_duration(self, obj):
        return format_duration(obj.duration)

    def get_video_url(self, obj):
        content = obj.main_contents[0] if obj.main_contents else None

        if not hasattr(content, "video"):
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
