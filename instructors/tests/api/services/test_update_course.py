from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.exceptions import ValidationError

from assessments.models import (
    AcceptedAnswer,
    Assignment,
    BooleanAnswer,
    Choice,
    Question,
    QuizContent,
)
from courses.models import (
    Category,
    Course,
    CourseFeature,
    LearningOutcome,
    Prerequisite,
    Tag,
    TargetAudience,
)
from curriculums.models import (
    ArticleContent,
    Attachment,
    FileContent,
    Lesson,
    LessonCompletionCriteria,
    LessonContent,
    Section,
    VideoCaption,
    VideoContent,
)
from instructors.api.services.update_course import CourseUpdateService

User = get_user_model()


@pytest.fixture
def instructor(db):
    return User.objects.create_user(
        username="instructor",
        email="instructor@example.com",
        password="test-password",
    )


@pytest.fixture
def another_instructor(db):
    return User.objects.create_user(
        username="another-instructor",
        email="another@example.com",
        password="test-password",
    )


@pytest.fixture
def category(db):
    return Category.objects.create(
        name="Programming",
        slug="programming",
        description="Programming courses",
    )


@pytest.fixture
def another_category(db):
    return Category.objects.create(
        name="Data Science",
        slug="data-science",
        description="Data science courses",
    )


@pytest.fixture
def course(instructor, category):
    return Course.objects.create(
        owner=instructor,
        title="Django Development",
        subtitle="Original subtitle",
        short_description="Original short description",
        description="Original description",
        language=Course.LANGUAGE.ENGLISH,
        level=Course.Level.BEGINNER,
        visibility=Course.Visibility.PUBLIC,
        category=category,
        duration=timedelta(hours=10),
        price_type=Course.PriceType.PAID,
        price=100,
        price_discount=10,
        version="1.0.0",
        version_note="Original version",
        seo_title="Original SEO title",
        seo_description="Original SEO description",
    )


@pytest.fixture
def another_course(another_instructor, another_category):
    return Course.objects.create(
        owner=another_instructor,
        title="Another Course",
        category=another_category,
    )


@pytest.fixture
def deleted_ids():
    return {
        "outcomes": [],
        "prerequisites": [],
        "target_audiences": [],
        "attachments": [],
        "sections": [],
        "lessons": [],
        "captions": [],
    }


@pytest.fixture
def existing_section(course):
    return Section.objects.create(
        course=course,
        title="Original Section",
        description="Original section description",
        order=1,
        duration=timedelta(hours=2),
    )


@pytest.fixture
def existing_lesson(existing_section):
    return Lesson.objects.create(
        section=existing_section,
        title="Original Lesson",
        description="Original lesson description",
        order=1,
        duration=timedelta(minutes=30),
        is_published=False,
        is_preview=False,
    )


@pytest.fixture
def existing_article_content(existing_lesson):
    lesson_content = LessonContent.objects.create(
        lesson=existing_lesson,
        content_type=LessonContent.Type.ARTICLE,
        order=0,
    )

    ArticleContent.objects.create(
        content=lesson_content,
        body="Original article body",
    )

    return lesson_content


@pytest.fixture
def existing_criteria(existing_lesson):
    return LessonCompletionCriteria.objects.create(
        lesson=existing_lesson,
        criteria_type=LessonCompletionCriteria.CriteriaType.MANUAL,
        video_watch_percentage=None,
        quiz_passing_score=None,
    )


@pytest.fixture
def existing_course_data():
    return {
        "title": "Updated Django Development",
        "subtitle": "Updated subtitle",
        "short_description": "Updated short description",
        "description": "Updated course description",
        "language": Course.LANGUAGE.PERSIAN,
        "level": Course.Level.ADVANCED,
        "visibility": Course.Visibility.UNLISTED,
        "duration": timedelta(hours=20),
        "price_type": Course.PriceType.PAID,
        "price": Decimal("150.00"),
        "price_discount": 25,
        "version": "2.0.0",
        "version_note": "Major update",
        "seo_title": "Updated SEO title",
        "seo_description": "Updated SEO description",
    }


class TestCourseUpdateServiceCourseFields:
    def test_update_course_updates_all_provided_course_fields(
        self,
        course,
        deleted_ids,
        existing_course_data,
    ):
        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        updated_course = service.update(existing_course_data)

        updated_course.refresh_from_db()

        assert updated_course.title == "Updated Django Development"
        assert updated_course.subtitle == "Updated subtitle"
        assert updated_course.short_description == ("Updated short description")
        assert updated_course.description == "Updated course description"
        assert updated_course.language == Course.LANGUAGE.PERSIAN
        assert updated_course.level == Course.Level.ADVANCED
        assert updated_course.visibility == Course.Visibility.UNLISTED
        assert updated_course.duration == timedelta(hours=20)
        assert updated_course.price_type == Course.PriceType.PAID
        assert updated_course.price == Decimal("150.00")
        assert updated_course.price_discount == 25
        assert updated_course.version == "2.0.0"
        assert updated_course.version_note == "Major update"
        assert updated_course.seo_title == "Updated SEO title"
        assert updated_course.seo_description == ("Updated SEO description")

    def test_update_course_preserves_fields_not_provided(
        self,
        course,
        deleted_ids,
    ):
        original_values = {
            "title": course.title,
            "subtitle": course.subtitle,
            "description": course.description,
            "language": course.language,
            "level": course.level,
            "visibility": course.visibility,
            "price": course.price,
            "price_discount": course.price_discount,
            "version": course.version,
        }

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update({})

        course.refresh_from_db()

        for field, value in original_values.items():
            assert getattr(course, field) == value

    def test_update_course_updates_category(
        self,
        course,
        another_category,
        deleted_ids,
    ):
        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update(
            {
                "category": another_category,
            }
        )

        course.refresh_from_db()

        assert course.category == another_category


class TestCourseUpdateServiceFeatures:
    def test_update_features_replaces_existing_features(
        self,
        course,
        deleted_ids,
    ):
        CourseFeature.objects.create(
            course=course,
            icon="old",
            text="Old feature",
        )

        CourseFeature.objects.create(
            course=course,
            icon="old-2",
            text="Another old feature",
        )

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update(
            {
                "features": [
                    {
                        "icon": "video",
                        "text": "Updated video feature",
                    },
                    {
                        "icon": "certificate",
                        "text": "Certificate included",
                    },
                ]
            }
        )

        features = list(
            course.features.order_by("id").values_list(
                "icon",
                "text",
            )
        )

        assert features == [
            ("video", "Updated video feature"),
            ("certificate", "Certificate included"),
        ]

    def test_update_features_with_empty_list_removes_existing_features(
        self,
        course,
        deleted_ids,
    ):
        CourseFeature.objects.create(
            course=course,
            icon="video",
            text="Video feature",
        )

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update({"features": []})

        assert course.features.count() == 0


