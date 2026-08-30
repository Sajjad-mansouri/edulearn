# serializers.py
from rest_framework import serializers


class PeriodRevenueSerializer(serializers.Serializer):
    value = serializers.DecimalField(max_digits=14, decimal_places=2)
    trend = serializers.IntegerField(allow_null=True)
    direction = serializers.CharField(allow_null=True, required=False)


class RevenueSummarySerializer(serializers.Serializer):
    lifetime = PeriodRevenueSerializer()
    period_revenue = PeriodRevenueSerializer()
    ytd = PeriodRevenueSerializer()


class CourseBreakdownSerializer(serializers.Serializer):
    course = serializers.CharField()
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)


class RevenueSerializer(serializers.Serializer):
    revenue_summary = RevenueSummarySerializer()
    course_breakdown = CourseBreakdownSerializer(many=True)
