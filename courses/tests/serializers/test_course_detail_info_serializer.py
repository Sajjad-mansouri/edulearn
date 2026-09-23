from datetime import UTC, timedelta
from decimal import Decimal

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from courses.api.serializers.course import CourseDetailInfoSerializer
from courses.models import (
    Category,
    Course,
    CourseFeature,
    LearningOutcome,
    Prerequisite,
    TargetAudience,
)
from curriculums.models import (
    Lesson,
    LessonContent,
    Section,
    VideoCaption,
    VideoContent,
)

pytestmark = pytest.mark.django_db


class TestCourseDetailInfoSerializer:
    @pytest.fixture
    def serializer_context(self):
        return {
            "best_sellers": set(),
            "now": timezone.now(),
        }

    @pytest.fixture
    def prepared_course(self, course, serializer_context):
        course.subtitle = "Master Django from beginner to advanced."
        course.description = "A complete Django development course."
        course.duration = timedelta(hours=8)
        course.published_at = serializer_context["now"]
        course.save(
            update_fields=[
                "subtitle",
                "description",
                "duration",
                "published_at",
            ]
        )

        return course

    @pytest.fixture
    def annotated_course(self, prepared_course):
        prepared_course.rating = 4.67
        prepared_course.rating_count = 25
        prepared_course.total_ratings = 25
        prepared_course.students = 100
        prepared_course.total_students = 100

        return prepared_course

    @pytest.fixture
    def serializer(self, annotated_course, serializer_context):
        return CourseDetailInfoSerializer(
            annotated_course,
            context=serializer_context,
        )

    @pytest.fixture
    def section(self, prepared_course):
        return Section.objects.create(
            course=prepared_course,
            title="Django Fundamentals",
            description="Learn the fundamentals of Django.",
            order=1,
            is_published=True,
            duration=timedelta(hours=4),
        )

    @pytest.fixture
    def lesson(self, section):
        return Lesson.objects.create(
            section=section,
            title="Introduction to Django",
            description="Introduction to Django fundamentals.",
            slug="introduction-to-django",
            order=1,
            duration=timedelta(minutes=45),
            is_published=True,
            is_preview=True,
        )

    @pytest.fixture
    def video_content(self, lesson):
        lesson_content = LessonContent.objects.create(
            lesson=lesson,
            is_main_content=True,
            title="Introduction Video",
            content_type=LessonContent.Type.VIDEO,
            order=1,
        )

        return VideoContent.objects.create(
            content=lesson_content,
            source=VideoContent.Source.URL,
            external_url="https://example.com/video.mp4",
            duration=timedelta(minutes=40),
        )

    def test_serializes_expected_fields(self, serializer):
        assert set(serializer.data.keys()) == {
            "id",
            "slug",
            "title",
            "subtitle",
            "description",
            "thumbnail",
            "price",
            "original_price",
            "price_discount",
            "level",
            "language",
            "subtitles",
            "rating",
            "total_ratings",
            "rating_count",
            "total_students",
            "last_updated",
            "category",
            "subcategory",
            "learning_outcomes",
            "prerequisites",
            "target_audience",
            "features",
            "instructor",
            "duration",
        }

    def test_serializes_course_basic_fields(
        self,
        serializer,
        prepared_course,
    ):
        data = serializer.data

        assert data["id"] == prepared_course.id
        assert data["slug"] == prepared_course.slug
        assert data["title"] == prepared_course.title
        assert data["subtitle"] == prepared_course.subtitle
        assert data["description"] == prepared_course.description
        assert data["level"] == prepared_course.level
        assert data["language"] == prepared_course.language

    def test_serializes_thumbnail(
        self,
        serializer,
        prepared_course,
    ):
        expected = prepared_course.thumbnail.url if prepared_course.thumbnail else None

        assert serializer.data["thumbnail"] == expected

    def test_serializes_category_for_root_category(
        self,
        serializer,
        category,
    ):
        assert category.parent is None
        assert serializer.data["category"] == category.name
        assert serializer.data["subcategory"] == ""

    def test_serializes_category_and_subcategory(
        self,
        test_user,
        category,
        serializer_context,
    ):
        subcategory = Category.objects.create(
            name="Django",
            slug="django",
            parent=category,
        )

        course = Course.objects.create(
            title="Django Development",
            owner=test_user,
            category=subcategory,
            subtitle="Learn Django",
            description="Django course description.",
            duration=timedelta(hours=5),
            published_at=serializer_context["now"],
        )

        # These values are normally supplied by the API queryset annotations.
        course.rating = 4.5
        course.rating_count = 10
        course.total_ratings = 10
        course.total_students = 50

        serializer = CourseDetailInfoSerializer(
            course,
            context=serializer_context,
        )

        assert serializer.data["category"] == category.name
        assert serializer.data["subcategory"] == subcategory.name

    def test_serializes_instructor(
        self,
        serializer,
        prepared_course,
    ):
        prepared_course.owner.first_name = "John"
        prepared_course.owner.last_name = "Doe"
        prepared_course.owner.save(update_fields=["first_name", "last_name"])

        assert serializer.data["instructor"] == "John Doe"

    def test_serializes_duration(
        self,
        serializer,
    ):
        assert serializer.data["duration"] == "8.0h"

    def test_serializes_rating_rounded_to_one_decimal_place(
        self,
        serializer,
    ):
        assert serializer.data["rating"] == 4.7

    def test_serializes_rating_when_rating_is_exact(
        self,
        serializer,
        annotated_course,
    ):
        annotated_course.rating = 4.0

        assert serializer.data["rating"] == 4.0

    def test_serializes_empty_string_when_rating_is_none(
        self,
        serializer,
        annotated_course,
    ):
        annotated_course.rating = None

        assert serializer.data["rating"] == ""

    def test_serializes_empty_string_when_rating_is_zero(
        self,
        serializer,
        annotated_course,
    ):
        annotated_course.rating = 0

        assert serializer.data["rating"] == ""

    def test_serializes_total_ratings(
        self,
        serializer,
        annotated_course,
    ):
        assert serializer.data["total_ratings"] == 25

    def test_serializes_rating_count(
        self,
        serializer,
        annotated_course,
    ):
        assert serializer.data["rating_count"] == 25

    def test_serializes_total_students(
        self,
        serializer,
        annotated_course,
    ):
        assert serializer.data["total_students"] == 100

    def test_serializes_learning_outcomes(
        self,
        serializer,
        prepared_course,
    ):
        LearningOutcome.objects.create(
            course=prepared_course,
            description="Build Django applications.",
            order=1,
        )
        LearningOutcome.objects.create(
            course=prepared_course,
            description="Create REST APIs with DRF.",
            order=2,
        )

        assert serializer.data["learning_outcomes"] == [
            "Build Django applications.",
            "Create REST APIs with DRF.",
        ]

    def test_serializes_empty_learning_outcomes(
        self,
        serializer,
    ):
        assert serializer.data["learning_outcomes"] == []

    def test_serializes_prerequisites(
        self,
        serializer,
        prepared_course,
    ):
        Prerequisite.objects.create(
            course=prepared_course,
            description="Basic Python knowledge.",
            order=1,
        )
        Prerequisite.objects.create(
            course=prepared_course,
            description="Basic programming knowledge.",
            order=2,
        )

        assert serializer.data["prerequisites"] == [
            "Basic Python knowledge.",
            "Basic programming knowledge.",
        ]

    def test_serializes_empty_prerequisites(
        self,
        serializer,
    ):
        assert serializer.data["prerequisites"] == []

    def test_serializes_target_audience(
        self,
        serializer,
        prepared_course,
    ):
        TargetAudience.objects.create(
            course=prepared_course,
            description="Python developers.",
            order=1,
        )
        TargetAudience.objects.create(
            course=prepared_course,
            description="Backend developers.",
            order=2,
        )

        assert serializer.data["target_audience"] == [
            "Python developers.",
            "Backend developers.",
        ]

    def test_serializes_empty_target_audience(
        self,
        serializer,
    ):
        assert serializer.data["target_audience"] == []

    def test_serializes_features(
        self,
        serializer,
        prepared_course,
    ):
        CourseFeature.objects.create(
            course=prepared_course,
            icon="video",
            text="High-quality video lessons.",
        )
        CourseFeature.objects.create(
            course=prepared_course,
            icon="project",
            text="Practical projects.",
        )

        data = serializer.data["features"]

        assert {(feature["icon"], feature["text"]) for feature in data} == {
            ("video", "High-quality video lessons."),
            ("project", "Practical projects."),
        }

    def test_serializes_empty_features(
        self,
        serializer,
    ):
        assert serializer.data["features"] == []

    def test_serializes_video_caption_languages(
        self,
        serializer,
        video_content,
    ):
        VideoCaption.objects.create(
            video=video_content,
            language="en",
            label="English",
            file=SimpleUploadedFile(
                "english.vtt",
                b"WEBVTT",
                content_type="text/vtt",
            ),
            file_format=VideoCaption.Format.VTT,
            is_default=True,
        )
        VideoCaption.objects.create(
            video=video_content,
            language="fa",
            label="Persian",
            file=SimpleUploadedFile(
                "persian.vtt",
                b"WEBVTT",
                content_type="text/vtt",
            ),
            file_format=VideoCaption.Format.VTT,
        )

        assert serializer.data["subtitles"] == {"en", "fa"}

    def test_serializes_empty_subtitles(
        self,
        serializer,
    ):
        assert serializer.data["subtitles"] == set()

    def test_subtitles_include_captions_from_course_lessons(
        self,
        serializer,
        video_content,
    ):
        VideoCaption.objects.create(
            video=video_content,
            language="en",
            label="English",
            file=SimpleUploadedFile(
                "english.vtt",
                b"WEBVTT",
                content_type="text/vtt",
            ),
            file_format=VideoCaption.Format.VTT,
            is_default=True,
        )

        assert serializer.data["subtitles"] == {"en"}

    def test_subtitles_are_unique_when_multiple_videos_use_same_language(
        self,
        serializer,
        prepared_course,
        section,
        video_content,
    ):
        VideoCaption.objects.create(
            video=video_content,
            language="en",
            label="English",
            file=SimpleUploadedFile(
                "english-1.vtt",
                b"WEBVTT",
                content_type="text/vtt",
            ),
            file_format=VideoCaption.Format.VTT,
            is_default=True,
        )

        second_lesson = Lesson.objects.create(
            section=section,
            title="Second Lesson",
            description="Second lesson.",
            slug="second-lesson",
            order=2,
            duration=timedelta(minutes=30),
            is_published=True,
            is_preview=False,
        )

        second_content = LessonContent.objects.create(
            lesson=second_lesson,
            is_main_content=True,
            title="Second Video",
            content_type=LessonContent.Type.VIDEO,
            order=1,
        )

        second_video = VideoContent.objects.create(
            content=second_content,
            source=VideoContent.Source.URL,
            external_url="https://example.com/video-2.mp4",
            duration=timedelta(minutes=25),
        )

        VideoCaption.objects.create(
            video=second_video,
            language="en",
            label="English",
            file=SimpleUploadedFile(
                "english-2.vtt",
                b"WEBVTT",
                content_type="text/vtt",
            ),
            file_format=VideoCaption.Format.VTT,
        )

        assert serializer.data["subtitles"] == {"en"}

    def test_subtitles_include_captions_from_all_course_lessons(
        self,
        serializer,
        section,
        video_content,
    ):
        VideoCaption.objects.create(
            video=video_content,
            language="en",
            label="English",
            file=SimpleUploadedFile(
                "english.vtt",
                b"WEBVTT",
                content_type="text/vtt",
            ),
            file_format=VideoCaption.Format.VTT,
            is_default=True,
        )

        second_lesson = Lesson.objects.create(
            section=section,
            title="Second Lesson",
            description="Second lesson.",
            slug="second-lesson",
            order=2,
            duration=timedelta(minutes=30),
            is_published=True,
            is_preview=False,
        )

        second_content = LessonContent.objects.create(
            lesson=second_lesson,
            is_main_content=True,
            title="Second Video",
            content_type=LessonContent.Type.VIDEO,
            order=1,
        )

        second_video = VideoContent.objects.create(
            content=second_content,
            source=VideoContent.Source.URL,
            external_url="https://example.com/video-2.mp4",
            duration=timedelta(minutes=25),
        )

        VideoCaption.objects.create(
            video=second_video,
            language="de",
            label="German",
            file=SimpleUploadedFile(
                "german.vtt",
                b"WEBVTT",
                content_type="text/vtt",
            ),
            file_format=VideoCaption.Format.VTT,
        )

        assert serializer.data["subtitles"] == {"en", "de"}

    def test_price_is_serialized(
        self,
        serializer,
        prepared_course,
        mocker,
    ):
        mocker.patch.object(
            type(prepared_course),
            "get_discounted_price",
            new_callable=mocker.PropertyMock,
            return_value=Decimal("79.99"),
        )

        assert serializer.data["price"] == Decimal("79.99")

    def test_original_price_is_serialized(
        self,
        serializer,
        prepared_course,
    ):
        assert serializer.data["original_price"] == prepared_course.original_price

    def test_price_discount_is_serialized(
        self,
        serializer,
        prepared_course,
    ):
        assert serializer.data["price_discount"] == prepared_course.price_discount

    def test_last_updated_is_serialized(
        self,
        serializer,
        prepared_course,
    ):
        serialized_last_updated = parse_datetime(serializer.data["last_updated"])

        assert serialized_last_updated is not None

        assert serialized_last_updated.astimezone(
            UTC
        ) == prepared_course.last_updated.astimezone(UTC)

    def test_serializer_does_not_modify_course(
        self,
        serializer,
        prepared_course,
    ):
        original_title = prepared_course.title
        original_description = prepared_course.description
        original_category_id = prepared_course.category_id

        prepared_course.refresh_from_db()

        assert prepared_course.title == original_title
        assert prepared_course.description == original_description
        assert prepared_course.category_id == original_category_id
