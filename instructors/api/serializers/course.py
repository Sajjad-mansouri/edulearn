from django.contrib.auth import get_user_model
from django.db.models import Avg
from rest_framework import serializers

from courses.models import (
    Category,
    Course,
    CourseFeature,
    CourseFeedback,
    LearningOutcome,
    Prerequisite,
    TargetAudience,
)
from curriculums.api.serializers import AttachmentSerializer, SectionSerializer

from .tag import TagSerializer

User = get_user_model()


class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseFeature
        fields = ["icon", "text"]


class LearningOutcomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningOutcome
        fields = ["id", "description"]


class PrerequisiteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Prerequisite
        fields = ["id", "description"]


class TargetAudienceSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = TargetAudience
        fields = ["id", "description"]


class CourseSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    learning_outcomes = LearningOutcomeSerializer(many=True)
    prerequisites = PrerequisiteSerializer(many=True)
    target_audiences = TargetAudienceSerializer(many=True)
    sections = SectionSerializer(many=True)
    attachments = AttachmentSerializer(many=True, required=False)
    category = serializers.SlugRelatedField(
        slug_field="slug", queryset=Category.objects.all()
    )
    features = FeatureSerializer(many=True)

    class Meta:
        model = Course
        fields = [
            "id",
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
            "seo_title",
            "seo_description",
            "tags",
            "learning_outcomes",
            "prerequisites",
            "target_audiences",
            "features",
            "sections",
            "attachments",
        ]

    def to_representation(self, instance):
        if isinstance(instance, Course):
            data = super().to_representation(instance)
            # Filter attachments in response

            data["attachments"] = AttachmentSerializer(
                instance.attachments.filter(lesson_content__isnull=True), many=True
            ).data
            return data
        return super().to_representation(instance)


class InstructorCourseSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="category.name", read_only=True)
    students = serializers.SerializerMethodField()
    revenue = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "category",
            "version",
            "rating",
            "students",
            "revenue",
            "thumbnail",
            "last_updated",
            "slug",
            "status",
            "review_status",
        ]

    def get_revenue(self, obj):
        return 10

    def get_students(self, obj):
        return obj.enrollments.count()

    def get_rating(self, obj):
        avg_rating = CourseFeedback.objects.filter(enrollment__course=obj).aggregate(
            avg=Avg("rating")
        )["avg"]
        if avg_rating:
            return round(avg_rating, 1)
        return avg_rating


class InstructorFilterCoursesSerializer(serializers.ModelSerializer):
    courses = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["courses"]

    def get_courses(self, obj):
        return {course.slug: course.title for course in obj.owned_courses.all()}
