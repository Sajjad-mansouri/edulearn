from decimal import Decimal

import pytest

from courses.models import Course
from instructors.api.serializers.analytics import (
    AnalyticFilterCoursesSerializer,
    AnalyticSerializer,
    CompletionSerializer,
    EnrollmentTrendSerializer,
    GeoDistributionSerializer,
    KPIItemSerializer,
    KPISerializer,
    QuizPerformanceSerializer,
    RevenueTrendSerializer,
    WatchTimeByCourseSerializer,
)


class TestKPIItemSerializer:
    def test_serializes_valid_data(self):
        data = {
            "value": 1250,
            "trend": 15,
            "direction": "up",
        }

        serializer = KPIItemSerializer(data=data)

        assert serializer.is_valid()
        assert serializer.validated_data == {
            "value": 1250,
            "trend": 15,
            "direction": "up",
        }

    @pytest.mark.parametrize("direction", ["up", "down", "neutral"])
    def test_accepts_allowed_direction(self, direction):
        data = {
            "value": 100,
            "trend": 10,
            "direction": direction,
        }

        serializer = KPIItemSerializer(data=data)

        assert serializer.is_valid()

    def test_rejects_invalid_direction(self):
        data = {
            "value": 100,
            "trend": 10,
            "direction": "sideways",
        }

        serializer = KPIItemSerializer(data=data)

        assert not serializer.is_valid()
        assert "direction" in serializer.errors

    @pytest.mark.parametrize(
        "field",
        ["value", "trend", "direction"],
    )
    def test_requires_all_fields(self, field):
        data = {
            "value": 100,
            "trend": 10,
            "direction": "up",
        }
        data.pop(field)

        serializer = KPIItemSerializer(data=data)

        assert not serializer.is_valid()
        assert field in serializer.errors

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("value", "not-an-integer"),
            ("trend", "not-an-integer"),
        ],
    )
    def test_rejects_non_integer_values(self, field, value):
        data = {
            "value": 100,
            "trend": 10,
            "direction": "up",
            field: value,
        }

        serializer = KPIItemSerializer(data=data)

        assert not serializer.is_valid()
        assert field in serializer.errors


class TestKPISerializer:
    def test_serializes_all_kpis(self):
        data = {
            "totalStudents": {
                "value": 100,
                "trend": 10,
                "direction": "up",
            },
            "revenue": {
                "value": 5000,
                "trend": 20,
                "direction": "up",
            },
            "completionRate": {
                "value": 75,
                "trend": 5,
                "direction": "up",
            },
            "watchTime": {
                "value": 240,
                "trend": 10,
                "direction": "neutral",
            },
            "quizAvg": {
                "value": 82,
                "trend": 3,
                "direction": "down",
            },
        }

        serializer = KPISerializer(data=data)

        assert serializer.is_valid()
        assert serializer.validated_data == data

    @pytest.mark.parametrize(
        "field",
        [
            "totalStudents",
            "revenue",
            "completionRate",
            "watchTime",
            "quizAvg",
        ],
    )
    def test_requires_all_kpi_fields(self, field):
        data = {
            "totalStudents": {
                "value": 100,
                "trend": 10,
                "direction": "up",
            },
            "revenue": {
                "value": 5000,
                "trend": 20,
                "direction": "up",
            },
            "completionRate": {
                "value": 75,
                "trend": 5,
                "direction": "up",
            },
            "watchTime": {
                "value": 240,
                "trend": 10,
                "direction": "neutral",
            },
            "quizAvg": {
                "value": 82,
                "trend": 3,
                "direction": "down",
            },
        }
        data.pop(field)

        serializer = KPISerializer(data=data)

        assert not serializer.is_valid()
        assert field in serializer.errors

    def test_rejects_invalid_nested_kpi(self):
        data = {
            "totalStudents": {
                "value": 100,
                "trend": 10,
                "direction": "invalid",
            },
            "revenue": {
                "value": 5000,
                "trend": 20,
                "direction": "up",
            },
            "completionRate": {
                "value": 75,
                "trend": 5,
                "direction": "up",
            },
            "watchTime": {
                "value": 240,
                "trend": 10,
                "direction": "neutral",
            },
            "quizAvg": {
                "value": 82,
                "trend": 3,
                "direction": "down",
            },
        }

        serializer = KPISerializer(data=data)

        assert not serializer.is_valid()
        assert "totalStudents" in serializer.errors
        assert "direction" in serializer.errors["totalStudents"]


