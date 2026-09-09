from datetime import timedelta

from django.conf import settings
from rest_framework import serializers

from courses.models import Course, CourseFeature
from curriculums.models import VideoCaption


class CourseSerializer(serializers.ModelSerializer):
    rating = serializers.FloatField(read_only=True)
    rating_count = serializers.IntegerField(read_only=True)
    students = serializers.IntegerField(read_only=True)
    instructor = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    subcategory = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    original_price = serializers.SerializerMethodField()
    badge = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "instructor",
            "category",
            "subcategory",
            "rating",
            "rating_count",
            "students",
            "level",
            "duration",
            "price",
            "original_price",
            "language",
            "badge",
            "thumbnail",
            "slug",
        ]

    def get_instructor(self, obj):
        return obj.owner.get_full_name()

    def get_category(self, obj):
        if obj.category.parent is not None:
            return obj.category.parent.name
        return obj.category.name

    def get_subcategory(self, obj):
        if obj.category.parent is not None:
            return obj.category.name
        return ""

    def get_duration(self, obj):
        print(obj.duration)
        course_duration = obj.duration
        total_seconds = course_duration.total_seconds()
        hour = total_seconds / (60 * 60)
        return f"{hour:.2}h"

    def get_price(self, obj):
        return obj.get_discounted_price

    def get_original_price(self, obj):
        return obj.original_price

    def get_badge(self, obj):
        # badges: new, bestseller
        best_sellers = self.context["best_sellers"]

        if obj.id in best_sellers:
            return "bestseller"
        now = self.context["now"]
        if now - obj.published_at <= timedelta(days=settings.NEW_COUSRE_RANGE):
            return "new"
        return ""


class CourseFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseFeature
        fields = ["icon", "text"]


class CourseDetailInfoSerializer(CourseSerializer):
    rating = serializers.FloatField(read_only=True)
    total_ratings = serializers.IntegerField(read_only=True)
    total_students = serializers.IntegerField(read_only=True)
    subtitles = serializers.SerializerMethodField()
    learning_outcomes = serializers.SerializerMethodField()
    prerequisites = serializers.SerializerMethodField()
    target_audience = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()

    features = CourseFeatureSerializer(many=True)

    class Meta(CourseSerializer.Meta):
        fields = [
            "id",
            "slug",
            "title",
            "subtitle",
            "description",
            "thumbnail",
            "price",
            "original_price",
            "price_discount",
            "level",
            "language",
            "subtitles",
            "rating",
            "total_ratings",
            "rating_count",
            "total_students",
            "last_updated",
            "category",
            "subcategory",
            "learning_outcomes",
            "prerequisites",
            "target_audience",
            "features",
            "instructor",
            "duration",
        ]

    def get_subtitles(self, obj):
        return set(
            VideoCaption.objects.filter(
                video__content__lesson__section__course=obj
            ).values_list("language", flat=True)
        )

    def get_learning_outcomes(self, obj):
        return list(obj.learning_outcomes.values_list("description", flat=True))

    def get_prerequisites(self, obj):
        return list(obj.prerequisites.values_list("description", flat=True))

    def get_target_audience(self, obj):
        return list(obj.target_audiences.values_list("description", flat=True))

    def get_rating(self, obj):
        if obj.rating:
            return round(obj.rating, 1)
        return ""


class CourseMetadataSerializer(serializers.Serializer):
    levels = serializers.SerializerMethodField()
    languages = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ["levels", "languages"]

    def get_levels(self, obj):
        return [
            {
                "label": level.label,
                "value": level.value,
            }
            for level in Course.Level
        ]

    def get_languages(self, obj):
        return [
            {
                "label": level.label,
                "value": level.value,
            }
            for level in Course.LANGUAGE
        ]
