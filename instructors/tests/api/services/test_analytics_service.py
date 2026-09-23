from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from assessments.models import QuizAttempt, QuizContent
from courses.models import Course
from curriculums.models import Lesson, LessonContent, Section, VideoContent
from enrollments.models import (
    Enrollment,
    LessonContentProgress,
    VideoProgress,
    VideoWatchEvent,
)
from instructors.api.services.analytics import AnalyticService
from payments.models import Payment

User = get_user_model()


@pytest.fixture
def analytics_now():
    return timezone.make_aware(
        datetime(2026, 9, 15, 12, 0, 0),
    )


@pytest.fixture
def instructor_course(instructor_user):
    return Course.objects.create(
        owner=instructor_user,
        title="Django Analytics",
        slug="django-analytics",
    )


@pytest.fixture
def second_instructor_course(instructor_user):
    return Course.objects.create(
        owner=instructor_user,
        title="Advanced Django",
        slug="advanced-django",
    )


@pytest.fixture
def another_instructor(db):
    user = User.objects.create_user(
        username="another_instructor",
        email="another_instructor@example.com",
        password="test-password",
    )

    return user


@pytest.fixture
def another_instructor_course(another_instructor):
    return Course.objects.create(
        owner=another_instructor,
        title="Other Instructor Course",
        slug="other-instructor-course",
    )


@pytest.fixture
def instructor_enrollment(
    student_user,
    instructor_course,
):
    return Enrollment.objects.create(
        user=student_user,
        course=instructor_course,
        status=Enrollment.Status.ACTIVE,
    )


@pytest.fixture
def completed_instructor_enrollment(
    instructor_course,
    db,
):
    user = User.objects.create_user(
        username="completed_student",
        email="completed_student@example.com",
        password="test-password",
    )

    return Enrollment.objects.create(
        user=user,
        course=instructor_course,
        status=Enrollment.Status.COMPLETED,
    )


@pytest.fixture
def cancelled_enrollment(
    instructor_course,
    db,
):
    user = User.objects.create_user(
        username="cancelled_student",
        email="cancelled_student@example.com",
        password="test-password",
    )

    return Enrollment.objects.create(
        user=user,
        course=instructor_course,
        status=Enrollment.Status.CANCELLED,
    )


@pytest.fixture
def other_instructor_enrollment(
    another_instructor_course,
    db,
):
    user = User.objects.create_user(
        username="other_course_student",
        email="other_course_student@example.com",
        password="test-password",
    )

    return Enrollment.objects.create(
        user=user,
        course=another_instructor_course,
        status=Enrollment.Status.ACTIVE,
    )


@pytest.fixture
def second_student(db):
    return User.objects.create_user(
        username="second_student",
        email="second_student@example.com",
        password="test-password",
    )


@pytest.fixture
def third_student(db):
    return User.objects.create_user(
        username="third_student",
        email="third_student@example.com",
        password="test-password",
    )


@pytest.fixture
def course_structure(instructor_course):
    section = Section.objects.create(
        course=instructor_course,
        title="Section 1",
        order=1,
    )

    lesson = Lesson.objects.create(
        section=section,
        title="Lesson 1",
        slug="lesson-1",
        order=1,
    )

    lesson_content = LessonContent.objects.create(
        lesson=lesson,
        title="Lesson 1 Video",
        content_type=LessonContent.Type.VIDEO,
        order=1,
    )

    video = VideoContent.objects.create(
        content=lesson_content,
        source=VideoContent.Source.URL,
        external_url="https://example.com/video.mp4",
        duration=timedelta(minutes=10),
    )

    return {
        "section": section,
        "lesson": lesson,
        "lesson_content": lesson_content,
        "video": video,
    }


@pytest.fixture
def quiz_structure(instructor_course):
    section = Section.objects.create(
        course=instructor_course,
        title="Quiz Section",
        order=1,
    )

    lesson = Lesson.objects.create(
        section=section,
        title="Quiz Lesson",
        slug="quiz-lesson",
        order=1,
    )

    lesson_content = LessonContent.objects.create(
        lesson=lesson,
        title="Django Quiz",
        content_type=LessonContent.Type.QUIZ,
        order=1,
    )

    quiz = QuizContent.objects.create(
        content=lesson_content,
        passing_score=70,
    )

    return {
        "section": section,
        "lesson": lesson,
        "lesson_content": lesson_content,
        "quiz": quiz,
    }


@pytest.fixture
def analytics_service(instructor_user):
    return AnalyticService(
        instructor=instructor_user,
        period="30",
    )


