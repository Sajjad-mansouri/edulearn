import pytest
from django.contrib.auth import get_user_model

from courses.api.services import (
    get_best_seller_ids,
    get_course_filter_metadata,
    toggle_course_wishlist,
)
from courses.models import Course, CourseWishlist

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestGetCourseFilterMetadata:
    def test_returns_expected_metadata_structure(
        self,
        mocker,
    ):
        category_options = [{"id": 1, "name": "Programming"}]
        language_options = [{"value": "en", "label": "English"}]
        level_options = [{"value": "beginner", "label": "Beginner"}]
        price_options = [{"value": "free", "label": "Free"}]
        duration_options = [{"value": "short", "label": "Short"}]
        rating_options = [{"value": 4, "label": "4 stars & up"}]

        mocker.patch(
            "courses.api.services.get_category_options",
            return_value=category_options,
        )
        mocker.patch(
            "courses.api.services.get_language_options",
            return_value=language_options,
        )
        mocker.patch(
            "courses.api.services.get_level_options",
            return_value=level_options,
        )
        mocker.patch(
            "courses.api.services.get_price_options",
            return_value=price_options,
        )
        mocker.patch(
            "courses.api.services.get_duration_options",
            return_value=duration_options,
        )
        mocker.patch(
            "courses.api.services.get_rating_options",
            return_value=rating_options,
        )

        result = get_course_filter_metadata()

        assert result == {
            "categories": category_options,
            "languages": language_options,
            "levels": level_options,
            "prices": price_options,
            "durations": duration_options,
            "ratings": rating_options,
        }

    def test_calls_every_filter_selector_once(
        self,
        mocker,
    ):
        get_category_options = mocker.patch(
            "courses.api.services.get_category_options",
            return_value=[],
        )
        get_language_options = mocker.patch(
            "courses.api.services.get_language_options",
            return_value=[],
        )
        get_level_options = mocker.patch(
            "courses.api.services.get_level_options",
            return_value=[],
        )
        get_price_options = mocker.patch(
            "courses.api.services.get_price_options",
            return_value=[],
        )
        get_duration_options = mocker.patch(
            "courses.api.services.get_duration_options",
            return_value=[],
        )
        get_rating_options = mocker.patch(
            "courses.api.services.get_rating_options",
            return_value=[],
        )

        result = get_course_filter_metadata()

        assert result == {
            "categories": [],
            "languages": [],
            "levels": [],
            "prices": [],
            "durations": [],
            "ratings": [],
        }

        get_category_options.assert_called_once_with()
        get_language_options.assert_called_once_with()
        get_level_options.assert_called_once_with()
        get_price_options.assert_called_once_with()
        get_duration_options.assert_called_once_with()
        get_rating_options.assert_called_once_with()

    def test_preserves_selector_results_without_modification(
        self,
        mocker,
    ):
        categories = [{"id": 1, "name": "Programming"}]
        languages = [{"value": "en"}]
        levels = [{"value": "beginner"}]
        prices = [{"value": "paid"}]
        durations = [{"value": "long"}]
        ratings = [{"value": 5}]

        mocker.patch(
            "courses.api.services.get_category_options",
            return_value=categories,
        )
        mocker.patch(
            "courses.api.services.get_language_options",
            return_value=languages,
        )
        mocker.patch(
            "courses.api.services.get_level_options",
            return_value=levels,
        )
        mocker.patch(
            "courses.api.services.get_price_options",
            return_value=prices,
        )
        mocker.patch(
            "courses.api.services.get_duration_options",
            return_value=durations,
        )
        mocker.patch(
            "courses.api.services.get_rating_options",
            return_value=ratings,
        )

        result = get_course_filter_metadata()

        assert result["categories"] is categories
        assert result["languages"] is languages
        assert result["levels"] is levels
        assert result["prices"] is prices
        assert result["durations"] is durations
        assert result["ratings"] is ratings


