from datetime import timedelta
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.test import APIRequestFactory

from courses.api.serializers import CourseSerializer
from courses.api.views import CoursesApiView
from courses.models.category import Category
from courses.models.course import Course
from courses.models.feedback import CourseFeedback
from enrollments.models import Enrollment

pytestmark = pytest.mark.django_db


@pytest.fixture
def courses_view():
    return CoursesApiView()


@pytest.fixture
def request_factory():
    return APIRequestFactory()


@pytest.fixture
def course_field_choices():
    def get_choices(field_name):
        field = Course._meta.get_field(field_name)
        return [value for value, _ in field.choices]

    return get_choices


@pytest.fixture
def valid_language(course_field_choices):
    choices = course_field_choices("language")

    assert choices, "Course.language must define at least one choice."

    return choices[0]


@pytest.fixture
def another_valid_language(course_field_choices):
    choices = course_field_choices("language")

    if len(choices) < 2:
        pytest.skip("Course.language does not define at least two choices.")

    return choices[1]


@pytest.fixture
def valid_level(course_field_choices):
    choices = course_field_choices("level")

    assert choices, "Course.level must define at least one choice."

    return choices[0]


@pytest.fixture
def another_valid_level(course_field_choices):
    choices = course_field_choices("level")

    if len(choices) < 2:
        pytest.skip("Course.level does not define at least two choices.")

    return choices[1]


@pytest.fixture
def valid_price_type(course_field_choices):
    choices = course_field_choices("price_type")

    assert choices, "Course.price_type must define at least one choice."

    return choices[0]


@pytest.fixture
def another_valid_price_type(course_field_choices):
    choices = course_field_choices("price_type")

    if len(choices) < 2:
        pytest.skip("Course.price_type does not define at least two choices.")

    return choices[1]


@pytest.fixture
def published_course(course):
    course.status = "published"
    course.duration = timedelta(hours=2)
    course.save(update_fields=["status", "duration"])
    return course


@pytest.fixture
def another_published_course(
    test_user,
    category,
):
    return Course.objects.create(
        title="Python Development",
        owner=test_user,
        category=category,
        status="published",
        duration=timedelta(hours=5),
    )


@pytest.fixture
def unrated_published_course(
    another_user,
    category,
):
    return Course.objects.create(
        title="Unrated Course",
        owner=another_user,
        category=category,
        status="published",
        duration=timedelta(hours=2),
    )


@pytest.fixture
def another_category(db):
    return Category.objects.create(
        name="Data Science",
        slug="data-science",
        description="Data science courses",
    )


@pytest.fixture
def child_category(category):
    return Category.objects.create(
        name="Django",
        slug="django",
        description="Django courses",
        parent=category,
    )


@pytest.fixture
def another_published_course_in_another_category(
    test_user,
    another_category,
):
    return Course.objects.create(
        title="Data Science Development",
        owner=test_user,
        category=another_category,
        status="published",
        duration=timedelta(hours=5),
    )


@pytest.fixture
def rated_published_course(
    published_course,
    test_user,
):
    enrollment = Enrollment.objects.create(
        user=test_user,
        course=published_course,
        status=Enrollment.Status.COMPLETED,
    )

    CourseFeedback.objects.create(
        enrollment=enrollment,
        rating=5,
        comment="Course feedback",
    )

    return published_course


@pytest.fixture
def another_rated_published_course(
    another_published_course,
    another_user,
):
    enrollment = Enrollment.objects.create(
        user=another_user,
        course=another_published_course,
        status=Enrollment.Status.COMPLETED,
    )

    CourseFeedback.objects.create(
        enrollment=enrollment,
        rating=3,
        comment="Course feedback",
    )

    return another_published_course