class TestCourseUpdateServiceLearningOutcomes:
    def test_update_outcomes_deletes_requested_outcomes(
        self,
        course,
        deleted_ids,
    ):
        outcome_to_delete = LearningOutcome.objects.create(
            course=course,
            description="Delete this outcome",
        )

        outcome_to_keep = LearningOutcome.objects.create(
            course=course,
            description="Keep this outcome",
        )

        deleted_ids["outcomes"] = [outcome_to_delete.pk]

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update(
            {
                "learning_outcomes": [
                    {
                        "description": "Keep this outcome",
                    }
                ]
            }
        )

        assert not LearningOutcome.objects.filter(pk=outcome_to_delete.pk).exists()

        assert LearningOutcome.objects.filter(
            pk=outcome_to_keep.pk,
            course=course,
        ).exists()

    def test_update_outcomes_creates_new_outcomes(
        self,
        course,
        deleted_ids,
    ):
        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update(
            {
                "learning_outcomes": [
                    {
                        "description": "New outcome one",
                    },
                    {
                        "description": "New outcome two",
                    },
                ]
            }
        )

        assert set(
            course.learning_outcomes.values_list(
                "description",
                flat=True,
            )
        ) == {
            "New outcome one",
            "New outcome two",
        }

    def test_update_outcomes_does_not_duplicate_same_description(
        self,
        course,
        deleted_ids,
    ):
        LearningOutcome.objects.create(
            course=course,
            description="Existing outcome",
        )

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update(
            {
                "learning_outcomes": [
                    {
                        "description": "Existing outcome",
                    },
                    {
                        "description": "Existing outcome",
                    },
                ]
            }
        )

        assert (
            LearningOutcome.objects.filter(
                course=course,
                description="Existing outcome",
            ).count()
            == 1
        )


class TestCourseUpdateServicePrerequisites:
    def test_update_prerequisite_updates_existing_record(
        self,
        course,
        deleted_ids,
    ):
        prerequisite = Prerequisite.objects.create(
            course=course,
            description="Original prerequisite",
        )

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update(
            {
                "prerequisites": [
                    {
                        "id": prerequisite.pk,
                        "description": "Updated prerequisite",
                    }
                ]
            }
        )

        prerequisite.refresh_from_db()

        assert prerequisite.description == "Updated prerequisite"

    def test_update_prerequisite_creates_new_record(
        self,
        course,
        deleted_ids,
    ):
        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update(
            {
                "prerequisites": [
                    {
                        "description": "New prerequisite",
                    }
                ]
            }
        )

        assert course.prerequisites.filter(description="New prerequisite").exists()

    def test_update_prerequisites_deletes_requested_records(
        self,
        course,
        deleted_ids,
    ):
        prerequisite = Prerequisite.objects.create(
            course=course,
            description="Delete prerequisite",
        )

        deleted_ids["prerequisites"] = [prerequisite.pk]

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update({"prerequisites": []})

        assert not Prerequisite.objects.filter(pk=prerequisite.pk).exists()

    def test_update_prerequisite_rejects_unknown_id(
        self,
        course,
        deleted_ids,
    ):
        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        with pytest.raises(
            ValidationError,
            match=r"Prerequisite with id 999999 not found",
        ):
            service.update(
                {
                    "prerequisites": [
                        {
                            "id": 999999,
                            "description": "Invalid",
                        }
                    ]
                }
            )


class TestCourseUpdateServiceTargetAudiences:
    def test_update_target_audience_updates_existing_record(
        self,
        course,
        deleted_ids,
    ):
        audience = TargetAudience.objects.create(
            course=course,
            description="Original audience",
        )

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update(
            {
                "target_audiences": [
                    {
                        "id": audience.pk,
                        "description": "Updated audience",
                    }
                ]
            }
        )

        audience.refresh_from_db()

        assert audience.description == "Updated audience"

    def test_update_target_audience_creates_new_record(
        self,
        course,
        deleted_ids,
    ):
        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update(
            {
                "target_audiences": [
                    {
                        "description": "New audience",
                    }
                ]
            }
        )

        assert course.target_audiences.filter(description="New audience").exists()

    def test_update_target_audiences_deletes_requested_records(
        self,
        course,
        deleted_ids,
    ):
        audience = TargetAudience.objects.create(
            course=course,
            description="Delete audience",
        )

        deleted_ids["target_audiences"] = [audience.pk]

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update({"target_audiences": []})

        assert not TargetAudience.objects.filter(pk=audience.pk).exists()

    def test_update_target_audience_rejects_unknown_id(
        self,
        course,
        deleted_ids,
    ):
        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        with pytest.raises(
            ValidationError,
            match=r"TargetAudience with id 999999 not found",
        ):
            service.update(
                {
                    "target_audiences": [
                        {
                            "id": 999999,
                            "description": "Invalid",
                        }
                    ]
                }
            )


class TestCourseUpdateServiceTags:
    def test_update_tags_replaces_existing_tags(
        self,
        course,
        deleted_ids,
    ):
        old_tag = Tag.objects.create(
            name="Old Tag",
            slug="old-tag",
        )

        new_tag = Tag.objects.create(
            name="New Tag",
            slug="new-tag",
        )

        course.tags.add(old_tag)

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update(
            {
                "tags": [
                    {
                        "name": new_tag.name,
                    }
                ]
            }
        )

        assert list(course.tags.values_list("name", flat=True)) == ["New Tag"]

    def test_update_tags_creates_missing_tags(
        self,
        course,
        deleted_ids,
    ):
        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update(
            {
                "tags": [
                    {
                        "name": "Django",
                    },
                    {
                        "name": "Python",
                    },
                ]
            }
        )

        assert set(course.tags.values_list("name", flat=True)) == {
            "Django",
            "Python",
        }

    def test_update_tags_with_empty_list_clears_tags(
        self,
        course,
        deleted_ids,
    ):
        tag = Tag.objects.create(
            name="Django",
            slug="django",
        )

        course.tags.add(tag)

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update({"tags": []})

        assert course.tags.count() == 0

    def test_update_without_tags_key_preserves_existing_tags(
        self,
        course,
        deleted_ids,
    ):
        tag = Tag.objects.create(
            name="Django",
            slug="django",
        )

        course.tags.add(tag)

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update({})

        assert list(course.tags.values_list("name", flat=True)) == ["Django"]


class TestCourseUpdateServiceCourseAttachments:
    def test_update_course_attachment_updates_existing_attachment(
        self,
        course,
        deleted_ids,
    ):
        old_file = SimpleUploadedFile(
            "old.pdf",
            b"old",
            content_type="application/pdf",
        )

        new_file = SimpleUploadedFile(
            "new.pdf",
            b"new",
            content_type="application/pdf",
        )

        attachment = Attachment.objects.create(
            course=course,
            file=old_file,
        )

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update(
            {
                "attachments": [
                    {
                        "id": attachment.pk,
                        "file": new_file,
                    }
                ]
            }
        )

        attachment.refresh_from_db()

        assert attachment.file
        assert "new" in attachment.file.name

    def test_update_course_attachment_creates_new_attachment(
        self,
        course,
        deleted_ids,
    ):
        new_file = SimpleUploadedFile(
            "new.pdf",
            b"new",
            content_type="application/pdf",
        )

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update(
            {
                "attachments": [
                    {
                        "file": new_file,
                    }
                ]
            }
        )

        assert (
            Attachment.objects.filter(
                course=course,
                lesson_content__isnull=True,
            ).count()
            == 1
        )

    def test_update_course_attachments_deletes_requested_attachments(
        self,
        course,
        deleted_ids,
    ):
        attachment = Attachment.objects.create(
            course=course,
            file=SimpleUploadedFile(
                "delete.pdf",
                b"delete",
                content_type="application/pdf",
            ),
        )

        deleted_ids["attachments"] = [attachment.pk]

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update({"attachments": []})

        assert not Attachment.objects.filter(pk=attachment.pk).exists()