class TestEnrollmentTrendSerializer:
    def test_serializes_valid_data(self):
        data = {
            "label": "January",
            "count": 125,
        }

        serializer = EnrollmentTrendSerializer(data=data)

        assert serializer.is_valid()
        assert serializer.validated_data == data

    def test_requires_label(self):
        serializer = EnrollmentTrendSerializer(
            data={"count": 125},
        )

        assert not serializer.is_valid()
        assert "label" in serializer.errors

    def test_requires_count(self):
        serializer = EnrollmentTrendSerializer(
            data={"label": "January"},
        )

        assert not serializer.is_valid()
        assert "count" in serializer.errors

    def test_rejects_non_integer_count(self):
        serializer = EnrollmentTrendSerializer(
            data={
                "label": "January",
                "count": "many",
            },
        )

        assert not serializer.is_valid()
        assert "count" in serializer.errors


class TestRevenueTrendSerializer:
    def test_serializes_valid_decimal_amount(self):
        data = {
            "label": "January",
            "amount": "1250.50",
        }

        serializer = RevenueTrendSerializer(data=data)

        assert serializer.is_valid()
        assert serializer.validated_data["label"] == "January"
        assert serializer.validated_data["amount"] == Decimal("1250.50")

    @pytest.mark.parametrize(
        "amount",
        [
            "0.00",
            "1.25",
            "9999999999.99",
            Decimal("1250.50"),
        ],
    )
    def test_accepts_valid_decimal_amounts(self, amount):
        serializer = RevenueTrendSerializer(
            data={
                "label": "January",
                "amount": amount,
            },
        )

        assert serializer.is_valid()

    def test_rejects_amount_with_more_than_two_decimal_places(self):
        serializer = RevenueTrendSerializer(
            data={
                "label": "January",
                "amount": "1250.123",
            },
        )

        assert not serializer.is_valid()
        assert "amount" in serializer.errors

    def test_rejects_amount_exceeding_max_digits(self):
        serializer = RevenueTrendSerializer(
            data={
                "label": "January",
                "amount": "12345678901.00",
            },
        )

        assert not serializer.is_valid()
        assert "amount" in serializer.errors

    def test_requires_label(self):
        serializer = RevenueTrendSerializer(
            data={"amount": "100.00"},
        )

        assert not serializer.is_valid()
        assert "label" in serializer.errors

    def test_requires_amount(self):
        serializer = RevenueTrendSerializer(
            data={"label": "January"},
        )

        assert not serializer.is_valid()
        assert "amount" in serializer.errors


class TestCompletionSerializer:
    def test_serializes_valid_data(self):
        data = {
            "completed": 75,
            "inProgress": 25,
        }

        serializer = CompletionSerializer(data=data)

        assert serializer.is_valid()
        assert serializer.validated_data == data

    @pytest.mark.parametrize(
        "field",
        ["completed", "inProgress"],
    )
    def test_requires_all_fields(self, field):
        data = {
            "completed": 75,
            "inProgress": 25,
        }
        data.pop(field)

        serializer = CompletionSerializer(data=data)

        assert not serializer.is_valid()
        assert field in serializer.errors

    @pytest.mark.parametrize(
        "field",
        ["completed", "inProgress"],
    )
    def test_rejects_non_integer_values(self, field):
        data = {
            "completed": 75,
            "inProgress": 25,
            field: "invalid",
        }

        serializer = CompletionSerializer(data=data)

        assert not serializer.is_valid()
        assert field in serializer.errors


