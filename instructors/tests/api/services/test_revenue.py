from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from courses.models import Course
from enrollments.models import Enrollment
from instructors.api.services.revenue import RevenueService
from payments.models import Payment

User = get_user_model()


@pytest.fixture
def second_instructor_user(db):
    return User.objects.create_user(
        username="second_instructor",
        email="second_instructor@example.com",
        password="test-password",
    )


@pytest.fixture
def second_instructor_course(db, second_instructor_user):
    return Course.objects.create(
        title="Second Instructor Course",
        slug="second-instructor-course",
        owner=second_instructor_user,
    )


@pytest.fixture
def second_instructor_enrollment(
    db,
    student_user,
    second_instructor_course,
):
    return Enrollment.objects.create(
        user=student_user,
        course=second_instructor_course,
    )


@pytest.fixture
def revenue_now(monkeypatch):
    """
    Freeze django.utils.timezone.now() for RevenueService tests.

    RevenueService imports django.utils.timezone as a module, so patching
    the module's now() function makes all RevenueService instances created
    during the test use the deterministic timestamp.
    """
    frozen_now = timezone.make_aware(
        datetime(2024, 3, 1, 12, 0, 0),
    )

    monkeypatch.setattr(
        "instructors.api.services.revenue.timezone.now",
        lambda: frozen_now,
    )

    return frozen_now


@pytest.fixture
def create_payment():
    def _create_payment(
        *,
        enrollment,
        amount,
        status=Payment.Status.SUCCEEDED,
        paid_at=None,
        refunded_at=None,
    ):
        return Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal(str(amount)),
            status=status,
            payment_type=Payment.Type.ONE_TIME,
            paid_at=paid_at,
            refunded_at=refunded_at,
        )

    return _create_payment


class TestRevenueServiceInitialization:
    def test_default_period_is_30_days(self, instructor_user):
        service = RevenueService(instructor_user)

        assert service.period == "30"
        assert service.days == 30

    def test_period_is_normalized_to_string_lowercase_and_trimmed(
        self,
        instructor_user,
    ):
        service = RevenueService(instructor_user, " 90 ")

        assert service.period == "90"
        assert service.days == 90

    def test_uppercase_period_is_normalized(self, instructor_user):
        service = RevenueService(instructor_user, "ALL")

        assert service.period == "all"
        assert service.days is None

    @pytest.mark.parametrize(
        "period",
        ["", None, "7", "3650", "invalid", "30days"],
    )
    def test_invalid_period_falls_back_to_30_days(
        self,
        instructor_user,
        period,
    ):
        service = RevenueService(instructor_user, period)

        assert service.period == "30"
        assert service.days == 30

    def test_all_period_has_no_date_range(self, instructor_user):
        service = RevenueService(instructor_user, "all")

        assert service.range_from is None
        assert service.previous_range_from is None
        assert service.previous_range_to is None

    def test_30_day_period_creates_current_and_previous_ranges(
        self,
        instructor_user,
        revenue_now,
    ):
        service = RevenueService(instructor_user, "30")

        assert service.range_from == revenue_now - timedelta(days=30)
        assert service.previous_range_from == revenue_now - timedelta(days=60)
        assert service.previous_range_to == revenue_now - timedelta(days=30)