class TestGetBestSellerIds:
    @pytest.fixture
    def published_paid_course(
        self,
        test_user,
    ):
        return Course.objects.create(
            title="Published Paid Course",
            owner=test_user,
            status=Course.Status.PUBLISHED,
            price_type=Course.PriceType.PAID,
        )

    @pytest.fixture
    def published_free_course(
        self,
        test_user,
    ):
        return Course.objects.create(
            title="Published Free Course",
            owner=test_user,
            status=Course.Status.PUBLISHED,
            price_type=Course.PriceType.FREE,
        )

    @pytest.fixture
    def draft_paid_course(
        self,
        test_user,
    ):
        return Course.objects.create(
            title="Draft Paid Course",
            owner=test_user,
            status=Course.Status.DRAFT,
            price_type=Course.PriceType.PAID,
        )

    def test_returns_published_paid_course_id(
        self,
        published_paid_course,
    ):
        result = get_best_seller_ids()

        assert published_paid_course.id in result

    def test_returns_set_of_course_ids(
        self,
        published_paid_course,
    ):
        result = get_best_seller_ids()

        assert isinstance(result, set)
        assert result == {published_paid_course.id}

    def test_excludes_free_courses(
        self,
        published_paid_course,
        published_free_course,
    ):
        result = get_best_seller_ids()

        assert published_paid_course.id in result
        assert published_free_course.id not in result

    def test_excludes_unpublished_paid_courses(
        self,
        published_paid_course,
        draft_paid_course,
    ):
        result = get_best_seller_ids()

        assert published_paid_course.id in result
        assert draft_paid_course.id not in result

    def test_excludes_unpublished_free_courses(
        self,
        test_user,
    ):
        course = Course.objects.create(
            title="Draft Free Course",
            owner=test_user,
            status=Course.Status.DRAFT,
            price_type=Course.PriceType.FREE,
        )

        result = get_best_seller_ids()

        assert course.id not in result

    def test_orders_courses_by_enrollment_count(
        self,
        test_user,
        settings,
    ):
        settings.BEST_SELLERS_COUNT = 2

        first_course = Course.objects.create(
            title="Popular Course",
            owner=test_user,
            status=Course.Status.PUBLISHED,
            price_type=Course.PriceType.PAID,
        )
        second_course = Course.objects.create(
            title="Second Popular Course",
            owner=test_user,
            status=Course.Status.PUBLISHED,
            price_type=Course.PriceType.PAID,
        )
        third_course = Course.objects.create(
            title="Least Popular Course",
            owner=test_user,
            status=Course.Status.PUBLISHED,
            price_type=Course.PriceType.PAID,
        )

        enrollment_users = [
            User.objects.create_user(
                username=f"student_{index}",
                email=f"student_{index}@example.com",
                password="test-password",
            )
            for index in range(6)
        ]

        # The service counts Course.enrollments, so create the
        # project's actual Enrollment records.
        from enrollments.models import Enrollment

        for user in enrollment_users[:4]:
            Enrollment.objects.create(
                user=user,
                course=first_course,
            )

        for user in enrollment_users[4:6]:
            Enrollment.objects.create(
                user=user,
                course=second_course,
            )

        Enrollment.objects.create(
            user=enrollment_users[0],
            course=third_course,
        )

        result = get_best_seller_ids()

        assert result == {
            first_course.id,
            second_course.id,
        }

    def test_respects_best_sellers_count_setting(
        self,
        test_user,
        settings,
    ):
        settings.BEST_SELLERS_COUNT = 2

        courses = [
            Course.objects.create(
                title=f"Course {index}",
                owner=test_user,
                status=Course.Status.PUBLISHED,
                price_type=Course.PriceType.PAID,
            )
            for index in range(3)
        ]

        from enrollments.models import Enrollment

        enrollment_index = 0

        for course, enrollment_count in zip(courses, [3, 2, 1], strict=False):
            for _ in range(enrollment_count):
                user = User.objects.create_user(
                    username=f"seller_student_{enrollment_index}",
                    email=f"seller_student_{enrollment_index}@example.com",
                    password="test-password",
                )
                Enrollment.objects.create(
                    user=user,
                    course=course,
                )
                enrollment_index += 1

        result = get_best_seller_ids()

        assert len(result) == 2
        assert courses[0].id in result
        assert courses[1].id in result
        assert courses[2].id not in result

    def test_returns_empty_set_when_no_published_paid_courses_exist(
        self,
        test_user,
    ):
        Course.objects.create(
            title="Free Course",
            owner=test_user,
            status=Course.Status.PUBLISHED,
            price_type=Course.PriceType.FREE,
        )

        Course.objects.create(
            title="Draft Course",
            owner=test_user,
            status=Course.Status.DRAFT,
            price_type=Course.PriceType.PAID,
        )

        result = get_best_seller_ids()

        assert result == set()

    def test_course_with_zero_enrollments_is_included_when_within_limit(
        self,
        published_paid_course,
        settings,
    ):
        settings.BEST_SELLERS_COUNT = 5

        result = get_best_seller_ids()

        assert published_paid_course.id in result

    def test_best_sellers_count_zero_returns_empty_set(
        self,
        published_paid_course,
        settings,
    ):
        settings.BEST_SELLERS_COUNT = 0

        result = get_best_seller_ids()

        assert result == set()


