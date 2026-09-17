import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from courses.models.feedback import CourseFeedback
from enrollments.models import Enrollment
from profiles.models import InstructorProfile, Profile, SocialLink

pytestmark = pytest.mark.django_db


class TestCourseDetailInstructorInfoApiView:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def instructor_profile(self, test_user):
        profile = Profile.objects.create(
            user=test_user,
        )

        return InstructorProfile.objects.create(
            profile=profile,
            professional_title="Instructor",
            headline="Django Instructor",
            biography="Django development instructor",
            organization="SM-LMS",
            is_verified=True,
        )

    @pytest.fixture
    def course_with_instructor(
        self,
        course,
        instructor_profile,
    ):
        return course

    @pytest.fixture
    def course_detail_instructor_url(
        self,
        course_with_instructor,
    ):
        return reverse(
            "courses_api:course_detail_instructor_info",
            kwargs={
                "course_id": course_with_instructor.pk,
            },
        )

    def test_course_instructor_can_be_retrieved(
        self,
        api_client,
        course_with_instructor,
        course_detail_instructor_url,
    ):
        response = api_client.get(course_detail_instructor_url)

        assert response.status_code == status.HTTP_200_OK
        assert (
            response.data["id"]
            == course_with_instructor.owner.profile.instructor_profile.id
        )

    def test_endpoint_allows_unauthenticated_requests(
        self,
        api_client,
        course_with_instructor,
        course_detail_instructor_url,
    ):
        response = api_client.get(course_detail_instructor_url)

        assert response.status_code == status.HTTP_200_OK

    def test_nonexistent_course_returns_404(
        self,
        api_client,
        course_with_instructor,
    ):
        nonexistent_course_id = course_with_instructor.pk + 1

        url = reverse(
            "courses_api:course_detail_instructor_info",
            kwargs={
                "course_id": nonexistent_course_id,
            },
        )

        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_course_owned_by_another_user_returns_404(
        self,
        api_client,
        course_with_instructor,
        another_user,
    ):
        another_course = course_with_instructor.__class__.objects.create(
            title="Another Course",
            owner=another_user,
            category=course_with_instructor.category,
        )

        url = reverse(
            "courses_api:course_detail_instructor_info",
            kwargs={
                "course_id": another_course.pk,
            },
        )

        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_course_without_instructor_profile_returns_404(
        self,
        api_client,
        course,
    ):
        url = reverse(
            "courses_api:course_detail_instructor_info",
            kwargs={
                "course_id": course.pk,
            },
        )

        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_response_contains_instructor_basic_information(
        self,
        api_client,
        instructor_profile,
        course_detail_instructor_url,
    ):
        response = api_client.get(course_detail_instructor_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == instructor_profile.id
        assert response.data["headline"] == instructor_profile.headline
        assert response.data["bio"] == instructor_profile.biography
        assert response.data["is_verified"] is True
        assert response.data["organization"] == instructor_profile.organization

    def test_response_contains_instructor_name(
        self,
        api_client,
        instructor_profile,
        test_user,
        course_detail_instructor_url,
    ):
        response = api_client.get(course_detail_instructor_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == test_user.get_full_name()

    def test_response_contains_empty_social_links_when_none_exist(
        self,
        api_client,
        instructor_profile,
        course_detail_instructor_url,
    ):
        response = api_client.get(course_detail_instructor_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["social_links"] == []

    def test_response_contains_instructor_social_links(
        self,
        api_client,
        instructor_profile,
        course_detail_instructor_url,
    ):
        SocialLink.objects.create(
            profile=instructor_profile.profile,
            platform="github",
            address="https://github.com/example",
        )

        SocialLink.objects.create(
            profile=instructor_profile.profile,
            platform="linkedin",
            address="https://linkedin.com/in/example",
        )

        response = api_client.get(course_detail_instructor_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["social_links"] == [
            {
                "github": "https://github.com/example",
            },
            {
                "linkedin": "https://linkedin.com/in/example",
            },
        ]

    def test_rating_is_empty_when_instructor_has_no_feedback(
        self,
        api_client,
        instructor_profile,
        course_detail_instructor_url,
    ):
        response = api_client.get(course_detail_instructor_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["rating"] == ""

    def test_total_students_is_zero_when_instructor_has_no_enrollments(
        self,
        api_client,
        instructor_profile,
        course_detail_instructor_url,
    ):
        response = api_client.get(course_detail_instructor_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_students"] == 0

    def test_total_courses_counts_courses_owned_by_instructor(
        self,
        api_client,
        instructor_profile,
        course,
        category,
    ):
        course.__class__.objects.create(
            title="Second Course",
            owner=course.owner,
            category=category,
        )

        url = reverse(
            "courses_api:course_detail_instructor_info",
            kwargs={
                "course_id": course.pk,
            },
        )

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_courses"] == 2

    def test_rating_is_average_of_instructor_course_feedback(
        self,
        api_client,
        instructor_profile,
        course,
        another_user,
        course_detail_instructor_url,
    ):
        enrollment = Enrollment.objects.create(
            user=another_user,
            course=course,
        )

        CourseFeedback.objects.create(
            enrollment=enrollment,
            rating=4,
        )

        response = api_client.get(course_detail_instructor_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["rating"] == 4.0

    def test_rating_is_rounded_to_one_decimal_place(
        self,
        api_client,
        instructor_profile,
        course,
        another_user,
        course_detail_instructor_url,
    ):
        second_student = another_user.__class__.objects.create_user(
            username="another_student",
            email="another_student@example.com",
            password="test-password",
        )

        first_enrollment = Enrollment.objects.create(
            user=another_user,
            course=course,
        )

        second_enrollment = Enrollment.objects.create(
            user=second_student,
            course=course,
        )

        CourseFeedback.objects.create(
            enrollment=first_enrollment,
            rating=4,
        )

        CourseFeedback.objects.create(
            enrollment=second_enrollment,
            rating=5,
        )

        response = api_client.get(course_detail_instructor_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["rating"] == 4.5

    def test_total_students_counts_distinct_students(
        self,
        api_client,
        instructor_profile,
        course,
        another_user,
        course_detail_instructor_url,
    ):
        second_course = course.__class__.objects.create(
            title="Second Course",
            owner=course.owner,
            category=course.category,
        )

        Enrollment.objects.create(
            user=another_user,
            course=course,
        )

        Enrollment.objects.create(
            user=another_user,
            course=second_course,
        )

        response = api_client.get(course_detail_instructor_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_students"] == 1

    def test_total_students_counts_different_students_separately(
        self,
        api_client,
        instructor_profile,
        course,
        another_user,
        course_detail_instructor_url,
    ):
        second_student = another_user.__class__.objects.create_user(
            username="another_student",
            email="another_student@example.com",
            password="test-password",
        )

        Enrollment.objects.create(
            user=another_user,
            course=course,
        )

        Enrollment.objects.create(
            user=second_student,
            course=course,
        )

        response = api_client.get(course_detail_instructor_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_students"] == 2

    def test_total_courses_is_one_for_single_owned_course(
        self,
        api_client,
        instructor_profile,
        course_detail_instructor_url,
    ):
        response = api_client.get(course_detail_instructor_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_courses"] == 1

    def test_instructor_queryset_contains_expected_annotations(
        self,
        instructor_profile,
        course,
    ):
        from courses.api.views import CourseDetailInstructorInfoApiView

        view = CourseDetailInstructorInfoApiView()

        instructor = view.get_queryset().get(
            pk=instructor_profile.pk,
        )

        assert instructor.total_courses == 1
        assert instructor.total_students == 0
        assert instructor.rating is None

    def test_instructor_queryset_counts_owned_courses_distinctly(
        self,
        instructor_profile,
        course,
    ):
        from courses.api.views import CourseDetailInstructorInfoApiView

        course.__class__.objects.create(
            title="Second Course",
            owner=course.owner,
            category=course.category,
        )

        view = CourseDetailInstructorInfoApiView()

        instructor = view.get_queryset().get(
            pk=instructor_profile.pk,
        )

        assert instructor.total_courses == 2

    def test_post_method_is_not_allowed(
        self,
        api_client,
        course_detail_instructor_url,
    ):
        response = api_client.post(course_detail_instructor_url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_put_method_is_not_allowed(
        self,
        api_client,
        course_detail_instructor_url,
    ):
        response = api_client.put(course_detail_instructor_url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_patch_method_is_not_allowed(
        self,
        api_client,
        course_detail_instructor_url,
    ):
        response = api_client.patch(course_detail_instructor_url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_delete_method_is_not_allowed(
        self,
        api_client,
        course_detail_instructor_url,
    ):
        response = api_client.delete(course_detail_instructor_url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