class TestRevenueServiceDateFiltering:
    def test_start_boundary_is_inclusive(
        self,
        instructor_user,
        instructor_enrollment,
        create_payment,
        revenue_now,
    ):
        service = RevenueService(instructor_user)

        payment = create_payment(
            enrollment=instructor_enrollment,
            amount="100.00",
            paid_at=revenue_now,
        )

        result = service._apply_date_filter(
            Payment.objects.all(),
            "paid_at",
            start=revenue_now,
        )

        assert list(result) == [payment]

    def test_end_boundary_is_exclusive(
        self,
        instructor_user,
        instructor_enrollment,
        create_payment,
        revenue_now,
    ):
        service = RevenueService(instructor_user)

        payment = create_payment(
            enrollment=instructor_enrollment,
            amount="100.00",
            paid_at=revenue_now,
        )

        result = service._apply_date_filter(
            Payment.objects.all(),
            "paid_at",
            end=revenue_now,
        )

        assert payment not in result

    def test_record_before_start_is_excluded(
        self,
        instructor_user,
        instructor_enrollment,
        create_payment,
        revenue_now,
    ):
        service = RevenueService(instructor_user)

        payment = create_payment(
            enrollment=instructor_enrollment,
            amount="100.00",
            paid_at=revenue_now - timedelta(seconds=1),
        )

        result = service._apply_date_filter(
            Payment.objects.all(),
            "paid_at",
            start=revenue_now,
        )

        assert payment not in result

    def test_record_before_end_is_included(
        self,
        instructor_user,
        instructor_enrollment,
        create_payment,
        revenue_now,
    ):
        service = RevenueService(instructor_user)

        payment = create_payment(
            enrollment=instructor_enrollment,
            amount="100.00",
            paid_at=revenue_now - timedelta(seconds=1),
        )

        result = service._apply_date_filter(
            Payment.objects.all(),
            "paid_at",
            end=revenue_now,
        )

        assert payment in result

    def test_both_boundaries_are_applied(
        self,
        instructor_user,
        instructor_enrollment,
        create_payment,
        revenue_now,
    ):
        service = RevenueService(instructor_user)

        before = create_payment(
            enrollment=instructor_enrollment,
            amount="10.00",
            paid_at=revenue_now - timedelta(days=2),
        )
        start = create_payment(
            enrollment=instructor_enrollment,
            amount="20.00",
            paid_at=revenue_now - timedelta(days=1),
        )
        inside = create_payment(
            enrollment=instructor_enrollment,
            amount="30.00",
            paid_at=revenue_now - timedelta(hours=1),
        )
        at_end = create_payment(
            enrollment=instructor_enrollment,
            amount="40.00",
            paid_at=revenue_now,
        )

        result = service._apply_date_filter(
            Payment.objects.all(),
            "paid_at",
            start=revenue_now - timedelta(days=1),
            end=revenue_now,
        )

        assert set(result) == {start, inside}
        assert before not in result
        assert at_end not in result


class TestRevenueServiceTrendCalculation:
    @pytest.mark.parametrize(
        ("current", "previous", "expected"),
        [
            (
                Decimal("100.00"),
                Decimal("100.00"),
                {"trend": 0, "direction": "neutral"},
            ),
            (
                Decimal("150.00"),
                Decimal("100.00"),
                {"trend": 50, "direction": "up"},
            ),
            (
                Decimal("50.00"),
                Decimal("100.00"),
                {"trend": 50, "direction": "down"},
            ),
            (
                Decimal("0.00"),
                Decimal("0.00"),
                {"trend": 0, "direction": "neutral"},
            ),
            (
                Decimal("100.00"),
                Decimal("0.00"),
                {"trend": 100, "direction": "up"},
            ),
            (
                Decimal("0.00"),
                Decimal("100.00"),
                {"trend": 100, "direction": "down"},
            ),
        ],
    )
    def test_calculate_trend(
        self,
        instructor_user,
        current,
        previous,
        expected,
    ):
        service = RevenueService(instructor_user)

        result = service._calculate_trend(current, previous)

        assert result == expected

    def test_calculate_trend_uses_absolute_percentage_for_downward_change(
        self,
        instructor_user,
    ):
        service = RevenueService(instructor_user)

        result = service._calculate_trend(
            Decimal("75.00"),
            Decimal("100.00"),
        )

        assert result["trend"] == 25
        assert result["direction"] == "down"

    def test_none_values_are_treated_as_zero(
        self,
        instructor_user,
    ):
        service = RevenueService(instructor_user)

        assert service._calculate_trend(None, None) == {
            "trend": 0,
            "direction": "neutral",
        }

        assert service._calculate_trend(
            Decimal("100.00"),
            None,
        ) == {
            "trend": 100,
            "direction": "up",
        }


