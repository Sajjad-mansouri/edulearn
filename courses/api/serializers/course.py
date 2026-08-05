from datetime import timedelta

from django.conf import settings
from rest_framework import serializers

from courses.models import Course


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
        total_seconds = obj.duration.total_seconds()
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