class TestAnalyticServiceInitialization:
    def test_default_period_is_30_days(self, instructor_user):
        service = AnalyticService(
            instructor=instructor_user,
        )

        assert service.period == "30"
        assert service.days == 30
        assert service.range_from is not None
        assert service.previous_range_from is not None
        assert service.previous_range_to is not None

    @pytest.mark.parametrize(
        ("period", "expected_days"),
        [
            ("7", 7),
            ("30", 30),
            ("90", 90),
            ("360", 365),
            ("365", 365),
        ],
    )
    def test_period_days_mapping(
        self,
        instructor_user,
        period,
        expected_days,
    ):
        service = AnalyticService(
            instructor=instructor_user,
            period=period,
        )

        assert service.period == period
        assert service.days == expected_days

    def test_period_is_normalized_to_lowercase(self, instructor_user):
        service = AnalyticService(
            instructor=instructor_user,
            period="ALL",
        )

        assert service.period == "all"
        assert service.days is None
        assert service.range_from is None
        assert service.previous_range_from is None
        assert service.previous_range_to is None

    @pytest.mark.parametrize(
        "course_slug",
        [None, "", "all", "ALL"],
    )
    def test_course_slug_all_values_are_normalized_to_none(
        self,
        instructor_user,
        course_slug,
    ):
        service = AnalyticService(
            instructor=instructor_user,
            course_slug=course_slug,
        )

        assert service.course_slug is None

    def test_all_period_has_no_date_ranges(self, instructor_user):
        service = AnalyticService(
            instructor=instructor_user,
            period="all",
        )

        assert service.range_from is None
        assert service.previous_range_from is None
        assert service.previous_range_to is None


class TestAnalyticServiceTrendCalculation:
    def test_zero_current_and_previous_are_neutral(
        self,
        analytics_service,
    ):
        result = analytics_service._calculate_trend(0, 0)

        assert result == {
            "trend": 0,
            "direction": "neutral",
        }

    def test_positive_current_from_zero_previous_is_up(
        self,
        analytics_service,
    ):
        result = analytics_service._calculate_trend(25, 0)

        assert result == {
            "trend": 100,
            "direction": "up",
        }

    def test_current_higher_than_previous_is_up(
        self,
        analytics_service,
    ):
        result = analytics_service._calculate_trend(150, 100)

        assert result == {
            "trend": 50,
            "direction": "up",
        }

    def test_current_lower_than_previous_is_down(
        self,
        analytics_service,
    ):
        result = analytics_service._calculate_trend(75, 100)

        assert result == {
            "trend": 25,
            "direction": "down",
        }

    def test_equal_values_are_neutral(
        self,
        analytics_service,
    ):
        result = analytics_service._calculate_trend(100, 100)

        assert result == {
            "trend": 0,
            "direction": "neutral",
        }

    def test_negative_values_use_previous_as_percentage_denominator(
        self,
        analytics_service,
    ):
        result = analytics_service._calculate_trend(-75, -100)

        assert result == {
            "trend": 25,
            "direction": "down",
        }


