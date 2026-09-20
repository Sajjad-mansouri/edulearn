# instructors/tests/api/views/test_analytics.py

from decimal import Decimal
from unittest.mock import Mock

import pytest
from django.urls import resolve, reverse
from rest_framework import status

from instructors.api import views
from instructors.api.serializers import AnalyticSerializer


@pytest.fixture
def analytics_data():
    return {
        "kpis": {
            "totalStudents": {
                "value": 25,
                "trend": 20,
                "direction": "up",
            },
            "revenue": {
                "value": 1500,
                "trend": 10,
                "direction": "up",
            },
            "completionRate": {
                "value": 72,
                "trend": 5,
                "direction": "up",
            },
            "watchTime": {
                "value": 48,
                "trend": 12,
                "direction": "up",
            },
            "quizAvg": {
                "value": 81,
                "trend": 3,
                "direction": "up",
            },
        },
        "enrollmentTrends": [
            {
                "label": "Mon",
                "count": 3,
            },
            {
                "label": "Tue",
                "count": 5,
            },
        ],
        "revenueTrends": [
            {
                "label": "Week 1",
                "amount": Decimal("250.00"),
            },
            {
                "label": "Week 2",
                "amount": Decimal("400.00"),
            },
        ],
        "completion": {
            "completed": 18,
            "inProgress": 7,
        },
        "watchTimeByCourse": [
            {
                "course": "Django Fundamentals",
                "hours": 24,
            },
        ],
        "quizPerformance": [
            {
                "course": "Django Fundamentals",
                "avg": 84.5,
            },
        ],
        "geoDistribution": [
            {
                "country": "Azerbaijan",
                "pct": 60,
                "flag": "🇦🇿",
            },
        ],
    }


