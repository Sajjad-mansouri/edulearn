from rest_framework import serializers

from courses.models import (
    Category,
    Course,
    LearningOutcome,
    Prerequisite,
    TargetAudience,
)
from curriculums.api.serializers import AttachmentSerializer, SectionSerializer

from .tag import TagSerializer


class LearningOutcomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningOutcome
        fields = ["description"]


class PrerequisiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prerequisite
        fields = ["description"]


class TargetAudienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TargetAudience
        fields = ["description"]


class CourseSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    outcomes = LearningOutcomeSerializer(many=True)
    prerequisites = PrerequisiteSerializer(many=True)
    targetAudience = TargetAudienceSerializer(many=True)
    sections = SectionSerializer(many=True)
    attachments = AttachmentSerializer(required=False, many=True)
    category = serializers.SlugRelatedField(
        slug_field="slug", queryset=Category.objects.all(), write_only=True
    )

    class Meta:
        model = Course
        fields = [
            "title",
            "subtitle",
            "short_description",
            "category",
            # subcategory
            "level",
            "language",
            "duration",
            "visibility",
            "description",
            "price_type",
            "price",
            "price_discount",
            "thumbnail",
            "promotional_video",
            "course_trailer",
            "version",
            "version_note",
            "status",
            "seo_title",
            "seo_description",
            "tags",
            "outcomes",
            "prerequisites",
            "targetAudience",
            "sections",
            "attachments",
        ]
