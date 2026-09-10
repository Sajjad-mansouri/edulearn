import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from courses.models.course import Course
from curriculums.models.lesson import Lesson
from curriculums.models.section import Section
from enrollments.models.bookmark import CourseLessonBookmark
from enrollments.models.enrollment import Enrollment

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestCourseLessonBookmarkFixtures:
    @pytest.fixture
    def test_user(self):
        return User.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test-password",
        )

    @pytest.fixture
    def course(self, test_user):
        return Course.objects.create(
            title="Django Development",
            owner=test_user,
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

    @pytest.fixture
    def bookmark(self, enrollment, lesson):
        return CourseLessonBookmark.objects.create(
            enrollment=enrollment,
            lesson=lesson,
        )


class TestCourseLessonBookmarkCreation(TestCourseLessonBookmarkFixtures):
    def test_bookmark_can_be_created(self, enrollment, lesson):
        bookmark = CourseLessonBookmark.objects.create(
            enrollment=enrollment,
            lesson=lesson,
        )

        assert bookmark.pk is not None
        assert bookmark.enrollment == enrollment
        assert bookmark.lesson == lesson

    def test_enrollment_is_required(self, lesson):
        bookmark = CourseLessonBookmark(lesson=lesson)

        with pytest.raises(ValidationError) as exc_info:
            bookmark.full_clean()

        assert "enrollment" in exc_info.value.message_dict

    def test_lesson_is_required(self, enrollment):
        bookmark = CourseLessonBookmark(enrollment=enrollment)

        with pytest.raises(ValidationError) as exc_info:
            bookmark.full_clean()

        assert "lesson" in exc_info.value.message_dict


class TestCourseLessonBookmarkStringRepresentation(TestCourseLessonBookmarkFixtures):
    def test_str_returns_expected_value(
        self,
        bookmark,
        test_user,
        lesson,
    ):
        assert str(bookmark) == (
            f"{test_user.username} bookmark '{lesson.title}' lesson"
        )


class TestCourseLessonBookmarkRelationships(TestCourseLessonBookmarkFixtures):
    def test_enrollment_has_reverse_bookmarks_relation(
        self,
        enrollment,
        bookmark,
    ):
        assert bookmark in enrollment.bookmarks.all()

    def test_lesson_has_reverse_bookmarks_relation(
        self,
        lesson,
        bookmark,
    ):
        assert bookmark in lesson.bookmarks.all()

    def test_multiple_lessons_can_be_bookmarked_for_same_enrollment(
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

        first_bookmark = CourseLessonBookmark.objects.create(
            enrollment=enrollment,
            lesson=lesson,
        )
        second_bookmark = CourseLessonBookmark.objects.create(
            enrollment=enrollment,
            lesson=second_lesson,
        )

        assert enrollment.bookmarks.count() == 2
        assert first_bookmark in enrollment.bookmarks.all()
        assert second_bookmark in enrollment.bookmarks.all()

    def test_same_lesson_can_be_bookmarked_by_different_enrollments(
        self,
        enrollment,
        test_user,
        course,
        lesson,
    ):
        another_user = User.objects.create_user(
            username="another_user",
            email="another_user@example.com",
            password="test-password",
        )

        another_enrollment = Enrollment.objects.create(
            user=another_user,
            course=course,
        )

        first_bookmark = CourseLessonBookmark.objects.create(
            enrollment=enrollment,
            lesson=lesson,
        )
        second_bookmark = CourseLessonBookmark.objects.create(
            enrollment=another_enrollment,
            lesson=lesson,
        )

        assert first_bookmark.pk != second_bookmark.pk
        assert lesson.bookmarks.count() == 2


class TestCourseLessonBookmarkDeletion(TestCourseLessonBookmarkFixtures):
    def test_deleting_enrollment_deletes_bookmarks(
        self,
        enrollment,
        bookmark,
    ):
        bookmark_id = bookmark.pk

        enrollment.delete()

        assert not CourseLessonBookmark.objects.filter(pk=bookmark_id).exists()

    def test_deleting_lesson_deletes_bookmarks(
        self,
        lesson,
        bookmark,
    ):
        bookmark_id = bookmark.pk

        lesson.delete()

        assert not CourseLessonBookmark.objects.filter(pk=bookmark_id).exists()


class TestCourseLessonBookmarkUpdate(TestCourseLessonBookmarkFixtures):
    def test_bookmark_lesson_can_be_changed(
        self,
        bookmark,
        section,
    ):
        new_lesson = Lesson.objects.create(
            section=section,
            title="New Lesson",
            slug="new-lesson",
            order=2,
        )

        bookmark.lesson = new_lesson
        bookmark.save()

        bookmark.refresh_from_db()

        assert bookmark.lesson == new_lesson

    def test_bookmark_enrollment_can_be_changed(
        self,
        bookmark,
        test_user,
        course,
        lesson,
    ):
        another_user = User.objects.create_user(
            username="another_user",
            email="another_user@example.com",
            password="test-password",
        )

        another_enrollment = Enrollment.objects.create(
            user=another_user,
            course=course,
        )

        bookmark.enrollment = another_enrollment
        bookmark.save()

        bookmark.refresh_from_db()

        assert bookmark.enrollment == another_enrollment