class TestRevenueServiceLifetimeRevenue:
    def test_lifetime_revenue_sums_successful_payments(
        self,
        instructor_user,
        instructor_enrollment,
        create_payment,
        revenue_now,
    ):
        create_payment(
            enrollment=instructor_enrollment,
            amount="100.00",
            status=Payment.Status.SUCCEEDED,
            paid_at=revenue_now - timedelta(days=500),
        )
        create_payment(
            enrollment=instructor_enrollment,
            amount="250.00",
            status=Payment.Status.SUCCEEDED,
            paid_at=revenue_now,
        )

        service = RevenueService(instructor_user)

        result = service._get_lifetime_revenue()

        assert result == {
            "value": Decimal("350.00"),
            "trend": None,
            "direction": None,
        }

    def test_lifetime_revenue_subtracts_refunds(
        self,
        instructor_user,
        instructor_enrollment,
        create_payment,
        revenue_now,
    ):
        create_payment(
            enrollment=instructor_enrollment,
            amount="500.00",
            status=Payment.Status.SUCCEEDED,
            paid_at=revenue_now,
        )
        create_payment(
            enrollment=instructor_enrollment,
            amount="100.00",
            status=Payment.Status.REFUNDED,
            refunded_at=revenue_now,
        )

        service = RevenueService(instructor_user)

        result = service._get_lifetime_revenue()

        assert result["value"] == Decimal("400.00")

    @pytest.mark.parametrize(
        "status",
        [
            Payment.Status.PENDING,
            Payment.Status.PROCESSING,
            Payment.Status.FAILED,
            Payment.Status.CANCELLED,
            Payment.Status.PARTIALLY_REFUNDED,
        ],
    )
    def test_lifetime_revenue_excludes_non_succeeded_payment_statuses(
        self,
        instructor_user,
        instructor_enrollment,
        create_payment,
        status,
        revenue_now,
    ):
        create_payment(
            enrollment=instructor_enrollment,
            amount="100.00",
            status=status,
            paid_at=revenue_now,
        )

        service = RevenueService(instructor_user)

        result = service._get_lifetime_revenue()

        assert result["value"] == Decimal("0.00")

    def test_lifetime_revenue_excludes_other_instructor(
        self,
        instructor_user,
        instructor_enrollment,
        second_instructor_enrollment,
        create_payment,
        revenue_now,
    ):
        create_payment(
            enrollment=instructor_enrollment,
            amount="100.00",
            status=Payment.Status.SUCCEEDED,
            paid_at=revenue_now,
        )
        create_payment(
            enrollment=second_instructor_enrollment,
            amount="900.00",
            status=Payment.Status.SUCCEEDED,
            paid_at=revenue_now,
        )

        service = RevenueService(instructor_user)

        result = service._get_lifetime_revenue()

        assert result["value"] == Decimal("100.00")

    def test_lifetime_revenue_is_zero_without_transactions(
        self,
        instructor_user,
    ):
        service = RevenueService(instructor_user)

        result = service._get_lifetime_revenue()

        assert result == {
            "value": Decimal("0.00"),
            "trend": None,
            "direction": None,
        }

    def test_lifetime_revenue_does_not_require_paid_at_for_successful_payment(
        self,
        instructor_user,
        instructor_enrollment,
        create_payment,
    ):
        create_payment(
            enrollment=instructor_enrollment,
            amount="100.00",
            status=Payment.Status.SUCCEEDED,
            paid_at=None,
        )

        service = RevenueService(instructor_user)

        result = service._get_lifetime_revenue()

        assert result["value"] == Decimal("100.00")