class TestCourseUpdateServiceSections:
    def test_update_existing_section(
        self,
        course,
        existing_section,
        deleted_ids,
    ):
        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update(
            {
                "sections": [
                    {
                        "id": existing_section.pk,
                        "title": "Updated Section",
                        "description": "Updated description",
                        "duration": timedelta(hours=3),
                        "lessons": [],
                    }
                ]
            }
        )

        existing_section.refresh_from_db()

        assert existing_section.title == "Updated Section"
        assert existing_section.description == "Updated description"
        assert existing_section.duration == timedelta(hours=3)
        assert existing_section.order == 1

    def test_create_new_section(
        self,
        course,
        deleted_ids,
    ):
        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update(
            {
                "sections": [
                    {
                        "title": "New Section",
                        "description": "New section",
                        "duration": timedelta(hours=1),
                        "lessons": [],
                    }
                ]
            }
        )

        section = course.sections.get(
            title="New Section",
        )

        assert section.description == "New section"
        assert section.duration == timedelta(hours=1)
        assert section.order == 1

    def test_update_sections_deletes_requested_sections(
        self,
        course,
        existing_section,
        deleted_ids,
    ):
        deleted_ids["sections"] = [existing_section.pk]

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update({"sections": []})

        assert not Section.objects.filter(pk=existing_section.pk).exists()

    def test_update_section_rejects_unknown_id(
        self,
        course,
        deleted_ids,
    ):
        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        with pytest.raises(
            ValidationError,
            match=r"Section with id 999999 not found",
        ):
            service.update(
                {
                    "sections": [
                        {
                            "id": 999999,
                            "title": "Invalid",
                            "lessons": [],
                        }
                    ]
                }
            )

    def test_update_section_rejects_section_from_another_course(
        self,
        course,
        another_course,
        deleted_ids,
    ):
        other_section = Section.objects.create(
            course=another_course,
            title="Other Section",
            order=1,
        )

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        with pytest.raises(
            ValidationError,
            match=rf"Section with id {other_section.pk} not found",
        ):
            service.update(
                {
                    "sections": [
                        {
                            "id": other_section.pk,
                            "title": "Attempted takeover",
                            "lessons": [],
                        }
                    ]
                }
            )


class TestCourseUpdateServiceLessons:
    def test_update_existing_lesson(
        self,
        course,
        existing_section,
        existing_lesson,
        deleted_ids,
    ):
        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        payload = {
            "sections": [
                {
                    "id": existing_section.id,
                    "title": existing_section.title,
                    "description": existing_section.description,
                    "lessons": [
                        {
                            "id": existing_lesson.id,
                            "title": "Updated Lesson",
                            "description": "Updated lesson description",
                            "duration": timedelta(minutes=45),
                            "is_published": True,
                            "is_preview": True,
                        }
                    ],
                }
            ]
        }

        service.update(payload)

        existing_lesson.refresh_from_db()

        assert existing_lesson.section_id == existing_section.id
        assert existing_lesson.title == "Updated Lesson"
        assert existing_lesson.description == "Updated lesson description"
        assert existing_lesson.duration == timedelta(minutes=45)
        assert existing_lesson.is_published is True
        assert existing_lesson.is_preview is True
        assert existing_lesson.order == 1

    def test_create_new_lesson(
        self,
        course,
        existing_section,
        deleted_ids,
    ):
        service = CourseUpdateService(
            course,
            deleted_ids,
        )
        payload = {
            "sections": [
                {
                    "id": existing_section.id,
                    "title": existing_section.title,
                    "lessons": [
                        {
                            "title": "New Lesson",
                            "description": "New lesson description",
                            "duration": timedelta(minutes=20),
                            "is_published": True,
                            "is_preview": False,
                        }
                    ],
                }
            ]
        }

        service.update(payload)

        created_lesson = Lesson.objects.get(
            section=existing_section,
            title="New Lesson",
        )

        assert created_lesson.description == "New lesson description"
        assert created_lesson.duration == timedelta(minutes=20)
        assert created_lesson.order == 1
        assert created_lesson.is_published is True
        assert created_lesson.is_preview is False

    def test_update_lessons_deletes_requested_lessons(
        self,
        course,
        existing_section,
        existing_lesson,
        deleted_ids,
    ):
        deleted_ids["lessons"] = [existing_lesson.pk]

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update(
            {
                "sections": [
                    {
                        "id": existing_section.pk,
                        "lessons": [],
                    }
                ]
            }
        )

        assert not Lesson.objects.filter(pk=existing_lesson.pk).exists()

    def test_update_lesson_rejects_unknown_id(
        self,
        course,
        existing_section,
        deleted_ids,
    ):
        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        with pytest.raises(
            ValidationError,
            match=r"Lesson with id 999999 not found",
        ):
            service.update(
                {
                    "sections": [
                        {
                            "id": existing_section.pk,
                            "lessons": [
                                {
                                    "id": 999999,
                                    "title": "Invalid",
                                    "content": {},
                                }
                            ],
                        }
                    ]
                }
            )

    def test_update_lesson_rejects_lesson_from_another_course(
        self,
        course,
        another_course,
        existing_section,
        deleted_ids,
    ):
        other_section = Section.objects.create(
            course=another_course,
            title="Other Section",
            order=1,
        )

        other_lesson = Lesson.objects.create(
            section=other_section,
            title="Other Lesson",
            order=1,
        )

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        with pytest.raises(
            ValidationError,
            match=rf"Lesson with id {other_lesson.pk} not found",
        ):
            service.update(
                {
                    "sections": [
                        {
                            "id": existing_section.pk,
                            "lessons": [
                                {
                                    "id": other_lesson.pk,
                                    "title": "Takeover",
                                    "content": {},
                                }
                            ],
                        }
                    ]
                }
            )