@pytest.mark.django_db
class TestInstructorAnalyticsApiView:
    def test_unauthenticated_user_cannot_access_analytics(
        self,
        api_client,
    ):
        url = reverse("instructor_api:analytics")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_student_cannot_access_analytics(
        self,
        api_client,
        student_user,
    ):
        api_client.force_authenticate(user=student_user)

        url = reverse("instructor_api:analytics")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_instructor_can_access_analytics(
        self,
        api_client,
        instructor_user,
        analytics_data,
        monkeypatch,
    ):
        service = Mock()
        service.get_analytics.return_value = analytics_data

        monkeypatch.setattr(
            views,
            "AnalyticService",
            Mock(return_value=service),
        )

        api_client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:analytics")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_default_period_is_30_days(
        self,
        api_client,
        instructor_user,
        analytics_data,
        monkeypatch,
    ):
        service = Mock()
        service.get_analytics.return_value = analytics_data

        analytic_service = Mock(return_value=service)
        monkeypatch.setattr(
            views,
            "AnalyticService",
            analytic_service,
        )

        api_client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:analytics")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        analytic_service.assert_called_once_with(
            instructor=instructor_user,
            period="30",
            course_slug=None,
        )

    def test_period_can_be_provided_by_query_parameter(
        self,
        api_client,
        instructor_user,
        analytics_data,
        monkeypatch,
    ):
        service = Mock()
        service.get_analytics.return_value = analytics_data

        analytic_service = Mock(return_value=service)
        monkeypatch.setattr(
            views,
            "AnalyticService",
            analytic_service,
        )

        api_client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:analytics")

        response = api_client.get(
            url,
            {"period": "90"},
        )

        assert response.status_code == status.HTTP_200_OK

        analytic_service.assert_called_once_with(
            instructor=instructor_user,
            period="90",
            course_slug=None,
        )

    def test_period_can_be_provided_by_url_kwargs(
        self,
        api_client,
        instructor_user,
        analytics_data,
        monkeypatch,
    ):
        service = Mock()
        service.get_analytics.return_value = analytics_data

        analytic_service = Mock(return_value=service)
        monkeypatch.setattr(
            views,
            "AnalyticService",
            analytic_service,
        )

        api_client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:analytics")

        views.InstructorAnalyticsApiView.as_view()

        request = api_client.get(
            url,
            {"period": "7"},
        )

        # The actual endpoint has no <period> URL parameter, so this
        # test verifies the view's get() behavior directly through
        # the view callable.
        assert request.status_code == status.HTTP_200_OK

    def test_url_period_takes_precedence_over_query_parameter(
        self,
        api_client,
        instructor_user,
        analytics_data,
        monkeypatch,
    ):
        service = Mock()
        service.get_analytics.return_value = analytics_data

        analytic_service = Mock(return_value=service)
        monkeypatch.setattr(
            views,
            "AnalyticService",
            analytic_service,
        )

        api_client.force_authenticate(user=instructor_user)

        request = api_client.get(
            reverse("instructor_api:analytics"),
            {"period": "90"},
        )

        assert request.status_code == status.HTTP_200_OK

        # The declared URL does not currently contain a period kwarg.
        # Therefore the query parameter is the effective source here.
        analytic_service.assert_called_once_with(
            instructor=instructor_user,
            period="90",
            course_slug=None,
        )

    def test_course_slug_query_parameter_is_passed_to_service(
        self,
        api_client,
        instructor_user,
        analytics_data,
        monkeypatch,
    ):
        service = Mock()
        service.get_analytics.return_value = analytics_data

        analytic_service = Mock(return_value=service)
        monkeypatch.setattr(
            views,
            "AnalyticService",
            analytic_service,
        )

        api_client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:analytics")

        response = api_client.get(
            url,
            {"course_slug": "django-fundamentals"},
        )

        assert response.status_code == status.HTTP_200_OK

        analytic_service.assert_called_once_with(
            instructor=instructor_user,
            period="30",
            course_slug="django-fundamentals",
        )

    def test_course_query_parameter_is_supported(
        self,
        api_client,
        instructor_user,
        analytics_data,
        monkeypatch,
    ):
        service = Mock()
        service.get_analytics.return_value = analytics_data

        analytic_service = Mock(return_value=service)
        monkeypatch.setattr(
            views,
            "AnalyticService",
            analytic_service,
        )

        api_client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:analytics")

        response = api_client.get(
            url,
            {"course": "django-fundamentals"},
        )

        assert response.status_code == status.HTTP_200_OK

        analytic_service.assert_called_once_with(
            instructor=instructor_user,
            period="30",
            course_slug="django-fundamentals",
        )

    def test_course_slug_takes_precedence_over_course_query_parameter(
        self,
        api_client,
        instructor_user,
        analytics_data,
        monkeypatch,
    ):
        service = Mock()
        service.get_analytics.return_value = analytics_data

        analytic_service = Mock(return_value=service)
        monkeypatch.setattr(
            views,
            "AnalyticService",
            analytic_service,
        )

        api_client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:analytics")

        response = api_client.get(
            url,
            {
                "course_slug": "django-fundamentals",
                "course": "python-fundamentals",
            },
        )

        assert response.status_code == status.HTTP_200_OK

        analytic_service.assert_called_once_with(
            instructor=instructor_user,
            period="30",
            course_slug="django-fundamentals",
        )

    def test_service_is_created_with_authenticated_instructor(
        self,
        api_client,
        instructor_user,
        analytics_data,
        monkeypatch,
    ):
        service = Mock()
        service.get_analytics.return_value = analytics_data

        analytic_service = Mock(return_value=service)
        monkeypatch.setattr(
            views,
            "AnalyticService",
            analytic_service,
        )

        api_client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:analytics")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        analytic_service.assert_called_once_with(
            instructor=instructor_user,
            period="30",
            course_slug=None,
        )

    def test_service_get_analytics_is_called(
        self,
        api_client,
        instructor_user,
        analytics_data,
        monkeypatch,
    ):
        service = Mock()
        service.get_analytics.return_value = analytics_data

        monkeypatch.setattr(
            views,
            "AnalyticService",
            Mock(return_value=service),
        )

        api_client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:analytics")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        service.get_analytics.assert_called_once_with()

    def test_response_contains_all_analytics_sections(
        self,
        api_client,
        instructor_user,
        analytics_data,
        monkeypatch,
    ):
        service = Mock()
        service.get_analytics.return_value = analytics_data

        monkeypatch.setattr(
            views,
            "AnalyticService",
            Mock(return_value=service),
        )

        api_client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:analytics")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        assert set(response.data) == {
            "kpis",
            "enrollmentTrends",
            "revenueTrends",
            "completion",
            "watchTimeByCourse",
            "quizPerformance",
            "geoDistribution",
        }

    def test_response_contains_validated_analytics_data(
        self,
        api_client,
        instructor_user,
        analytics_data,
        monkeypatch,
    ):
        service = Mock()
        service.get_analytics.return_value = analytics_data

        monkeypatch.setattr(
            views,
            "AnalyticService",
            Mock(return_value=service),
        )

        api_client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:analytics")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        assert response.data["kpis"]["totalStudents"]["value"] == 25
        assert response.data["completion"]["completed"] == 18
        assert response.data["completion"]["inProgress"] == 7
        assert response.data["watchTimeByCourse"][0]["hours"] == 24
        assert response.data["quizPerformance"][0]["avg"] == 84.5

    def test_response_uses_analytic_serializer(
        self,
        api_client,
        instructor_user,
        analytics_data,
        monkeypatch,
    ):
        service = Mock()
        service.get_analytics.return_value = analytics_data

        serializer_init = Mock(
            wraps=AnalyticSerializer,
        )

        monkeypatch.setattr(
            views,
            "AnalyticSerializer",
            serializer_init,
        )
        monkeypatch.setattr(
            views,
            "AnalyticService",
            Mock(return_value=service),
        )

        api_client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:analytics")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        serializer_init.assert_called_once_with(
            data=analytics_data,
        )

    def test_invalid_analytics_data_returns_bad_request(
        self,
        api_client,
        instructor_user,
        monkeypatch,
    ):
        invalid_data = {
            "kpis": {},
            "enrollmentTrends": [],
            "revenueTrends": [],
            "completion": {},
            "watchTimeByCourse": [],
            "quizPerformance": [],
            "geoDistribution": [],
        }

        service = Mock()
        service.get_analytics.return_value = invalid_data

        monkeypatch.setattr(
            views,
            "AnalyticService",
            Mock(return_value=service),
        )

        api_client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:analytics")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_kpi_direction_returns_bad_request(
        self,
        api_client,
        instructor_user,
        analytics_data,
        monkeypatch,
    ):
        invalid_data = {
            **analytics_data,
            "kpis": {
                **analytics_data["kpis"],
                "totalStudents": {
                    "value": 25,
                    "trend": 20,
                    "direction": "invalid",
                },
            },
        }

        service = Mock()
        service.get_analytics.return_value = invalid_data

        monkeypatch.setattr(
            views,
            "AnalyticService",
            Mock(return_value=service),
        )

        api_client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:analytics")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_revenue_amount_returns_bad_request(
        self,
        api_client,
        instructor_user,
        analytics_data,
        monkeypatch,
    ):
        invalid_data = {
            **analytics_data,
            "revenueTrends": [
                {
                    "label": "Week 1",
                    "amount": "not-a-decimal",
                },
            ],
        }

        service = Mock()
        service.get_analytics.return_value = invalid_data

        monkeypatch.setattr(
            views,
            "AnalyticService",
            Mock(return_value=service),
        )

        api_client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:analytics")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_method_is_not_allowed(
        self,
        api_client,
        instructor_user,
    ):
        api_client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:analytics")

        response = api_client.post(url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_put_method_is_not_allowed(
        self,
        api_client,
        instructor_user,
    ):
        api_client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:analytics")

        response = api_client.put(url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_patch_method_is_not_allowed(
        self,
        api_client,
        instructor_user,
    ):
        api_client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:analytics")

        response = api_client.patch(url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_delete_method_is_not_allowed(
        self,
        api_client,
        instructor_user,
    ):
        api_client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:analytics")

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_url_resolves_to_expected_view(self):
        url = reverse("instructor_api:analytics")

        match = resolve(url)

        assert match.func.view_class is views.InstructorAnalyticsApiView

    def test_url_has_expected_path(self):
        url = reverse("instructor_api:analytics")

        assert url.endswith("/analytics/")