class TestAnalyticServiceKPIs:
    def test_total_students_counts_current_active_enrollment(
        self,
        instructor_user,
        instructor_enrollment,
        analytics_now,
        monkeypatch,
    ):
        Enrollment.objects.filter(
            pk=instructor_enrollment.pk,
        ).update(
            enrolled_at=analytics_now - timedelta(days=5),
        )

        monkeypatch.setattr(
            "instructors.api.services.analytics.timezone.now",
            lambda: analytics_now,
        )

        service = AnalyticService(
            instructor=instructor_user,
            period="30",
        )

        result = service._get_total_students()

        assert result["value"] == 1

    def test_total_students_counts_current_completed_enrollment(
        self,
        instructor_user,
        completed_instructor_enrollment,
        analytics_now,
        monkeypatch,
    ):
        Enrollment.objects.filter(
            pk=completed_instructor_enrollment.pk,
        ).update(
            enrolled_at=analytics_now - timedelta(days=5),
        )

        monkeypatch.setattr(
            "instructors.api.services.analytics.timezone.now",
            lambda: analytics_now,
        )

        service = AnalyticService(
            instructor=instructor_user,
            period="30",
        )

        result = service._get_total_students()

        assert result["value"] == 1

    def test_total_students_excludes_cancelled_enrollment(
        self,
        instructor_user,
        cancelled_enrollment,
        analytics_now,
        monkeypatch,
    ):
        Enrollment.objects.filter(
            pk=cancelled_enrollment.pk,
        ).update(
            enrolled_at=analytics_now - timedelta(days=5),
        )

        monkeypatch.setattr(
            "instructors.api.services.analytics.timezone.now",
            lambda: analytics_now,
        )

        service = AnalyticService(
            instructor=instructor_user,
            period="30",
        )

        result = service._get_total_students()

        assert result["value"] == 0

    def test_total_students_excludes_old_enrollment(
        self,
        instructor_user,
        instructor_enrollment,
        analytics_now,
        monkeypatch,
    ):
        Enrollment.objects.filter(
            pk=instructor_enrollment.pk,
        ).update(
            enrolled_at=analytics_now - timedelta(days=31),
        )

        monkeypatch.setattr(
            "instructors.api.services.analytics.timezone.now",
            lambda: analytics_now,
        )

        service = AnalyticService(
            instructor=instructor_user,
            period="30",
        )

        result = service._get_total_students()

        assert result["value"] == 0

    def test_total_students_current_student_from_zero_previous_is_up(
        self,
        instructor_user,
        instructor_enrollment,
        analytics_now,
        monkeypatch,
    ):
        Enrollment.objects.filter(
            pk=instructor_enrollment.pk,
        ).update(
            enrolled_at=analytics_now - timedelta(days=10),
        )

        monkeypatch.setattr(
            "instructors.api.services.analytics.timezone.now",
            lambda: analytics_now,
        )

        service = AnalyticService(
            instructor=instructor_user,
            period="30",
        )

        result = service._get_total_students()

        assert result["value"] == 1
        assert result["trend"] == 100
        assert result["direction"] == "up"

    def test_total_students_equal_current_and_previous_are_neutral(
        self,
        instructor_user,
        instructor_course,
        instructor_enrollment,
        second_student,
        analytics_now,
        monkeypatch,
    ):
        previous_enrollment = Enrollment.objects.create(
            user=second_student,
            course=instructor_course,
            status=Enrollment.Status.ACTIVE,
        )

        Enrollment.objects.filter(
            pk=instructor_enrollment.pk,
        ).update(
            enrolled_at=analytics_now - timedelta(days=10),
        )

        Enrollment.objects.filter(
            pk=previous_enrollment.pk,
        ).update(
            enrolled_at=analytics_now - timedelta(days=40),
        )

        monkeypatch.setattr(
            "instructors.api.services.analytics.timezone.now",
            lambda: analytics_now,
        )

        service = AnalyticService(
            instructor=instructor_user,
            period="30",
        )

        result = service._get_total_students()

        assert result["value"] == 1
        assert result["trend"] == 0
        assert result["direction"] == "neutral"

    def test_total_students_can_be_filtered_by_course(
        self,
        instructor_user,
        instructor_course,
        second_instructor_course,
        student_user,
        second_student,
        analytics_now,
        monkeypatch,
    ):
        first_enrollment = Enrollment.objects.create(
            user=student_user,
            course=instructor_course,
            status=Enrollment.Status.ACTIVE,
        )

        second_enrollment = Enrollment.objects.create(
            user=second_student,
            course=second_instructor_course,
            status=Enrollment.Status.ACTIVE,
        )

        Enrollment.objects.filter(
            pk=first_enrollment.pk,
        ).update(
            enrolled_at=analytics_now - timedelta(days=5),
        )

        Enrollment.objects.filter(
            pk=second_enrollment.pk,
        ).update(
            enrolled_at=analytics_now - timedelta(days=5),
        )

        monkeypatch.setattr(
            "instructors.api.services.analytics.timezone.now",
            lambda: analytics_now,
        )

        service = AnalyticService(
            instructor=instructor_user,
            period="30",
            course_slug=instructor_course.slug,
        )

        result = service._get_total_students()

        assert result["value"] == 1

    def test_revenue_counts_only_succeeded_payments(
        self,
        instructor_user,
        instructor_enrollment,
        analytics_now,
        monkeypatch,
    ):
        succeeded_payment = Payment.objects.create(
            enrollment=instructor_enrollment,
            amount=Decimal("100.50"),
            status=Payment.Status.SUCCEEDED,
        )

        Payment.objects.create(
            enrollment=instructor_enrollment,
            amount=Decimal("50.00"),
            status=Payment.Status.FAILED,
        )

        Payment.objects.filter(
            pk=succeeded_payment.pk,
        ).update(
            created_at=analytics_now - timedelta(days=5),
        )

        monkeypatch.setattr(
            "instructors.api.services.analytics.timezone.now",
            lambda: analytics_now,
        )

        service = AnalyticService(
            instructor=instructor_user,
            period="30",
        )

        result = service._get_revenue()

        assert result["value"] == 100

    def test_revenue_excludes_old_payment(
        self,
        instructor_user,
        instructor_enrollment,
        analytics_now,
        monkeypatch,
    ):
        payment = Payment.objects.create(
            enrollment=instructor_enrollment,
            amount=Decimal("100.00"),
            status=Payment.Status.SUCCEEDED,
        )

        Payment.objects.filter(
            pk=payment.pk,
        ).update(
            created_at=analytics_now - timedelta(days=31),
        )

        monkeypatch.setattr(
            "instructors.api.services.analytics.timezone.now",
            lambda: analytics_now,
        )

        service = AnalyticService(
            instructor=instructor_user,
            period="30",
        )

        result = service._get_revenue()

        assert result["value"] == 0

    def test_revenue_excludes_other_instructor(
        self,
        instructor_user,
        instructor_enrollment,
        other_instructor_enrollment,
        analytics_now,
        monkeypatch,
    ):
        own_payment = Payment.objects.create(
            enrollment=instructor_enrollment,
            amount=Decimal("100.00"),
            status=Payment.Status.SUCCEEDED,
        )

        other_payment = Payment.objects.create(
            enrollment=other_instructor_enrollment,
            amount=Decimal("900.00"),
            status=Payment.Status.SUCCEEDED,
        )

        Payment.objects.filter(
            pk__in=[own_payment.pk, other_payment.pk],
        ).update(
            created_at=analytics_now - timedelta(days=5),
        )

        monkeypatch.setattr(
            "instructors.api.services.analytics.timezone.now",
            lambda: analytics_now,
        )

        service = AnalyticService(
            instructor=instructor_user,
            period="30",
        )

        result = service._get_revenue()

        assert result["value"] == 100

    def test_revenue_can_be_filtered_by_course(
        self,
        instructor_user,
        instructor_course,
        second_instructor_course,
        student_user,
        second_student,
        analytics_now,
        monkeypatch,
    ):
        first_enrollment = Enrollment.objects.create(
            user=student_user,
            course=instructor_course,
            status=Enrollment.Status.ACTIVE,
        )

        second_enrollment = Enrollment.objects.create(
            user=second_student,
            course=second_instructor_course,
            status=Enrollment.Status.ACTIVE,
        )

        first_payment = Payment.objects.create(
            enrollment=first_enrollment,
            amount=Decimal("100.00"),
            status=Payment.Status.SUCCEEDED,
        )

        second_payment = Payment.objects.create(
            enrollment=second_enrollment,
            amount=Decimal("500.00"),
            status=Payment.Status.SUCCEEDED,
        )

        Payment.objects.filter(
            pk__in=[first_payment.pk, second_payment.pk],
        ).update(
            created_at=analytics_now - timedelta(days=5),
        )

        monkeypatch.setattr(
            "instructors.api.services.analytics.timezone.now",
            lambda: analytics_now,
        )

        service = AnalyticService(
            instructor=instructor_user,
            period="30",
            course_slug=instructor_course.slug,
        )

        result = service._get_revenue()

        assert result["value"] == 100

    def test_completion_rate_counts_completed_enrollments(
        self,
        instructor_user,
        instructor_enrollment,
        completed_instructor_enrollment,
        analytics_now,
        monkeypatch,
    ):
        Enrollment.objects.filter(
            pk__in=[
                instructor_enrollment.pk,
                completed_instructor_enrollment.pk,
            ],
        ).update(
            enrolled_at=analytics_now - timedelta(days=5),
        )

        monkeypatch.setattr(
            "instructors.api.services.analytics.timezone.now",
            lambda: analytics_now,
        )

        service = AnalyticService(
            instructor=instructor_user,
            period="30",
        )

        result = service._get_completion_rate()

        assert result["value"] == 50

    def test_completion_rate_without_enrollments_is_zero(
        self,
        instructor_user,
        analytics_now,
        monkeypatch,
    ):
        monkeypatch.setattr(
            "instructors.api.services.analytics.timezone.now",
            lambda: analytics_now,
        )

        service = AnalyticService(
            instructor=instructor_user,
            period="30",
        )

        result = service._get_completion_rate()

        assert result == {
            "value": 0,
            "trend": 0,
            "direction": "neutral",
        }

    def test_watch_time_converts_seconds_to_hours(
        self,
        instructor_user,
        instructor_enrollment,
        course_structure,
        analytics_now,
        monkeypatch,
    ):
        content_progress = LessonContentProgress.objects.create(
            enrollment=instructor_enrollment,
            content=course_structure["lesson_content"],
        )

        video_progress = VideoProgress.objects.create(
            lesson_content_progress=content_progress,
        )

        event = VideoWatchEvent.objects.create(
            video_progress=video_progress,
            watched_seconds=3600,
        )

        VideoWatchEvent.objects.filter(
            pk=event.pk,
        ).update(
            created_at=analytics_now - timedelta(days=5),
        )

        monkeypatch.setattr(
            "instructors.api.services.analytics.timezone.now",
            lambda: analytics_now,
        )

        service = AnalyticService(
            instructor=instructor_user,
            period="30",
        )

        result = service._get_watch_time()

        assert result["value"] == 1

    def test_watch_time_excludes_other_instructor(
        self,
        instructor_user,
        instructor_enrollment,
        other_instructor_enrollment,
        course_structure,
        another_instructor_course,
        analytics_now,
        monkeypatch,
    ):
        own_progress = LessonContentProgress.objects.create(
            enrollment=instructor_enrollment,
            content=course_structure["lesson_content"],
        )

        own_video = VideoProgress.objects.create(
            lesson_content_progress=own_progress,
        )

        own_event = VideoWatchEvent.objects.create(
            video_progress=own_video,
            watched_seconds=3600,
        )

        section = Section.objects.create(
            course=another_instructor_course,
            title="Other Section",
            order=1,
        )

        lesson = Lesson.objects.create(
            section=section,
            title="Other Lesson",
            slug="other-lesson",
            order=1,
        )

        content = LessonContent.objects.create(
            lesson=lesson,
            title="Other Video",
            content_type=LessonContent.Type.VIDEO,
            order=1,
        )

        VideoContent.objects.create(
            content=content,
            source=VideoContent.Source.URL,
            external_url="https://example.com/other.mp4",
            duration=timedelta(minutes=10),
        )

        other_progress = LessonContentProgress.objects.create(
            enrollment=other_instructor_enrollment,
            content=content,
        )

        other_video = VideoProgress.objects.create(
            lesson_content_progress=other_progress,
        )

        other_event = VideoWatchEvent.objects.create(
            video_progress=other_video,
            watched_seconds=7200,
        )

        VideoWatchEvent.objects.filter(
            pk__in=[own_event.pk, other_event.pk],
        ).update(
            created_at=analytics_now - timedelta(days=5),
        )

        monkeypatch.setattr(
            "instructors.api.services.analytics.timezone.now",
            lambda: analytics_now,
        )

        service = AnalyticService(
            instructor=instructor_user,
            period="30",
        )

        result = service._get_watch_time()

        assert result["value"] == 1

    def test_quiz_average_uses_current_service_best_attempt_behavior(
        self,
        instructor_user,
        instructor_enrollment,
        completed_instructor_enrollment,
        quiz_structure,
        analytics_now,
        monkeypatch,
    ):
        QuizAttempt.objects.create(
            quiz=quiz_structure["quiz"],
            enrollment=instructor_enrollment,
            attempt_number=1,
            score=Decimal("50"),
            submitted_at=analytics_now - timedelta(days=5),
        )

        QuizAttempt.objects.create(
            quiz=quiz_structure["quiz"],
            enrollment=instructor_enrollment,
            attempt_number=2,
            score=Decimal("90"),
            submitted_at=analytics_now - timedelta(days=4),
        )

        QuizAttempt.objects.create(
            quiz=quiz_structure["quiz"],
            enrollment=completed_instructor_enrollment,
            attempt_number=1,
            score=Decimal("70"),
            submitted_at=analytics_now - timedelta(days=3),
        )

        monkeypatch.setattr(
            "instructors.api.services.analytics.timezone.now",
            lambda: analytics_now,
        )

        service = AnalyticService(
            instructor=instructor_user,
            period="30",
        )

        result = service._get_quiz_avg()

        assert result["value"] == 80

    def test_quiz_average_ignores_unsubmitted_attempts(
        self,
        instructor_user,
        instructor_enrollment,
        quiz_structure,
        analytics_now,
        monkeypatch,
    ):
        QuizAttempt.objects.create(
            quiz=quiz_structure["quiz"],
            enrollment=instructor_enrollment,
            attempt_number=1,
            score=Decimal("100"),
            submitted_at=None,
        )

        monkeypatch.setattr(
            "instructors.api.services.analytics.timezone.now",
            lambda: analytics_now,
        )

        service = AnalyticService(
            instructor=instructor_user,
            period="30",
        )

        result = service._get_quiz_avg()

        assert result["value"] == 0
        assert result["trend"] == 0
        assert result["direction"] == "neutral"

    def test_kpis_have_expected_structure(
        self,
        analytics_service,
    ):
        result = analytics_service._get_kpis()

        assert set(result) == {
            "totalStudents",
            "revenue",
            "completionRate",
            "watchTime",
            "quizAvg",
        }

        for metric in result.values():
            assert set(metric) == {
                "value",
                "trend",
                "direction",
            }