class TestCourseUpdateServiceCompletionCriteria:
    def test_update_existing_completion_criteria(
        self,
        course,
        existing_section,
        existing_lesson,
        existing_criteria,
        deleted_ids,
    ):
        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        payload = {
            "sections": [
                {
                    "id": existing_section.id,
                    "title": existing_section.title,
                    "lessons": [
                        {
                            "id": existing_lesson.id,
                            "title": existing_lesson.title,
                            "description": existing_lesson.description,
                            "duration": existing_lesson.duration,
                            "is_published": existing_lesson.is_published,
                            "is_preview": existing_lesson.is_preview,
                            "completion_criteria": {
                                "criteria_type": "watch_video",
                                "video_watch_percentage": 90,
                                "quiz_passing_score": None,
                            },
                        }
                    ],
                }
            ]
        }

        service.update(payload)

        existing_criteria.refresh_from_db()

        assert existing_criteria.lesson_id == existing_lesson.id
        assert existing_criteria.criteria_type == "watch_video"
        assert existing_criteria.video_watch_percentage == 90
        assert existing_criteria.quiz_passing_score is None

    def test_create_completion_criteria_when_missing(
        self,
        course,
        existing_section,
        existing_lesson,
        deleted_ids,
    ):
        LessonCompletionCriteria.objects.filter(
            lesson=existing_lesson,
        ).delete()

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        payload = {
            "sections": [
                {
                    "id": existing_section.id,
                    "title": existing_section.title,
                    "lessons": [
                        {
                            "id": existing_lesson.id,
                            "title": existing_lesson.title,
                            "description": existing_lesson.description,
                            "duration": existing_lesson.duration,
                            "is_published": existing_lesson.is_published,
                            "is_preview": existing_lesson.is_preview,
                            "completion_criteria": {
                                "criteria_type": "watch_video",
                                "video_watch_percentage": 80,
                                "quiz_passing_score": None,
                            },
                        }
                    ],
                }
            ]
        }

        service.update(payload)

        criteria = LessonCompletionCriteria.objects.get(
            lesson=existing_lesson,
        )

        assert criteria.criteria_type == "watch_video"
        assert criteria.video_watch_percentage == 80
        assert criteria.quiz_passing_score is None

    def test_missing_completion_criteria_payload_preserves_existing_criteria(
        self,
        course,
        existing_section,
        existing_lesson,
        existing_criteria,
        deleted_ids,
    ):
        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        original_criteria_type = existing_criteria.criteria_type
        original_video_watch_percentage = existing_criteria.video_watch_percentage
        original_quiz_passing_score = existing_criteria.quiz_passing_score

        payload = {
            "sections": [
                {
                    "id": existing_section.id,
                    "title": existing_section.title,
                    "lessons": [
                        {
                            "id": existing_lesson.id,
                            "title": "Updated Lesson Title",
                            "description": existing_lesson.description,
                            "duration": existing_lesson.duration,
                            "is_published": existing_lesson.is_published,
                            "is_preview": existing_lesson.is_preview,
                        }
                    ],
                }
            ]
        }

        service.update(payload)

        existing_lesson.refresh_from_db()
        existing_criteria.refresh_from_db()

        assert existing_lesson.title == "Updated Lesson Title"

        assert existing_criteria.criteria_type == original_criteria_type
        assert (
            existing_criteria.video_watch_percentage == original_video_watch_percentage
        )
        assert existing_criteria.quiz_passing_score == original_quiz_passing_score


class TestCourseUpdateServiceLessonContent:
    def test_update_existing_article_content(
        self,
        course,
        existing_section,
        existing_lesson,
        existing_article_content,
        deleted_ids,
    ):
        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update(
            {
                "sections": [
                    {
                        "id": existing_section.pk,
                        "lessons": [
                            {
                                "id": existing_lesson.pk,
                                "content": {
                                    "id": existing_article_content.pk,
                                    "content_type": LessonContent.Type.ARTICLE,
                                    "article": {
                                        "body": "Updated article body",
                                    },
                                },
                            }
                        ],
                    }
                ]
            }
        )

        article = existing_article_content.article

        article.refresh_from_db()

        assert article.body == "Updated article body"

    def test_create_new_lesson_content(
        self,
        course,
        existing_section,
        existing_lesson,
        deleted_ids,
    ):
        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update(
            {
                "sections": [
                    {
                        "id": existing_section.pk,
                        "lessons": [
                            {
                                "id": existing_lesson.pk,
                                "content": {
                                    "content_type": LessonContent.Type.ARTICLE,
                                    "article": {
                                        "body": "New article",
                                    },
                                },
                            }
                        ],
                    }
                ]
            }
        )

        content = existing_lesson.content

        assert content.content_type == LessonContent.Type.ARTICLE
        assert content.article.body == "New article"

    def test_change_existing_content_type_deletes_old_specific_content(
        self,
        course,
        existing_section,
        existing_lesson,
        existing_article_content,
        deleted_ids,
    ):
        article_id = existing_article_content.article.pk

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update(
            {
                "sections": [
                    {
                        "id": existing_section.pk,
                        "lessons": [
                            {
                                "id": existing_lesson.pk,
                                "content": {
                                    "id": existing_article_content.pk,
                                    "content_type": LessonContent.Type.FILE,
                                    "file": {
                                        "file": SimpleUploadedFile(
                                            "new.pdf",
                                            b"new",
                                            content_type="application/pdf",
                                        ),
                                        "file_url": "",
                                    },
                                },
                            }
                        ],
                    }
                ]
            }
        )

        existing_article_content.refresh_from_db()

        assert existing_article_content.content_type == (LessonContent.Type.FILE)

        assert not ArticleContent.objects.filter(pk=article_id).exists()

        assert FileContent.objects.filter(content=existing_article_content).exists()

    def test_update_lesson_content_rejects_unknown_id(
        self,
        course,
        existing_section,
        existing_lesson,
        deleted_ids,
    ):
        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        with pytest.raises(
            ValidationError,
            match=r"Lesson content with id 999999 not found",
        ):
            service.update(
                {
                    "sections": [
                        {
                            "id": existing_section.pk,
                            "lessons": [
                                {
                                    "id": existing_lesson.pk,
                                    "content": {
                                        "id": 999999,
                                        "content_type": (LessonContent.Type.ARTICLE),
                                        "article": {
                                            "body": "Invalid",
                                        },
                                    },
                                }
                            ],
                        }
                    ]
                }
            )


class TestCourseUpdateServiceFileContent:
    def test_update_existing_file_content(
        self,
        course,
        existing_lesson,
        deleted_ids,
    ):
        content = LessonContent.objects.create(
            lesson=existing_lesson,
            content_type=LessonContent.Type.FILE,
            order=0,
        )

        old_file = SimpleUploadedFile(
            "old.pdf",
            b"old",
            content_type="application/pdf",
        )

        FileContent.objects.create(
            content=content,
            file=old_file,
            file_url="",
        )

        new_file = SimpleUploadedFile(
            "updated.pdf",
            b"updated",
            content_type="application/pdf",
        )

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update(
            {
                "sections": [
                    {
                        "id": existing_lesson.section_id,
                        "lessons": [
                            {
                                "id": existing_lesson.pk,
                                "content": {
                                    "id": content.pk,
                                    "content_type": LessonContent.Type.FILE,
                                    "file": {
                                        "file": new_file,
                                        "file_url": "",
                                    },
                                },
                            }
                        ],
                    }
                ]
            }
        )

        file_content = content.file
        file_content.refresh_from_db()

        assert file_content.file
        assert "updated" in file_content.file.name

    def test_create_file_content_when_missing(
        self,
        course,
        existing_lesson,
        deleted_ids,
    ):
        content = LessonContent.objects.create(
            lesson=existing_lesson,
            content_type=LessonContent.Type.FILE,
            order=0,
        )

        uploaded_file = SimpleUploadedFile(
            "material.pdf",
            b"material",
            content_type="application/pdf",
        )

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update(
            {
                "sections": [
                    {
                        "id": existing_lesson.section_id,
                        "lessons": [
                            {
                                "id": existing_lesson.pk,
                                "content": {
                                    "id": content.pk,
                                    "content_type": LessonContent.Type.FILE,
                                    "file": {
                                        "file": uploaded_file,
                                        "file_url": "",
                                    },
                                },
                            }
                        ],
                    }
                ]
            }
        )

        assert FileContent.objects.filter(content=content).exists()