class TestCoursesApiView:
    def setup_request(
        self,
        view,
        request_factory,
        query_string="",
    ):
        request = request_factory.get(
            f"/courses/{query_string}",
        )

        view.setup(request)
        view.request = view.initialize_request(request)

        # get_serializer_context() calls APIView.get_serializer_context(),
        # which expects format_kwarg to exist.
        view.format_kwarg = None

        return request

    def get_queryset(
        self,
        view,
        request_factory,
        query_string="",
    ):
        self.setup_request(
            view=view,
            request_factory=request_factory,
            query_string=query_string,
        )

        return view.get_queryset()

    # ------------------------------------------------------------------
    # View configuration
    # ------------------------------------------------------------------

    def test_permission_classes_allow_anonymous_users(self):
        assert CoursesApiView.permission_classes == [AllowAny]

    def test_serializer_class_is_course_serializer(self):
        assert CoursesApiView.serializer_class is CourseSerializer

    # ------------------------------------------------------------------
    # Base queryset
    # ------------------------------------------------------------------

    def test_get_queryset_returns_only_published_courses(
        self,
        courses_view,
        request_factory,
        rated_published_course,
        another_rated_published_course,
        test_user,
        category,
    ):
        draft_course = Course.objects.create(
            title="Draft Course",
            owner=test_user,
            category=category,
            status="draft",
            duration=timedelta(hours=2),
        )

        queryset = self.get_queryset(
            courses_view,
            request_factory,
        )

        course_ids = set(
            queryset.values_list("pk", flat=True),
        )

        assert rated_published_course.pk in course_ids
        assert another_rated_published_course.pk in course_ids
        assert draft_course.pk not in course_ids

    def test_get_queryset_does_not_return_unrated_course_when_min_rating_is_requested(
        self,
        courses_view,
        request_factory,
        rated_published_course,
        unrated_published_course,
    ):
        queryset = self.get_queryset(
            courses_view,
            request_factory,
            "?min_rating=4",
        )

        course_ids = set(
            queryset.values_list("pk", flat=True),
        )

        assert rated_published_course.pk in course_ids
        assert unrated_published_course.pk not in course_ids

    # ------------------------------------------------------------------
    # Annotations
    # ------------------------------------------------------------------

    def test_get_queryset_annotates_rating(
        self,
        courses_view,
        request_factory,
        rated_published_course,
    ):
        queryset = self.get_queryset(
            courses_view,
            request_factory,
        )

        course = queryset.get(
            pk=rated_published_course.pk,
        )

        assert course.rating == 5

    def test_get_queryset_annotates_rating_count(
        self,
        courses_view,
        request_factory,
        rated_published_course,
    ):
        queryset = self.get_queryset(
            courses_view,
            request_factory,
        )

        course = queryset.get(
            pk=rated_published_course.pk,
        )

        assert course.rating_count == 1

    def test_get_queryset_annotates_student_count(
        self,
        courses_view,
        request_factory,
        rated_published_course,
        another_user,
    ):
        Enrollment.objects.create(
            user=another_user,
            course=rated_published_course,
            status=Enrollment.Status.ACTIVE,
        )

        queryset = self.get_queryset(
            courses_view,
            request_factory,
        )

        course = queryset.get(
            pk=rated_published_course.pk,
        )

        assert course.students == 2

    def test_get_queryset_calculates_average_rating(
        self,
        courses_view,
        request_factory,
        rated_published_course,
        another_user,
    ):
        enrollment = Enrollment.objects.create(
            user=another_user,
            course=rated_published_course,
            status=Enrollment.Status.COMPLETED,
        )

        CourseFeedback.objects.create(
            enrollment=enrollment,
            rating=3,
            comment="Course feedback",
        )

        queryset = self.get_queryset(
            courses_view,
            request_factory,
        )

        course = queryset.get(
            pk=rated_published_course.pk,
        )

        assert course.rating == 4

    # ------------------------------------------------------------------
    # Language filtering
    # ------------------------------------------------------------------

    def test_get_queryset_filters_by_language(
        self,
        courses_view,
        request_factory,
        rated_published_course,
        another_rated_published_course,
        valid_language,
        another_valid_language,
    ):
        rated_published_course.language = valid_language
        rated_published_course.save(
            update_fields=["language"],
        )

        another_rated_published_course.language = another_valid_language
        another_rated_published_course.save(
            update_fields=["language"],
        )

        queryset = self.get_queryset(
            courses_view,
            request_factory,
            f"?language={valid_language}",
        )

        course_ids = set(
            queryset.values_list("pk", flat=True),
        )

        assert course_ids == {
            rated_published_course.pk,
        }

    def test_get_queryset_filters_by_multiple_languages(
        self,
        courses_view,
        request_factory,
        rated_published_course,
        another_rated_published_course,
        valid_language,
        another_valid_language,
    ):
        rated_published_course.language = valid_language
        rated_published_course.save(
            update_fields=["language"],
        )

        another_rated_published_course.language = another_valid_language
        another_rated_published_course.save(
            update_fields=["language"],
        )

        queryset = self.get_queryset(
            courses_view,
            request_factory,
            (f"?language={valid_language}&language={another_valid_language}"),
        )

        course_ids = set(
            queryset.values_list("pk", flat=True),
        )

        assert course_ids == {
            rated_published_course.pk,
            another_rated_published_course.pk,
        }

    # ------------------------------------------------------------------
    # Level filtering
    # ------------------------------------------------------------------

    def test_get_queryset_filters_by_level(
        self,
        courses_view,
        request_factory,
        rated_published_course,
        another_rated_published_course,
        valid_level,
        another_valid_level,
    ):
        rated_published_course.level = valid_level
        rated_published_course.save(
            update_fields=["level"],
        )

        another_rated_published_course.level = another_valid_level
        another_rated_published_course.save(
            update_fields=["level"],
        )

        queryset = self.get_queryset(
            courses_view,
            request_factory,
            f"?level={valid_level}",
        )

        course_ids = set(
            queryset.values_list("pk", flat=True),
        )

        assert course_ids == {
            rated_published_course.pk,
        }

    def test_get_queryset_filters_by_multiple_levels(
        self,
        courses_view,
        request_factory,
        rated_published_course,
        another_rated_published_course,
        valid_level,
        another_valid_level,
    ):
        rated_published_course.level = valid_level
        rated_published_course.save(
            update_fields=["level"],
        )

        another_rated_published_course.level = another_valid_level
        another_rated_published_course.save(
            update_fields=["level"],
        )

        queryset = self.get_queryset(
            courses_view,
            request_factory,
            (f"?level={valid_level}&level={another_valid_level}"),
        )

        course_ids = set(
            queryset.values_list("pk", flat=True),
        )

        assert course_ids == {
            rated_published_course.pk,
            another_rated_published_course.pk,
        }

    # ------------------------------------------------------------------
    # Price filtering
    # ------------------------------------------------------------------

    def test_get_queryset_filters_by_price_type(
        self,
        courses_view,
        request_factory,
        rated_published_course,
        another_rated_published_course,
        valid_price_type,
        another_valid_price_type,
    ):
        rated_published_course.price_type = valid_price_type
        rated_published_course.save(
            update_fields=["price_type"],
        )

        another_rated_published_course.price_type = another_valid_price_type
        another_rated_published_course.save(
            update_fields=["price_type"],
        )

        queryset = self.get_queryset(
            courses_view,
            request_factory,
            f"?price_type={valid_price_type}",
        )

        course_ids = set(
            queryset.values_list("pk", flat=True),
        )

        assert course_ids == {
            rated_published_course.pk,
        }

    def test_get_queryset_filters_by_multiple_price_types(
        self,
        courses_view,
        request_factory,
        rated_published_course,
        another_rated_published_course,
        valid_price_type,
        another_valid_price_type,
    ):
        rated_published_course.price_type = valid_price_type
        rated_published_course.save(
            update_fields=["price_type"],
        )

        another_rated_published_course.price_type = another_valid_price_type
        another_rated_published_course.save(
            update_fields=["price_type"],
        )

        queryset = self.get_queryset(
            courses_view,
            request_factory,
            (f"?price_type={valid_price_type}&price_type={another_valid_price_type}"),
        )

        course_ids = set(
            queryset.values_list("pk", flat=True),
        )

        assert course_ids == {
            rated_published_course.pk,
            another_rated_published_course.pk,
        }

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def test_get_queryset_searches_title(
        self,
        courses_view,
        request_factory,
        rated_published_course,
        another_rated_published_course,
    ):
        rated_published_course.title = "Django Development"
        rated_published_course.save(
            update_fields=["title"],
        )

        another_rated_published_course.title = "Python Development"
        another_rated_published_course.save(
            update_fields=["title"],
        )

        queryset = self.get_queryset(
            courses_view,
            request_factory,
            "?search=Django",
        )

        course_ids = set(
            queryset.values_list("pk", flat=True),
        )

        assert course_ids == {
            rated_published_course.pk,
        }

    def test_get_queryset_searches_description(
        self,
        courses_view,
        request_factory,
        rated_published_course,
        another_rated_published_course,
    ):
        rated_published_course.description = "Learn Django development."
        rated_published_course.save(
            update_fields=["description"],
        )

        another_rated_published_course.description = "Learn Python development."
        another_rated_published_course.save(
            update_fields=["description"],
        )

        queryset = self.get_queryset(
            courses_view,
            request_factory,
            "?search=Django",
        )

        course_ids = set(
            queryset.values_list("pk", flat=True),
        )

        assert course_ids == {
            rated_published_course.pk,
        }

    def test_get_queryset_search_is_case_insensitive(
        self,
        courses_view,
        request_factory,
        rated_published_course,
    ):
        rated_published_course.title = "Django Development"
        rated_published_course.save(
            update_fields=["title"],
        )

        queryset = self.get_queryset(
            courses_view,
            request_factory,
            "?search=DJANGO",
        )

        course_ids = set(
            queryset.values_list("pk", flat=True),
        )

        assert rated_published_course.pk in course_ids

    # ------------------------------------------------------------------
    # Rating filtering
    # ------------------------------------------------------------------

    def test_get_queryset_filters_by_minimum_rating(
        self,
        courses_view,
        request_factory,
        rated_published_course,
        another_rated_published_course,
    ):
        queryset = self.get_queryset(
            courses_view,
            request_factory,
            "?min_rating=4",
        )

        course_ids = set(
            queryset.values_list("pk", flat=True),
        )

        assert rated_published_course.pk in course_ids
        assert another_rated_published_course.pk not in course_ids

    def test_get_queryset_accepts_invalid_minimum_rating(
        self,
        courses_view,
        request_factory,
        rated_published_course,
    ):
        queryset = self.get_queryset(
            courses_view,
            request_factory,
            "?min_rating=invalid",
        )

        course_ids = set(
            queryset.values_list("pk", flat=True),
        )

        assert rated_published_course.pk in course_ids

    def test_get_queryset_excludes_unrated_courses_when_minimum_rating_is_zero(
        self,
        courses_view,
        request_factory,
        rated_published_course,
        unrated_published_course,
    ):
        queryset = self.get_queryset(
            courses_view,
            request_factory,
            "?min_rating=0",
        )

        course_ids = set(
            queryset.values_list("pk", flat=True),
        )

        assert rated_published_course.pk in course_ids
        assert unrated_published_course.pk not in course_ids

    # ------------------------------------------------------------------
    # Category filtering
    # ------------------------------------------------------------------

    def test_get_queryset_filters_by_category(
        self,
        courses_view,
        request_factory,
        rated_published_course,
        another_published_course_in_another_category,
        another_user,
    ):
        enrollment = Enrollment.objects.create(
            user=another_user,
            course=another_published_course_in_another_category,
            status=Enrollment.Status.COMPLETED,
        )

        CourseFeedback.objects.create(
            enrollment=enrollment,
            rating=4,
            comment="Course feedback",
        )

        queryset = self.get_queryset(
            courses_view,
            request_factory,
            "?category=data-science",
        )

        course_ids = set(
            queryset.values_list("pk", flat=True),
        )

        assert course_ids == {
            another_published_course_in_another_category.pk,
        }

        assert rated_published_course.pk not in course_ids

    def test_get_queryset_filters_by_subcategory(
        self,
        courses_view,
        request_factory,
        child_category,
        another_user,
    ):
        subcategory_course = Course.objects.create(
            title="Django Course",
            owner=another_user,
            category=child_category,
            status="published",
            duration=timedelta(hours=3),
            published_at=timezone.now(),
        )

        enrollment = Enrollment.objects.create(
            user=another_user,
            course=subcategory_course,
            status=Enrollment.Status.COMPLETED,
        )

        CourseFeedback.objects.create(
            enrollment=enrollment,
            rating=5,
            comment="Course feedback",
        )

        queryset = self.get_queryset(
            courses_view,
            request_factory,
            "?subcategory=django",
        )

        course_ids = set(
            queryset.values_list("pk", flat=True),
        )

        assert course_ids == {
            subcategory_course.pk,
        }

    def test_get_queryset_ignores_subcategory_values_starting_with_all(
        self,
        courses_view,
        request_factory,
        rated_published_course,
        another_rated_published_course,
    ):
        queryset = self.get_queryset(
            courses_view,
            request_factory,
            "?subcategory=all",
        )

        course_ids = set(
            queryset.values_list("pk", flat=True),
        )

        assert course_ids == {
            rated_published_course.pk,
            another_rated_published_course.pk,
        }

    def test_get_queryset_ignores_subcategory_values_starting_with_all_case_insensitive(
        self,
        courses_view,
        request_factory,
        rated_published_course,
        another_rated_published_course,
    ):
        queryset = self.get_queryset(
            courses_view,
            request_factory,
            "?subcategory=All",
        )

        course_ids = set(
            queryset.values_list("pk", flat=True),
        )

        assert course_ids == {
            rated_published_course.pk,
            another_rated_published_course.pk,
        }

    # ------------------------------------------------------------------
    # Duration filtering
    # ------------------------------------------------------------------

    def test_get_queryset_filters_short_duration(
        self,
        courses_view,
        request_factory,
        test_user,
        category,
        another_user,
    ):
        short_course = Course.objects.create(
            title="Short Course",
            owner=test_user,
            category=category,
            status="published",
            duration=timedelta(hours=2),
            published_at=timezone.now(),
        )

        long_course = Course.objects.create(
            title="Long Course",
            owner=test_user,
            category=category,
            status="published",
            duration=timedelta(hours=12),
            published_at=timezone.now(),
        )

        for current_course in (
            short_course,
            long_course,
        ):
            enrollment = Enrollment.objects.create(
                user=another_user,
                course=current_course,
                status=Enrollment.Status.COMPLETED,
            )

            CourseFeedback.objects.create(
                enrollment=enrollment,
                rating=5,
                comment="Course feedback",
            )

        queryset = self.get_queryset(
            courses_view,
            request_factory,
            "?duration=short",
        )

        course_ids = set(
            queryset.values_list("pk", flat=True),
        )

        assert short_course.pk in course_ids
        assert long_course.pk not in course_ids

    def test_get_queryset_filters_medium_duration(
        self,
        courses_view,
        request_factory,
        test_user,
        category,
        another_user,
    ):
        medium_course = Course.objects.create(
            title="Medium Course",
            owner=test_user,
            category=category,
            status="published",
            duration=timedelta(hours=5),
            published_at=timezone.now(),
        )

        short_course = Course.objects.create(
            title="Short Course",
            owner=test_user,
            category=category,
            status="published",
            duration=timedelta(hours=2),
            published_at=timezone.now(),
        )

        long_course = Course.objects.create(
            title="Long Course",
            owner=test_user,
            category=category,
            status="published",
            duration=timedelta(hours=12),
            published_at=timezone.now(),
        )

        for current_course in (
            medium_course,
            short_course,
            long_course,
        ):
            enrollment = Enrollment.objects.create(
                user=another_user,
                course=current_course,
                status=Enrollment.Status.COMPLETED,
            )

            CourseFeedback.objects.create(
                enrollment=enrollment,
                rating=5,
                comment="Course feedback",
            )

        queryset = self.get_queryset(
            courses_view,
            request_factory,
            "?duration=medium",
        )

        course_ids = set(
            queryset.values_list("pk", flat=True),
        )

        assert medium_course.pk in course_ids
        assert short_course.pk not in course_ids
        assert long_course.pk not in course_ids

    def test_get_queryset_filters_long_duration(
        self,
        courses_view,
        request_factory,
        test_user,
        category,
        another_user,
    ):
        long_course = Course.objects.create(
            title="Long Course",
            owner=test_user,
            category=category,
            status="published",
            duration=timedelta(hours=12),
            published_at=timezone.now(),
        )

        short_course = Course.objects.create(
            title="Short Course",
            owner=test_user,
            category=category,
            status="published",
            duration=timedelta(hours=2),
            published_at=timezone.now(),
        )

        for current_course in (
            long_course,
            short_course,
        ):
            enrollment = Enrollment.objects.create(
                user=another_user,
                course=current_course,
                status=Enrollment.Status.COMPLETED,
            )

            CourseFeedback.objects.create(
                enrollment=enrollment,
                rating=5,
                comment="Course feedback",
            )

        queryset = self.get_queryset(
            courses_view,
            request_factory,
            "?duration=long",
        )

        course_ids = set(
            queryset.values_list("pk", flat=True),
        )

        assert long_course.pk in course_ids
        assert short_course.pk not in course_ids

    def test_get_queryset_short_duration_includes_exactly_three_hours(
        self,
        courses_view,
        request_factory,
        test_user,
        category,
    ):
        course = Course.objects.create(
            title="Three Hour Course",
            owner=test_user,
            category=category,
            status="published",
            duration=timedelta(hours=3),
            published_at=timezone.now(),
        )

        queryset = self.get_queryset(
            courses_view,
            request_factory,
            "?duration=short",
        )

        assert queryset.filter(pk=course.pk).exists()

    def test_get_queryset_medium_duration_excludes_exactly_three_hours(
        self,
        courses_view,
        request_factory,
        test_user,
        category,
    ):
        course = Course.objects.create(
            title="Three Hour Course",
            owner=test_user,
            category=category,
            status="published",
            duration=timedelta(hours=3),
            published_at=timezone.now(),
        )

        queryset = self.get_queryset(
            courses_view,
            request_factory,
            "?duration=medium",
        )

        assert not queryset.filter(pk=course.pk).exists()

    def test_get_queryset_medium_duration_includes_exactly_ten_hours(
        self,
        courses_view,
        request_factory,
        test_user,
        category,
    ):
        course = Course.objects.create(
            title="Ten Hour Course",
            owner=test_user,
            category=category,
            status="published",
            duration=timedelta(hours=10),
            published_at=timezone.now(),
        )

        queryset = self.get_queryset(
            courses_view,
            request_factory,
            "?duration=medium",
        )

        assert queryset.filter(pk=course.pk).exists()

    def test_get_queryset_long_duration_excludes_exactly_ten_hours(
        self,
        courses_view,
        request_factory,
        test_user,
        category,
    ):
        course = Course.objects.create(
            title="Ten Hour Course",
            owner=test_user,
            category=category,
            status="published",
            duration=timedelta(hours=10),
            published_at=timezone.now(),
        )

        queryset = self.get_queryset(
            courses_view,
            request_factory,
            "?duration=long",
        )

        assert not queryset.filter(pk=course.pk).exists()

    def test_get_queryset_long_duration_includes_more_than_ten_hours(
        self,
        courses_view,
        request_factory,
        test_user,
        category,
    ):
        course = Course.objects.create(
            title="Long Course",
            owner=test_user,
            category=category,
            status="published",
            duration=timedelta(hours=10, minutes=1),
            published_at=timezone.now(),
        )

        queryset = self.get_queryset(
            courses_view,
            request_factory,
            "?duration=long",
        )

        assert queryset.filter(pk=course.pk).exists()

    def test_get_queryset_accepts_multiple_durations(
        self,
        courses_view,
        request_factory,
        test_user,
        category,
    ):
        short_course = Course.objects.create(
            title="Short Course",
            owner=test_user,
            category=category,
            status="published",
            duration=timedelta(hours=2),
            published_at=timezone.now(),
        )

        medium_course = Course.objects.create(
            title="Medium Course",
            owner=test_user,
            category=category,
            status="published",
            duration=timedelta(hours=5),
            published_at=timezone.now(),
        )

        long_course = Course.objects.create(
            title="Long Course",
            owner=test_user,
            category=category,
            status="published",
            duration=timedelta(hours=12),
            published_at=timezone.now(),
        )

        queryset = self.get_queryset(
            courses_view,
            request_factory,
            "?duration=short&duration=long",
        )

        course_ids = set(
            queryset.values_list("pk", flat=True),
        )

        assert course_ids == {
            short_course.pk,
            long_course.pk,
        }

        assert medium_course.pk not in course_ids

    def test_get_queryset_ignores_unknown_duration(
        self,
        courses_view,
        request_factory,
        test_user,
        category,
    ):
        first_course = Course.objects.create(
            title="First Course",
            owner=test_user,
            category=category,
            status="published",
            duration=timedelta(hours=2),
            published_at=timezone.now(),
        )

        second_course = Course.objects.create(
            title="Second Course",
            owner=test_user,
            category=category,
            status="published",
            duration=timedelta(hours=12),
            published_at=timezone.now(),
        )

        queryset = self.get_queryset(
            courses_view,
            request_factory,
            "?duration=unknown",
        )

        course_ids = set(
            queryset.values_list("pk", flat=True),
        )

        assert course_ids == {
            first_course.pk,
            second_course.pk,
        }

    # ------------------------------------------------------------------
    # Combined filtering
    # ------------------------------------------------------------------

    def test_get_queryset_combines_multiple_filters(
        self,
        courses_view,
        request_factory,
        rated_published_course,
        another_rated_published_course,
        valid_language,
        another_valid_language,
        valid_level,
        another_valid_level,
        valid_price_type,
        another_valid_price_type,
    ):
        rated_published_course.language = valid_language
        rated_published_course.level = valid_level
        rated_published_course.price_type = valid_price_type
        rated_published_course.title = "Django Development"
        rated_published_course.save(
            update_fields=[
                "language",
                "level",
                "price_type",
                "title",
            ],
        )

        another_rated_published_course.language = another_valid_language
        another_rated_published_course.level = another_valid_level
        another_rated_published_course.price_type = another_valid_price_type
        another_rated_published_course.title = "Python Development"
        another_rated_published_course.save(
            update_fields=[
                "language",
                "level",
                "price_type",
                "title",
            ],
        )

        queryset = self.get_queryset(
            courses_view,
            request_factory,
            (
                f"?language={valid_language}"
                f"&level={valid_level}"
                f"&price_type={valid_price_type}"
                "&search=Django"
                "&min_rating=4"
            ),
        )

        course_ids = set(
            queryset.values_list("pk", flat=True),
        )

        assert course_ids == {
            rated_published_course.pk,
        }

    # ------------------------------------------------------------------
    # Serializer context
    # ------------------------------------------------------------------

    def test_get_serializer_context_contains_best_seller_ids(
        self,
        courses_view,
        request_factory,
        rated_published_course,
    ):
        self.setup_request(
            courses_view,
            request_factory,
        )

        with patch(
            "courses.api.views.get_best_seller_ids",
            return_value=[rated_published_course.pk],
        ) as mock_get_best_seller_ids:
            context = courses_view.get_serializer_context()

        assert context["best_sellers"] == [
            rated_published_course.pk,
        ]

        mock_get_best_seller_ids.assert_called_once_with()

    def test_get_serializer_context_contains_current_time(
        self,
        courses_view,
        request_factory,
    ):
        self.setup_request(
            courses_view,
            request_factory,
        )

        context = courses_view.get_serializer_context()

        assert context["now"] is not None
        assert timezone.is_aware(context["now"])

    def test_get_serializer_context_contains_request(
        self,
        courses_view,
        request_factory,
    ):
        self.setup_request(
            courses_view,
            request_factory,
        )

        context = courses_view.get_serializer_context()

        assert context["request"] is courses_view.request

    # ------------------------------------------------------------------
    # Serializer badge behavior
    # ------------------------------------------------------------------

    def test_get_badge_returns_empty_string_when_published_at_is_none(
        self,
        rated_published_course,
        request_factory,
        courses_view,
    ):
        rated_published_course.published_at = None
        rated_published_course.save(
            update_fields=["published_at"],
        )

        self.setup_request(
            courses_view,
            request_factory,
        )

        with patch(
            "courses.api.views.get_best_seller_ids",
            return_value=[],
        ):
            serializer = CourseSerializer(
                rated_published_course,
                context=courses_view.get_serializer_context(),
            )

        assert serializer.data["badge"] == ""

    def test_get_badge_returns_bestseller_before_new(
        self,
        rated_published_course,
        request_factory,
        courses_view,
    ):
        rated_published_course.published_at = timezone.now()
        rated_published_course.save(
            update_fields=["published_at"],
        )

        self.setup_request(
            courses_view,
            request_factory,
        )

        with patch(
            "courses.api.views.get_best_seller_ids",
            return_value=[rated_published_course.pk],
        ):
            serializer = CourseSerializer(
                rated_published_course,
                context=courses_view.get_serializer_context(),
            )

        assert serializer.data["badge"] == "bestseller"

    # ------------------------------------------------------------------
    # API endpoint
    # ------------------------------------------------------------------

    def test_get_returns_success_for_anonymous_user(
        self,
        client,
        rated_published_course,
    ):
        url = reverse("courses_api:courses")

        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_get_returns_paginated_response(
        self,
        client,
        rated_published_course,
    ):
        url = reverse("courses_api:courses")

        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "count" in response.data
        assert "next" in response.data
        assert "previous" in response.data
        assert "results" in response.data

    def test_get_applies_language_filter(
        self,
        client,
        rated_published_course,
        another_rated_published_course,
        valid_language,
        another_valid_language,
    ):
        rated_published_course.language = valid_language
        rated_published_course.save(
            update_fields=["language"],
        )

        another_rated_published_course.language = another_valid_language
        another_rated_published_course.save(
            update_fields=["language"],
        )

        url = reverse("courses_api:courses")

        response = client.get(
            url,
            {"language": valid_language},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_get_applies_minimum_rating_filter(
        self,
        client,
        rated_published_course,
        another_rated_published_course,
    ):
        url = reverse("courses_api:courses")

        response = client.get(
            url,
            {"min_rating": "4"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
