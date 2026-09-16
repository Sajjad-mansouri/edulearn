import pytest
from django.urls import reverse
from django.views.generic import DetailView, TemplateView

from courses.models.course import Course
from courses.views import CourseCatalog, CourseDetailView

pytestmark = pytest.mark.django_db


class TestCourseCatalog:
    url = reverse("courses:catalog")

    def test_catalog_returns_200(
        self,
        client,
    ):
        response = client.get(self.url)

        assert response.status_code == 200

    def test_catalog_uses_expected_template(
        self,
        client,
    ):
        response = client.get(self.url)

        assert response.status_code == 200
        assert "courses/catalog.html" in [
            template.name for template in response.templates if template.name
        ]

    def test_catalog_returns_expected_template_directly(
        self,
    ):
        assert CourseCatalog.template_name == "courses/catalog.html"

    def test_catalog_does_not_require_authentication(
        self,
        client,
    ):
        response = client.get(self.url)

        assert response.status_code == 200

    def test_catalog_uses_template_view(
        self,
    ):
        assert issubclass(CourseCatalog, TemplateView)

    def test_catalog_does_not_require_course_parameter(
        self,
        client,
    ):
        response = client.get(self.url)

        assert response.status_code == 200


class TestCourseDetailView:
    def test_published_course_returns_200(
        self,
        client,
        course,
    ):
        course.status = Course.Status.PUBLISHED
        course.save(update_fields=["status"])

        url = reverse(
            "courses:course_detail",
            kwargs={
                "pk": course.pk,
                "slug": course.slug,
            },
        )

        response = client.get(url)

        assert response.status_code == 200

    def test_published_course_uses_expected_template(
        self,
        client,
        course,
    ):
        course.status = Course.Status.PUBLISHED
        course.save(update_fields=["status"])

        url = reverse(
            "courses:course_detail",
            kwargs={
                "pk": course.pk,
                "slug": course.slug,
            },
        )

        response = client.get(url)

        assert response.status_code == 200
        assert "courses/course_detail.html" in [
            template.name for template in response.templates if template.name
        ]

    def test_detail_view_uses_expected_template_directly(
        self,
    ):
        assert CourseDetailView.template_name == ("courses/course_detail.html")

    def test_detail_view_uses_detail_view(
        self,
    ):
        assert issubclass(CourseDetailView, DetailView)

    def test_published_course_is_available_in_context(
        self,
        client,
        course,
    ):
        course.status = Course.Status.PUBLISHED
        course.save(update_fields=["status"])

        url = reverse(
            "courses:course_detail",
            kwargs={
                "pk": course.pk,
                "slug": course.slug,
            },
        )

        response = client.get(url)

        assert response.status_code == 200
        assert response.context["course"] == course
        assert response.context["object"] == course

    def test_draft_course_returns_404(
        self,
        client,
        course,
    ):
        course.status = Course.Status.DRAFT
        course.save(update_fields=["status"])

        url = reverse(
            "courses:course_detail",
            kwargs={
                "pk": course.pk,
                "slug": course.slug,
            },
        )

        response = client.get(url)

        assert response.status_code == 404

    def test_archived_course_returns_404(
        self,
        client,
        course,
    ):
        course.status = Course.Status.ARCHIVED
        course.save(update_fields=["status"])

        url = reverse(
            "courses:course_detail",
            kwargs={
                "pk": course.pk,
                "slug": course.slug,
            },
        )

        response = client.get(url)

        assert response.status_code == 404

    def test_non_published_course_is_not_returned(
        self,
        client,
        course,
    ):
        course.status = Course.Status.DRAFT
        course.save(update_fields=["status"])

        url = reverse(
            "courses:course_detail",
            kwargs={
                "pk": course.pk,
                "slug": course.slug,
            },
        )

        response = client.get(url)

        assert response.status_code == 404

    def test_nonexistent_course_returns_404(
        self,
        client,
    ):
        url = reverse(
            "courses:course_detail",
            kwargs={
                "pk": 999999,
                "slug": "does-not-exist",
            },
        )

        response = client.get(url)

        assert response.status_code == 404

    def test_course_lookup_uses_published_queryset(
        self,
        course,
    ):
        course.status = Course.Status.PUBLISHED
        course.save(update_fields=["status"])

        view = CourseDetailView()

        queryset = view.get_queryset()

        assert queryset.model is Course
        assert queryset.filter(pk=course.pk).exists()

    def test_course_lookup_excludes_draft_courses(
        self,
        course,
    ):
        course.status = Course.Status.DRAFT
        course.save(update_fields=["status"])

        view = CourseDetailView()

        queryset = view.get_queryset()

        assert not queryset.filter(pk=course.pk).exists()

    def test_course_lookup_excludes_archived_courses(
        self,
        course,
    ):
        course.status = Course.Status.ARCHIVED
        course.save(update_fields=["status"])

        view = CourseDetailView()

        queryset = view.get_queryset()

        assert not queryset.filter(pk=course.pk).exists()

    def test_detail_view_does_not_require_authentication(
        self,
        client,
        course,
    ):
        course.status = Course.Status.PUBLISHED
        course.save(update_fields=["status"])

        url = reverse(
            "courses:course_detail",
            kwargs={
                "pk": course.pk,
                "slug": course.slug,
            },
        )

        response = client.get(url)

        assert response.status_code == 200

    def test_wrong_slug_does_not_prevent_lookup_by_pk(
        self,
        client,
        course,
    ):
        course.status = Course.Status.PUBLISHED
        course.save(update_fields=["status"])

        url = reverse(
            "courses:course_detail",
            kwargs={
                "pk": course.pk,
                "slug": "different-slug",
            },
        )

        response = client.get(url)

        assert response.status_code == 200
        assert response.context["course"] == course

    def test_post_request_is_not_allowed(
        self,
        client,
        course,
    ):
        course.status = Course.Status.PUBLISHED
        course.save(update_fields=["status"])

        url = reverse(
            "courses:course_detail",
            kwargs={
                "pk": course.pk,
                "slug": course.slug,
            },
        )

        response = client.post(url)

        assert response.status_code == 405

    def test_put_request_is_not_allowed(
        self,
        client,
        course,
    ):
        course.status = Course.Status.PUBLISHED
        course.save(update_fields=["status"])

        url = reverse(
            "courses:course_detail",
            kwargs={
                "pk": course.pk,
                "slug": course.slug,
            },
        )

        response = client.put(url)

        assert response.status_code == 405

    def test_patch_request_is_not_allowed(
        self,
        client,
        course,
    ):
        course.status = Course.Status.PUBLISHED
        course.save(update_fields=["status"])

        url = reverse(
            "courses:course_detail",
            kwargs={
                "pk": course.pk,
                "slug": course.slug,
            },
        )

        response = client.patch(url)

        assert response.status_code == 405

    def test_delete_request_is_not_allowed(
        self,
        client,
        course,
    ):
        course.status = Course.Status.PUBLISHED
        course.save(update_fields=["status"])

        url = reverse(
            "courses:course_detail",
            kwargs={
                "pk": course.pk,
                "slug": course.slug,
            },
        )

        response = client.delete(url)

        assert response.status_code == 405