class TestCourseUpdateServiceVideoContent:
    def test_update_existing_video_content(
        self,
        course,
        existing_lesson,
        deleted_ids,
    ):
        content = LessonContent.objects.create(
            lesson=existing_lesson,
            content_type=LessonContent.Type.VIDEO,
            order=0,
        )

        video = VideoContent.objects.create(
            content=content,
            source=VideoContent.Source.URL,
            external_url="https://example.com/old.mp4",
            text="Old text",
            transcript="Old transcript",
        )

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update(
            {
                "sections": [
                    {
                        "id": existing_lesson.section_id,
                        "lessons": [
                            {
                                "id": existing_lesson.pk,
                                "content": {
                                    "id": content.pk,
                                    "content_type": LessonContent.Type.VIDEO,
                                    "video": {
                                        "external_url": ("https://example.com/new.mp4"),
                                        "text": "New text",
                                        "transcript": "New transcript",
                                        "captions": [],
                                    },
                                },
                            }
                        ],
                    }
                ]
            }
        )

        video.refresh_from_db()

        assert video.source == VideoContent.Source.URL
        assert video.external_url == ("https://example.com/new.mp4")
        assert video.text == "New text"
        assert video.transcript == "New transcript"

    def test_create_video_content_when_missing(
        self,
        course,
        existing_lesson,
        deleted_ids,
    ):
        content = LessonContent.objects.create(
            lesson=existing_lesson,
            content_type=LessonContent.Type.VIDEO,
            order=0,
        )

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update(
            {
                "sections": [
                    {
                        "id": existing_lesson.section_id,
                        "lessons": [
                            {
                                "id": existing_lesson.pk,
                                "content": {
                                    "id": content.pk,
                                    "content_type": LessonContent.Type.VIDEO,
                                    "video": {
                                        "external_url": ("https://example.com/new.mp4"),
                                        "captions": [],
                                    },
                                },
                            }
                        ],
                    }
                ]
            }
        )

        assert VideoContent.objects.filter(content=content).exists()

    def test_update_video_captions_updates_existing_and_creates_new(
        self,
        course,
        existing_lesson,
        deleted_ids,
    ):
        content = LessonContent.objects.create(
            lesson=existing_lesson,
            content_type=LessonContent.Type.VIDEO,
            order=0,
        )

        video = VideoContent.objects.create(
            content=content,
            source=VideoContent.Source.URL,
            external_url="https://example.com/video.mp4",
        )

        old_caption = VideoCaption.objects.create(
            video=video,
            language="en",
            label="English",
            file=SimpleUploadedFile(
                "old.vtt",
                b"old",
                content_type="text/vtt",
            ),
            file_format=VideoCaption.Format.VTT,
            is_default=True,
        )

        new_caption_file = SimpleUploadedFile(
            "new.vtt",
            b"new",
            content_type="text/vtt",
        )

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update(
            {
                "sections": [
                    {
                        "id": existing_lesson.section_id,
                        "lessons": [
                            {
                                "id": existing_lesson.pk,
                                "content": {
                                    "id": content.pk,
                                    "content_type": LessonContent.Type.VIDEO,
                                    "video": {
                                        "external_url": (
                                            "https://example.com/video.mp4"
                                        ),
                                        "captions": [
                                            {
                                                "id": old_caption.pk,
                                                "language": "en",
                                                "label": "Updated English",
                                                "file": new_caption_file,
                                                "file_format": (
                                                    VideoCaption.Format.VTT
                                                ),
                                                "is_default": True,
                                            },
                                            {
                                                "language": "fa",
                                                "label": "Persian",
                                                "file": SimpleUploadedFile(
                                                    "fa.vtt",
                                                    b"fa",
                                                    content_type="text/vtt",
                                                ),
                                                "file_format": (
                                                    VideoCaption.Format.VTT
                                                ),
                                                "is_default": False,
                                            },
                                        ],
                                    },
                                },
                            }
                        ],
                    }
                ]
            }
        )

        old_caption.refresh_from_db()

        assert old_caption.label == "Updated English"

        assert video.captions.filter(language="fa").exists()

        assert video.captions.count() == 2

    def test_update_video_captions_deletes_requested_captions(
        self,
        course,
        existing_lesson,
        deleted_ids,
    ):
        content = LessonContent.objects.create(
            lesson=existing_lesson,
            content_type=LessonContent.Type.VIDEO,
            order=0,
        )

        video = VideoContent.objects.create(
            content=content,
            source=VideoContent.Source.URL,
            external_url="https://example.com/video.mp4",
        )

        caption = VideoCaption.objects.create(
            video=video,
            language="en",
            label="English",
            file=SimpleUploadedFile(
                "en.vtt",
                b"en",
                content_type="text/vtt",
            ),
            file_format=VideoCaption.Format.VTT,
        )

        deleted_ids["captions"] = [caption.pk]

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update(
            {
                "sections": [
                    {
                        "id": existing_lesson.section_id,
                        "lessons": [
                            {
                                "id": existing_lesson.pk,
                                "content": {
                                    "id": content.pk,
                                    "content_type": LessonContent.Type.VIDEO,
                                    "video": {
                                        "external_url": (
                                            "https://example.com/video.mp4"
                                        ),
                                        "captions": [],
                                    },
                                },
                            }
                        ],
                    }
                ]
            }
        )

        assert not VideoCaption.objects.filter(pk=caption.pk).exists()


