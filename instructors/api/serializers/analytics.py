# serializers.py
from rest_framework import serializers

from courses.models import Course


class KPIItemSerializer(serializers.Serializer):
    value = serializers.IntegerField()
    trend = serializers.IntegerField()
    direction = serializers.ChoiceField(choices=["up", "down", "neutral"])


class KPISerializer(serializers.Serializer):
    totalStudents = KPIItemSerializer()
    revenue = KPIItemSerializer()
    completionRate = KPIItemSerializer()
    watchTime = KPIItemSerializer()
    quizAvg = KPIItemSerializer()


class EnrollmentTrendSerializer(serializers.Serializer):
    label = serializers.CharField()
    count = serializers.IntegerField()


class RevenueTrendSerializer(serializers.Serializer):
    label = serializers.CharField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)


class CompletionSerializer(serializers.Serializer):
    completed = serializers.IntegerField()
    inProgress = serializers.IntegerField()


class WatchTimeByCourseSerializer(serializers.Serializer):
    course = serializers.CharField()
    hours = serializers.IntegerField()


class QuizPerformanceSerializer(serializers.Serializer):
    course = serializers.CharField()
    avg = serializers.FloatField()


class GeoDistributionSerializer(serializers.Serializer):
    country = serializers.CharField()
    pct = serializers.IntegerField()
    flag = serializers.CharField()


class AnalyticSerializer(serializers.Serializer):
    kpis = KPISerializer()
    enrollmentTrends = EnrollmentTrendSerializer(many=True)
    revenueTrends = RevenueTrendSerializer(many=True)
    completion = CompletionSerializer()
    watchTimeByCourse = WatchTimeByCourseSerializer(many=True)
    quizPerformance = QuizPerformanceSerializer(many=True)
    geoDistribution = GeoDistributionSerializer(many=True)


class AnalyticFilterCoursesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["slug", "title"]
