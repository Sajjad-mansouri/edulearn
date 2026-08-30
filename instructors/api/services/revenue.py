# services.py
from datetime import timedelta
from decimal import Decimal

from django.db.models import F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from payments.models import Payment


class RevenueService:
    PERIOD_DAYS = {
        "30": 30,
        "90": 90,
        "365": 365,
        "all": None,
    }

    ALLOWED_PERIODS = set(PERIOD_DAYS.keys())

    def __init__(self, instructor, period: str = "30"):
        self.instructor = instructor
        self.period = str(period).lower().strip() if period else "30"
        print("period", period)
        if self.period not in self.ALLOWED_PERIODS:
            self.period = "30"

        self.base_payment_q = Q(enrollment__course__owner=self.instructor) & Q(
            status=Payment.Status.SUCCEEDED
        )
        self.base_refund_q = Q(enrollment__course__owner=self.instructor) & Q(
            status=Payment.Status.REFUNDED
        )

        self.now = timezone.now()
        self.days = self.PERIOD_DAYS.get(self.period)

        if self.days is None:
            # period == "all"
            self.range_from = None
            self.previous_range_from = None
            self.previous_range_to = None
        else:
            self.range_from = self.now - timedelta(days=self.days)
            self.previous_range_from = self.range_from - timedelta(days=self.days)
            self.previous_range_to = self.range_from

    def _apply_date_filter(self, qs, field: str, start=None, end=None):
        """Apply optional date range filter."""
        if start is not None:
            qs = qs.filter(**{f"{field}__gte": start})
        if end is not None:
            qs = qs.filter(**{f"{field}__lt": end})
        return qs

    def _calculate_trend(self, current, previous) -> dict:
        current = current or Decimal("0.00")
        previous = previous or Decimal("0.00")

        if previous == 0:
            if current == 0:
                return {"trend": 0, "direction": "neutral"}
            return {"trend": 100, "direction": "up"}

        change = ((current - previous) / previous) * 100
        trend = abs(round(change))

        if change > 0:
            direction = "up"
        elif change < 0:
            direction = "down"
        else:
            direction = "neutral"

        return {"trend": trend, "direction": direction}

    def _period_revenue(
        self,
        range_from,
        previous_range_from,
        previous_range_to,
        include_trend: bool = True,
    ):
        payment_qs = Payment.objects.filter(self.base_payment_q)
        current_payment_qs = self._apply_date_filter(payment_qs, "paid_at", range_from)

        refund_qs = Payment.objects.filter(self.base_refund_q)
        current_refund_qs = self._apply_date_filter(
            refund_qs, "refunded_at", range_from
        )

        current_payments = current_payment_qs.aggregate(
            amount=Coalesce(Sum("amount"), Value(Decimal("0.00")))
        )["amount"]
        current_refunds = current_refund_qs.aggregate(
            amount=Coalesce(Sum("amount"), Value(Decimal("0.00")))
        )["amount"]

        current_revenue = current_payments - current_refunds

        if not include_trend or range_from is None:
            return {
                "value": current_revenue.quantize(Decimal("0.01")),
                "trend": None,
                "direction": None,
            }

        previous_payment_qs = self._apply_date_filter(
            payment_qs,
            "paid_at",
            previous_range_from,
            previous_range_to,
        )
        previous_refund_qs = self._apply_date_filter(
            refund_qs,
            "refunded_at",
            previous_range_from,
            previous_range_to,
        )

        previous_payments = previous_payment_qs.aggregate(
            amount=Coalesce(Sum("amount"), Value(Decimal("0.00")))
        )["amount"]
        previous_refunds = previous_refund_qs.aggregate(
            amount=Coalesce(Sum("amount"), Value(Decimal("0.00")))
        )["amount"]

        previous_revenue = previous_payments - previous_refunds
        trend_data = self._calculate_trend(current_revenue, previous_revenue)

        return {
            "value": current_revenue.quantize(Decimal("0.01")),
            **trend_data,
        }

    def get_revenue(self):
        return {
            "revenue_summary": self._get_revenue_summary(),
            "course_breakdown": self._get_course_breakdown(),
        }

    def _get_revenue_summary(self):
        return {
            "lifetime": self._get_lifetime_revenue(),
            "period_revenue": self._get_period_revenue(),
            "ytd": self._get_ytd_revenue(),
        }

    def _get_lifetime_revenue(self):
        payments = Payment.objects.filter(self.base_payment_q)
        refunds = Payment.objects.filter(self.base_refund_q)

        pay = payments.aggregate(
            amount=Coalesce(Sum("amount"), Value(Decimal("0.00")))
        )["amount"]
        refund = refunds.aggregate(
            amount=Coalesce(Sum("amount"), Value(Decimal("0.00")))
        )["amount"]

        return {
            "value": (pay - refund).quantize(Decimal("0.01")),
            "trend": None,
            "direction": None,
        }

    def _get_period_revenue(self):
        # For "all" we deliberately omit trend
        include_trend = self.period != "all"
        return self._period_revenue(
            self.range_from,
            self.previous_range_from,
            self.previous_range_to,
            include_trend=include_trend,
        )

    def _get_ytd_revenue(self):
        range_from = self.now.replace(
            month=1,
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        # Previous YTD: same window last year
        previous_range_from = range_from - timedelta(days=365)
        previous_range_to = self.now - timedelta(days=365)

        return self._period_revenue(
            range_from,
            previous_range_from,
            previous_range_to,
            include_trend=True,
        )

    def _get_course_breakdown(self):
        """
        Course breakdown respects the selected period.
        For period="all" it returns lifetime breakdown per course.
        """
        print("range from", self.range_from)
        payment_qs = Payment.objects.filter(self.base_payment_q)
        payment_qs = self._apply_date_filter(payment_qs, "paid_at", self.range_from)

        refund_qs = Payment.objects.filter(self.base_refund_q)
        refund_qs = self._apply_date_filter(refund_qs, "refunded_at", self.range_from)

        course_payments = payment_qs.values(
            course_title=F("enrollment__course__title")
        ).annotate(amount=Coalesce(Sum("amount"), Value(Decimal("0.00"))))
        course_refunds = refund_qs.values(
            course_title=F("enrollment__course__title")
        ).annotate(amount=Coalesce(Sum("amount"), Value(Decimal("0.00"))))

        payments = {row["course_title"]: row["amount"] for row in course_payments}
        refunds = {row["course_title"]: row["amount"] for row in course_refunds}

        # Include courses that only have refunds (edge case)
        all_courses = set(payments.keys()) | set(refunds.keys())

        return [
            {
                "course": course_title,
                "amount": (
                    payments.get(course_title, Decimal("0.00"))
                    - refunds.get(course_title, Decimal("0.00"))
                ).quantize(Decimal("0.01")),
            }
            for course_title in sorted(all_courses)
            if course_title is not None
        ]