class TestWatchTimeByCourseSerializer:
    def test_serializes_valid_data(self):
        data = {
            "course": "Django REST Framework",
            "hours": 25,
        }

        serializer = WatchTimeByCourseSerializer(data=data)

        assert serializer.is_valid()
        assert serializer.validated_data == data

    def test_requires_course(self):
        serializer = WatchTimeByCourseSerializer(
            data={"hours": 25},
        )

        assert not serializer.is_valid()
        assert "course" in serializer.errors

    def test_requires_hours(self):
        serializer = WatchTimeByCourseSerializer(
            data={"course": "Django REST Framework"},
        )

        assert not serializer.is_valid()
        assert "hours" in serializer.errors

    def test_rejects_non_integer_hours(self):
        serializer = WatchTimeByCourseSerializer(
            data={
                "course": "Django REST Framework",
                "hours": "twenty-five",
            },
        )

        assert not serializer.is_valid()
        assert "hours" in serializer.errors


class TestQuizPerformanceSerializer:
    def test_serializes_valid_data(self):
        data = {
            "course": "Django REST Framework",
            "avg": 87.5,
        }

        serializer = QuizPerformanceSerializer(data=data)

        assert serializer.is_valid()
        assert serializer.validated_data["course"] == "Django REST Framework"
        assert serializer.validated_data["avg"] == 87.5

    @pytest.mark.parametrize(
        "avg",
        [0.0, 50.5, 100.0],
    )
    def test_accepts_valid_float_average(self, avg):
        serializer = QuizPerformanceSerializer(
            data={
                "course": "Django REST Framework",
                "avg": avg,
            },
        )

        assert serializer.is_valid()

    def test_requires_course(self):
        serializer = QuizPerformanceSerializer(
            data={"avg": 85.5},
        )

        assert not serializer.is_valid()
        assert "course" in serializer.errors

    def test_requires_avg(self):
        serializer = QuizPerformanceSerializer(
            data={"course": "Django REST Framework"},
        )

        assert not serializer.is_valid()
        assert "avg" in serializer.errors

    def test_rejects_non_numeric_average(self):
        serializer = QuizPerformanceSerializer(
            data={
                "course": "Django REST Framework",
                "avg": "excellent",
            },
        )

        assert not serializer.is_valid()
        assert "avg" in serializer.errors


class TestGeoDistributionSerializer:
    def test_serializes_valid_data(self):
        data = {
            "country": "United States",
            "pct": 35,
            "flag": "🇺🇸",
        }

        serializer = GeoDistributionSerializer(data=data)

        assert serializer.is_valid()
        assert serializer.validated_data == data

    @pytest.mark.parametrize(
        "field",
        ["country", "pct", "flag"],
    )
    def test_requires_all_fields(self, field):
        data = {
            "country": "United States",
            "pct": 35,
            "flag": "🇺🇸",
        }
        data.pop(field)

        serializer = GeoDistributionSerializer(data=data)

        assert not serializer.is_valid()
        assert field in serializer.errors

    def test_rejects_non_integer_percentage(self):
        serializer = GeoDistributionSerializer(
            data={
                "country": "United States",
                "pct": "35%",
                "flag": "🇺🇸",
            },
        )

        assert not serializer.is_valid()
        assert "pct" in serializer.errors