class TestCourseUpdateServiceQuiz:
    def test_update_existing_quiz_content(
        self,
        course,
        existing_lesson,
        deleted_ids,
    ):
        content = LessonContent.objects.create(
            lesson=existing_lesson,
            content_type=LessonContent.Type.QUIZ,
            order=0,
        )

        quiz = QuizContent.objects.create(
            content=content,
            instructions="Old instructions",
            passing_score=60,
            time_limit=20,
            max_attempts=2,
            shuffle_questions=False,
            shuffle_choices=False,
            show_correct_answers=True,
        )

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update(
            {
                "sections": [
                    {
                        "id": existing_lesson.section_id,
                        "lessons": [
                            {
                                "id": existing_lesson.pk,
                                "content": {
                                    "id": content.pk,
                                    "content_type": LessonContent.Type.QUIZ,
                                    "quiz": {
                                        "instructions": "New instructions",
                                        "passing_score": 80,
                                        "time_limit": 30,
                                        "max_attempts": 3,
                                        "shuffle_questions": True,
                                        "shuffle_choices": True,
                                        "show_correct_answers": False,
                                        "questions": [],
                                    },
                                },
                            }
                        ],
                    }
                ]
            }
        )

        quiz.refresh_from_db()

        assert quiz.instructions == "New instructions"
        assert quiz.passing_score == 80
        assert quiz.time_limit == 30
        assert quiz.max_attempts == 3
        assert quiz.shuffle_questions is True
        assert quiz.shuffle_choices is True
        assert quiz.show_correct_answers is False

    def test_create_quiz_content_when_missing(
        self,
        course,
        existing_lesson,
        deleted_ids,
    ):
        content = LessonContent.objects.create(
            lesson=existing_lesson,
            content_type=LessonContent.Type.QUIZ,
            order=0,
        )

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update(
            {
                "sections": [
                    {
                        "id": existing_lesson.section_id,
                        "lessons": [
                            {
                                "id": existing_lesson.pk,
                                "content": {
                                    "id": content.pk,
                                    "content_type": LessonContent.Type.QUIZ,
                                    "quiz": {
                                        "instructions": "Quiz instructions",
                                        "passing_score": 70,
                                        "time_limit": 15,
                                        "max_attempts": 2,
                                        "questions": [],
                                    },
                                },
                            }
                        ],
                    }
                ]
            }
        )

        quiz = content.quiz

        assert quiz.instructions == "Quiz instructions"
        assert quiz.passing_score == 70
        assert quiz.time_limit == 15
        assert quiz.max_attempts == 2

    def test_update_quiz_questions_updates_existing_question(
        self,
        course,
        existing_lesson,
        deleted_ids,
    ):
        content = LessonContent.objects.create(
            lesson=existing_lesson,
            content_type=LessonContent.Type.QUIZ,
            order=0,
        )

        quiz = QuizContent.objects.create(
            content=content,
            passing_score=70,
        )

        question = Question.objects.create(
            quiz=quiz,
            text="Original question",
            question_type=Question.Type.SINGLE_CHOICE,
            difficulty=Question.Difficulty.EASY,
            points=1,
            order=1,
        )

        Choice.objects.create(
            question=question,
            text="Old choice",
            is_correct=True,
            order=1,
        )

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update(
            {
                "sections": [
                    {
                        "id": existing_lesson.section_id,
                        "lessons": [
                            {
                                "id": existing_lesson.pk,
                                "content": {
                                    "id": content.pk,
                                    "content_type": LessonContent.Type.QUIZ,
                                    "quiz": {
                                        "questions": [
                                            {
                                                "id": question.pk,
                                                "text": "Updated question",
                                                "question_type": (
                                                    Question.Type.SINGLE_CHOICE
                                                ),
                                                "difficulty": (
                                                    Question.Difficulty.MEDIUM
                                                ),
                                                "points": 3,
                                                "explanation": "Updated explanation",
                                                "is_required": False,
                                                "choices": [
                                                    {
                                                        "text": "New correct",
                                                        "is_correct": True,
                                                    },
                                                    {
                                                        "text": "New wrong",
                                                        "is_correct": False,
                                                    },
                                                ],
                                            }
                                        ]
                                    },
                                },
                            }
                        ],
                    }
                ]
            }
        )

        question.refresh_from_db()

        assert question.text == "Updated question"
        assert question.difficulty == Question.Difficulty.MEDIUM
        assert question.points == 3
        assert question.explanation == "Updated explanation"
        assert question.is_required is False

        choices = list(question.choices.order_by("order"))

        assert len(choices) == 2
        assert choices[0].text == "New correct"
        assert choices[0].is_correct is True
        assert choices[1].text == "New wrong"
        assert choices[1].is_correct is False

    def test_update_quiz_questions_creates_new_question(
        self,
        course,
        existing_lesson,
        deleted_ids,
    ):
        content = LessonContent.objects.create(
            lesson=existing_lesson,
            content_type=LessonContent.Type.QUIZ,
            order=0,
        )

        QuizContent.objects.create(
            content=content,
            passing_score=70,
        )

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update(
            {
                "sections": [
                    {
                        "id": existing_lesson.section_id,
                        "lessons": [
                            {
                                "id": existing_lesson.pk,
                                "content": {
                                    "id": content.pk,
                                    "content_type": LessonContent.Type.QUIZ,
                                    "quiz": {
                                        "questions": [
                                            {
                                                "text": "New question",
                                                "question_type": (
                                                    Question.Type.TRUE_FALSE
                                                ),
                                                "difficulty": (
                                                    Question.Difficulty.EASY
                                                ),
                                                "points": 2,
                                                "boolean_answer": {
                                                    "answer": True,
                                                },
                                            }
                                        ]
                                    },
                                },
                            }
                        ],
                    }
                ]
            }
        )

        question = content.quiz.questions.get()

        assert question.text == "New question"
        assert question.question_type == Question.Type.TRUE_FALSE
        assert question.points == 2
        assert question.boolean_answer.answer is True

    def test_update_quiz_questions_deletes_questions_not_in_payload(
        self,
        course,
        existing_lesson,
        deleted_ids,
    ):
        content = LessonContent.objects.create(
            lesson=existing_lesson,
            content_type=LessonContent.Type.QUIZ,
            order=0,
        )

        quiz = QuizContent.objects.create(
            content=content,
            passing_score=70,
        )

        question_to_keep = Question.objects.create(
            quiz=quiz,
            text="Keep",
            question_type=Question.Type.TRUE_FALSE,
            order=1,
        )

        question_to_delete = Question.objects.create(
            quiz=quiz,
            text="Delete",
            question_type=Question.Type.TRUE_FALSE,
            order=2,
        )

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update(
            {
                "sections": [
                    {
                        "id": existing_lesson.section_id,
                        "lessons": [
                            {
                                "id": existing_lesson.pk,
                                "content": {
                                    "id": content.pk,
                                    "content_type": LessonContent.Type.QUIZ,
                                    "quiz": {
                                        "questions": [
                                            {
                                                "id": question_to_keep.pk,
                                                "text": "Keep updated",
                                                "question_type": (
                                                    Question.Type.TRUE_FALSE
                                                ),
                                                "boolean_answer": {
                                                    "answer": False,
                                                },
                                            }
                                        ]
                                    },
                                },
                            }
                        ],
                    }
                ]
            }
        )

        assert Question.objects.filter(pk=question_to_keep.pk).exists()

        assert not Question.objects.filter(pk=question_to_delete.pk).exists()

    def test_update_true_false_question_replaces_boolean_answer(
        self,
        course,
        existing_section,
        existing_lesson,
        deleted_ids,
    ):
        lesson_content = LessonContent.objects.create(
            lesson=existing_lesson,
            content_type="quiz",
            order=0,
        )

        quiz = QuizContent.objects.create(
            content=lesson_content,
            instructions="Original quiz instructions",
            passing_score=70,
            time_limit=30,
            max_attempts=3,
            shuffle_questions=False,
            shuffle_choices=False,
            show_correct_answers=True,
        )

        question = Question.objects.create(
            quiz=quiz,
            text="Django is a Python web framework.",
            question_type="true_false",
            difficulty="medium",
            points=2,
            explanation="Django is implemented in Python.",
            is_required=True,
            estimated_time=timedelta(seconds=30),
            order=1,
        )

        old_boolean_answer = BooleanAnswer.objects.create(
            question=question,
            answer=True,
        )

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        payload = {
            "sections": [
                {
                    "id": existing_section.id,
                    "title": existing_section.title,
                    "lessons": [
                        {
                            "id": existing_lesson.id,
                            "title": existing_lesson.title,
                            "description": existing_lesson.description,
                            "duration": existing_lesson.duration,
                            "is_published": existing_lesson.is_published,
                            "is_preview": existing_lesson.is_preview,
                            "content": {
                                "id": lesson_content.id,
                                "content_type": "quiz",
                                "quiz": {
                                    "instructions": quiz.instructions,
                                    "passing_score": quiz.passing_score,
                                    "time_limit": quiz.time_limit,
                                    "max_attempts": quiz.max_attempts,
                                    "shuffle_questions": quiz.shuffle_questions,
                                    "shuffle_choices": quiz.shuffle_choices,
                                    "show_correct_answers": quiz.show_correct_answers,
                                    "questions": [
                                        {
                                            "id": question.id,
                                            "text": question.text,
                                            "question_type": "true_false",
                                            "difficulty": question.difficulty,
                                            "points": question.points,
                                            "explanation": question.explanation,
                                            "is_required": question.is_required,
                                            "estimated_time": question.estimated_time,
                                            "boolean_answer": {
                                                "answer": False,
                                            },
                                        }
                                    ],
                                },
                            },
                        }
                    ],
                }
            ],
        }

        service.update(payload)

        question.refresh_from_db()

        assert not BooleanAnswer.objects.filter(
            pk=old_boolean_answer.pk,
        ).exists()

        boolean_answer = BooleanAnswer.objects.get(
            question=question,
        )

        assert boolean_answer.answer is False
        assert boolean_answer.question_id == question.id

    def test_update_short_answer_question_replaces_accepted_answers(
        self,
        course,
        existing_lesson,
        deleted_ids,
    ):
        content = LessonContent.objects.create(
            lesson=existing_lesson,
            content_type=LessonContent.Type.QUIZ,
            order=0,
        )

        quiz = QuizContent.objects.create(
            content=content,
        )

        question = Question.objects.create(
            quiz=quiz,
            text="What language is Django written in?",
            question_type=Question.Type.SHORT_ANSWER,
            order=1,
        )

        AcceptedAnswer.objects.create(
            question=question,
            answer="Python",
        )

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update(
            {
                "sections": [
                    {
                        "id": existing_lesson.section_id,
                        "lessons": [
                            {
                                "id": existing_lesson.pk,
                                "content": {
                                    "id": content.pk,
                                    "content_type": LessonContent.Type.QUIZ,
                                    "quiz": {
                                        "questions": [
                                            {
                                                "id": question.pk,
                                                "text": (
                                                    "What language is Django written in?"
                                                ),
                                                "question_type": (
                                                    Question.Type.SHORT_ANSWER
                                                ),
                                                "accepted_answers": [
                                                    {
                                                        "answer": "Python",
                                                    },
                                                    {
                                                        "answer": "python",
                                                    },
                                                ],
                                            }
                                        ]
                                    },
                                },
                            }
                        ],
                    }
                ]
            }
        )

        assert list(
            question.accepted_answers.values_list(
                "answer",
                flat=True,
            )
        ) == ["Python", "python"]