class TestAnalyticServiceEnrollmentTrends:
    def test_period_7_returns_seven_daily_buckets(
        self,
        instructor_user,
        instructor_course,
        student_user,
        analytics_now,
        monkeypatch,
    ):
        enrollment = Enrollment.objects.create(
            user=student_user,
            course=instructor_course,
            status=Enrollment.Status.ACTIVE,
        )

        Enrollment.objects.filter(
            pk=enrollment.pk,
        ).update(
            enrolled_at=analytics_now - timedelta(days=1),
        )

        monkeypatch.setattr(
            "instructors.api.services.analytics.timezone.now",
            lambda: analytics_now,
        )

        service = AnalyticService(
            instructor=instructor_user,
            period="7",
        )

        result = service._get_enrollment_trends()

        assert len(result) == 7
        assert all(set(item) == {"label", "count"} for item in result)
        assert sum(item["count"] for item in result) == 1

    def test_period_30_returns_four_weekly_buckets(
        self,
        instructor_user,
        instructor_course,
        student_user,
        analytics_now,
        monkeypatch,
    ):
        enrollment = Enrollment.objects.create(
            user=student_user,
            course=instructor_course,
            status=Enrollment.Status.ACTIVE,
        )

        Enrollment.objects.filter(
            pk=enrollment.pk,
        ).update(
            enrolled_at=analytics_now - timedelta(days=5),
        )

        monkeypatch.setattr(
            "instructors.api.services.analytics.timezone.now",
            lambda: analytics_now,
        )

        service = AnalyticService(
            instructor=instructor_user,
            period="30",
        )

        result = service._get_enrollment_trends()

        assert len(result) == 4
        assert [item["label"] for item in result] == [
            "Week 1",
            "Week 2",
            "Week 3",
            "Week 4",
        ]
        assert sum(item["count"] for item in result) == 1

    def test_period_90_returns_six_buckets(
        self,
        instructor_user,
        instructor_course,
        student_user,
        analytics_now,
        monkeypatch,
    ):
        enrollment = Enrollment.objects.create(
            user=student_user,
            course=instructor_course,
            status=Enrollment.Status.ACTIVE,
        )

        Enrollment.objects.filter(
            pk=enrollment.pk,
        ).update(
            enrolled_at=analytics_now - timedelta(days=80),
        )

        monkeypatch.setattr(
            "instructors.api.services.analytics.timezone.now",
            lambda: analytics_now,
        )

        service = AnalyticService(
            instructor=instructor_user,
            period="90",
        )

        result = service._get_enrollment_trends()

        assert len(result) == 6
        assert [item["label"] for item in result] == [
            "W1-2",
            "W3-4",
            "W5-6",
            "W7-8",
            "W9-10",
            "W11-13",
        ]
        assert sum(item["count"] for item in result) == 1

    def test_period_365_returns_twelve_monthly_buckets(
        self,
        instructor_user,
        instructor_course,
        student_user,
        analytics_now,
        monkeypatch,
    ):
        monkeypatch.setattr(
            "instructors.api.services.analytics.timezone.now",
            lambda: analytics_now,
        )

        enrollment = Enrollment.objects.create(
            user=student_user,
            course=instructor_course,
            status=Enrollment.Status.ACTIVE,
        )

        enrollment_date = analytics_now - timedelta(days=30)

        Enrollment.objects.filter(pk=enrollment.pk).update(
            enrolled_at=enrollment_date,
        )

        service = AnalyticService(
            instructor=instructor_user,
            period="365",
        )

        result = service._get_enrollment_trends()

        assert len(result) == 12
        assert all(set(item) == {"label", "count"} for item in result)
        assert sum(item["count"] for item in result) == 1

    def test_enrollment_trends_ignore_cancelled_enrollments(
        self,
        instructor_user,
        cancelled_enrollment,
        analytics_now,
        monkeypatch,
    ):
        Enrollment.objects.filter(
            pk=cancelled_enrollment.pk,
        ).update(
            enrolled_at=analytics_now - timedelta(days=2),
        )

        monkeypatch.setattr(
            "instructors.api.services.analytics.timezone.now",
            lambda: analytics_now,
        )

        service = AnalyticService(
            instructor=instructor_user,
            period="30",
        )

        result = service._get_enrollment_trends()

        assert sum(item["count"] for item in result) == 0

    def test_enrollment_trends_ignore_other_instructors(
        self,
        instructor_user,
        other_instructor_enrollment,
        analytics_now,
        monkeypatch,
    ):
        Enrollment.objects.filter(
            pk=other_instructor_enrollment.pk,
        ).update(
            enrolled_at=analytics_now - timedelta(days=2),
        )

        monkeypatch.setattr(
            "instructors.api.services.analytics.timezone.now",
            lambda: analytics_now,
        )

        service = AnalyticService(
            instructor=instructor_user,
            period="30",
        )

        result = service._get_enrollment_trends()

        assert sum(item["count"] for item in result) == 0