class TestAnalyticSerializer:
    @pytest.fixture
    def valid_analytics_data(self):
        return {
            "kpis": {
                "totalStudents": {
                    "value": 100,
                    "trend": 10,
                    "direction": "up",
                },
                "revenue": {
                    "value": 5000,
                    "trend": 15,
                    "direction": "up",
                },
                "completionRate": {
                    "value": 75,
                    "trend": 5,
                    "direction": "up",
                },
                "watchTime": {
                    "value": 250,
                    "trend": 8,
                    "direction": "neutral",
                },
                "quizAvg": {
                    "value": 85,
                    "trend": 2,
                    "direction": "down",
                },
            },
            "enrollmentTrends": [
                {
                    "label": "January",
                    "count": 100,
                },
                {
                    "label": "February",
                    "count": 125,
                },
            ],
            "revenueTrends": [
                {
                    "label": "January",
                    "amount": "1000.00",
                },
                {
                    "label": "February",
                    "amount": "1500.50",
                },
            ],
            "completion": {
                "completed": 80,
                "inProgress": 20,
            },
            "watchTimeByCourse": [
                {
                    "course": "Django",
                    "hours": 25,
                },
                {
                    "course": "DRF",
                    "hours": 30,
                },
            ],
            "quizPerformance": [
                {
                    "course": "Django",
                    "avg": 85.5,
                },
                {
                    "course": "DRF",
                    "avg": 90.0,
                },
            ],
            "geoDistribution": [
                {
                    "country": "United States",
                    "pct": 40,
                    "flag": "🇺🇸",
                },
                {
                    "country": "Germany",
                    "pct": 25,
                    "flag": "🇩🇪",
                },
            ],
        }

    def test_serializes_complete_analytics_payload(
        self,
        valid_analytics_data,
    ):
        serializer = AnalyticSerializer(
            data=valid_analytics_data,
        )

        assert serializer.is_valid()
        assert serializer.validated_data["kpis"]["revenue"]["value"] == 5000
        assert len(serializer.validated_data["enrollmentTrends"]) == 2
        assert len(serializer.validated_data["revenueTrends"]) == 2
        assert len(serializer.validated_data["watchTimeByCourse"]) == 2
        assert len(serializer.validated_data["quizPerformance"]) == 2
        assert len(serializer.validated_data["geoDistribution"]) == 2

    @pytest.mark.parametrize(
        "field",
        [
            "kpis",
            "enrollmentTrends",
            "revenueTrends",
            "completion",
            "watchTimeByCourse",
            "quizPerformance",
            "geoDistribution",
        ],
    )
    def test_requires_all_top_level_fields(
        self,
        valid_analytics_data,
        field,
    ):
        valid_analytics_data.pop(field)

        serializer = AnalyticSerializer(
            data=valid_analytics_data,
        )

        assert not serializer.is_valid()
        assert field in serializer.errors

    def test_validates_nested_kpis(
        self,
        valid_analytics_data,
    ):
        valid_analytics_data["kpis"]["revenue"]["direction"] = "invalid"

        serializer = AnalyticSerializer(
            data=valid_analytics_data,
        )

        assert not serializer.is_valid()
        assert "kpis" in serializer.errors

    def test_validates_nested_enrollment_trends(
        self,
        valid_analytics_data,
    ):
        valid_analytics_data["enrollmentTrends"][0]["count"] = "invalid"

        serializer = AnalyticSerializer(
            data=valid_analytics_data,
        )

        assert not serializer.is_valid()
        assert "enrollmentTrends" in serializer.errors

    def test_validates_nested_revenue_trends(
        self,
        valid_analytics_data,
    ):
        valid_analytics_data["revenueTrends"][0]["amount"] = "not-a-decimal"

        serializer = AnalyticSerializer(
            data=valid_analytics_data,
        )

        assert not serializer.is_valid()
        assert "revenueTrends" in serializer.errors

    def test_validates_nested_completion(
        self,
        valid_analytics_data,
    ):
        valid_analytics_data["completion"]["completed"] = "invalid"

        serializer = AnalyticSerializer(
            data=valid_analytics_data,
        )

        assert not serializer.is_valid()
        assert "completion" in serializer.errors

    def test_validates_nested_watch_time(
        self,
        valid_analytics_data,
    ):
        valid_analytics_data["watchTimeByCourse"][0]["hours"] = "invalid"

        serializer = AnalyticSerializer(
            data=valid_analytics_data,
        )

        assert not serializer.is_valid()
        assert "watchTimeByCourse" in serializer.errors

    def test_validates_nested_quiz_performance(
        self,
        valid_analytics_data,
    ):
        valid_analytics_data["quizPerformance"][0]["avg"] = "invalid"

        serializer = AnalyticSerializer(
            data=valid_analytics_data,
        )

        assert not serializer.is_valid()
        assert "quizPerformance" in serializer.errors

    def test_validates_nested_geo_distribution(
        self,
        valid_analytics_data,
    ):
        valid_analytics_data["geoDistribution"][0]["pct"] = "invalid"

        serializer = AnalyticSerializer(
            data=valid_analytics_data,
        )

        assert not serializer.is_valid()
        assert "geoDistribution" in serializer.errors

    def test_supports_empty_many_fields(
        self,
        valid_analytics_data,
    ):
        valid_analytics_data["enrollmentTrends"] = []
        valid_analytics_data["revenueTrends"] = []
        valid_analytics_data["watchTimeByCourse"] = []
        valid_analytics_data["quizPerformance"] = []
        valid_analytics_data["geoDistribution"] = []

        serializer = AnalyticSerializer(
            data=valid_analytics_data,
        )

        assert serializer.is_valid()

        assert serializer.validated_data["enrollmentTrends"] == []
        assert serializer.validated_data["revenueTrends"] == []
        assert serializer.validated_data["watchTimeByCourse"] == []
        assert serializer.validated_data["quizPerformance"] == []
        assert serializer.validated_data["geoDistribution"] == []

    def test_serializes_representation_with_nested_data(
        self,
        valid_analytics_data,
    ):
        serializer = AnalyticSerializer(
            data=valid_analytics_data,
        )

        assert serializer.is_valid()

        output = serializer.data

        assert output["kpis"]["totalStudents"]["value"] == 100
        assert output["kpis"]["revenue"]["direction"] == "up"

        assert output["enrollmentTrends"][0] == {
            "label": "January",
            "count": 100,
        }

        assert output["revenueTrends"][0] == {
            "label": "January",
            "amount": "1000.00",
        }

        assert output["completion"] == {
            "completed": 80,
            "inProgress": 20,
        }

        assert output["watchTimeByCourse"][0] == {
            "course": "Django",
            "hours": 25,
        }

        assert output["quizPerformance"][0] == {
            "course": "Django",
            "avg": 85.5,
        }

        assert output["geoDistribution"][0] == {
            "country": "United States",
            "pct": 40,
            "flag": "🇺🇸",
        }


