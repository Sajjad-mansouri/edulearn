from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from courses.models.category import Category
from courses.models.course import Course
from curriculums.models.lesson import Lesson
from curriculums.models.section import Section
from enrollments.models.enrollment import Enrollment
from enrollments.models.lesson_progress import LessonProgress

pytestmark = pytest.mark.django_db


class TestEnrollmentFixtures:
    @pytest.fixture
    def test_user(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()

        return User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

    @pytest.fixture
    def another_user(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()

        return User.objects.create_user(
            username="another_user",
            email="another_user@example.com",
            password="test-password",
        )

    @pytest.fixture
    def category(self):
        return Category.objects.create(
            name="Programming",
            slug="programming",
            description="Programming courses",
        )

    @pytest.fixture
    def course(self, test_user, category):
        return Course.objects.create(
            title="Django Development",
            owner=test_user,
            category=category,
        )

    @pytest.fixture
    def another_course(self, test_user, category):
        return Course.objects.create(
            title="Python Development",
            owner=test_user,
            category=category,
        )

    @pytest.fixture
    def section(self, course):
        return Section.objects.create(
            course=course,
            title="Introduction",
            order=1,
        )

    @pytest.fixture
    def lesson(self, section):
        return Lesson.objects.create(
            section=section,
            title="Getting Started",
            slug="getting-started",
            order=1,
        )

    @pytest.fixture
    def enrollment(self, test_user, course):
        return Enrollment.objects.create(
            user=test_user,
            course=course,
        )


class TestEnrollmentCreation(TestEnrollmentFixtures):
    def test_enrollment_can_be_created(self, test_user, course):
        enrollment = Enrollment.objects.create(
            user=test_user,
            course=course,
        )

        assert enrollment.pk is not None
        assert enrollment.user == test_user
        assert enrollment.course == course

    def test_default_status_is_pending(self, enrollment):
        assert enrollment.status == Enrollment.Status.PENDING

    def test_default_progress_is_zero(self, enrollment):
        assert enrollment.progress == Decimal("0")

    def test_enrolled_at_is_set_automatically(self, enrollment):
        assert enrollment.enrolled_at is not None

    def test_updated_at_is_set_automatically(self, enrollment):
        assert enrollment.updated_at is not None

    def test_optional_dates_are_empty_by_default(self, enrollment):
        assert enrollment.started_at is None
        assert enrollment.last_activity_at is None
        assert enrollment.completed_at is None

    def test_explicit_status_can_be_set(self, test_user, course):
        enrollment = Enrollment.objects.create(
            user=test_user,
            course=course,
            status=Enrollment.Status.ACTIVE,
        )

        assert enrollment.status == Enrollment.Status.ACTIVE

    @pytest.mark.parametrize(
        "status",
        [
            Enrollment.Status.ACTIVE,
            Enrollment.Status.COMPLETED,
            Enrollment.Status.CANCELLED,
            Enrollment.Status.SUSPENDED,
            Enrollment.Status.PENDING,
        ],
    )
    def test_all_defined_statuses_are_valid(
        self,
        test_user,
        course,
        status,
    ):
        enrollment = Enrollment(
            user=test_user,
            course=course,
            status=status,
        )

        enrollment.full_clean()

        assert enrollment.status == status


class TestEnrollmentStringRepresentation(TestEnrollmentFixtures):
    def test_str_contains_user_and_course(
        self,
        test_user,
        course,
        enrollment,
    ):
        result = str(enrollment)

        assert str(test_user) in result
        assert str(course) in result
        assert "→" in result


class TestEnrollmentValidation(TestEnrollmentFixtures):
    def test_user_is_required(self, course):
        enrollment = Enrollment(course=course)

        with pytest.raises(ValidationError) as exc_info:
            enrollment.full_clean()

        assert "user" in exc_info.value.message_dict

    def test_course_is_required(self, test_user):
        enrollment = Enrollment(user=test_user)

        with pytest.raises(ValidationError) as exc_info:
            enrollment.full_clean()

        assert "course" in exc_info.value.message_dict

    @pytest.mark.parametrize(
        "progress",
        [
            Decimal("-0.01"),
            Decimal("-1"),
            Decimal("100.01"),
            Decimal("101"),
        ],
    )
    def test_progress_cannot_be_outside_zero_to_one_hundred(
        self,
        test_user,
        course,
        progress,
    ):
        enrollment = Enrollment(
            user=test_user,
            course=course,
            progress=progress,
        )

        with pytest.raises(ValidationError) as exc_info:
            enrollment.full_clean()

        assert "progress" in exc_info.value.message_dict

    @pytest.mark.parametrize(
        "progress",
        [
            Decimal("0"),
            Decimal("0.01"),
            Decimal("25"),
            Decimal("50.50"),
            Decimal("99.99"),
            Decimal("100"),
        ],
    )
    def test_progress_accepts_values_between_zero_and_one_hundred(
        self,
        test_user,
        course,
        progress,
    ):
        enrollment = Enrollment(
            user=test_user,
            course=course,
            progress=progress,
        )

        enrollment.full_clean()

        assert enrollment.progress == progress

    def test_progress_accepts_zero(self, test_user, course):
        enrollment = Enrollment(
            user=test_user,
            course=course,
            progress=0,
        )

        enrollment.full_clean()

        assert enrollment.progress == 0

    def test_progress_accepts_one_hundred(self, test_user, course):
        enrollment = Enrollment(
            user=test_user,
            course=course,
            progress=100,
        )

        enrollment.full_clean()

        assert enrollment.progress == 100


class TestEnrollmentUniqueness(TestEnrollmentFixtures):
    def test_same_user_cannot_enroll_in_same_course_twice(
        self,
        enrollment,
        test_user,
        course,
    ):
        duplicate = Enrollment(
            user=test_user,
            course=course,
        )

        with pytest.raises(ValidationError) as exc_info:
            duplicate.full_clean()

        assert "__all__" in exc_info.value.message_dict

    def test_same_user_cannot_enroll_in_same_course_at_database_level(
        self,
        enrollment,
        test_user,
        course,
    ):
        with pytest.raises(IntegrityError):
            Enrollment.objects.create(
                user=test_user,
                course=course,
            )

    def test_same_user_can_enroll_in_different_courses(
        self,
        enrollment,
        test_user,
        another_course,
    ):
        another_enrollment = Enrollment.objects.create(
            user=test_user,
            course=another_course,
        )

        assert another_enrollment.pk is not None

    def test_different_users_can_enroll_in_same_course(
        self,
        enrollment,
        another_user,
        course,
    ):
        another_enrollment = Enrollment.objects.create(
            user=another_user,
            course=course,
        )

        assert another_enrollment.pk is not None


class TestEnrollmentRelationships(TestEnrollmentFixtures):
    def test_user_has_reverse_enrollments_relation(
        self,
        test_user,
        enrollment,
    ):
        assert enrollment in test_user.enrollments.all()

    def test_course_has_reverse_enrollments_relation(
        self,
        course,
        enrollment,
    ):
        assert enrollment in course.enrollments.all()

    def test_deleting_user_deletes_enrollment(
        self,
        test_user,
        enrollment,
    ):
        enrollment_id = enrollment.pk

        test_user.delete()

        assert not Enrollment.objects.filter(pk=enrollment_id).exists()

    def test_deleting_course_deletes_enrollment(
        self,
        course,
        enrollment,
    ):
        enrollment_id = enrollment.pk

        course.delete()

        assert not Enrollment.objects.filter(pk=enrollment_id).exists()


class TestEnrollmentActivityStatus(TestEnrollmentFixtures):
    def test_completed_enrollment_is_always_completed(
        self,
        enrollment,
    ):
        enrollment.status = Enrollment.Status.COMPLETED
        enrollment.last_activity_at = timezone.now() - timedelta(days=60)
        enrollment.save(update_fields=["status", "last_activity_at"])

        assert enrollment.activity_status == "completed"

    def test_enrollment_without_activity_is_not_started(
        self,
        enrollment,
    ):
        assert enrollment.last_activity_at is None

        assert enrollment.activity_status == "not_started"

    def test_activity_within_seven_days_is_active(
        self,
        enrollment,
    ):
        enrollment.last_activity_at = timezone.now() - timedelta(
            days=6,
            hours=23,
            minutes=59,
        )

        assert enrollment.activity_status == "active"

    def test_activity_just_over_seven_days_is_idle(
        self,
        enrollment,
    ):
        enrollment.last_activity_at = timezone.now() - timedelta(
            days=7,
            seconds=1,
        )

        assert enrollment.activity_status == "idle"

    def test_activity_within_thirty_days_is_idle(
        self,
        enrollment,
    ):
        enrollment.last_activity_at = timezone.now() - timedelta(
            days=29,
            hours=23,
            minutes=59,
        )

        assert enrollment.activity_status == "idle"

    def test_activity_just_over_thirty_days_is_stale(
        self,
        enrollment,
    ):
        enrollment.last_activity_at = timezone.now() - timedelta(
            days=30,
            seconds=1,
        )

        assert enrollment.activity_status == "stale"

    @pytest.mark.parametrize(
        "status",
        [
            Enrollment.Status.ACTIVE,
            Enrollment.Status.CANCELLED,
            Enrollment.Status.SUSPENDED,
            Enrollment.Status.PENDING,
        ],
    )
    def test_non_completed_status_uses_last_activity(
        self,
        enrollment,
        status,
    ):
        enrollment.status = status
        enrollment.last_activity_at = timezone.now() - timedelta(days=2)

        assert enrollment.activity_status == "active"


class TestEnrollmentRecalculateProgress(TestEnrollmentFixtures):
    def test_progress_is_zero_when_course_has_no_lessons(
        self,
        enrollment,
    ):
        enrollment.recalculate_progress()

        enrollment.refresh_from_db()

        assert enrollment.progress == Decimal("0")
        assert enrollment.completed_at is None

    def test_progress_is_zero_when_no_lessons_are_completed(
        self,
        enrollment,
        lesson,
    ):
        enrollment.recalculate_progress()

        enrollment.refresh_from_db()

        assert enrollment.progress == Decimal("0")
        assert enrollment.completed_at is None

    def test_progress_is_one_hundred_when_all_lessons_are_completed(
        self,
        enrollment,
        lesson,
    ):
        LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=lesson,
            status="completed",
        )

        enrollment.recalculate_progress()

        enrollment.refresh_from_db()

        assert enrollment.progress == Decimal("100.00")
        assert enrollment.completed_at is not None

    def test_progress_is_calculated_from_completed_lessons(
        self,
        enrollment,
        section,
        lesson,
    ):
        second_lesson = Lesson.objects.create(
            section=section,
            title="Second Lesson",
            slug="second-lesson",
            order=2,
        )
        third_lesson = Lesson.objects.create(
            section=section,
            title="Third Lesson",
            slug="third-lesson",
            order=3,
        )

        LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=lesson,
            status="completed",
        )
        LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=second_lesson,
            status="completed",
        )
        LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=third_lesson,
            status="in_progress",
        )

        enrollment.recalculate_progress()

        enrollment.refresh_from_db()

        assert enrollment.progress == Decimal("66.67")
        assert enrollment.completed_at is None

    @pytest.mark.parametrize(
        "completed_count,total_lessons,expected_progress",
        [
            (0, 1, Decimal("0.00")),
            (1, 2, Decimal("50.00")),
            (1, 3, Decimal("33.33")),
            (2, 3, Decimal("66.67")),
            (3, 4, Decimal("75.00")),
            (4, 5, Decimal("80.00")),
        ],
    )
    def test_progress_percentage_is_calculated_correctly(
        self,
        enrollment,
        section,
        completed_count,
        total_lessons,
        expected_progress,
    ):
        lessons = []

        for index in range(total_lessons):
            lessons.append(
                Lesson.objects.create(
                    section=section,
                    title=f"Lesson {index + 1}",
                    slug=f"lesson-{index + 1}",
                    order=index + 1,
                )
            )

        for lesson in lessons[:completed_count]:
            LessonProgress.objects.create(
                enrollment=enrollment,
                lesson=lesson,
                status="completed",
            )

        enrollment.recalculate_progress()

        enrollment.refresh_from_db()

        assert enrollment.progress == expected_progress

    def test_only_completed_lesson_progress_counts(
        self,
        enrollment,
        section,
    ):
        completed_lesson = Lesson.objects.create(
            section=section,
            title="Completed Lesson",
            slug="completed-lesson",
            order=1,
        )
        in_progress_lesson = Lesson.objects.create(
            section=section,
            title="In Progress Lesson",
            slug="in-progress-lesson",
            order=2,
        )
        not_started_lesson = Lesson.objects.create(
            section=section,
            title="Not Started Lesson",
            slug="not-started-lesson",
            order=3,
        )

        LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=completed_lesson,
            status="completed",
        )
        LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=in_progress_lesson,
            status="in_progress",
        )
        LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=not_started_lesson,
            status="not_started",
        )

        enrollment.recalculate_progress()

        enrollment.refresh_from_db()

        assert enrollment.progress == Decimal("33.33")

    def test_completed_at_is_set_when_progress_reaches_one_hundred(
        self,
        enrollment,
        lesson,
    ):
        assert enrollment.completed_at is None

        LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=lesson,
            status="completed",
        )

        enrollment.recalculate_progress()

        enrollment.refresh_from_db()

        assert enrollment.progress == Decimal("100.00")
        assert enrollment.completed_at is not None

    def test_existing_completed_at_is_preserved_when_progress_remains_one_hundred(
        self,
        enrollment,
        lesson,
    ):
        completed_at = timezone.now() - timedelta(days=1)

        enrollment.completed_at = completed_at
        enrollment.save(update_fields=["completed_at"])

        LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=lesson,
            status="completed",
        )

        enrollment.recalculate_progress()

        enrollment.refresh_from_db()

        assert enrollment.progress == Decimal("100.00")
        assert enrollment.completed_at == completed_at

    def test_completed_at_is_cleared_when_progress_falls_below_one_hundred(
        self,
        enrollment,
        section,
    ):
        completed_lesson = Lesson.objects.create(
            section=section,
            title="Completed Lesson",
            slug="completed-lesson",
            order=1,
        )
        Lesson.objects.create(
            section=section,
            title="Incomplete Lesson",
            slug="incomplete-lesson",
            order=2,
        )

        enrollment.completed_at = timezone.now() - timedelta(days=1)
        enrollment.progress = Decimal("100")
        enrollment.save(
            update_fields=["completed_at", "progress"],
        )

        LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=completed_lesson,
            status="completed",
        )

        enrollment.recalculate_progress()

        enrollment.refresh_from_db()

        assert enrollment.progress == Decimal("50.00")
        assert enrollment.completed_at is None

    def test_recalculate_progress_only_considers_lessons_from_enrolled_course(
        self,
        enrollment,
        course,
        test_user,
        category,
        section,
        lesson,
    ):
        other_course = Course.objects.create(
            title="Another Course",
            owner=test_user,
            category=category,
        )
        other_section = Section.objects.create(
            course=other_course,
            title="Other Section",
            order=1,
        )
        other_lesson = Lesson.objects.create(
            section=other_section,
            title="Other Lesson",
            slug="other-lesson",
            order=1,
        )

        LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=lesson,
            status="completed",
        )
        LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=other_lesson,
            status="completed",
        )

        enrollment.recalculate_progress()

        enrollment.refresh_from_db()

        assert enrollment.progress == Decimal("100.00")


