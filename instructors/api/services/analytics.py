# services.py

from datetime import datetime, timedelta
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.db.models import Avg, Count, F, Max, OuterRef, Q, Subquery, Sum
from django.db.models.functions import TruncDay, TruncMonth, TruncWeek
from django.utils import timezone

from assessments.models import QuizAttempt
from enrollments.models import (
    Enrollment,
    VideoWatchEvent,
)
from payments.models import Payment
from profiles.models import Profile

COUNTRY_FLAGS = {
    "US": "🇺🇸",
    "IR": "🇮🇷",
    "IN": "🇮🇳",
    "GB": "🇬🇧",
    "DE": "🇩🇪",
    "CA": "🇨🇦",
    "AU": "🇦🇺",
    "FR": "🇫🇷",
    "BR": "🇧🇷",
    "JP": "🇯🇵",
    "KR": "🇰🇷",
    "IT": "🇮🇹",
    "ES": "🇪🇸",
    "NL": "🇳🇱",
    "MX": "🇲🇽",
    "ID": "🇮🇩",
    "TR": "🇹🇷",
    "SA": "🇸🇦",
    "AE": "🇦🇪",
    "SG": "🇸🇬",
    "PK": "🇵🇰",
    "BD": "🇧🇩",
    "NG": "🇳🇬",
    "EG": "🇪🇬",
    "ZA": "🇿🇦",
    "AR": "🇦🇷",
    "PL": "🇵🇱",
    "SE": "🇸🇪",
    "NO": "🇳🇴",
    "DK": "🇩🇰",
    "FI": "🇫🇮",
    "CH": "🇨🇭",
    "AT": "🇦🇹",
    "BE": "🇧🇪",
    "PT": "🇵🇹",
    "IE": "🇮🇪",
    "NZ": "🇳🇿",
    "PH": "🇵🇭",
    "VN": "🇻🇳",
    "TH": "🇹🇭",
    "MY": "🇲🇾",
    "RU": "🇷🇺",
    "CN": "🇨🇳",
    "OTHER": "🌍",
}


