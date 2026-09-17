from datetime import timedelta

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from curriculums.models.lesson import Lesson
from curriculums.models.lesson_content import LessonContent
from curriculums.models.section import Section

pytestmark = pytest.mark.django_db


class TestCourseDetailCurriculumApiView:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def published_course(self, course):
        course.status = "published"
        course.save(update_fields=["status"])

        return course

    @pytest.fixture
    def curriculum_url(self, published_course):
        return reverse(
            "courses_api:course_detail_curriculum_info",
            kwargs={
                "course_id": published_course.pk,
            },
        )

    @pytest.fixture
    def curriculum_sections(self, published_course):
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

        first_lesson = Lesson.objects.create(
            section=first_section,
            title="Lesson 1",
            order=1,
            duration=timedelta(minutes=30),
        )

        second_lesson = Lesson.objects.create(
            section=first_section,
            title="Lesson 2",
            order=2,
            duration=timedelta(minutes=45),
        )

        third_lesson = Lesson.objects.create(
            section=second_section,
            title="Lesson 3",
            order=1,
            duration=timedelta(minutes=20),
        )

        LessonContent.objects.create(
            lesson=first_lesson,
            title="Lesson 1 Content",
            content_type=LessonContent.Type.ARTICLE,
            order=1,
            is_main_content=True,
        )

        LessonContent.objects.create(
            lesson=second_lesson,
            title="Lesson 2 Content",
            content_type=LessonContent.Type.VIDEO,
            order=1,
            is_main_content=True,
        )

        LessonContent.objects.create(
            lesson=third_lesson,
            title="Lesson 3 Content",
            content_type=LessonContent.Type.ARTICLE,
            order=1,
            is_main_content=True,
        )

        return {
            "first_section": first_section,
            "second_section": second_section,
            "first_lesson": first_lesson,
            "second_lesson": second_lesson,
            "third_lesson": third_lesson,
        }

    def test_course_curriculum_can_be_retrieved(
        self,
        api_client,
        curriculum_sections,
        curriculum_url,
    ):
        response = api_client.get(curriculum_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2
        assert len(response.data["results"]) == 2

    def test_endpoint_allows_unauthenticated_requests(
        self,
        api_client,
        curriculum_sections,
        curriculum_url,
    ):
        response = api_client.get(curriculum_url)

        assert response.status_code == status.HTTP_200_OK

    def test_nonexistent_course_returns_empty_curriculum(
        self,
        api_client,
        published_course,
    ):
        nonexistent_course_id = published_course.pk + 1

        url = reverse(
            "courses_api:course_detail_curriculum_info",
            kwargs={
                "course_id": nonexistent_course_id,
            },
        )

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0
        assert response.data["results"] == []

    def test_only_sections_belonging_to_requested_course_are_returned(
        self,
        api_client,
        published_course,
        curriculum_sections,
        another_user,
        category,
    ):
        another_course = published_course.__class__.objects.create(
            title="Another Course",
            owner=another_user,
            category=category,
        )

        Section.objects.create(
            course=another_course,
            title="Other Course Section",
            order=1,
        )

        url = reverse(
            "courses_api:course_detail_curriculum_info",
            kwargs={
                "course_id": published_course.pk,
            },
        )

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

        results = response.data["results"]

        returned_titles = [section["title"] for section in results]

        assert "Other Course Section" not in returned_titles

    def test_sections_are_ordered_by_order(
        self,
        api_client,
        curriculum_sections,
        curriculum_url,
    ):
        first_section = curriculum_sections["first_section"]
        second_section = curriculum_sections["second_section"]

        response = api_client.get(curriculum_url)

        assert response.status_code == status.HTTP_200_OK

        results = response.data["results"]

        assert [section["id"] for section in results] == [
            first_section.id,
            second_section.id,
        ]

    def test_section_response_contains_expected_fields(
        self,
        api_client,
        curriculum_sections,
        curriculum_url,
    ):
        response = api_client.get(curriculum_url)

        assert response.status_code == status.HTTP_200_OK

        section = response.data["results"][0]

        assert set(section) == {
            "id",
            "title",
            "total_duration",
            "lessons_count",
            "lessons",
        }

    def test_section_title_is_serialized(
        self,
        api_client,
        curriculum_sections,
        curriculum_url,
    ):
        first_section = curriculum_sections["first_section"]

        response = api_client.get(curriculum_url)

        assert response.status_code == status.HTTP_200_OK

        section = next(
            section
            for section in response.data["results"]
            if section["id"] == first_section.id
        )

        assert section["title"] == first_section.title

    def test_lessons_count_counts_all_lessons_in_section(
        self,
        api_client,
        curriculum_sections,
        curriculum_url,
    ):
        first_section = curriculum_sections["first_section"]

        response = api_client.get(curriculum_url)

        assert response.status_code == status.HTTP_200_OK

        section = next(
            section
            for section in response.data["results"]
            if section["id"] == first_section.id
        )

        assert section["lessons_count"] == 2

    def test_section_total_duration_is_returned(
        self,
        api_client,
        curriculum_sections,
        curriculum_url,
    ):
        first_section = curriculum_sections["first_section"]

        response = api_client.get(curriculum_url)

        assert response.status_code == status.HTTP_200_OK

        section = next(
            section
            for section in response.data["results"]
            if section["id"] == first_section.id
        )

        assert section["total_duration"] is not None

    def test_section_duration_annotation_is_sum_of_lesson_durations(
        self,
        curriculum_sections,
    ):
        first_section = curriculum_sections["first_section"]

        expected_duration = timedelta(minutes=75)

        actual_duration = Lesson.objects.filter(
            section=first_section,
        ).aggregate(
            total=pytest.importorskip("django.db.models").Sum("duration"),
        )["total"]

        assert actual_duration == expected_duration

    def test_each_section_has_its_own_duration(
        self,
        api_client,
        curriculum_sections,
        curriculum_url,
    ):
        first_section = curriculum_sections["first_section"]
        second_section = curriculum_sections["second_section"]

        response = api_client.get(curriculum_url)

        assert response.status_code == status.HTTP_200_OK

        results = response.data["results"]

        first_section_data = next(
            section for section in results if section["id"] == first_section.id
        )

        second_section_data = next(
            section for section in results if section["id"] == second_section.id
        )

        assert first_section_data["total_duration"] is not None
        assert second_section_data["total_duration"] is not None

        assert (
            first_section_data["total_duration"]
            != (second_section_data["total_duration"])
        )

    def test_only_main_content_lessons_are_returned(
        self,
        api_client,
        published_course,
        curriculum_url,
    ):
        section = Section.objects.create(
            course=published_course,
            title="Section 1",
            order=1,
        )

        main_lesson = Lesson.objects.create(
            section=section,
            title="Main Lesson",
            order=1,
            duration=timedelta(minutes=30),
        )

        non_main_lesson = Lesson.objects.create(
            section=section,
            title="Non Main Lesson",
            order=2,
            duration=timedelta(minutes=20),
        )

        LessonContent.objects.create(
            lesson=main_lesson,
            title="Main Content",
            content_type=LessonContent.Type.ARTICLE,
            order=1,
            is_main_content=True,
        )

        LessonContent.objects.create(
            lesson=non_main_lesson,
            title="Non Main Content",
            content_type=LessonContent.Type.ARTICLE,
            order=1,
            is_main_content=False,
        )

        response = api_client.get(curriculum_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

        results = response.data["results"]

        assert len(results) == 1
        assert len(results[0]["lessons"]) == 1
        assert results[0]["lessons"][0]["id"] == main_lesson.id

    def test_lesson_without_main_content_is_not_returned(
        self,
        api_client,
        published_course,
        curriculum_url,
    ):
        section = Section.objects.create(
            course=published_course,
            title="Section 1",
            order=1,
        )

        Lesson.objects.create(
            section=section,
            title="Lesson Without Content",
            order=1,
            duration=timedelta(minutes=30),
        )

        response = api_client.get(curriculum_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["lessons"] == []

    def test_lessons_count_includes_lessons_without_main_content(
        self,
        api_client,
        published_course,
        curriculum_url,
    ):
        section = Section.objects.create(
            course=published_course,
            title="Section 1",
            order=1,
        )

        main_lesson = Lesson.objects.create(
            section=section,
            title="Main Lesson",
            order=1,
            duration=timedelta(minutes=30),
        )

        Lesson.objects.create(
            section=section,
            title="Lesson Without Main Content",
            order=2,
            duration=timedelta(minutes=20),
        )

        LessonContent.objects.create(
            lesson=main_lesson,
            title="Main Content",
            content_type=LessonContent.Type.ARTICLE,
            order=1,
            is_main_content=True,
        )

        response = api_client.get(curriculum_url)

        assert response.status_code == status.HTTP_200_OK

        section_data = response.data["results"][0]

        assert section_data["lessons_count"] == 2
        assert len(section_data["lessons"]) == 1

    def test_section_duration_includes_lessons_without_main_content(
        self,
        api_client,
        published_course,
        curriculum_url,
    ):
        section = Section.objects.create(
            course=published_course,
            title="Section 1",
            order=1,
        )

        main_lesson = Lesson.objects.create(
            section=section,
            title="Main Lesson",
            order=1,
            duration=timedelta(minutes=30),
        )

        Lesson.objects.create(
            section=section,
            title="Lesson Without Main Content",
            order=2,
            duration=timedelta(minutes=20),
        )

        LessonContent.objects.create(
            lesson=main_lesson,
            title="Main Content",
            content_type=LessonContent.Type.ARTICLE,
            order=1,
            is_main_content=True,
        )

        response = api_client.get(curriculum_url)

        assert response.status_code == status.HTTP_200_OK

        section_data = response.data["results"][0]

        assert section_data["lessons_count"] == 2
        assert section_data["total_duration"] is not None

    def test_lesson_response_contains_expected_fields(
        self,
        api_client,
        curriculum_sections,
        curriculum_url,
    ):
        response = api_client.get(curriculum_url)

        assert response.status_code == status.HTTP_200_OK

        lesson = response.data["results"][0]["lessons"][0]

        assert set(lesson) == {
            "id",
            "title",
            "type",
            "duration",
            "is_previewable",
            "video_url",
        }

    def test_lesson_title_is_serialized(
        self,
        api_client,
        curriculum_sections,
        curriculum_url,
    ):
        first_lesson = curriculum_sections["first_lesson"]

        response = api_client.get(curriculum_url)

        assert response.status_code == status.HTTP_200_OK

        lesson = next(
            lesson
            for section in response.data["results"]
            for lesson in section["lessons"]
            if lesson["id"] == first_lesson.id
        )

        assert lesson["title"] == first_lesson.title

    def test_lesson_type_comes_from_main_content(
        self,
        api_client,
        curriculum_sections,
        curriculum_url,
    ):
        first_lesson = curriculum_sections["first_lesson"]

        response = api_client.get(curriculum_url)

        assert response.status_code == status.HTTP_200_OK

        lesson = next(
            lesson
            for section in response.data["results"]
            for lesson in section["lessons"]
            if lesson["id"] == first_lesson.id
        )

        assert lesson["type"] == LessonContent.Type.ARTICLE

    def test_article_lesson_has_no_video_url(
        self,
        api_client,
        curriculum_sections,
        curriculum_url,
    ):
        first_lesson = curriculum_sections["first_lesson"]

        response = api_client.get(curriculum_url)

        assert response.status_code == status.HTTP_200_OK

        lesson = next(
            lesson
            for section in response.data["results"]
            for lesson in section["lessons"]
            if lesson["id"] == first_lesson.id
        )

        assert lesson["video_url"] is None

    def test_lesson_is_previewable_matches_is_preview(
        self,
        api_client,
        published_course,
        curriculum_url,
    ):
        section = Section.objects.create(
            course=published_course,
            title="Section 1",
            order=1,
        )

        lesson = Lesson.objects.create(
            section=section,
            title="Preview Lesson",
            order=1,
            duration=timedelta(minutes=30),
            is_preview=True,
        )

        LessonContent.objects.create(
            lesson=lesson,
            title="Preview Content",
            content_type=LessonContent.Type.ARTICLE,
            order=1,
            is_main_content=True,
        )

        response = api_client.get(curriculum_url)

        assert response.status_code == status.HTTP_200_OK

        lesson_data = response.data["results"][0]["lessons"][0]

        assert lesson_data["is_previewable"] is True

    def test_lesson_duration_is_serialized(
        self,
        api_client,
        curriculum_sections,
        curriculum_url,
    ):
        first_lesson = curriculum_sections["first_lesson"]

        response = api_client.get(curriculum_url)

        assert response.status_code == status.HTTP_200_OK

        lesson_data = next(
            lesson
            for section in response.data["results"]
            for lesson in section["lessons"]
            if lesson["id"] == first_lesson.id
        )

        assert lesson_data["duration"] is not None

    def test_course_without_sections_returns_empty_results(
        self,
        api_client,
        published_course,
        curriculum_url,
    ):
        response = api_client.get(curriculum_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0
        assert response.data["results"] == []

    def test_post_method_is_not_allowed(
        self,
        api_client,
        curriculum_url,
    ):
        response = api_client.post(curriculum_url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_put_method_is_not_allowed(
        self,
        api_client,
        curriculum_url,
    ):
        response = api_client.put(curriculum_url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_patch_method_is_not_allowed(
        self,
        api_client,
        curriculum_url,
    ):
        response = api_client.patch(curriculum_url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_delete_method_is_not_allowed(
        self,
        api_client,
        curriculum_url,
    ):
        response = api_client.delete(curriculum_url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