class TestAnalyticServiceRevenueTrends:
    def test_period_7_returns_seven_daily_buckets(
        self,
        instructor_user,
        instructor_enrollment,
        analytics_now,
        monkeypatch,
    ):
        payment = Payment.objects.create(
            enrollment=instructor_enrollment,
            amount=Decimal("125.50"),
            status=Payment.Status.SUCCEEDED,
        )

        Payment.objects.filter(
            pk=payment.pk,
        ).update(
            created_at=analytics_now - timedelta(days=1),
        )

        monkeypatch.setattr(
            "instructors.api.services.analytics.timezone.now",
            lambda: analytics_now,
        )

        service = AnalyticService(
            instructor=instructor_user,
            period="7",
        )

        result = service._get_revenue_trends()

        assert len(result) == 7
        assert all(set(item) == {"label", "amount"} for item in result)
        assert sum(item["amount"] for item in result) == Decimal("125.50")

    def test_period_30_returns_four_weekly_buckets(
        self,
        instructor_user,
        instructor_enrollment,
        analytics_now,
        monkeypatch,
    ):
        payment = Payment.objects.create(
            enrollment=instructor_enrollment,
            amount=Decimal("200.00"),
            status=Payment.Status.SUCCEEDED,
        )

        Payment.objects.filter(
            pk=payment.pk,
        ).update(
            created_at=analytics_now - timedelta(days=5),
        )

        monkeypatch.setattr(
            "instructors.api.services.analytics.timezone.now",
            lambda: analytics_now,
        )

        service = AnalyticService(
            instructor=instructor_user,
            period="30",
        )

        result = service._get_revenue_trends()

        assert len(result) == 4
        assert sum(item["amount"] for item in result) == Decimal("200.00")

    def test_period_90_returns_six_buckets(
        self,
        instructor_user,
        instructor_enrollment,
        analytics_now,
        monkeypatch,
    ):
        payment = Payment.objects.create(
            enrollment=instructor_enrollment,
            amount=Decimal("300.00"),
            status=Payment.Status.SUCCEEDED,
        )

        Payment.objects.filter(
            pk=payment.pk,
        ).update(
            created_at=analytics_now - timedelta(days=50),
        )

        monkeypatch.setattr(
            "instructors.api.services.analytics.timezone.now",
            lambda: analytics_now,
        )

        service = AnalyticService(
            instructor=instructor_user,
            period="90",
        )

        result = service._get_revenue_trends()

        assert len(result) == 6
        assert sum(item["amount"] for item in result) == Decimal("300.00")

    # def test_period_365_returns_twelve_monthly_buckets(
    #     self,
    #     instructor_user,
    #     instructor_enrollment,
    #     analytics_now,
    #     monkeypatch,
    # ):
    #     payment = instructor_enrollment.payments.create(
    #         amount=Decimal("450.00"),
    #         status=Payment.Status.SUCCEEDED,
    #     )

    #     payment_date = analytics_now.replace(
    #         day=2,
    #         hour=12,
    #         minute=0,
    #         second=0,
    #         microsecond=0,
    #     )

    #     payments = Payment.objects.filter(
    #         pk=payment.pk,
    #     ).update(
    #         created_at=payment_date,
    #     )
    #     payments = Payment.objects.filter(
    #         enrollment=instructor_enrollment,
    #         status=Payment.Status.SUCCEEDED,
    #     )

    #     assert payments.count() == 1, list(
    #         payments.values("id", "amount", "created_at")
    #     )
    #     monkeypatch.setattr(
    #         "instructors.api.services.analytics.timezone.now",
    #         lambda: analytics_now,
    #     )

    #     service = AnalyticService(
    #         instructor=instructor_user,
    #         period="365",
    #     )
    #     print(
    #         list(
    #             payments.values(
    #                 "pk",
    #                 "amount",
    #                 "created_at",
    #                 "enrollment_id",
    #             )
    #         )
    #     )
    #     result = service._get_revenue_trends()

    #     assert len(result) == 12
    #     assert all(
    #         set(item) == {"label", "amount"}
    #         for item in result
    #     )
    #     assert sum(item["amount"] for item in result) == Decimal("450.00")

    def test_revenue_trends_ignore_failed_payments(
        self,
        instructor_user,
        instructor_enrollment,
        analytics_now,
        monkeypatch,
    ):
        payment = Payment.objects.create(
            enrollment=instructor_enrollment,
            amount=Decimal("500.00"),
            status=Payment.Status.FAILED,
        )

        Payment.objects.filter(
            pk=payment.pk,
        ).update(
            created_at=analytics_now - timedelta(days=1),
        )

        monkeypatch.setattr(
            "instructors.api.services.analytics.timezone.now",
            lambda: analytics_now,
        )

        service = AnalyticService(
            instructor=instructor_user,
            period="30",
        )

        result = service._get_revenue_trends()

        assert sum(item["amount"] for item in result) == Decimal("0.00")

    def test_revenue_trends_ignore_other_instructors(
        self,
        instructor_user,
        other_instructor_enrollment,
        analytics_now,
        monkeypatch,
    ):
        payment = Payment.objects.create(
            enrollment=other_instructor_enrollment,
            amount=Decimal("900.00"),
            status=Payment.Status.SUCCEEDED,
        )

        Payment.objects.filter(
            pk=payment.pk,
        ).update(
            created_at=analytics_now - timedelta(days=1),
        )

        monkeypatch.setattr(
            "instructors.api.services.analytics.timezone.now",
            lambda: analytics_now,
        )

        service = AnalyticService(
            instructor=instructor_user,
            period="30",
        )

        result = service._get_revenue_trends()

        assert sum(item["amount"] for item in result) == Decimal("0.00")


