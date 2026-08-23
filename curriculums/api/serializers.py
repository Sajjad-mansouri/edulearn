from rest_framework import serializers

from assessments.api.serializers import AssignmentSerializer, QuizContentSerializer
from curriculums.models import (
    ArticleContent,
    Attachment,
    FileContent,
    Lesson,
    LessonCompletionCriteria,
    LessonContent,
    Section,
    VideoCaption,
    VideoContent,
)


class AttachmentSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Attachment
        fields = ["id", "file", "file_url"]


class ArticleContenttSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = ArticleContent
        fields = ["id", "body", "estimated_read_time"]


class FileContentSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = FileContent
        fields = ["id", "file", "file_url"]


class VideoCaptionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = VideoCaption
        fields = ["id", "language", "label", "file", "file_format", "is_default"]


class VideoContentSerializer(serializers.ModelSerializer):
    captions = VideoCaptionSerializer(required=False, many=True)
    id = serializers.IntegerField(required=False)

    class Meta:
        model = VideoContent
        fields = [
            "id",
            "source",
            "video_file",
            "external_url",
            "duration",
            "transcript",
            "text",
            "captions",
        ]


class LessonContentSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    assignment = AssignmentSerializer(required=False)
    quiz = QuizContentSerializer(required=False)
    article = ArticleContenttSerializer(required=False)
    video = VideoContentSerializer(required=False)
    file = FileContentSerializer(required=False)
    attachments = AttachmentSerializer(required=False, many=True)

    class Meta:
        model = LessonContent
        fields = [
            "id",
            "content_type",
            "video",
            "file",
            "article",
            "attachments",
            "quiz",
            "assignment",
        ]


class CompletionCriteraSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonCompletionCriteria
        fields = ["criteria_type", "quiz_passing_score", "video_watch_percentage"]


class LessonSerializer(serializers.ModelSerializer):
    contents = LessonContentSerializer(many=True)
    completion_criteria = CompletionCriteraSerializer()
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Lesson
        fields = [
            "id",
            "title",
            "description",
            "duration",
            "contents",
            "is_published",
            "is_preview",
            "completion_criteria",
        ]


class SectionSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True)
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Section
        fields = ["id", "title", "description", "duration", "lessons"]
