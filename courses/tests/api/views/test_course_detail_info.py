from datetime import timedelta

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory

from courses.api.views import CourseDetailInfoApiView
from curriculums.models.lesson import Lesson
from curriculums.models.section import Section

pytestmark = pytest.mark.django_db


class TestCourseDetailInfoApiView:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def published_course(self, course):
        course.status = "published"
        course.duration = timedelta(hours=2)
        course.save(update_fields=["status", "duration"])

        return course

    @pytest.fixture
    def course_detail_url(self, published_course):
        return reverse(
            "courses_api:course_detail_info",
            kwargs={"pk": published_course.pk},
        )

    @pytest.fixture
    def course_with_lessons(self, published_course):
        first_section = Section.objects.create(
            course=published_course,
            title="Section 1",
            order=1,
        )

        second_section = Section.objects.create(
            course=published_course,
            title="Section 2",
            order=2,
        )

        Lesson.objects.create(
            section=first_section,
            title="Lesson 1",
            order=1,
            duration=timedelta(minutes=30),
        )

        Lesson.objects.create(
            section=first_section,
            title="Lesson 2",
            order=2,
            duration=timedelta(minutes=45),
        )

        Lesson.objects.create(
            section=second_section,
            title="Lesson 3",
            order=1,
            duration=timedelta(minutes=15),
        )

        return published_course

    def test_published_course_can_be_retrieved(
        self,
        api_client,
        published_course,
        course_detail_url,
    ):
        response = api_client.get(course_detail_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == published_course.id
        assert response.data["slug"] == published_course.slug
        assert response.data["title"] == published_course.title

    def test_endpoint_allows_unauthenticated_requests(
        self,
        api_client,
        published_course,
        course_detail_url,
    ):
        response = api_client.get(course_detail_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == published_course.id

    def test_draft_course_cannot_be_retrieved(
        self,
        api_client,
        course,
    ):
        course.status = "draft"
        course.duration = timedelta(hours=2)
        course.save(update_fields=["status", "duration"])

        url = reverse(
            "courses_api:course_detail_info",
            kwargs={"pk": course.pk},
        )

        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_nonexistent_course_returns_404(
        self,
        api_client,
        published_course,
    ):
        nonexistent_course_id = published_course.pk + 1

        url = reverse(
            "courses_api:course_detail_info",
            kwargs={"pk": nonexistent_course_id},
        )

        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_post_method_is_not_allowed(
        self,
        api_client,
        course_detail_url,
    ):
        response = api_client.post(course_detail_url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_put_method_is_not_allowed(
        self,
        api_client,
        course_detail_url,
    ):
        response = api_client.put(course_detail_url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_patch_method_is_not_allowed(
        self,
        api_client,
        course_detail_url,
    ):
        response = api_client.patch(course_detail_url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_delete_method_is_not_allowed(
        self,
        api_client,
        course_detail_url,
    ):
        response = api_client.delete(course_detail_url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_queryset_returns_published_course(
        self,
        published_course,
    ):
        view = CourseDetailInfoApiView()

        queryset = view.get_queryset()

        result = queryset.get(pk=published_course.pk)

        assert result.pk == published_course.pk

    def test_queryset_excludes_draft_course(
        self,
        course,
    ):
        course.status = "draft"
        course.duration = timedelta(hours=2)
        course.save(update_fields=["status", "duration"])

        view = CourseDetailInfoApiView()

        queryset = view.get_queryset()

        assert not queryset.filter(pk=course.pk).exists()

    def test_queryset_annotations_are_zero_without_enrollments(
        self,
        published_course,
    ):
        view = CourseDetailInfoApiView()

        annotated_course = view.get_queryset().get(
            pk=published_course.pk,
        )

        assert annotated_course.rating is None
        assert annotated_course.total_ratings == 0
        assert annotated_course.total_students == 0

    def test_serializer_context_contains_sum_of_lesson_durations(
        self,
        course_with_lessons,
    ):
        factory = APIRequestFactory()

        url = reverse(
            "courses_api:course_detail_info",
            kwargs={"pk": course_with_lessons.pk},
        )

        request = factory.get(url)

        view = CourseDetailInfoApiView()
        view.setup(
            request,
            pk=course_with_lessons.pk,
        )
        view.request = view.initialize_request(request)
        view.format_kwarg = None

        context = view.get_serializer_context()

        assert context["course_duration"] == timedelta(minutes=90)

    def test_serializer_context_contains_none_when_course_has_no_lessons(
        self,
        published_course,
    ):
        factory = APIRequestFactory()

        url = reverse(
            "courses_api:course_detail_info",
            kwargs={"pk": published_course.pk},
        )

        request = factory.get(url)

        view = CourseDetailInfoApiView()
        view.setup(
            request,
            pk=published_course.pk,
        )
        view.request = view.initialize_request(request)
        view.format_kwarg = None

        context = view.get_serializer_context()

        assert context["course_duration"] is None

    def test_serializer_context_sums_lessons_across_all_sections(
        self,
        course_with_lessons,
    ):
        factory = APIRequestFactory()

        url = reverse(
            "courses_api:course_detail_info",
            kwargs={"pk": course_with_lessons.pk},
        )

        request = factory.get(url)

        view = CourseDetailInfoApiView()
        view.setup(
            request,
            pk=course_with_lessons.pk,
        )
        view.request = view.initialize_request(request)
        view.format_kwarg = None

        context = view.get_serializer_context()

        expected_duration = timedelta(minutes=90)

        assert context["course_duration"] == expected_duration

    def test_serializer_context_ignores_lessons_with_null_duration(
        self,
        published_course,
    ):
        section = Section.objects.create(
            course=published_course,
            title="Section 1",
            order=1,
        )

        Lesson.objects.create(
            section=section,
            title="Lesson with duration",
            order=1,
            duration=timedelta(minutes=30),
        )

        Lesson.objects.create(
            section=section,
            title="Lesson without duration",
            order=2,
            duration=None,
        )

        factory = APIRequestFactory()

        url = reverse(
            "courses_api:course_detail_info",
            kwargs={"pk": published_course.pk},
        )

        request = factory.get(url)

        view = CourseDetailInfoApiView()
        view.setup(
            request,
            pk=published_course.pk,
        )
        view.request = view.initialize_request(request)
        view.format_kwarg = None

        context = view.get_serializer_context()

        assert context["course_duration"] == timedelta(minutes=30)

    def test_serializer_context_is_none_when_all_lesson_durations_are_null(
        self,
        published_course,
    ):
        section = Section.objects.create(
            course=published_course,
            title="Section 1",
            order=1,
        )

        Lesson.objects.create(
            section=section,
            title="Lesson without duration",
            order=1,
            duration=None,
        )

        factory = APIRequestFactory()

        url = reverse(
            "courses_api:course_detail_info",
            kwargs={"pk": published_course.pk},
        )

        request = factory.get(url)

        view = CourseDetailInfoApiView()
        view.setup(
            request,
            pk=published_course.pk,
        )
        view.request = view.initialize_request(request)
        view.format_kwarg = None

        context = view.get_serializer_context()

        assert context["course_duration"] is None