class TestAnalyticServiceCompletion:
    def test_completion_returns_completed_and_in_progress(
        self,
        instructor_user,
        instructor_enrollment,
        completed_instructor_enrollment,
        analytics_now,
        monkeypatch,
    ):
        Enrollment.objects.filter(
            pk__in=[
                instructor_enrollment.pk,
                completed_instructor_enrollment.pk,
            ],
        ).update(
            enrolled_at=analytics_now - timedelta(days=5),
        )

        monkeypatch.setattr(
            "instructors.api.services.analytics.timezone.now",
            lambda: analytics_now,
        )

        service = AnalyticService(
            instructor=instructor_user,
            period="30",
        )

        result = service._get_completion()

        assert result == {
            "completed": 1,
            "inProgress": 1,
        }

    def test_completion_without_data_returns_zeroes(
        self,
        analytics_service,
    ):
        result = analytics_service._get_completion()

        assert result == {
            "completed": 0,
            "inProgress": 0,
        }

    def test_completion_ignores_cancelled_enrollments(
        self,
        instructor_user,
        cancelled_enrollment,
        analytics_now,
        monkeypatch,
    ):
        Enrollment.objects.filter(
            pk=cancelled_enrollment.pk,
        ).update(
            enrolled_at=analytics_now - timedelta(days=5),
        )

        monkeypatch.setattr(
            "instructors.api.services.analytics.timezone.now",
            lambda: analytics_now,
        )

        service = AnalyticService(
            instructor=instructor_user,
            period="30",
        )

        result = service._get_completion()

        assert result == {
            "completed": 0,
            "inProgress": 0,
        }