class AnalyticService:
    PERIOD_DAYS = {
        "7": 7,
        "30": 30,
        "90": 90,
        "360": 365,
        "365": 365,
        "all": None,
    }

    def __init__(self, instructor, period: str = "30", course_slug: str | None = None):
        self.instructor = instructor
        self.period = str(period).lower() if period else "30"
        self.course_slug = (
            course_slug if course_slug and course_slug.lower() != "all" else None
        )
        self.now = timezone.now()

        self.days = self.PERIOD_DAYS.get(self.period, 30)

        if self.days is None:
            # period == "all"
            self.range_from = None
            self.previous_range_from = None
            self.previous_range_to = None
        else:
            self.range_from = self.now - timedelta(days=self.days)
            self.previous_range_from = self.range_from - timedelta(days=self.days)
            self.previous_range_to = self.range_from

        # Base enrollment filter
        self.base_enrollment_q = Q(course__owner=self.instructor) & Q(
            status__in=["active", "completed"]
        )

        if self.course_slug:
            self.base_enrollment_q &= Q(course__slug=self.course_slug)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_analytics(self) -> dict:
        return {
            "kpis": self._get_kpis(),
            "enrollmentTrends": self._get_enrollment_trends(),
            "revenueTrends": self._get_revenue_trends(),
            "completion": self._get_completion(),
            "watchTimeByCourse": self._get_watch_time_by_course(),
            "quizPerformance": self._get_quiz_performance(),
            "geoDistribution": self._get_geo_distribution(),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _apply_date_filter(self, qs, field: str, start=None, end=None):
        """Apply optional date range filter."""
        if start is not None:
            qs = qs.filter(**{f"{field}__gte": start})
        if end is not None:
            qs = qs.filter(**{f"{field}__lt": end})
        return qs

    def _calculate_trend(self, current: int | float, previous: int | float) -> dict:
        current = current or 0
        previous = previous or 0

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

    def _period_best_average(self, start=None, end=None) -> float:
        filters = Q(
            enrollment__course__owner=self.instructor,
            enrollment__status__in=["active", "completed"],
            submitted_at__isnull=False,
        )

        if self.course_slug:
            filters &= Q(enrollment__course__slug=self.course_slug)

        if start is not None:
            filters &= Q(submitted_at__gte=start)
        if end is not None:
            filters &= Q(submitted_at__lt=end)

        best = (
            QuizAttempt.objects.filter(filters)
            .values("enrollment_id", "quiz_id")
            .annotate(best=Max("score"))
        )

        result = best.aggregate(avg=Avg("best"))["avg"]
        return float(result) if result is not None else 0.0

    # ------------------------------------------------------------------
    # KPIs
    # ------------------------------------------------------------------
    def _get_kpis(self) -> dict:
        return {
            "totalStudents": self._get_total_students(),
            "revenue": self._get_revenue(),
            "completionRate": self._get_completion_rate(),
            "watchTime": self._get_watch_time(),
            "quizAvg": self._get_quiz_avg(),
        }

    def _get_total_students(self) -> dict:
        current_qs = Enrollment.objects.filter(self.base_enrollment_q)
        current_qs = self._apply_date_filter(current_qs, "enrolled_at", self.range_from)
        current = current_qs.count()

        if self.period == "all":
            previous = 0
        else:
            previous_qs = Enrollment.objects.filter(self.base_enrollment_q)
            previous_qs = self._apply_date_filter(
                previous_qs,
                "enrolled_at",
                self.previous_range_from,
                self.previous_range_to,
            )
            previous = previous_qs.count()

        trend_data = self._calculate_trend(current, previous)
        return {
            "value": current,
            **trend_data,
        }

    def _get_revenue(self) -> dict:
        base_q = Q(
            enrollment__course__owner=self.instructor,
            status="succeeded",
        )
        if self.course_slug:
            base_q &= Q(enrollment__course__slug=self.course_slug)

        current_qs = Payment.objects.filter(base_q)
        current_qs = self._apply_date_filter(current_qs, "created_at", self.range_from)
        current = current_qs.aggregate(total=Sum("amount"))["total"] or Decimal("0")

        if self.period == "all":
            previous = Decimal("0")
        else:
            previous_qs = Payment.objects.filter(base_q)
            previous_qs = self._apply_date_filter(
                previous_qs,
                "created_at",
                self.previous_range_from,
                self.previous_range_to,
            )
            previous = previous_qs.aggregate(total=Sum("amount"))["total"] or Decimal(
                "0"
            )

        trend_data = self._calculate_trend(float(current), float(previous))
        return {
            "value": int(current),
            **trend_data,
        }

    def _get_completion_rate(self) -> dict:
        current_total_qs = Enrollment.objects.filter(self.base_enrollment_q)
        current_total_qs = self._apply_date_filter(
            current_total_qs, "enrolled_at", self.range_from
        )
        current_total = current_total_qs.count()

        current_completed_qs = Enrollment.objects.filter(
            self.base_enrollment_q,
            status="completed",
        )
        current_completed_qs = self._apply_date_filter(
            current_completed_qs, "enrolled_at", self.range_from
        )
        current_completed = current_completed_qs.count()

        current_rate = (
            round((current_completed / current_total) * 100) if current_total else 0
        )

        if self.period == "all":
            previous_rate = 0
        else:
            previous_total_qs = Enrollment.objects.filter(self.base_enrollment_q)
            previous_total_qs = self._apply_date_filter(
                previous_total_qs,
                "enrolled_at",
                self.previous_range_from,
                self.previous_range_to,
            )
            previous_total = previous_total_qs.count()

            previous_completed_qs = Enrollment.objects.filter(
                self.base_enrollment_q,
                status="completed",
            )
            previous_completed_qs = self._apply_date_filter(
                previous_completed_qs,
                "enrolled_at",
                self.previous_range_from,
                self.previous_range_to,
            )
            previous_completed = previous_completed_qs.count()

            previous_rate = (
                round((previous_completed / previous_total) * 100)
                if previous_total
                else 0
            )

        trend_data = self._calculate_trend(current_rate, previous_rate)
        return {
            "value": current_rate,
            **trend_data,
        }

    def _get_watch_time(self) -> dict:
        base_q = Q(
            video_progress__lesson_content_progress__enrollment__course__owner=self.instructor
        )
        if self.course_slug:
            base_q &= Q(
                video_progress__lesson_content_progress__enrollment__course__slug=self.course_slug
            )

        current_qs = VideoWatchEvent.objects.filter(base_q)
        current_qs = self._apply_date_filter(current_qs, "created_at", self.range_from)
        current_seconds = (
            current_qs.aggregate(total=Sum("watched_seconds"))["total"] or 0
        )

        if self.period == "all":
            previous_seconds = 0
        else:
            previous_qs = VideoWatchEvent.objects.filter(base_q)
            previous_qs = self._apply_date_filter(
                previous_qs,
                "created_at",
                self.previous_range_from,
                self.previous_range_to,
            )
            previous_seconds = (
                previous_qs.aggregate(total=Sum("watched_seconds"))["total"] or 0
            )

        current_hours = round(current_seconds / 3600)
        previous_hours = round(previous_seconds / 3600)

        trend_data = self._calculate_trend(current_hours, previous_hours)
        return {
            "value": current_hours,
            **trend_data,
        }

    def _get_quiz_avg(self) -> dict:
        current = self._period_best_average(start=self.range_from)

        if self.period == "all":
            previous = 0.0
        else:
            previous = self._period_best_average(
                start=self.previous_range_from,
                end=self.previous_range_to,
            )

        trend_data = self._calculate_trend(current, previous)
        return {
            "value": round(current),
            **trend_data,
        }

    # ------------------------------------------------------------------
    # Enrollment Trends
    # ------------------------------------------------------------------
    def _get_enrollment_trends(self) -> list[dict]:
        base_qs = Enrollment.objects.filter(self.base_enrollment_q)

        if self.period == "7":
            return self._trends_last_7_days(base_qs)
        elif self.period == "30":
            return self._trends_last_4_weeks(base_qs)
        elif self.period == "90":
            return self._trends_last_90_days(base_qs)
        else:
            # "365", "360", "all"
            return self._trends_last_12_months(base_qs)

    def _trends_last_7_days(self, qs) -> list[dict]:
        start = (self.now - timedelta(days=6)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        daily = (
            qs.filter(enrolled_at__gte=start)
            .annotate(day=TruncDay("enrolled_at"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )

        day_map = {}
        for item in daily:
            if item["day"]:
                label = item["day"].strftime("%a")
                day_map[label] = item["count"]

        labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return [{"label": label, "count": day_map.get(label, 0)} for label in labels]

    def _trends_last_4_weeks(self, qs) -> list[dict]:
        start = (self.now - timedelta(days=27)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        weekly = (
            qs.filter(enrolled_at__gte=start)
            .annotate(week=TruncWeek("enrolled_at"))
            .values("week")
            .annotate(count=Count("id"))
            .order_by("week")
        )

        week_map = {item["week"]: item["count"] for item in weekly if item["week"]}

        current_week_start = (self.now - timedelta(days=self.now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        result = []
        for i in range(3, -1, -1):
            week_start = current_week_start - timedelta(weeks=i)
            count = week_map.get(week_start, 0)
            result.append(
                {
                    "label": f"Week {4 - i}",
                    "count": count,
                }
            )
        return result

    def _trends_last_90_days(self, qs) -> list[dict]:
        start = (self.now - timedelta(days=89)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        buckets = [
            ("W1-2", 0, 14),
            ("W3-4", 14, 28),
            ("W5-6", 28, 42),
            ("W7-8", 42, 56),
            ("W9-10", 56, 70),
            ("W11-13", 70, 90),
        ]

        result = []
        for label, offset_start, offset_end in buckets:
            bucket_start = start + timedelta(days=offset_start)
            bucket_end = start + timedelta(days=offset_end)

            count = qs.filter(
                enrolled_at__gte=bucket_start,
                enrolled_at__lt=bucket_end,
            ).count()

            result.append({"label": label, "count": count})
        return result

    def _trends_last_12_months(self, qs) -> list[dict]:
        current = self.now.replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        start = current - relativedelta(months=11)

        monthly = (
            qs.filter(enrolled_at__gte=start)
            .annotate(month=TruncMonth("enrolled_at"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )

        month_map = {}

        for item in monthly:
            month = item["month"]

            if month:
                month_map[(month.year, month.month)] = item["count"]

        result = []

        for i in range(12):
            month = start + relativedelta(months=i)
            key = (month.year, month.month)

            result.append(
                {
                    "label": month.strftime("%b"),
                    "count": month_map.get(key, 0),
                }
            )

        return result

    # ------------------------------------------------------------------
    # Revenue Trends
    # ------------------------------------------------------------------
    def _get_revenue_trends(self) -> list[dict]:
        base_q = Q(
            enrollment__course__owner=self.instructor,
            status="succeeded",
        )
        if self.course_slug:
            base_q &= Q(enrollment__course__slug=self.course_slug)

        base_qs = Payment.objects.filter(base_q)

        if self.period == "7":
            return self._revenue_last_7_days(base_qs)
        elif self.period == "30":
            return self._revenue_last_4_weeks(base_qs)
        elif self.period == "90":
            return self._revenue_last_90_days(base_qs)
        else:
            return self._revenue_last_12_months(base_qs)

    def _revenue_last_7_days(self, qs) -> list[dict]:
        start = (self.now - timedelta(days=6)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        daily = (
            qs.filter(created_at__gte=start)
            .annotate(day=TruncDay("created_at"))
            .values("day")
            .annotate(amount=Sum("amount"))
            .order_by("day")
        )

        day_map = {}
        for item in daily:
            if item["day"]:
                label = item["day"].strftime("%a")
                day_map[label] = item["amount"] or Decimal("0")

        labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return [
            {
                "label": label,
                "amount": day_map.get(label, Decimal("0")).quantize(Decimal("0.01")),
            }
            for label in labels
        ]

    def _revenue_last_4_weeks(self, qs) -> list[dict]:
        start = (self.now - timedelta(days=27)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        weekly = (
            qs.filter(created_at__gte=start)
            .annotate(week=TruncWeek("created_at"))
            .values("week")
            .annotate(amount=Sum("amount"))
            .order_by("week")
        )

        week_map = {
            item["week"]: (item["amount"] or Decimal("0"))
            for item in weekly
            if item["week"]
        }

        current_week_start = (self.now - timedelta(days=self.now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        result = []
        for i in range(3, -1, -1):
            week_start = current_week_start - timedelta(weeks=i)
            amount = week_map.get(week_start, Decimal("0"))
            result.append(
                {
                    "label": f"Week {4 - i}",
                    "amount": amount.quantize(Decimal("0.01")),
                }
            )
        return result

    def _revenue_last_90_days(self, qs) -> list[dict]:
        start = (self.now - timedelta(days=89)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        buckets = [
            ("W1-2", 0, 14),
            ("W3-4", 14, 28),
            ("W5-6", 28, 42),
            ("W7-8", 42, 56),
            ("W9-10", 56, 70),
            ("W11-13", 70, 90),
        ]

        result = []
        for label, offset_start, offset_end in buckets:
            bucket_start = start + timedelta(days=offset_start)
            bucket_end = start + timedelta(days=offset_end)

            amount = qs.filter(
                created_at__gte=bucket_start,
                created_at__lt=bucket_end,
            ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

            result.append({"label": label, "amount": amount.quantize(Decimal("0.01"))})
        return result

    def _revenue_last_12_months(self, qs) -> list[dict]:
        current = self.now.replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        start = current.replace(
            year=current.year - 1,
        )

        monthly = (
            qs.filter(created_at__gte=start)
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(amount=Sum("amount"))
            .order_by("month")
        )

        month_map = {}

        for item in monthly:
            month = item["month"]

            if month:
                amount = item["amount"] or Decimal("0.00")

                if isinstance(amount, Decimal):
                    amount = amount.quantize(Decimal("0.01"))

                month_map[(month.year, month.month)] = amount

        result = []

        for i in range(12):
            month_number = current.month - 11 + i
            year = current.year

            while month_number <= 0:
                month_number += 12
                year -= 1

            key = (year, month_number)

            result.append(
                {
                    "label": datetime(
                        year,
                        month_number,
                        1,
                    ).strftime("%b"),
                    "amount": month_map.get(
                        key,
                        Decimal("0.00"),
                    ),
                }
            )

        return result

    # ------------------------------------------------------------------
    # Completion
    # ------------------------------------------------------------------
    def _get_completion(self) -> dict:
        completed_qs = Enrollment.objects.filter(
            self.base_enrollment_q,
            status="completed",
        )
        completed_qs = self._apply_date_filter(
            completed_qs, "enrolled_at", self.range_from
        )
        completed = completed_qs.count()

        in_progress_qs = Enrollment.objects.filter(
            self.base_enrollment_q,
            status="active",
        )
        in_progress_qs = self._apply_date_filter(
            in_progress_qs, "enrolled_at", self.range_from
        )
        in_progress = in_progress_qs.count()

        return {
            "completed": completed,
            "inProgress": in_progress,
        }

    # ------------------------------------------------------------------
    # Watch time by course
    # ------------------------------------------------------------------
    def _get_watch_time_by_course(self) -> list[dict]:
        base_q = Q(
            video_progress__lesson_content_progress__enrollment__course__owner=self.instructor
        )
        if self.course_slug:
            base_q &= Q(
                video_progress__lesson_content_progress__enrollment__course__slug=self.course_slug
            )

        qs = VideoWatchEvent.objects.filter(base_q)
        qs = self._apply_date_filter(qs, "created_at", self.range_from)

        qs = (
            qs.values(
                course_title=F(
                    "video_progress__lesson_content_progress__enrollment__course__title"
                )
            )
            .annotate(total_seconds=Sum("watched_seconds"))
            .order_by("-total_seconds")
        )

        return [
            {
                "course": row["course_title"],
                "hours": round((row["total_seconds"] or 0) / 3600),
            }
            for row in qs
            if row["course_title"]
        ]

    # ------------------------------------------------------------------
    # Quiz performance by course
    # ------------------------------------------------------------------
    def _get_quiz_performance(self) -> list[dict]:
        filters = Q(
            enrollment__course__owner=self.instructor,
            submitted_at__isnull=False,
            enrollment__status__in=["active", "completed"],
        )

        if self.course_slug:
            filters &= Q(enrollment__course__slug=self.course_slug)

        if self.range_from is not None:
            filters &= Q(submitted_at__gte=self.range_from)

        best_attempt_id = (
            QuizAttempt.objects.filter(
                enrollment_id=OuterRef("enrollment_id"),
                quiz_id=OuterRef("quiz_id"),
                submitted_at__isnull=False,
            )
            .order_by("-score", "-attempt_number")
            .values("pk")[:1]
        )

        qs = (
            QuizAttempt.objects.filter(filters)
            .annotate(best_attempt_id=Subquery(best_attempt_id))
            .filter(pk=F("best_attempt_id"))
            .values(course_title=F("enrollment__course__title"))
            .annotate(avg=Avg("score"))
            .order_by("-avg")
        )

        return [
            {
                "course": item["course_title"],
                "avg": round(float(item["avg"] or 0), 1),
            }
            for item in qs
            if item["course_title"]
        ]

    # ------------------------------------------------------------------
    # Geo distribution
    # ------------------------------------------------------------------
    def _get_geo_distribution(self) -> list[dict]:
        filters = Q(
            user__enrollments__course__owner=self.instructor,
            user__enrollments__status__in=["active", "completed"],
        )
        if self.course_slug:
            filters &= Q(user__enrollments__course__slug=self.course_slug)

        if self.range_from is not None:
            filters &= Q(user__enrollments__enrolled_at__gte=self.range_from)

        qs = (
            Profile.objects.filter(filters)
            .values("country")
            .annotate(count=Count("id", distinct=True))
            .order_by("-count")
        )

        total_students = qs.aggregate(total=Sum("count"))["total"] or 1

        result = []
        others_count = 0

        for row in qs:
            country = row["country"]
            count = row["count"] or 0
            pct = round((count / total_students) * 100)

            if not country or pct < 2:
                others_count += count
                continue

            flag = COUNTRY_FLAGS.get(country, COUNTRY_FLAGS["OTHER"])
            result.append(
                {
                    "country": country,
                    "flag": flag,
                    "pct": pct,
                }
            )

        if others_count > 0:
            result.append(
                {
                    "country": "OTHER",
                    "flag": COUNTRY_FLAGS["OTHER"],
                    "pct": round((others_count / total_students) * 100),
                }
            )

        return result[:8]