class TestCourseUpdateServiceAssignment:
    def test_update_existing_assignment(
        self,
        course,
        existing_lesson,
        deleted_ids,
    ):
        content = LessonContent.objects.create(
            lesson=existing_lesson,
            content_type=LessonContent.Type.ASSIGNMENT,
            order=0,
        )

        assignment = Assignment.objects.create(
            content=content,
            instructions="Old instructions",
            passing_score=70,
            max_score=100,
            allow_late_submission=False,
            max_attempts=1,
            accepted_file_types=".pdf",
            max_file_size_mb=10,
        )

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update(
            {
                "sections": [
                    {
                        "id": existing_lesson.section_id,
                        "lessons": [
                            {
                                "id": existing_lesson.pk,
                                "content": {
                                    "id": content.pk,
                                    "content_type": (LessonContent.Type.ASSIGNMENT),
                                    "assignment": {
                                        "instructions": "Updated instructions",
                                        "max_score": 200,
                                        "allow_late_submission": True,
                                        "max_attempts": 3,
                                        "accepted_file_types": ".zip",
                                        "max_file_size_mb": 25,
                                    },
                                },
                            }
                        ],
                    }
                ]
            }
        )

        assignment.refresh_from_db()

        assert assignment.instructions == "Updated instructions"
        assert assignment.max_score == 200
        assert assignment.allow_late_submission is True
        assert assignment.max_attempts == 3
        assert assignment.accepted_file_types == ".zip"
        assert assignment.max_file_size_mb == 25

    def test_update_assignment_preserves_fields_not_provided(
        self,
        course,
        existing_lesson,
        deleted_ids,
    ):
        content = LessonContent.objects.create(
            lesson=existing_lesson,
            content_type=LessonContent.Type.ASSIGNMENT,
            order=0,
        )

        assignment = Assignment.objects.create(
            content=content,
            instructions="Original",
            max_score=100,
            max_attempts=2,
        )

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update(
            {
                "sections": [
                    {
                        "id": existing_lesson.section_id,
                        "lessons": [
                            {
                                "id": existing_lesson.pk,
                                "content": {
                                    "id": content.pk,
                                    "content_type": (LessonContent.Type.ASSIGNMENT),
                                    "assignment": {
                                        "instructions": "Updated",
                                    },
                                },
                            }
                        ],
                    }
                ]
            }
        )

        assignment.refresh_from_db()

        assert assignment.instructions == "Updated"
        assert assignment.max_score == 100
        assert assignment.max_attempts == 2

    def test_create_assignment_when_missing(
        self,
        course,
        existing_lesson,
        deleted_ids,
    ):
        content = LessonContent.objects.create(
            lesson=existing_lesson,
            content_type=LessonContent.Type.ASSIGNMENT,
            order=0,
        )

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update(
            {
                "sections": [
                    {
                        "id": existing_lesson.section_id,
                        "lessons": [
                            {
                                "id": existing_lesson.pk,
                                "content": {
                                    "id": content.pk,
                                    "content_type": (LessonContent.Type.ASSIGNMENT),
                                    "assignment": {
                                        "instructions": "New assignment",
                                        "max_score": 100,
                                        "max_attempts": 2,
                                        "allow_late_submission": True,
                                    },
                                },
                            }
                        ],
                    }
                ]
            }
        )

        assignment = content.assignment

        assert assignment.instructions == "New assignment"
        assert assignment.max_score == 100
        assert assignment.max_attempts == 2
        assert assignment.allow_late_submission is True


class TestCourseUpdateServiceLessonContentAttachments:
    def test_update_lesson_content_attachments_updates_existing_attachment(
        self,
        course,
        existing_lesson,
        deleted_ids,
    ):
        content = LessonContent.objects.create(
            lesson=existing_lesson,
            content_type=LessonContent.Type.ARTICLE,
            order=0,
        )

        old_file = SimpleUploadedFile(
            "old.pdf",
            b"old",
            content_type="application/pdf",
        )

        attachment = Attachment.objects.create(
            course=course,
            lesson_content=content,
            file=old_file,
        )

        new_file = SimpleUploadedFile(
            "new.pdf",
            b"new",
            content_type="application/pdf",
        )

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update(
            {
                "sections": [
                    {
                        "id": existing_lesson.section_id,
                        "lessons": [
                            {
                                "id": existing_lesson.pk,
                                "content": {
                                    "id": content.pk,
                                    "content_type": LessonContent.Type.ARTICLE,
                                    "article": {
                                        "body": "Updated",
                                    },
                                    "attachments": [
                                        {
                                            "id": attachment.pk,
                                            "file": new_file,
                                        }
                                    ],
                                },
                            }
                        ],
                    }
                ]
            }
        )

        attachment.refresh_from_db()

        assert attachment.file
        assert "new" in attachment.file.name

    def test_update_lesson_content_attachments_creates_new_attachment(
        self,
        course,
        existing_lesson,
        deleted_ids,
    ):
        content = LessonContent.objects.create(
            lesson=existing_lesson,
            content_type=LessonContent.Type.ARTICLE,
            order=0,
        )

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update(
            {
                "sections": [
                    {
                        "id": existing_lesson.section_id,
                        "lessons": [
                            {
                                "id": existing_lesson.pk,
                                "content": {
                                    "id": content.pk,
                                    "content_type": LessonContent.Type.ARTICLE,
                                    "article": {
                                        "body": "Updated",
                                    },
                                    "attachments": [
                                        {
                                            "file": SimpleUploadedFile(
                                                "new.pdf",
                                                b"new",
                                                content_type="application/pdf",
                                            )
                                        }
                                    ],
                                },
                            }
                        ],
                    }
                ]
            }
        )

        assert (
            Attachment.objects.filter(
                course=course,
                lesson_content=content,
            ).count()
            == 1
        )

    def test_update_lesson_content_attachments_removes_attachments_not_in_payload(
        self,
        course,
        existing_lesson,
        deleted_ids,
    ):
        content = LessonContent.objects.create(
            lesson=existing_lesson,
            content_type=LessonContent.Type.ARTICLE,
            order=0,
        )

        attachment = Attachment.objects.create(
            course=course,
            lesson_content=content,
            file=SimpleUploadedFile(
                "old.pdf",
                b"old",
                content_type="application/pdf",
            ),
        )

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update(
            {
                "sections": [
                    {
                        "id": existing_lesson.section_id,
                        "lessons": [
                            {
                                "id": existing_lesson.pk,
                                "content": {
                                    "id": content.pk,
                                    "content_type": LessonContent.Type.ARTICLE,
                                    "article": {
                                        "body": "Updated",
                                    },
                                    "attachments": [],
                                },
                            }
                        ],
                    }
                ]
            }
        )

        assert not Attachment.objects.filter(pk=attachment.pk).exists()