class TestRevenueServicePeriodRevenue:
    def test_period_revenue_includes_current_successful_payments(
        self,
        instructor_user,
        instructor_enrollment,
        create_payment,
        revenue_now,
    ):
        create_payment(
            enrollment=instructor_enrollment,
            amount="100.00",
            status=Payment.Status.SUCCEEDED,
            paid_at=revenue_now - timedelta(days=10),
        )
        create_payment(
            enrollment=instructor_enrollment,
            amount="200.00",
            status=Payment.Status.SUCCEEDED,
            paid_at=revenue_now - timedelta(days=20),
        )

        service = RevenueService(instructor_user, "30")

        result = service._get_period_revenue()

        assert result["value"] == Decimal("300.00")

    def test_period_revenue_excludes_payment_before_period(
        self,
        instructor_user,
        instructor_enrollment,
        create_payment,
        revenue_now,
    ):
        create_payment(
            enrollment=instructor_enrollment,
            amount="100.00",
            status=Payment.Status.SUCCEEDED,
            paid_at=revenue_now - timedelta(days=31),
        )

        service = RevenueService(instructor_user, "30")

        result = service._get_period_revenue()

        assert result["value"] == Decimal("0.00")

    def test_period_revenue_subtracts_current_refunds(
        self,
        instructor_user,
        instructor_enrollment,
        create_payment,
        revenue_now,
    ):
        create_payment(
            enrollment=instructor_enrollment,
            amount="500.00",
            status=Payment.Status.SUCCEEDED,
            paid_at=revenue_now - timedelta(days=5),
        )
        create_payment(
            enrollment=instructor_enrollment,
            amount="125.00",
            status=Payment.Status.REFUNDED,
            refunded_at=revenue_now - timedelta(days=3),
        )

        service = RevenueService(instructor_user, "30")

        result = service._get_period_revenue()

        assert result["value"] == Decimal("375.00")

    def test_period_revenue_uses_previous_period_for_trend(
        self,
        instructor_user,
        instructor_enrollment,
        create_payment,
        revenue_now,
    ):
        create_payment(
            enrollment=instructor_enrollment,
            amount="200.00",
            status=Payment.Status.SUCCEEDED,
            paid_at=revenue_now - timedelta(days=10),
        )
        create_payment(
            enrollment=instructor_enrollment,
            amount="100.00",
            status=Payment.Status.SUCCEEDED,
            paid_at=revenue_now - timedelta(days=40),
        )

        service = RevenueService(instructor_user, "30")

        result = service._get_period_revenue()

        assert result == {
            "value": Decimal("200.00"),
            "trend": 100,
            "direction": "up",
        }

    def test_period_revenue_uses_refunds_in_previous_period_for_trend(
        self,
        instructor_user,
        instructor_enrollment,
        create_payment,
        revenue_now,
    ):
        create_payment(
            enrollment=instructor_enrollment,
            amount="300.00",
            status=Payment.Status.SUCCEEDED,
            paid_at=revenue_now - timedelta(days=5),
        )
        create_payment(
            enrollment=instructor_enrollment,
            amount="200.00",
            status=Payment.Status.SUCCEEDED,
            paid_at=revenue_now - timedelta(days=40),
        )
        create_payment(
            enrollment=instructor_enrollment,
            amount="50.00",
            status=Payment.Status.REFUNDED,
            refunded_at=revenue_now - timedelta(days=35),
        )

        service = RevenueService(instructor_user, "30")

        result = service._get_period_revenue()

        assert result["value"] == Decimal("300.00")
        assert result["trend"] == 100
        assert result["direction"] == "up"

    def test_period_revenue_returns_neutral_when_both_periods_are_zero(
        self,
        instructor_user,
    ):
        service = RevenueService(instructor_user, "30")

        result = service._get_period_revenue()

        assert result == {
            "value": Decimal("0.00"),
            "trend": 0,
            "direction": "neutral",
        }

    def test_period_revenue_returns_100_percent_increase_from_zero(
        self,
        instructor_user,
        instructor_enrollment,
        create_payment,
        revenue_now,
    ):
        create_payment(
            enrollment=instructor_enrollment,
            amount="100.00",
            status=Payment.Status.SUCCEEDED,
            paid_at=revenue_now - timedelta(days=5),
        )

        service = RevenueService(instructor_user, "30")

        result = service._get_period_revenue()

        assert result["value"] == Decimal("100.00")
        assert result["trend"] == 100
        assert result["direction"] == "up"


class TestRevenueServiceAllPeriod:
    def test_all_period_returns_lifetime_net_revenue_without_trend(
        self,
        instructor_user,
        instructor_enrollment,
        create_payment,
        revenue_now,
    ):
        create_payment(
            enrollment=instructor_enrollment,
            amount="100.00",
            status=Payment.Status.SUCCEEDED,
            paid_at=revenue_now - timedelta(days=500),
        )
        create_payment(
            enrollment=instructor_enrollment,
            amount="50.00",
            status=Payment.Status.REFUNDED,
            refunded_at=revenue_now - timedelta(days=400),
        )

        service = RevenueService(instructor_user, "all")

        result = service._get_period_revenue()

        assert result == {
            "value": Decimal("50.00"),
            "trend": None,
            "direction": None,
        }