@pytest.mark.django_db
class TestAnalyticFilterCoursesSerializer:
    @pytest.fixture
    def course(self, instructor_user):
        return Course.objects.create(
            title="Django REST Framework",
            slug="django-rest-framework",
            owner=instructor_user,
        )

    def test_serializes_slug_and_title_only(self, course):
        serializer = AnalyticFilterCoursesSerializer(
            instance=course,
        )

        assert serializer.data == {
            "slug": "django-rest-framework",
            "title": "Django REST Framework",
        }

    def test_does_not_expose_other_course_fields(self, course):
        serializer = AnalyticFilterCoursesSerializer(
            instance=course,
        )

        assert set(serializer.data.keys()) == {
            "slug",
            "title",
        }

    def test_deserializes_valid_course_data(self):
        data = {
            "slug": "django-rest-framework",
            "title": "Django REST Framework",
        }

        serializer = AnalyticFilterCoursesSerializer(data=data)

        assert serializer.is_valid()
        assert serializer.validated_data["slug"] == "django-rest-framework"
        assert serializer.validated_data["title"] == ("Django REST Framework")

    def test_requires_slug_when_deserializing(self):
        serializer = AnalyticFilterCoursesSerializer(
            data={
                "title": "Django REST Framework",
            },
        )

        assert not serializer.is_valid()
        assert "slug" in serializer.errors

    def test_requires_title_when_deserializing(self):
        serializer = AnalyticFilterCoursesSerializer(
            data={
                "slug": "django-rest-framework",
            },
        )

        assert not serializer.is_valid()
        assert "title" in serializer.errors

    def test_rejects_title_longer_than_course_max_length(self):
        serializer = AnalyticFilterCoursesSerializer(
            data={
                "slug": "django-rest-framework",
                "title": "x" * 256,
            },
        )

        assert not serializer.is_valid()
        assert "title" in serializer.errors

    def test_rejects_slug_longer_than_course_max_length(self):
        serializer = AnalyticFilterCoursesSerializer(
            data={
                "slug": "x" * 281,
                "title": "Django REST Framework",
            },
        )

        assert not serializer.is_valid()
        assert "slug" in serializer.errors

    def test_rejects_invalid_slug(self):
        serializer = AnalyticFilterCoursesSerializer(
            data={
                "slug": "invalid slug with spaces",
                "title": "Django REST Framework",
            },
        )

        assert not serializer.is_valid()
        assert "slug" in serializer.errors