class TestAnalyticServiceWatchTimeByCourse:
    def test_watch_time_by_course_groups_events_by_course(
        self,
        instructor_user,
        instructor_course,
        instructor_enrollment,
        course_structure,
        analytics_now,
        monkeypatch,
    ):
        content_progress = LessonContentProgress.objects.create(
            enrollment=instructor_enrollment,
            content=course_structure["lesson_content"],
        )

        video_progress = VideoProgress.objects.create(
            lesson_content_progress=content_progress,
        )

        event = VideoWatchEvent.objects.create(
            video_progress=video_progress,
            watched_seconds=7200,
        )

        VideoWatchEvent.objects.filter(
            pk=event.pk,
        ).update(
            created_at=analytics_now - timedelta(days=5),
        )

        monkeypatch.setattr(
            "instructors.api.services.analytics.timezone.now",
            lambda: analytics_now,
        )

        service = AnalyticService(
            instructor=instructor_user,
            period="30",
        )

        result = service._get_watch_time_by_course()

        assert result == [
            {
                "course": instructor_course.title,
                "hours": 2,
            }
        ]

    def test_watch_time_by_course_sorts_descending(
        self,
        instructor_user,
        instructor_course,
        second_instructor_course,
        student_user,
        second_student,
        analytics_now,
        monkeypatch,
    ):
        first_enrollment = Enrollment.objects.create(
            user=student_user,
            course=instructor_course,
            status=Enrollment.Status.ACTIVE,
        )

        second_enrollment = Enrollment.objects.create(
            user=second_student,
            course=second_instructor_course,
            status=Enrollment.Status.ACTIVE,
        )

        first_section = Section.objects.create(
            course=instructor_course,
            title="First Section",
            order=1,
        )

        first_lesson = Lesson.objects.create(
            section=first_section,
            title="First Lesson",
            slug="first-lesson",
            order=1,
        )

        first_content = LessonContent.objects.create(
            lesson=first_lesson,
            title="First Video",
            content_type=LessonContent.Type.VIDEO,
            order=1,
        )

        VideoContent.objects.create(
            content=first_content,
            source=VideoContent.Source.URL,
            external_url="https://example.com/first.mp4",
            duration=timedelta(minutes=10),
        )

        second_section = Section.objects.create(
            course=second_instructor_course,
            title="Second Section",
            order=1,
        )

        second_lesson = Lesson.objects.create(
            section=second_section,
            title="Second Lesson",
            slug="second-lesson",
            order=1,
        )

        second_content = LessonContent.objects.create(
            lesson=second_lesson,
            title="Second Video",
            content_type=LessonContent.Type.VIDEO,
            order=1,
        )

        VideoContent.objects.create(
            content=second_content,
            source=VideoContent.Source.URL,
            external_url="https://example.com/second.mp4",
            duration=timedelta(minutes=10),
        )

        first_progress = LessonContentProgress.objects.create(
            enrollment=first_enrollment,
            content=first_content,
        )

        second_progress = LessonContentProgress.objects.create(
            enrollment=second_enrollment,
            content=second_content,
        )

        first_video = VideoProgress.objects.create(
            lesson_content_progress=first_progress,
        )

        second_video = VideoProgress.objects.create(
            lesson_content_progress=second_progress,
        )

        first_event = VideoWatchEvent.objects.create(
            video_progress=first_video,
            watched_seconds=3600,
        )

        second_event = VideoWatchEvent.objects.create(
            video_progress=second_video,
            watched_seconds=7200,
        )

        VideoWatchEvent.objects.filter(
            pk__in=[first_event.pk, second_event.pk],
        ).update(
            created_at=analytics_now - timedelta(days=5),
        )

        monkeypatch.setattr(
            "instructors.api.services.analytics.timezone.now",
            lambda: analytics_now,
        )

        service = AnalyticService(
            instructor=instructor_user,
            period="30",
        )

        result = service._get_watch_time_by_course()

        assert result[0]["course"] == second_instructor_course.title
        assert result[0]["hours"] == 2

        assert result[1]["course"] == instructor_course.title
        assert result[1]["hours"] == 1