class TestRevenueServiceYTDRevenue:
    def test_ytd_revenue_includes_current_year_payment(
        self,
        instructor_user,
        instructor_enrollment,
        create_payment,
        revenue_now,
    ):
        create_payment(
            enrollment=instructor_enrollment,
            amount="100.00",
            status=Payment.Status.SUCCEEDED,
            paid_at=revenue_now - timedelta(days=10),
        )

        service = RevenueService(instructor_user, "30")

        result = service._get_ytd_revenue()

        assert result["value"] == Decimal("100.00")

    def test_ytd_revenue_excludes_previous_year_payment(
        self,
        instructor_user,
        instructor_enrollment,
        create_payment,
        revenue_now,
    ):
        create_payment(
            enrollment=instructor_enrollment,
            amount="100.00",
            status=Payment.Status.SUCCEEDED,
            paid_at=datetime(
                2023,
                12,
                31,
                23,
                59,
                59,
                tzinfo=revenue_now.tzinfo,
            ),
        )

        service = RevenueService(instructor_user, "30")

        result = service._get_ytd_revenue()

        assert result["value"] == Decimal("0.00")

    def test_ytd_previous_year_boundary_uses_calendar_year(
        self,
        instructor_user,
        instructor_enrollment,
        create_payment,
        revenue_now,
    ):
        """
        Regression test for leap-year handling.

        Current RevenueService uses:

            previous_range_to = self.now - timedelta(days=365)

        For 2024-03-01 this becomes 2023-03-02.

        Calendar YTD should use:
            2023-01-01 <= paid_at < 2023-03-01

        Therefore a payment exactly on 2023-03-01 must NOT belong
        to the previous YTD period.
        """
        create_payment(
            enrollment=instructor_enrollment,
            amount="100.00",
            status=Payment.Status.SUCCEEDED,
            paid_at=datetime(
                2023,
                3,
                1,
                0,
                0,
                0,
                tzinfo=revenue_now.tzinfo,
            ),
        )

        create_payment(
            enrollment=instructor_enrollment,
            amount="200.00",
            status=Payment.Status.SUCCEEDED,
            paid_at=datetime(
                2024,
                2,
                15,
                0,
                0,
                0,
                tzinfo=revenue_now.tzinfo,
            ),
        )

        service = RevenueService(instructor_user, "30")

        result = service._get_ytd_revenue()

        assert result["value"] == Decimal("200.00")
        assert result["trend"] == 100
        assert result["direction"] == "up"

    def test_ytd_revenue_subtracts_current_year_refunds(
        self,
        instructor_user,
        instructor_enrollment,
        create_payment,
        revenue_now,
    ):
        create_payment(
            enrollment=instructor_enrollment,
            amount="500.00",
            status=Payment.Status.SUCCEEDED,
            paid_at=revenue_now - timedelta(days=10),
        )
        create_payment(
            enrollment=instructor_enrollment,
            amount="125.00",
            status=Payment.Status.REFUNDED,
            refunded_at=revenue_now - timedelta(days=5),
        )

        service = RevenueService(instructor_user, "30")

        result = service._get_ytd_revenue()

        assert result["value"] == Decimal("375.00")


