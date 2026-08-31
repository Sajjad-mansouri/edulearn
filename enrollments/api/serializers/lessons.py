from rest_framework import serializers

from curriculums.models import Lesson, LessonCompletionCriteria
from utils.datetime.format_duration import format_duration


class LessonCompletionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonCompletionCriteria
        fields = ["criteria_type", "video_watch_percentage", "quiz_passing_score"]


class EnrollmentLessonSerializer(serializers.ModelSerializer):
    duration = serializers.SerializerMethodField()
    duration_seconds = serializers.SerializerMethodField()
    has_resources = serializers.SerializerMethodField()
    completion_criteria = LessonCompletionSerializer()
    type = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = [
            "id",
            "title",
            "type",
            "duration",
            "duration_seconds",
            "order",
            "has_resources",
            "completion_criteria",
            "description",
        ]

    def get_duration(self, obj):
        if obj.duration:
            return format_duration(obj.duration)
        return None

    def get_duration_seconds(self, obj):
        if obj.duration:
            return obj.duration.total_seconds()
        else:
            return None

    def get_has_resources(self, obj):
        return obj.has_attachments

    def get_type(self, obj):
        print("obj in get_type", obj, obj.type)
        return obj.type