class TestEnrollmentUpdate(TestEnrollmentFixtures):
    def test_enrollment_fields_can_be_updated(
        self,
        enrollment,
    ):
        started_at = timezone.now() - timedelta(days=2)
        last_activity_at = timezone.now()

        enrollment.status = Enrollment.Status.ACTIVE
        enrollment.started_at = started_at
        enrollment.last_activity_at = last_activity_at
        enrollment.progress = Decimal("45.50")
        enrollment.save()

        enrollment.refresh_from_db()

        assert enrollment.status == Enrollment.Status.ACTIVE
        assert enrollment.started_at == started_at
        assert enrollment.last_activity_at == last_activity_at
        assert enrollment.progress == Decimal("45.50")

    def test_completed_at_can_be_set_explicitly(
        self,
        enrollment,
    ):
        completed_at = timezone.now()

        enrollment.completed_at = completed_at
        enrollment.status = Enrollment.Status.COMPLETED
        enrollment.progress = Decimal("100")
        enrollment.save()

        enrollment.refresh_from_db()

        assert enrollment.completed_at == completed_at
        assert enrollment.status == Enrollment.Status.COMPLETED
        assert enrollment.progress == Decimal("100")


class TestEnrollmentOrdering(TestEnrollmentFixtures):
    def test_enrollments_are_ordered_by_latest_enrollment_first(
        self,
        test_user,
        course,
        another_course,
    ):
        first = Enrollment.objects.create(
            user=test_user,
            course=course,
        )
        second = Enrollment.objects.create(
            user=test_user,
            course=another_course,
        )

        Enrollment.objects.filter(pk=first.pk).update(
            enrolled_at=timezone.now() - timedelta(days=1),
        )
        Enrollment.objects.filter(pk=second.pk).update(
            enrolled_at=timezone.now(),
        )

        enrollments = list(Enrollment.objects.all())

        assert enrollments == [second, first]