class TestRevenueServiceCourseBreakdown:
    def test_course_breakdown_groups_successful_payments_by_course(
        self,
        instructor_user,
        instructor_course,
        instructor_enrollment,
        create_payment,
        revenue_now,
    ):
        second_course = Course.objects.create(
            title="Python Fundamentals",
            slug="python-fundamentals",
            owner=instructor_user,
        )
        second_enrollment = Enrollment.objects.create(
            user=instructor_enrollment.user,
            course=second_course,
        )

        create_payment(
            enrollment=instructor_enrollment,
            amount="300.00",
            status=Payment.Status.SUCCEEDED,
            paid_at=revenue_now - timedelta(days=5),
        )
        create_payment(
            enrollment=second_enrollment,
            amount="200.00",
            status=Payment.Status.SUCCEEDED,
            paid_at=revenue_now - timedelta(days=5),
        )

        service = RevenueService(instructor_user, "30")

        result = service._get_course_breakdown()

        assert result == [
            {
                "course": "Django Testing",
                "amount": Decimal("300.00"),
            },
            {
                "course": "Python Fundamentals",
                "amount": Decimal("200.00"),
            },
        ]

    def test_course_breakdown_subtracts_refunds(
        self,
        instructor_user,
        instructor_course,
        instructor_enrollment,
        create_payment,
        revenue_now,
    ):
        create_payment(
            enrollment=instructor_enrollment,
            amount="500.00",
            status=Payment.Status.SUCCEEDED,
            paid_at=revenue_now - timedelta(days=5),
        )
        create_payment(
            enrollment=instructor_enrollment,
            amount="150.00",
            status=Payment.Status.REFUNDED,
            refunded_at=revenue_now - timedelta(days=4),
        )

        service = RevenueService(instructor_user, "30")

        result = service._get_course_breakdown()

        assert result == [
            {
                "course": "Django Testing",
                "amount": Decimal("350.00"),
            }
        ]

    def test_course_breakdown_includes_refund_only_course(
        self,
        instructor_user,
        instructor_course,
        instructor_enrollment,
        create_payment,
        revenue_now,
    ):
        create_payment(
            enrollment=instructor_enrollment,
            amount="100.00",
            status=Payment.Status.REFUNDED,
            refunded_at=revenue_now - timedelta(days=5),
        )

        service = RevenueService(instructor_user, "30")

        result = service._get_course_breakdown()

        assert result == [
            {
                "course": "Django Testing",
                "amount": Decimal("-100.00"),
            }
        ]

    def test_course_breakdown_excludes_other_instructor(
        self,
        instructor_user,
        instructor_enrollment,
        second_instructor_enrollment,
        create_payment,
        revenue_now,
    ):
        create_payment(
            enrollment=instructor_enrollment,
            amount="100.00",
            status=Payment.Status.SUCCEEDED,
            paid_at=revenue_now,
        )
        create_payment(
            enrollment=second_instructor_enrollment,
            amount="900.00",
            status=Payment.Status.SUCCEEDED,
            paid_at=revenue_now,
        )

        service = RevenueService(instructor_user, "30")

        result = service._get_course_breakdown()

        assert result == [
            {
                "course": "Django Testing",
                "amount": Decimal("100.00"),
            }
        ]

    def test_course_breakdown_respects_selected_period(
        self,
        instructor_user,
        instructor_enrollment,
        create_payment,
        revenue_now,
    ):
        create_payment(
            enrollment=instructor_enrollment,
            amount="100.00",
            status=Payment.Status.SUCCEEDED,
            paid_at=revenue_now - timedelta(days=10),
        )
        create_payment(
            enrollment=instructor_enrollment,
            amount="500.00",
            status=Payment.Status.SUCCEEDED,
            paid_at=revenue_now - timedelta(days=40),
        )

        service = RevenueService(instructor_user, "30")

        result = service._get_course_breakdown()

        assert result == [
            {
                "course": "Django Testing",
                "amount": Decimal("100.00"),
            }
        ]

    def test_course_breakdown_all_period_includes_old_transactions(
        self,
        instructor_user,
        instructor_enrollment,
        create_payment,
        revenue_now,
    ):
        create_payment(
            enrollment=instructor_enrollment,
            amount="500.00",
            status=Payment.Status.SUCCEEDED,
            paid_at=revenue_now - timedelta(days=500),
        )

        service = RevenueService(instructor_user, "all")

        result = service._get_course_breakdown()

        assert result == [
            {
                "course": "Django Testing",
                "amount": Decimal("500.00"),
            }
        ]

    def test_course_breakdown_is_sorted_by_course_title(
        self,
        instructor_user,
        instructor_enrollment,
        create_payment,
        revenue_now,
    ):
        z_course = Course.objects.create(
            title="Z Course",
            slug="z-course",
            owner=instructor_user,
        )
        a_course = Course.objects.create(
            title="A Course",
            slug="a-course",
            owner=instructor_user,
        )

        z_enrollment = Enrollment.objects.create(
            user=instructor_enrollment.user,
            course=z_course,
        )
        a_enrollment = Enrollment.objects.create(
            user=instructor_enrollment.user,
            course=a_course,
        )

        create_payment(
            enrollment=z_enrollment,
            amount="100.00",
            status=Payment.Status.SUCCEEDED,
            paid_at=revenue_now,
        )
        create_payment(
            enrollment=a_enrollment,
            amount="200.00",
            status=Payment.Status.SUCCEEDED,
            paid_at=revenue_now,
        )

        service = RevenueService(instructor_user, "30")

        result = service._get_course_breakdown()

        assert [item["course"] for item in result] == [
            "A Course",
            "Z Course",
        ]


