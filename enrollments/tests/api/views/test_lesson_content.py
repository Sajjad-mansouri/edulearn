from datetime import timedelta

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from curriculums.models import (
    ArticleContent,
    Attachment,
    FileContent,
    Lesson,
    LessonContent,
    Section,
    VideoContent,
)
from enrollments.api.views import LessonContentApiView
from enrollments.models import Enrollment, LessonContentProgress, VideoProgress


@pytest.mark.django_db
class TestLessonContentApiView:
    """Tests for LessonContentApiView."""

    @pytest.fixture
    def factory(self):
        return APIRequestFactory()

    @pytest.fixture
    def section(self, course):
        return Section.objects.create(
            course=course,
            title="Django Basics",
            description="Django fundamentals",
            order=1,
            duration=timedelta(hours=1),
        )

    @pytest.fixture
    def lesson(self, section):
        return Lesson.objects.create(
            section=section,
            title="Introduction to Django",
            description="Learn Django fundamentals.",
            order=1,
            duration=timedelta(minutes=30),
            is_published=True,
            is_preview=False,
        )

    @pytest.fixture
    def article_content(self, lesson):
        content = LessonContent.objects.create(
            lesson=lesson,
            content_type=LessonContent.Type.ARTICLE,
            order=1,
            is_main_content=True,
        )

        ArticleContent.objects.create(
            content=content,
            body="<p>Django is a Python web framework.</p>",
        )

        return content

    @pytest.fixture
    def video_content(self, lesson):
        content = LessonContent.objects.create(
            lesson=lesson,
            content_type=LessonContent.Type.VIDEO,
            order=1,
            is_main_content=True,
        )

        video_file = SimpleUploadedFile(
            "django-introduction.mp4",
            b"fake-video-content",
            content_type="video/mp4",
        )

        VideoContent.objects.create(
            content=content,
            source="upload",
            video_file=video_file,
            external_url="",
            text="Django introduction",
            duration=timedelta(minutes=10),
            transcript="Django is a Python web framework.",
        )

        return content

    @pytest.fixture
    def file_content(self, lesson):
        content = LessonContent.objects.create(
            lesson=lesson,
            content_type=LessonContent.Type.FILE,
            order=1,
            is_main_content=True,
        )

        uploaded_file = SimpleUploadedFile(
            "django-notes.pdf",
            b"fake-pdf-content",
            content_type="application/pdf",
        )

        return FileContent.objects.create(
            content=content,
            file=uploaded_file,
            file_url="",
        )

    @pytest.fixture
    def attachment(self, course, article_content):
        uploaded_file = SimpleUploadedFile(
            "course-resource.pdf",
            b"attachment-content",
            content_type="application/pdf",
        )

        return Attachment.objects.create(
            course=course,
            lesson_content=article_content,
            file=uploaded_file,
        )

    def _url(self, enrollment, lesson):
        return reverse(
            "enrollment_api:lesson_content",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": lesson.id,
            },
        )

    def _authenticated_request(self, factory, user, url):
        request = factory.get(url)
        force_authenticate(request, user=user)
        return request

    def _get_response(
        self,
        factory,
        user,
        enrollment,
        lesson,
    ):
        url = self._url(enrollment, lesson)
        request = self._authenticated_request(factory, user, url)

        return LessonContentApiView.as_view()(
            request,
            enrollment_id=enrollment.id,
            lesson_id=lesson.id,
        )

    # ------------------------------------------------------------------
    # Article content
    # ------------------------------------------------------------------

    def test_get_article_content_returns_expected_response(
        self,
        factory,
        test_user,
        enrollment,
        lesson,
        article_content,
    ):
        response = self._get_response(
            factory,
            test_user,
            enrollment,
            lesson,
        )

        assert response.status_code == status.HTTP_200_OK

        assert response.data["id"] == lesson.id
        assert response.data["description"] == lesson.description
        assert response.data["resources"] == []
        assert response.data["video_progress"] == {"timestamp": 0}
        assert response.data["articleContent"] == (
            "<p>Django is a Python web framework.</p>"
        )

    def test_get_article_content_returns_lesson_description(
        self,
        factory,
        test_user,
        enrollment,
        lesson,
        article_content,
    ):
        response = self._get_response(
            factory,
            test_user,
            enrollment,
            lesson,
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["description"] == lesson.description

    def test_get_article_content_does_not_create_video_progress(
        self,
        factory,
        test_user,
        enrollment,
        lesson,
        article_content,
    ):
        response = self._get_response(
            factory,
            test_user,
            enrollment,
            lesson,
        )

        assert response.status_code == status.HTTP_200_OK

        assert not LessonContentProgress.objects.filter(
            enrollment=enrollment,
            content=article_content,
        ).exists()

        assert not VideoProgress.objects.filter(
            lesson_content_progress__enrollment=enrollment,
            lesson_content_progress__content=article_content,
        ).exists()

    # ------------------------------------------------------------------
    # Attachments
    # ------------------------------------------------------------------

    def test_get_content_returns_attachments_as_resources(
        self,
        factory,
        test_user,
        enrollment,
        lesson,
        article_content,
        attachment,
    ):
        response = self._get_response(
            factory,
            test_user,
            enrollment,
            lesson,
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["resources"]) == 1

    def test_get_content_returns_empty_resources_without_attachments(
        self,
        factory,
        test_user,
        enrollment,
        lesson,
        article_content,
    ):
        response = self._get_response(
            factory,
            test_user,
            enrollment,
            lesson,
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["resources"] == []

    # ------------------------------------------------------------------
    # File content
    # ------------------------------------------------------------------

    def test_get_file_content_returns_file_information(
        self,
        factory,
        test_user,
        enrollment,
        lesson,
        file_content,
    ):
        response = self._get_response(
            factory,
            test_user,
            enrollment,
            lesson,
        )

        assert response.status_code == status.HTTP_200_OK

        assert "fileUrl" in response.data
        assert "fileName" in response.data
        assert "fileSize" in response.data

        assert response.data["fileName"] == file_content.file.name
        assert response.data["fileSize"] == file_content.file.size

    # ------------------------------------------------------------------
    # Video content
    # ------------------------------------------------------------------

    def test_get_video_content_returns_video_url(
        self,
        factory,
        test_user,
        enrollment,
        lesson,
        video_content,
    ):
        response = self._get_response(
            factory,
            test_user,
            enrollment,
            lesson,
        )

        assert response.status_code == status.HTTP_200_OK

        assert "videoUrl" in response.data
        assert response.data["videoUrl"]
        assert response.data["video_progress"] == {"timestamp": 0}

    def test_get_video_content_creates_progress(
        self,
        factory,
        test_user,
        enrollment,
        lesson,
        video_content,
    ):
        assert not LessonContentProgress.objects.filter(
            enrollment=enrollment,
            content=video_content,
        ).exists()

        assert not VideoProgress.objects.filter(
            lesson_content_progress__enrollment=enrollment,
            lesson_content_progress__content=video_content,
        ).exists()

        response = self._get_response(
            factory,
            test_user,
            enrollment,
            lesson,
        )

        assert response.status_code == status.HTTP_200_OK

        content_progress = LessonContentProgress.objects.get(
            enrollment=enrollment,
            content=video_content,
        )

        assert content_progress.status == (LessonContentProgress.Status.IN_PROGRESS)

        video_progress = VideoProgress.objects.get(
            lesson_content_progress=content_progress,
        )

        assert video_progress.watched_seconds == 0
        assert response.data["video_progress"] == {"timestamp": 0}

    def test_get_video_content_reuses_existing_progress(
        self,
        factory,
        test_user,
        enrollment,
        lesson,
        video_content,
    ):
        content_progress = LessonContentProgress.objects.create(
            enrollment=enrollment,
            content=video_content,
            status=LessonContentProgress.Status.IN_PROGRESS,
        )

        video_progress = VideoProgress.objects.create(
            lesson_content_progress=content_progress,
            watched_seconds=125,
        )

        response = self._get_response(
            factory,
            test_user,
            enrollment,
            lesson,
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["video_progress"] == {"timestamp": 125}

        assert (
            VideoProgress.objects.filter(
                lesson_content_progress=content_progress,
            ).count()
            == 1
        )

        video_progress.refresh_from_db()

        assert video_progress.watched_seconds == 125

    # ------------------------------------------------------------------
    # Main content
    # ------------------------------------------------------------------

    def test_lesson_without_main_content_returns_404(
        self,
        factory,
        test_user,
        enrollment,
        lesson,
    ):
        LessonContent.objects.create(
            lesson=lesson,
            content_type=LessonContent.Type.ARTICLE,
            order=1,
            is_main_content=False,
        )

        response = self._get_response(
            factory,
            test_user,
            enrollment,
            lesson,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_non_main_content_is_not_used(
        self,
        factory,
        test_user,
        enrollment,
        lesson,
    ):
        content = LessonContent.objects.create(
            lesson=lesson,
            content_type=LessonContent.Type.ARTICLE,
            order=1,
            is_main_content=False,
        )

        ArticleContent.objects.create(
            content=content,
            body="This is not the main content.",
        )

        response = self._get_response(
            factory,
            test_user,
            enrollment,
            lesson,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    # ------------------------------------------------------------------
    # Lesson lookup
    # ------------------------------------------------------------------

    def test_nonexistent_lesson_returns_404(
        self,
        factory,
        test_user,
        enrollment,
    ):
        url = reverse(
            "enrollment_api:lesson_content",
            kwargs={
                "enrollment_id": enrollment.id,
                "lesson_id": 999999,
            },
        )

        request = self._authenticated_request(
            factory,
            test_user,
            url,
        )

        response = LessonContentApiView.as_view()(
            request,
            enrollment_id=enrollment.id,
            lesson_id=999999,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_lesson_from_another_course_returns_404(
        self,
        factory,
        test_user,
        enrollment,
        another_user,
        category,
    ):
        from courses.models.course import Course

        another_course = Course.objects.create(
            title="Another Django Course",
            owner=another_user,
            category=category,
        )

        another_section = Section.objects.create(
            course=another_course,
            title="Another Section",
            description="Another course section",
            order=1,
            duration=timedelta(minutes=30),
        )

        another_lesson = Lesson.objects.create(
            section=another_section,
            title="Another Lesson",
            description="Another course lesson",
            order=1,
            duration=timedelta(minutes=10),
            is_published=True,
            is_preview=False,
        )

        content = LessonContent.objects.create(
            lesson=another_lesson,
            content_type=LessonContent.Type.ARTICLE,
            order=1,
            is_main_content=True,
        )

        ArticleContent.objects.create(
            content=content,
            body="Other course content.",
        )

        response = self._get_response(
            factory,
            test_user,
            enrollment,
            another_lesson,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    # ------------------------------------------------------------------
    # Enrollment authorization
    # ------------------------------------------------------------------

    def test_another_user_cannot_use_enrollment(
        self,
        factory,
        another_user,
        enrollment,
        lesson,
        article_content,
    ):
        response = self._get_response(
            factory,
            another_user,
            enrollment,
            lesson,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize(
        "enrollment_status",
        [
            Enrollment.Status.PENDING,
            Enrollment.Status.CANCELLED,
            Enrollment.Status.SUSPENDED,
        ],
    )
    def test_ineligible_enrollment_is_forbidden(
        self,
        factory,
        test_user,
        enrollment,
        lesson,
        article_content,
        enrollment_status,
    ):
        enrollment.status = enrollment_status
        enrollment.save(update_fields=["status"])

        response = self._get_response(
            factory,
            test_user,
            enrollment,
            lesson,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_completed_enrollment_can_access_content(
        self,
        factory,
        test_user,
        enrollment,
        lesson,
        article_content,
    ):
        enrollment.status = Enrollment.Status.COMPLETED
        enrollment.save(update_fields=["status"])

        response = self._get_response(
            factory,
            test_user,
            enrollment,
            lesson,
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == lesson.id

    def test_nonexistent_enrollment_is_forbidden(
        self,
        factory,
        test_user,
        lesson,
    ):
        enrollment_id = 999999

        url = reverse(
            "enrollment_api:lesson_content",
            kwargs={
                "enrollment_id": enrollment_id,
                "lesson_id": lesson.id,
            },
        )

        request = self._authenticated_request(
            factory,
            test_user,
            url,
        )

        response = LessonContentApiView.as_view()(
            request,
            enrollment_id=enrollment_id,
            lesson_id=lesson.id,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def test_unauthenticated_user_cannot_access_content(
        self,
        factory,
        enrollment,
        lesson,
        article_content,
    ):
        url = self._url(enrollment, lesson)

        request = factory.get(url)

        response = LessonContentApiView.as_view()(
            request,
            enrollment_id=enrollment.id,
            lesson_id=lesson.id,
        )

        assert response.status_code in {
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        }

    # ------------------------------------------------------------------
    # Unsupported content type
    # ------------------------------------------------------------------

    def test_unsupported_content_type_returns_error(
        self,
        factory,
        test_user,
        enrollment,
        lesson,
    ):
        LessonContent.objects.create(
            lesson=lesson,
            content_type="unsupported",
            order=1,
            is_main_content=True,
        )

        response = self._get_response(
            factory,
            test_user,
            enrollment,
            lesson,
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == lesson.id
        assert response.data["resources"] == []
        assert response.data["video_progress"] == {"timestamp": 0}
        assert response.data["error"] == ("Unsupported content type: unsupported")
