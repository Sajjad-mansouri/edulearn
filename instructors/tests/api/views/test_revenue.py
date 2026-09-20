from unittest.mock import Mock

import pytest
from django.urls import reverse
from rest_framework import status

from instructors.api import views
from instructors.api.services.revenue import RevenueService

pytestmark = pytest.mark.django_db


class TestInstructorRevenueApiView:
    @pytest.fixture
    def url(self):
        return reverse("instructor_api:revenue")

    @pytest.fixture
    def revenue_data(self):
        return {
            "revenue_summary": {
                "lifetime": {
                    "value": "1000.00",
                    "trend": None,
                    "direction": None,
                },
                "period_revenue": {
                    "value": "300.00",
                    "trend": 20,
                    "direction": "up",
                },
                "ytd": {
                    "value": "700.00",
                    "trend": 10,
                    "direction": "up",
                },
            },
            "course_breakdown": [
                {
                    "course": "Django Fundamentals",
                    "amount": "200.00",
                },
                {
                    "course": "Advanced Python",
                    "amount": "100.00",
                },
            ],
        }

    def _mock_revenue_service(
        self,
        monkeypatch,
        revenue_data,
    ):
        service = Mock()
        service.get_revenue.return_value = revenue_data

        service_class = Mock(
            return_value=service,
            ALLOWED_PERIODS=RevenueService.ALLOWED_PERIODS,
        )

        monkeypatch.setattr(
            views,
            "RevenueService",
            service_class,
        )

        return service, service_class

    def test_unauthenticated_user_cannot_access_revenue(
        self,
        api_client,
        url,
    ):
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_non_instructor_user_cannot_access_revenue(
        self,
        api_client,
        student_user,
        url,
    ):
        api_client.force_authenticate(user=student_user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == (
            "You must be an instructor to access this resource."
        )

    def test_instructor_can_access_revenue(
        self,
        api_client,
        instructor_user,
        url,
        revenue_data,
        monkeypatch,
    ):
        service, service_class = self._mock_revenue_service(
            monkeypatch,
            revenue_data,
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == revenue_data

        service_class.assert_called_once_with(
            instructor=instructor_user,
            period="30",
        )
        service.get_revenue.assert_called_once_with()

    def test_missing_period_defaults_to_30(
        self,
        api_client,
        instructor_user,
        url,
        revenue_data,
        monkeypatch,
    ):
        _, service_class = self._mock_revenue_service(
            monkeypatch,
            revenue_data,
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        service_class.assert_called_once_with(
            instructor=instructor_user,
            period="30",
        )

    @pytest.mark.parametrize(
        "period",
        [
            "30",
            "90",
            "365",
            "all",
        ],
    )
    def test_allowed_period_is_passed_to_revenue_service(
        self,
        api_client,
        instructor_user,
        url,
        revenue_data,
        monkeypatch,
        period,
    ):
        _, service_class = self._mock_revenue_service(
            monkeypatch,
            revenue_data,
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(
            url,
            {"period": period},
        )

        assert response.status_code == status.HTTP_200_OK

        service_class.assert_called_once_with(
            instructor=instructor_user,
            period=period,
        )

    @pytest.mark.parametrize(
        ("period", "expected_period"),
        [
            (" 30 ", "30"),
            (" 90 ", "90"),
            (" 365 ", "365"),
            (" ALL ", "all"),
            (" All ", "all"),
            ("aLl", "all"),
        ],
    )
    def test_period_is_normalized_before_validation(
        self,
        api_client,
        instructor_user,
        url,
        revenue_data,
        monkeypatch,
        period,
        expected_period,
    ):
        _, service_class = self._mock_revenue_service(
            monkeypatch,
            revenue_data,
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(
            url,
            {"period": period},
        )

        assert response.status_code == status.HTTP_200_OK

        service_class.assert_called_once_with(
            instructor=instructor_user,
            period=expected_period,
        )

    @pytest.mark.parametrize(
        "period",
        [
            "",
            "7",
            "60",
            "180",
            "12",
            "30days",
            "month",
            "year",
            "invalid",
            "foo",
        ],
    )
    def test_invalid_period_returns_400(
        self,
        api_client,
        instructor_user,
        url,
        monkeypatch,
        period,
    ):
        service_class = Mock(
            ALLOWED_PERIODS=RevenueService.ALLOWED_PERIODS,
        )

        monkeypatch.setattr(
            views,
            "RevenueService",
            service_class,
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(
            url,
            {"period": period},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "period" in response.data

        error_data = response.data["period"]

        assert error_data

        message = str(error_data)

        assert "Invalid period. Allowed values:" in message

        service_class.assert_not_called()

    def test_invalid_period_message_contains_all_allowed_periods(
        self,
        api_client,
        instructor_user,
        url,
        monkeypatch,
    ):
        service_class = Mock(
            ALLOWED_PERIODS=RevenueService.ALLOWED_PERIODS,
        )

        monkeypatch.setattr(
            views,
            "RevenueService",
            service_class,
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(
            url,
            {"period": "7"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "period" in response.data

        message = str(response.data["period"])

        assert "Invalid period. Allowed values:" in message

        for allowed_period in RevenueService.ALLOWED_PERIODS:
            assert allowed_period in message

        service_class.assert_not_called()

    def test_invalid_period_does_not_instantiate_service(
        self,
        api_client,
        instructor_user,
        url,
        monkeypatch,
    ):
        service_class = Mock(
            ALLOWED_PERIODS=RevenueService.ALLOWED_PERIODS,
        )

        monkeypatch.setattr(
            views,
            "RevenueService",
            service_class,
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(
            url,
            {"period": "7"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        service_class.assert_not_called()

    def test_revenue_service_get_revenue_is_called_once(
        self,
        api_client,
        instructor_user,
        url,
        revenue_data,
        monkeypatch,
    ):
        service, _ = self._mock_revenue_service(
            monkeypatch,
            revenue_data,
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        service.get_revenue.assert_called_once_with()

    def test_revenue_service_receives_authenticated_instructor(
        self,
        api_client,
        instructor_user,
        url,
        revenue_data,
        monkeypatch,
    ):
        _, service_class = self._mock_revenue_service(
            monkeypatch,
            revenue_data,
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(
            url,
            {"period": "90"},
        )

        assert response.status_code == status.HTTP_200_OK

        service_class.assert_called_once_with(
            instructor=instructor_user,
            period="90",
        )

    def test_response_contains_revenue_data(
        self,
        api_client,
        instructor_user,
        url,
        revenue_data,
        monkeypatch,
    ):
        self._mock_revenue_service(
            monkeypatch,
            revenue_data,
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == revenue_data

    def test_response_contains_expected_top_level_fields(
        self,
        api_client,
        instructor_user,
        url,
        revenue_data,
        monkeypatch,
    ):
        self._mock_revenue_service(
            monkeypatch,
            revenue_data,
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert set(response.data.keys()) == {
            "revenue_summary",
            "course_breakdown",
        }

    def test_revenue_summary_contains_expected_fields(
        self,
        api_client,
        instructor_user,
        url,
        revenue_data,
        monkeypatch,
    ):
        self._mock_revenue_service(
            monkeypatch,
            revenue_data,
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        assert set(response.data["revenue_summary"].keys()) == {
            "lifetime",
            "period_revenue",
            "ytd",
        }

    def test_lifetime_revenue_contains_expected_fields(
        self,
        api_client,
        instructor_user,
        url,
        revenue_data,
        monkeypatch,
    ):
        self._mock_revenue_service(
            monkeypatch,
            revenue_data,
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(url)

        lifetime = response.data["revenue_summary"]["lifetime"]

        assert set(lifetime.keys()) == {
            "value",
            "trend",
            "direction",
        }

    def test_period_revenue_contains_expected_fields(
        self,
        api_client,
        instructor_user,
        url,
        revenue_data,
        monkeypatch,
    ):
        self._mock_revenue_service(
            monkeypatch,
            revenue_data,
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(url)

        period_revenue = response.data["revenue_summary"]["period_revenue"]

        assert set(period_revenue.keys()) == {
            "value",
            "trend",
            "direction",
        }

    def test_ytd_revenue_contains_expected_fields(
        self,
        api_client,
        instructor_user,
        url,
        revenue_data,
        monkeypatch,
    ):
        self._mock_revenue_service(
            monkeypatch,
            revenue_data,
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(url)

        ytd = response.data["revenue_summary"]["ytd"]

        assert set(ytd.keys()) == {
            "value",
            "trend",
            "direction",
        }

    def test_course_breakdown_is_returned_as_list(
        self,
        api_client,
        instructor_user,
        url,
        revenue_data,
        monkeypatch,
    ):
        self._mock_revenue_service(
            monkeypatch,
            revenue_data,
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(
            response.data["course_breakdown"],
            list,
        )

    def test_course_breakdown_contains_expected_fields(
        self,
        api_client,
        instructor_user,
        url,
        revenue_data,
        monkeypatch,
    ):
        self._mock_revenue_service(
            monkeypatch,
            revenue_data,
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(url)

        course_breakdown = response.data["course_breakdown"]

        assert course_breakdown

        for course_data in course_breakdown:
            assert set(course_data.keys()) == {
                "course",
                "amount",
            }

    def test_decimal_values_are_serialized_with_two_decimal_places(
        self,
        api_client,
        instructor_user,
        url,
        monkeypatch,
    ):
        revenue_data = {
            "revenue_summary": {
                "lifetime": {
                    "value": "1234.50",
                    "trend": None,
                    "direction": None,
                },
                "period_revenue": {
                    "value": "456.75",
                    "trend": 25,
                    "direction": "up",
                },
                "ytd": {
                    "value": "789.25",
                    "trend": 10,
                    "direction": "up",
                },
            },
            "course_breakdown": [
                {
                    "course": "Django Fundamentals",
                    "amount": "456.75",
                },
            ],
        }

        self._mock_revenue_service(
            monkeypatch,
            revenue_data,
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        assert response.data["revenue_summary"]["lifetime"]["value"] == "1234.50"
        assert response.data["revenue_summary"]["period_revenue"]["value"] == "456.75"
        assert response.data["revenue_summary"]["ytd"]["value"] == "789.25"
        assert response.data["course_breakdown"][0]["amount"] == "456.75"

    def test_null_trend_and_direction_are_allowed(
        self,
        api_client,
        instructor_user,
        url,
        monkeypatch,
    ):
        revenue_data = {
            "revenue_summary": {
                "lifetime": {
                    "value": "1000.00",
                    "trend": None,
                    "direction": None,
                },
                "period_revenue": {
                    "value": "1000.00",
                    "trend": None,
                    "direction": None,
                },
                "ytd": {
                    "value": "1000.00",
                    "trend": None,
                    "direction": None,
                },
            },
            "course_breakdown": [],
        }

        self._mock_revenue_service(
            monkeypatch,
            revenue_data,
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        for revenue in response.data["revenue_summary"].values():
            assert revenue["trend"] is None
            assert revenue["direction"] is None

    def test_empty_course_breakdown_is_returned(
        self,
        api_client,
        instructor_user,
        url,
        monkeypatch,
    ):
        revenue_data = {
            "revenue_summary": {
                "lifetime": {
                    "value": "0.00",
                    "trend": None,
                    "direction": None,
                },
                "period_revenue": {
                    "value": "0.00",
                    "trend": 0,
                    "direction": "neutral",
                },
                "ytd": {
                    "value": "0.00",
                    "trend": 0,
                    "direction": "neutral",
                },
            },
            "course_breakdown": [],
        }

        self._mock_revenue_service(
            monkeypatch,
            revenue_data,
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["course_breakdown"] == []

    @pytest.mark.parametrize(
        "method",
        [
            "post",
            "put",
            "patch",
            "delete",
        ],
    )
    def test_unsupported_http_methods_return_405(
        self,
        api_client,
        instructor_user,
        url,
        method,
    ):
        api_client.force_authenticate(user=instructor_user)

        response = getattr(api_client, method)(url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_revenue_url_resolves_correctly(self):
        url = reverse("instructor_api:revenue")

        assert url.endswith("/revenue/")