class TestRevenueServicePublicAPI:
    def test_get_revenue_returns_summary_and_course_breakdown(
        self,
        instructor_user,
        instructor_enrollment,
        create_payment,
        revenue_now,
    ):
        create_payment(
            enrollment=instructor_enrollment,
            amount="250.00",
            status=Payment.Status.SUCCEEDED,
            paid_at=revenue_now - timedelta(days=5),
        )

        service = RevenueService(instructor_user, "30")

        result = service.get_revenue()

        assert set(result) == {
            "revenue_summary",
            "course_breakdown",
        }

        assert set(result["revenue_summary"]) == {
            "lifetime",
            "period_revenue",
            "ytd",
        }

        assert result["course_breakdown"] == [
            {
                "course": "Django Testing",
                "amount": Decimal("250.00"),
            }
        ]

    def test_get_revenue_lifetime_and_period_values_are_consistent(
        self,
        instructor_user,
        instructor_enrollment,
        create_payment,
        revenue_now,
    ):
        create_payment(
            enrollment=instructor_enrollment,
            amount="250.00",
            status=Payment.Status.SUCCEEDED,
            paid_at=revenue_now - timedelta(days=5),
        )

        service = RevenueService(instructor_user, "30")

        result = service.get_revenue()

        assert result["revenue_summary"]["lifetime"]["value"] == Decimal("250.00")
        assert result["revenue_summary"]["period_revenue"]["value"] == Decimal("250.00")
        assert result["revenue_summary"]["ytd"]["value"] == Decimal("250.00")


class TestRevenueServiceInstructorIsolation:
    def test_lifetime_revenue_only_contains_current_instructors_payments(
        self,
        instructor_user,
        instructor_enrollment,
        second_instructor_enrollment,
        create_payment,
        revenue_now,
    ):
        create_payment(
            enrollment=instructor_enrollment,
            amount="100.00",
            status=Payment.Status.SUCCEEDED,
            paid_at=revenue_now,
        )
        create_payment(
            enrollment=second_instructor_enrollment,
            amount="900.00",
            status=Payment.Status.SUCCEEDED,
            paid_at=revenue_now,
        )

        service = RevenueService(instructor_user)

        result = service._get_lifetime_revenue()

        assert result["value"] == Decimal("100.00")

    def test_period_revenue_only_contains_current_instructors_payments(
        self,
        instructor_user,
        instructor_enrollment,
        second_instructor_enrollment,
        create_payment,
        revenue_now,
    ):
        create_payment(
            enrollment=instructor_enrollment,
            amount="100.00",
            status=Payment.Status.SUCCEEDED,
            paid_at=revenue_now - timedelta(days=5),
        )
        create_payment(
            enrollment=second_instructor_enrollment,
            amount="900.00",
            status=Payment.Status.SUCCEEDED,
            paid_at=revenue_now - timedelta(days=5),
        )

        service = RevenueService(instructor_user, "30")

        result = service._get_period_revenue()

        assert result["value"] == Decimal("100.00")

    def test_course_breakdown_only_contains_current_instructors_courses(
        self,
        instructor_user,
        instructor_enrollment,
        second_instructor_enrollment,
        create_payment,
        revenue_now,
    ):
        create_payment(
            enrollment=instructor_enrollment,
            amount="100.00",
            status=Payment.Status.SUCCEEDED,
            paid_at=revenue_now,
        )
        create_payment(
            enrollment=second_instructor_enrollment,
            amount="900.00",
            status=Payment.Status.SUCCEEDED,
            paid_at=revenue_now,
        )

        service = RevenueService(instructor_user, "30")

        result = service._get_course_breakdown()

        assert result == [
            {
                "course": "Django Testing",
                "amount": Decimal("100.00"),
            }
        ]
