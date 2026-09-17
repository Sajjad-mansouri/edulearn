import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from courses.models.feedback import (
    CourseFeedback,
    CourseFeedbackInteraction,
)
from enrollments.models import Enrollment


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def review_enrollments(course, test_user, another_user):
    first_enrollment = Enrollment.objects.create(
        course=course,
        user=test_user,
    )
    second_enrollment = Enrollment.objects.create(
        course=course,
        user=another_user,
    )

    return first_enrollment, second_enrollment


@pytest.fixture
def course_reviews(review_enrollments):
    first_enrollment, second_enrollment = review_enrollments

    first_review = CourseFeedback.objects.create(
        enrollment=first_enrollment,
        rating=5,
        comment="Excellent course.",
    )
    second_review = CourseFeedback.objects.create(
        enrollment=second_enrollment,
        rating=4,
        comment="Very useful course.",
    )

    return first_review, second_review


@pytest.fixture
def course_review_url(course):
    return reverse(
        "courses_api:course_reviews",
        kwargs={"course_id": course.id},
    )


class TestCourseReviewListApiView:
    def test_get_returns_course_reviews(
        self,
        api_client,
        course_review_url,
        course_reviews,
    ):
        response = api_client.get(course_review_url)

        assert response.status_code == 200

        data = response.json()

        assert data["current_page"] == 1
        assert data["per_page"] == 3
        assert data["total_reviews"] == 2
        assert data["total_pages"] == 1
        assert len(data["items"]) == 2

    def test_get_returns_expected_review_fields(
        self,
        api_client,
        course_review_url,
        course_reviews,
    ):
        first_review, second_review = course_reviews

        response = api_client.get(course_review_url)

        assert response.status_code == 200

        items = response.json()["items"]

        assert items[0]["id"] == first_review.id
        assert items[0]["rating"] == 5
        assert items[0]["comment"] == "Excellent course."

        assert items[1]["id"] == second_review.id
        assert items[1]["rating"] == 4
        assert items[1]["comment"] == "Very useful course."

    def test_get_orders_reviews_by_created_at_ascending(
        self,
        api_client,
        course_review_url,
        course_reviews,
    ):
        first_review, second_review = course_reviews

        response = api_client.get(course_review_url)

        assert response.status_code == 200

        items = response.json()["items"]

        assert items[0]["id"] == first_review.id
        assert items[1]["id"] == second_review.id

        assert first_review.created_at <= second_review.created_at

    def test_get_calculates_helpful_count(
        self,
        api_client,
        course_review_url,
        course_reviews,
        review_enrollments,
    ):
        first_review, second_review = course_reviews
        first_enrollment, _ = review_enrollments

        CourseFeedbackInteraction.objects.create(
            feedback=first_review,
            enrollment=first_enrollment,
        )
        CourseFeedbackInteraction.objects.create(
            feedback=first_review,
            enrollment=first_enrollment,
        )

        response = api_client.get(course_review_url)

        assert response.status_code == 200

        items = response.json()["items"]

        assert items[0]["id"] == first_review.id
        assert items[0]["helpful_count"] == 2

        assert items[1]["id"] == second_review.id
        assert items[1]["helpful_count"] == 0

    def test_get_returns_user_has_liked_false_for_anonymous_user(
        self,
        api_client,
        course_review_url,
        course_reviews,
        review_enrollments,
    ):
        first_review, _ = course_reviews
        first_enrollment, _ = review_enrollments

        CourseFeedbackInteraction.objects.create(
            feedback=first_review,
            enrollment=first_enrollment,
        )

        response = api_client.get(course_review_url)

        assert response.status_code == 200

        items = response.json()["items"]

        assert items[0]["user_has_liked"] is False

    def test_get_returns_user_has_liked_true_for_authenticated_user(
        self,
        api_client,
        course_review_url,
        course_reviews,
        review_enrollments,
        test_user,
    ):
        first_review, _ = course_reviews
        first_enrollment, _ = review_enrollments

        CourseFeedbackInteraction.objects.create(
            feedback=first_review,
            enrollment=first_enrollment,
        )

        api_client.force_authenticate(user=test_user)

        response = api_client.get(course_review_url)

        assert response.status_code == 200

        items = response.json()["items"]

        assert items[0]["user_has_liked"] is True

    def test_get_returns_user_has_liked_false_when_authenticated_user_has_not_liked(
        self,
        api_client,
        course_review_url,
        course_reviews,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.get(course_review_url)

        assert response.status_code == 200

        items = response.json()["items"]

        assert items[0]["user_has_liked"] is False
        assert items[1]["user_has_liked"] is False

    def test_get_marks_review_owner(
        self,
        api_client,
        course_review_url,
        course_reviews,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.get(course_review_url)

        assert response.status_code == 200

        items = response.json()["items"]

        assert items[0]["is_owner"] is True
        assert items[1]["is_owner"] is False

    def test_get_marks_non_owner_reviews_correctly(
        self,
        api_client,
        course_review_url,
        course_reviews,
        another_user,
    ):
        api_client.force_authenticate(user=another_user)

        response = api_client.get(course_review_url)

        assert response.status_code == 200

        items = response.json()["items"]

        assert items[0]["is_owner"] is False
        assert items[1]["is_owner"] is True

    def test_get_calculates_rating_distribution(
        self,
        api_client,
        course,
        test_user,
        another_user,
    ):
        first_enrollment = Enrollment.objects.create(
            course=course,
            user=test_user,
        )
        second_enrollment = Enrollment.objects.create(
            course=course,
            user=another_user,
        )

        CourseFeedback.objects.create(
            enrollment=first_enrollment,
            rating=5,
            comment="Excellent course.",
        )
        CourseFeedback.objects.create(
            enrollment=second_enrollment,
            rating=5,
            comment="Very useful course.",
        )

        url = reverse(
            "courses_api:course_reviews",
            kwargs={"course_id": course.id},
        )

        response = api_client.get(url)

        assert response.status_code == 200

        distribution = response.json()["distribution"]

        assert distribution["5"] == 100
        assert distribution["1"] == 0
        assert distribution["2"] == 0
        assert distribution["3"] == 0
        assert distribution["4"] == 0

    def test_get_calculates_mixed_rating_distribution(
        self,
        api_client,
        course,
        test_user,
        another_user,
    ):
        first_enrollment = Enrollment.objects.create(
            course=course,
            user=test_user,
        )
        second_enrollment = Enrollment.objects.create(
            course=course,
            user=another_user,
        )

        CourseFeedback.objects.create(
            enrollment=first_enrollment,
            rating=5,
            comment="Excellent course.",
        )
        CourseFeedback.objects.create(
            enrollment=second_enrollment,
            rating=4,
            comment="Very useful course.",
        )

        url = reverse(
            "courses_api:course_reviews",
            kwargs={"course_id": course.id},
        )

        response = api_client.get(url)

        assert response.status_code == 200

        distribution = response.json()["distribution"]

        assert distribution["4"] == 50
        assert distribution["5"] == 50
        assert distribution["1"] == 0
        assert distribution["2"] == 0
        assert distribution["3"] == 0

    def test_get_returns_zero_for_ratings_without_reviews(
        self,
        api_client,
        course_review_url,
        course_reviews,
    ):
        response = api_client.get(course_review_url)

        assert response.status_code == 200

        distribution = response.json()["distribution"]

        assert distribution["1"] == 0
        assert distribution["2"] == 0
        assert distribution["3"] == 0

    def test_get_uses_per_page_query_parameter(
        self,
        api_client,
        course,
        test_user,
        another_user,
    ):
        first_enrollment = Enrollment.objects.create(
            course=course,
            user=test_user,
        )
        second_enrollment = Enrollment.objects.create(
            course=course,
            user=another_user,
        )

        CourseFeedback.objects.create(
            enrollment=first_enrollment,
            rating=5,
            comment="Excellent course.",
        )
        CourseFeedback.objects.create(
            enrollment=second_enrollment,
            rating=4,
            comment="Very useful course.",
        )

        url = reverse(
            "courses_api:course_reviews",
            kwargs={"course_id": course.id},
        )

        response = api_client.get(
            url,
            {"per_page": 1},
        )

        assert response.status_code == 200

        data = response.json()

        assert data["per_page"] == 1
        assert data["total_reviews"] == 2
        assert data["total_pages"] == 2
        assert data["current_page"] == 1
        assert len(data["items"]) == 1

    def test_get_uses_page_number_query_parameter(
        self,
        api_client,
        course,
        test_user,
        another_user,
    ):
        first_enrollment = Enrollment.objects.create(
            course=course,
            user=test_user,
        )
        second_enrollment = Enrollment.objects.create(
            course=course,
            user=another_user,
        )

        first_review = CourseFeedback.objects.create(
            enrollment=first_enrollment,
            rating=5,
            comment="Excellent course.",
        )
        second_review = CourseFeedback.objects.create(
            enrollment=second_enrollment,
            rating=4,
            comment="Very useful course.",
        )

        url = reverse(
            "courses_api:course_reviews",
            kwargs={"course_id": course.id},
        )

        response = api_client.get(
            url,
            {
                "per_page": 1,
                "page_number": 2,
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["current_page"] == 2
        assert data["per_page"] == 1
        assert data["total_reviews"] == 2
        assert data["total_pages"] == 2
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == second_review.id
        assert data["items"][0]["id"] != first_review.id

    def test_get_out_of_range_page_returns_last_page(
        self,
        api_client,
        course_review_url,
        course_reviews,
    ):
        response = api_client.get(
            course_review_url,
            {
                "per_page": 1,
                "page_number": 100,
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["current_page"] == data["total_pages"]
        assert len(data["items"]) == 1

    def test_get_without_reviews_returns_empty_items(
        self,
        api_client,
        course_review_url,
    ):
        response = api_client.get(course_review_url)

        assert response.status_code == 200

        data = response.json()

        assert data["current_page"] == 1
        assert data["per_page"] == 3
        assert data["total_reviews"] == 0
        assert data["total_pages"] == 1
        assert data["items"] == []

    def test_get_without_reviews_returns_zero_distribution(
        self,
        api_client,
        course_review_url,
    ):
        response = api_client.get(course_review_url)

        assert response.status_code == 200

        distribution = response.json()["distribution"]

        assert distribution == {
            "1": 0,
            "2": 0,
            "3": 0,
            "4": 0,
            "5": 0,
        }

    def test_get_only_returns_reviews_for_requested_course(
        self,
        api_client,
        course,
        category,
        test_user,
        another_user,
    ):
        from courses.models.course import Course

        another_course = Course.objects.create(
            title="Another Course",
            owner=test_user,
            category=category,
        )

        first_enrollment = Enrollment.objects.create(
            course=course,
            user=test_user,
        )
        second_enrollment = Enrollment.objects.create(
            course=another_course,
            user=another_user,
        )

        requested_course_review = CourseFeedback.objects.create(
            enrollment=first_enrollment,
            rating=5,
            comment="Excellent course.",
        )
        CourseFeedback.objects.create(
            enrollment=second_enrollment,
            rating=1,
            comment="Another course review.",
        )

        url = reverse(
            "courses_api:course_reviews",
            kwargs={"course_id": course.id},
        )

        response = api_client.get(url)

        assert response.status_code == 200

        data = response.json()

        assert data["total_reviews"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == requested_course_review.id

    def test_get_allows_unauthenticated_users(
        self,
        api_client,
        course_review_url,
        course_reviews,
    ):
        response = api_client.get(course_review_url)

        assert response.status_code == 200

    def test_get_ignores_page_query_parameter(
        self,
        api_client,
        course,
        test_user,
        another_user,
    ):
        first_enrollment = Enrollment.objects.create(
            course=course,
            user=test_user,
        )
        second_enrollment = Enrollment.objects.create(
            course=course,
            user=another_user,
        )

        first_review = CourseFeedback.objects.create(
            enrollment=first_enrollment,
            rating=5,
            comment="Excellent course.",
        )
        second_review = CourseFeedback.objects.create(
            enrollment=second_enrollment,
            rating=4,
            comment="Very useful course.",
        )

        url = reverse(
            "courses_api:course_reviews",
            kwargs={"course_id": course.id},
        )

        response = api_client.get(
            url,
            {
                "per_page": 1,
                "page": 2,
            },
        )

        assert response.status_code == 200

        data = response.json()

        # The view reads `page_number`, not `page`.
        assert data["current_page"] == 1
        assert data["items"][0]["id"] == first_review.id
        assert data["items"][0]["id"] != second_review.id

    def test_get_uses_default_per_page_when_not_provided(
        self,
        api_client,
        course_review_url,
        course_reviews,
    ):
        response = api_client.get(course_review_url)

        assert response.status_code == 200

        data = response.json()

        assert data["per_page"] == 3

    def test_get_preserves_rating_as_integer(
        self,
        api_client,
        course_review_url,
        course_reviews,
    ):
        response = api_client.get(course_review_url)

        assert response.status_code == 200

        items = response.json()["items"]

        assert items[0]["rating"] == 5
        assert items[1]["rating"] == 4

    def test_get_returns_correct_total_pages(
        self,
        api_client,
        course,
        test_user,
        another_user,
    ):
        first_enrollment = Enrollment.objects.create(
            course=course,
            user=test_user,
        )
        second_enrollment = Enrollment.objects.create(
            course=course,
            user=another_user,
        )

        CourseFeedback.objects.create(
            enrollment=first_enrollment,
            rating=5,
            comment="Excellent course.",
        )
        CourseFeedback.objects.create(
            enrollment=second_enrollment,
            rating=4,
            comment="Very useful course.",
        )

        url = reverse(
            "courses_api:course_reviews",
            kwargs={"course_id": course.id},
        )

        response = api_client.get(
            url,
            {
                "per_page": 1,
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["total_reviews"] == 2
        assert data["total_pages"] == 2


@pytest.fixture
def student_enrollment(course, student_user):
    return Enrollment.objects.create(
        user=student_user,
        course=course,
    )


@pytest.fixture
def submit_review_url(course):
    return reverse(
        "courses_api:submit_review",
        kwargs={"course_id": course.id},
    )


class TestCourseReviewApiView:
    def test_student_can_submit_review(
        self,
        api_client,
        submit_review_url,
        student_user,
        student_enrollment,
    ):
        api_client.force_authenticate(user=student_user)

        data = {
            "rating": 5,
            "comment": "Excellent course.",
        }

        response = api_client.post(
            submit_review_url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data == {
            "enrollment": student_enrollment.id,
            "rating": 5,
            "comment": "Excellent course.",
        }

        feedback = CourseFeedback.objects.get(
            enrollment=student_enrollment,
        )

        assert feedback.enrollment == student_enrollment
        assert feedback.rating == 5
        assert feedback.comment == "Excellent course."

    def test_student_can_submit_review_without_comment(
        self,
        api_client,
        submit_review_url,
        student_user,
        student_enrollment,
    ):
        api_client.force_authenticate(user=student_user)

        data = {
            "rating": 5,
        }

        response = api_client.post(
            submit_review_url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data["enrollment"] == student_enrollment.id
        assert response_data["rating"] == 5

        feedback = CourseFeedback.objects.get(
            enrollment=student_enrollment,
        )

        assert feedback.enrollment == student_enrollment
        assert feedback.rating == 5

    def test_submit_review_uses_authenticated_users_enrollment(
        self,
        api_client,
        submit_review_url,
        student_user,
        student_enrollment,
    ):
        api_client.force_authenticate(user=student_user)

        data = {
            "rating": 4,
            "comment": "Very useful course.",
        }

        response = api_client.post(
            submit_review_url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data["enrollment"] == student_enrollment.id

        feedback = CourseFeedback.objects.get(
            enrollment=student_enrollment,
        )

        assert feedback.enrollment == student_enrollment

    def test_submit_review_returns_404_when_student_is_not_enrolled(
        self,
        api_client,
        submit_review_url,
        student_user,
    ):
        api_client.force_authenticate(user=student_user)

        data = {
            "rating": 5,
            "comment": "Excellent course.",
        }

        response = api_client.post(
            submit_review_url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

        assert CourseFeedback.objects.count() == 0

    def test_submit_review_requires_student_role(
        self,
        api_client,
        submit_review_url,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        data = {
            "rating": 5,
            "comment": "Excellent course.",
        }

        response = api_client.post(
            submit_review_url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

        assert CourseFeedback.objects.count() == 0

    def test_submit_review_requires_authentication(
        self,
        api_client,
        submit_review_url,
    ):
        data = {
            "rating": 5,
            "comment": "Excellent course.",
        }

        response = api_client.post(
            submit_review_url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        assert CourseFeedback.objects.count() == 0

    @pytest.mark.parametrize(
        "rating",
        [0, 6, -1, 10],
    )
    def test_submit_review_rejects_invalid_rating(
        self,
        api_client,
        submit_review_url,
        student_user,
        student_enrollment,
        rating,
    ):
        api_client.force_authenticate(user=student_user)

        data = {
            "rating": rating,
            "comment": "Course review.",
        }

        response = api_client.post(
            submit_review_url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        response_data = response.json()

        assert "rating" in response_data

        assert not CourseFeedback.objects.filter(
            enrollment=student_enrollment,
        ).exists()

    def test_submit_review_rejects_missing_rating(
        self,
        api_client,
        submit_review_url,
        student_user,
        student_enrollment,
    ):
        api_client.force_authenticate(user=student_user)

        data = {
            "comment": "Excellent course.",
        }

        response = api_client.post(
            submit_review_url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        response_data = response.json()

        assert "rating" in response_data

        assert not CourseFeedback.objects.filter(
            enrollment=student_enrollment,
        ).exists()

    def test_submit_review_with_empty_request_body_is_invalid(
        self,
        api_client,
        submit_review_url,
        student_user,
        student_enrollment,
    ):
        api_client.force_authenticate(user=student_user)

        response = api_client.post(
            submit_review_url,
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        response_data = response.json()

        assert "rating" in response_data
        assert "comment" not in response_data

        assert not CourseFeedback.objects.filter(
            enrollment=student_enrollment,
        ).exists()

    def test_submit_review_returns_serializer_fields_only(
        self,
        api_client,
        submit_review_url,
        student_user,
        student_enrollment,
    ):
        api_client.force_authenticate(user=student_user)

        data = {
            "rating": 5,
            "comment": "Excellent course.",
        }

        response = api_client.post(
            submit_review_url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        assert set(response.json()) == {
            "enrollment",
            "rating",
            "comment",
        }

    def test_submit_review_does_not_use_enrollment_from_request_data(
        self,
        api_client,
        submit_review_url,
        student_user,
        student_enrollment,
        another_user,
        course,
    ):
        another_enrollment = Enrollment.objects.create(
            user=another_user,
            course=course,
        )

        api_client.force_authenticate(user=student_user)

        data = {
            "enrollment": another_enrollment.id,
            "rating": 5,
            "comment": "Excellent course.",
        }

        response = api_client.post(
            submit_review_url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data["enrollment"] == another_enrollment.id
        assert response_data["enrollment"] != student_enrollment.id

    def test_submit_review_for_nonexistent_course_returns_404(
        self,
        api_client,
        student_user,
    ):
        api_client.force_authenticate(user=student_user)

        url = reverse(
            "courses_api:submit_review",
            kwargs={"course_id": 999999},
        )

        data = {
            "rating": 5,
            "comment": "Excellent course.",
        }

        response = api_client.post(
            url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

        assert CourseFeedback.objects.count() == 0