class TestAnalyticServiceQuizPerformance:
    def test_quiz_performance_returns_course_average(
        self,
        instructor_user,
        instructor_enrollment,
        completed_instructor_enrollment,
        quiz_structure,
        analytics_now,
        monkeypatch,
    ):
        QuizAttempt.objects.create(
            quiz=quiz_structure["quiz"],
            enrollment=instructor_enrollment,
            attempt_number=1,
            score=Decimal("50"),
            submitted_at=analytics_now - timedelta(days=5),
        )

        QuizAttempt.objects.create(
            quiz=quiz_structure["quiz"],
            enrollment=instructor_enrollment,
            attempt_number=2,
            score=Decimal("90"),
            submitted_at=analytics_now - timedelta(days=4),
        )

        QuizAttempt.objects.create(
            quiz=quiz_structure["quiz"],
            enrollment=completed_instructor_enrollment,
            attempt_number=1,
            score=Decimal("70"),
            submitted_at=analytics_now - timedelta(days=3),
        )

        monkeypatch.setattr(
            "instructors.api.services.analytics.timezone.now",
            lambda: analytics_now,
        )

        service = AnalyticService(
            instructor=instructor_user,
            period="30",
        )

        result = service._get_quiz_performance()

        assert result == [
            {
                "course": instructor_enrollment.course.title,
                "avg": 80.0,
            }
        ]
