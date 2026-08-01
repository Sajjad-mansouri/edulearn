from rest_framework import serializers

from assessments.api.serializers import AssignmentSerializer, QuizContentSerializer
from curriculums.models import (
    ArticleContent,
    Attachment,
    FileContent,
    Lesson,
    LessonContent,
    Section,
    VideoCaption,
    VideoContent,
)


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ["file", "file_url"]


class ArticleContenttSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleContent
        fields = ["body", "estimated_read_time"]


class FileContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileContent
        fields = ["file", "file_url"]


class VideoCaptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoCaption
        fields = ["language", "label", "file", "file_format", "is_default"]


class VideoContentSerializer(serializers.ModelSerializer):
    captions = VideoCaptionSerializer(required=False, many=True)

    class Meta:
        model = VideoContent
        fields = [
            "source",
            "video_file",
            "external_url",
            "duration",
            "transcript",
            "text",
            "captions",
        ]


class LessonContentSerializer(serializers.ModelSerializer):
    assignment_content = AssignmentSerializer(required=False)
    quiz_content = QuizContentSerializer(required=False)
    article_content = ArticleContenttSerializer(required=False)
    video_content = VideoContentSerializer(required=False)
    file_content = FileContentSerializer(required=False)
    attachments = AttachmentSerializer(required=False, many=True)

    class Meta:
        model = LessonContent
        fields = [
            "content_type",
            "video_content",
            "file_content",
            "article_content",
            "attachments",
            "quiz_content",
            "assignment_content",
        ]


class LessonSerializer(serializers.ModelSerializer):
    contents = LessonContentSerializer(many=True)

    class Meta:
        model = Lesson
        fields = [
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

    class Meta:
        model = Section
        fields = ["title", "description", "duration", "lessons"]