class TestCourseUpdateServiceTransaction:
    def test_update_is_atomic_when_later_operation_fails(
        self,
        course,
        deleted_ids,
    ):
        original_title = course.title

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        with pytest.raises(
            ValidationError,
            match="Forced update failure",
        ):
            with pytest.MonkeyPatch.context() as monkeypatch:

                def fail_after_course_update(*args, **kwargs):
                    raise ValidationError("Forced update failure")

                monkeypatch.setattr(
                    service,
                    "_update_sections",
                    fail_after_course_update,
                )

                service.update(
                    {
                        "title": "Should Roll Back",
                        "sections": [],
                    }
                )

        course.refresh_from_db()

        assert course.title == original_title

    def test_update_does_not_leave_partial_features_when_later_operation_fails(
        self,
        course,
        deleted_ids,
    ):
        CourseFeature.objects.create(
            course=course,
            icon="old",
            text="Old feature",
        )

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        with pytest.raises(
            ValidationError,
            match="Forced update failure",
        ):
            with pytest.MonkeyPatch.context() as monkeypatch:

                def fail_after_features(*args, **kwargs):
                    raise ValidationError("Forced update failure")

                monkeypatch.setattr(
                    service,
                    "_update_outcomes",
                    fail_after_features,
                )

                service.update(
                    {
                        "features": [
                            {
                                "icon": "new",
                                "text": "New feature",
                            }
                        ],
                    }
                )

        assert list(
            course.features.values_list(
                "text",
                flat=True,
            )
        ) == ["Old feature"]


class TestCourseUpdateServiceIsolation:
    def test_updating_section_cannot_modify_section_from_another_course(
        self,
        course,
        another_course,
        deleted_ids,
    ):
        other_section = Section.objects.create(
            course=another_course,
            title="Other Section",
            order=1,
        )

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        with pytest.raises(
            ValidationError,
            match=rf"Section with id {other_section.pk} not found",
        ):
            service.update(
                {
                    "sections": [
                        {
                            "id": other_section.pk,
                            "title": "Modified",
                            "lessons": [],
                        }
                    ]
                }
            )

        other_section.refresh_from_db()

        assert other_section.title == "Other Section"

    def test_updating_lesson_cannot_modify_lesson_from_another_course(
        self,
        course,
        another_course,
        deleted_ids,
    ):
        section = Section.objects.create(
            course=course,
            title="Current Course Section",
            order=1,
        )

        other_section = Section.objects.create(
            course=another_course,
            title="Other Section",
            order=1,
        )

        other_lesson = Lesson.objects.create(
            section=other_section,
            title="Other Lesson",
            order=1,
        )

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        payload = {
            "sections": [
                {
                    "id": section.id,
                    "title": section.title,
                    "description": section.description,
                    "lessons": [
                        {
                            "id": other_lesson.id,
                            "title": "Attempted Modification",
                            "description": "This must not be allowed.",
                        }
                    ],
                }
            ],
        }

        assert section.course_id == course.id
        assert other_lesson.section.course_id == another_course.id
        assert other_lesson.section.course_id != course.id

        with pytest.raises(
            ValidationError,
            match=rf"Lesson with id {other_lesson.pk} not found",
        ):
            service.update(payload)

        other_lesson.refresh_from_db()

        assert other_lesson.title == "Other Lesson"
        assert other_lesson.description == ""

    def test_deleting_outcome_from_another_course_does_not_delete_it(
        self,
        course,
        another_course,
        deleted_ids,
    ):
        other_outcome = LearningOutcome.objects.create(
            course=another_course,
            description="Other course outcome",
        )

        deleted_ids["outcomes"] = [other_outcome.pk]

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update({})

        assert LearningOutcome.objects.filter(pk=other_outcome.pk).exists()

    def test_deleting_prerequisite_from_another_course_does_not_delete_it(
        self,
        course,
        another_course,
        deleted_ids,
    ):
        other_prerequisite = Prerequisite.objects.create(
            course=another_course,
            description="Other prerequisite",
        )

        deleted_ids["prerequisites"] = [other_prerequisite.pk]

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update({})

        assert Prerequisite.objects.filter(pk=other_prerequisite.pk).exists()

    def test_deleting_target_audience_from_another_course_does_not_delete_it(
        self,
        course,
        another_course,
        deleted_ids,
    ):
        other_audience = TargetAudience.objects.create(
            course=another_course,
            description="Other audience",
        )

        deleted_ids["target_audiences"] = [other_audience.pk]

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update({})

        assert TargetAudience.objects.filter(pk=other_audience.pk).exists()

    def test_deleting_attachment_from_another_course_does_not_delete_it(
        self,
        course,
        another_course,
        deleted_ids,
    ):
        other_attachment = Attachment.objects.create(
            course=another_course,
            file=SimpleUploadedFile(
                "other.pdf",
                b"other",
                content_type="application/pdf",
            ),
        )

        deleted_ids["attachments"] = [other_attachment.pk]

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update({})

        assert Attachment.objects.filter(pk=other_attachment.pk).exists()

    def test_deleting_section_from_another_course_does_not_delete_it(
        self,
        course,
        another_course,
        deleted_ids,
    ):
        other_section = Section.objects.create(
            course=another_course,
            title="Other Section",
            order=1,
        )

        deleted_ids["sections"] = [other_section.pk]

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update({})

        assert Section.objects.filter(pk=other_section.pk).exists()

    def test_deleting_lesson_from_another_course_does_not_delete_it(
        self,
        course,
        another_course,
        deleted_ids,
    ):
        other_section = Section.objects.create(
            course=another_course,
            title="Other Section",
            order=1,
        )

        other_lesson = Lesson.objects.create(
            section=other_section,
            title="Other Lesson",
            order=1,
        )

        deleted_ids["lessons"] = [other_lesson.pk]

        service = CourseUpdateService(
            course,
            deleted_ids,
        )

        service.update({})

        assert Lesson.objects.filter(pk=other_lesson.pk).exists()