class TestToggleCourseWishlist:
    def test_creates_wishlist_when_course_is_not_in_wishlist(
        self,
        test_user,
        course,
    ):
        result = toggle_course_wishlist(
            user=test_user,
            course=course,
        )

        assert result is True
        assert CourseWishlist.objects.filter(
            user=test_user,
            course=course,
        ).exists()

    def test_returns_true_when_wishlist_is_created(
        self,
        test_user,
        course,
    ):
        result = toggle_course_wishlist(
            user=test_user,
            course=course,
        )

        assert result is True

    def test_creates_exactly_one_wishlist_entry(
        self,
        test_user,
        course,
    ):
        toggle_course_wishlist(
            user=test_user,
            course=course,
        )

        assert (
            CourseWishlist.objects.filter(
                user=test_user,
                course=course,
            ).count()
            == 1
        )

    def test_removes_existing_wishlist(
        self,
        test_user,
        course,
    ):
        wishlist = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )

        result = toggle_course_wishlist(
            user=test_user,
            course=course,
        )

        assert result is False
        assert not CourseWishlist.objects.filter(
            pk=wishlist.pk,
        ).exists()

    def test_returns_false_when_wishlist_is_removed(
        self,
        test_user,
        course,
    ):
        CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )

        result = toggle_course_wishlist(
            user=test_user,
            course=course,
        )

        assert result is False

    def test_second_toggle_removes_wishlist(
        self,
        test_user,
        course,
    ):
        first_result = toggle_course_wishlist(
            user=test_user,
            course=course,
        )

        second_result = toggle_course_wishlist(
            user=test_user,
            course=course,
        )

        assert first_result is True
        assert second_result is False

        assert not CourseWishlist.objects.filter(
            user=test_user,
            course=course,
        ).exists()

    def test_third_toggle_recreates_wishlist(
        self,
        test_user,
        course,
    ):
        first_result = toggle_course_wishlist(
            user=test_user,
            course=course,
        )

        second_result = toggle_course_wishlist(
            user=test_user,
            course=course,
        )

        third_result = toggle_course_wishlist(
            user=test_user,
            course=course,
        )

        assert first_result is True
        assert second_result is False
        assert third_result is True

        assert (
            CourseWishlist.objects.filter(
                user=test_user,
                course=course,
            ).count()
            == 1
        )

    def test_does_not_create_duplicate_wishlist(
        self,
        test_user,
        course,
    ):
        CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )

        toggle_course_wishlist(
            user=test_user,
            course=course,
        )

        toggle_course_wishlist(
            user=test_user,
            course=course,
        )

        assert (
            CourseWishlist.objects.filter(
                user=test_user,
                course=course,
            ).count()
            == 1
        )

    def test_different_users_have_independent_wishlists(
        self,
        test_user,
        another_user,
        course,
    ):
        first_result = toggle_course_wishlist(
            user=test_user,
            course=course,
        )
        second_result = toggle_course_wishlist(
            user=another_user,
            course=course,
        )

        assert first_result is True
        assert second_result is True

        assert CourseWishlist.objects.filter(
            user=test_user,
            course=course,
        ).exists()

        assert CourseWishlist.objects.filter(
            user=another_user,
            course=course,
        ).exists()

    def test_different_courses_have_independent_wishlists(
        self,
        test_user,
        course,
    ):
        second_course = Course.objects.create(
            title="Another Course",
            owner=test_user,
        )

        first_result = toggle_course_wishlist(
            user=test_user,
            course=course,
        )
        second_result = toggle_course_wishlist(
            user=test_user,
            course=second_course,
        )

        assert first_result is True
        assert second_result is True

        assert CourseWishlist.objects.filter(
            user=test_user,
            course=course,
        ).exists()

        assert CourseWishlist.objects.filter(
            user=test_user,
            course=second_course,
        ).exists()
