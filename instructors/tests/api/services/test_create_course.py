from copy import deepcopy
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from assessments.models import (
    Assignment,
    BooleanAnswer,
    Question,
    QuizContent,
)
from courses.models import (
    Category,
    Course,
    Tag,
)
from curriculums.models import (
    Attachment,
    Lesson,
    LessonCompletionCriteria,
    LessonContent,
    Section,
    VideoCaption,
    VideoContent,
)
from instructors.api.services.create_course import CourseService

User = get_user_model()


@pytest.fixture
def instructor(db):
    return User.objects.create_user(
        username="instructor",
        email="instructor@example.com",
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
def course_data():
    syllabus = SimpleUploadedFile(
        "syllabus.pdf",
        b"course syllabus",
        content_type="application/pdf",
    )

    material = SimpleUploadedFile(
        "material.pdf",
        b"lesson material",
        content_type="application/pdf",
    )

    reference = SimpleUploadedFile(
        "reference.pdf",
        b"lesson reference",
        content_type="application/pdf",
    )

    SimpleUploadedFile(
        "lesson-video.mp4",
        b"video content",
        content_type="video/mp4",
    )

    caption_en = SimpleUploadedFile(
        "english.vtt",
        b"WEBVTT",
        content_type="text/vtt",
    )

    caption_fa = SimpleUploadedFile(
        "persian.vtt",
        b"WEBVTT",
        content_type="text/vtt",
    )

    return {
        "title": "Django Development",
        "subtitle": "Build professional Django applications",
        "short_description": "Learn Django from fundamentals to advanced topics.",
        "description": "A complete Django development course.",
        "thumbnail": None,
        "promotional_video": "",
        "course_trailer": "",
        "language": Course.LANGUAGE.ENGLISH,
        "level": Course.Level.INTERMEDIATE,
        "visibility": Course.Visibility.PUBLIC,
        "category": None,
        "duration": timedelta(hours=12),
        "price_type": Course.PriceType.PAID,
        "price": 100,
        "price_discount": 20,
        "version": "1.0.0",
        "version_note": "Initial release",
        "seo_title": "",
        "seo_description": "",
        "tags": [
            {"name": "Django"},
            {"name": "Python"},
        ],
        "attachments": [
            {"file": syllabus},
        ],
        "sections": [
            {
                "title": "Django Fundamentals",
                "description": "Learn the fundamentals of Django.",
                "duration": timedelta(hours=4),
                "lessons": [
                    {
                        "title": "Introduction to Django",
                        "description": "Introduction to Django and its architecture.",
                        "duration": 30,
                        "is_published": True,
                        "is_preview": True,
                        "completion_criteria": {
                            "criteria_type": (
                                LessonCompletionCriteria.CriteriaType.MANUAL
                            ),
                            "video_watch_percentage": None,
                            "quiz_passing_score": None,
                        },
                        "content": {
                            "content_type": LessonContent.Type.ARTICLE,
                            "article": {
                                "body": "Django is a Python web framework.",
                            },
                            "attachments": [
                                {"file": reference},
                            ],
                        },
                    },
                    {
                        "title": "Django Models",
                        "description": "Learn Django models and ORM.",
                        "duration": 45,
                        "is_published": True,
                        "is_preview": False,
                        "completion_criteria": {
                            "criteria_type": (
                                LessonCompletionCriteria.CriteriaType.WATCH_VIDEO
                            ),
                            "video_watch_percentage": 80,
                            "quiz_passing_score": None,
                        },
                        "content": {
                            "content_type": LessonContent.Type.VIDEO,
                            "video": {
                                "external_url": (
                                    "https://example.com/django-models.mp4"
                                ),
                                "video_file": None,
                                "text": "Video transcript text",
                                "transcript": "Full transcript",
                                "captions": [
                                    {
                                        "language": "en",
                                        "label": "English",
                                        "file": caption_en,
                                        "file_format": VideoCaption.Format.VTT,
                                        "is_default": True,
                                    },
                                    {
                                        "language": "fa",
                                        "label": "Persian",
                                        "file": caption_fa,
                                        "file_format": VideoCaption.Format.VTT,
                                        "is_default": False,
                                    },
                                ],
                            },
                            "attachments": [],
                        },
                    },
                    {
                        "title": "Django Files",
                        "description": "Learn how to work with uploaded files.",
                        "duration": 25,
                        "is_published": False,
                        "is_preview": False,
                        "completion_criteria": {
                            "criteria_type": (
                                LessonCompletionCriteria.CriteriaType.READ_ARTICLE
                            ),
                            "video_watch_percentage": None,
                            "quiz_passing_score": None,
                        },
                        "content": {
                            "content_type": LessonContent.Type.FILE,
                            "file": {
                                "file": material,
                                "file_url": "",
                            },
                            "attachments": [],
                        },
                    },
                    {
                        "title": "Django Quiz",
                        "description": "Test Django knowledge.",
                        "duration": 20,
                        "is_published": True,
                        "is_preview": False,
                        "completion_criteria": {
                            "criteria_type": (
                                LessonCompletionCriteria.CriteriaType.PASS_QUIZ
                            ),
                            "video_watch_percentage": None,
                            "quiz_passing_score": 70,
                        },
                        "content": {
                            "content_type": LessonContent.Type.QUIZ,
                            "quiz": {
                                "instructions": "Answer all questions.",
                                "passing_score": 70,
                                "time_limit": 30,
                                "max_attempts": 3,
                                "shuffle_questions": True,
                                "shuffle_choices": True,
                                "show_correct_answers": True,
                                "questions": [
                                    {
                                        "text": "Which language is Django written in?",
                                        "question_type": Question.Type.SINGLE_CHOICE,
                                        "difficulty": Question.Difficulty.EASY,
                                        "points": 2,
                                        "explanation": "Django is written in Python.",
                                        "is_required": True,
                                        "estimated_time": timedelta(minutes=1),
                                        "choices": [
                                            {
                                                "text": "Python",
                                                "is_correct": True,
                                            },
                                            {
                                                "text": "Java",
                                                "is_correct": False,
                                            },
                                            {
                                                "text": "Go",
                                                "is_correct": False,
                                            },
                                        ],
                                    },
                                    {
                                        "text": "Which are Python web frameworks?",
                                        "question_type": Question.Type.MULTIPLE_CHOICE,
                                        "difficulty": Question.Difficulty.MEDIUM,
                                        "points": 3,
                                        "explanation": "Django and Flask are Python web frameworks.",
                                        "is_required": True,
                                        "estimated_time": timedelta(minutes=2),
                                        "choices": [
                                            {
                                                "text": "Django",
                                                "is_correct": True,
                                            },
                                            {
                                                "text": "Flask",
                                                "is_correct": True,
                                            },
                                            {
                                                "text": "Laravel",
                                                "is_correct": False,
                                            },
                                        ],
                                    },
                                    {
                                        "text": "Django is a Python framework.",
                                        "question_type": Question.Type.TRUE_FALSE,
                                        "difficulty": Question.Difficulty.EASY,
                                        "points": 1,
                                        "explanation": "Django is written in Python.",
                                        "is_required": True,
                                        "estimated_time": timedelta(minutes=1),
                                        "boolean_answer": {
                                            "answer": True,
                                        },
                                    },
                                    {
                                        "text": "Name the language Django is written in.",
                                        "question_type": Question.Type.SHORT_ANSWER,
                                        "difficulty": Question.Difficulty.EASY,
                                        "points": 2,
                                        "explanation": "Django is written in Python.",
                                        "is_required": True,
                                        "estimated_time": timedelta(minutes=1),
                                        "accepted_answers": [
                                            {"answer": "Python"},
                                            {"answer": "python"},
                                        ],
                                    },
                                ],
                            },
                            "attachments": [],
                        },
                    },
                    {
                        "title": "Final Assignment",
                        "description": "Build a Django application.",
                        "duration": 60,
                        "is_published": True,
                        "is_preview": False,
                        "completion_criteria": {
                            "criteria_type": (
                                LessonCompletionCriteria.CriteriaType.SUBMIT_ASSIGNMENT
                            ),
                            "video_watch_percentage": None,
                            "quiz_passing_score": None,
                        },
                        "content": {
                            "content_type": LessonContent.Type.ASSIGNMENT,
                            "assignment": {
                                "instructions": "Build a Django project.",
                                "passing_score": 80,
                                "max_score": 100,
                                "due_date": None,
                                "allow_late_submission": True,
                                "max_attempts": 2,
                                "accepted_file_types": ".zip,.pdf",
                                "max_file_size_mb": 25,
                            },
                            "attachments": [],
                        },
                    },
                ],
            },
        ],
        "features": [
            {
                "icon": "video",
                "text": "12 hours of video content",
            },
            {
                "icon": "certificate",
                "text": "Certificate of completion",
            },
        ],
        "target_audiences": [
            {"description": "Python developers"},
            {"description": "Web developers"},
        ],
        "prerequisites": [
            {"description": "Basic Python knowledge"},
            {"description": "Basic programming knowledge"},
        ],
        "learning_outcomes": [
            {"description": "Build Django applications"},
            {"description": "Use Django ORM effectively"},
        ],
    }


class TestCourseServiceCreate:
    def test_create_course_creates_basic_fields(
        self,
        instructor,
        category,
        course_data,
    ):
        data = deepcopy(course_data)
        data["category"] = category

        course = CourseService(instructor).create(data)

        assert course.owner == instructor
        assert course.title == "Django Development"
        assert course.subtitle == "Build professional Django applications"
        assert (
            course.short_description
            == "Learn Django from fundamentals to advanced topics."
        )
        assert course.description == "A complete Django development course."
        assert course.language == Course.LANGUAGE.ENGLISH
        assert course.level == Course.Level.INTERMEDIATE
        assert course.visibility == Course.Visibility.PUBLIC
        assert course.category == category
        assert course.duration == timedelta(hours=12)
        assert course.price_type == Course.PriceType.PAID
        assert course.price == 100
        assert course.price_discount == 20
        assert course.version == "1.0.0"
        assert course.version_note == "Initial release"
        assert course.promotional_video == ""
        assert course.course_trailer == ""

    def test_create_course_sets_slug_and_seo_defaults(
        self,
        instructor,
        course_data,
    ):
        course = CourseService(instructor).create(course_data)

        assert course.slug == "django-development"
        assert course.seo_title == "Django Development"
        assert course.seo_description == "A complete Django development course."

    def test_create_course_preserves_explicit_seo_values(
        self,
        instructor,
        course_data,
    ):
        data = deepcopy(course_data)
        data["seo_title"] = "Custom Django SEO Title"
        data["seo_description"] = "Custom Django SEO description."

        course = CourseService(instructor).create(data)

        assert course.seo_title == "Custom Django SEO Title"
        assert course.seo_description == "Custom Django SEO description."

    def test_create_course_creates_tags(
        self,
        instructor,
        course_data,
    ):
        course = CourseService(instructor).create(course_data)

        assert set(course.tags.values_list("name", flat=True)) == {
            "Django",
            "Python",
        }

    def test_create_course_reuses_existing_tags(
        self,
        instructor,
        course_data,
    ):
        existing_tag = Tag.objects.create(
            name="Django",
            slug="django",
        )

        course = CourseService(instructor).create(course_data)

        assert course.tags.count() == 2
        assert course.tags.get(name="Django").pk == existing_tag.pk
        assert Tag.objects.filter(name="Django").count() == 1

    def test_create_course_without_tags_key(
        self,
        instructor,
        course_data,
    ):
        data = deepcopy(course_data)
        data.pop("tags")

        course = CourseService(instructor).create(data)

        assert course.tags.count() == 0

    def test_create_course_with_empty_tags(
        self,
        instructor,
        course_data,
    ):
        data = deepcopy(course_data)
        data["tags"] = []

        course = CourseService(instructor).create(data)

        assert course.tags.count() == 0

    def test_create_course_creates_course_attachments(
        self,
        instructor,
        course_data,
    ):
        course = CourseService(instructor).create(course_data)

        attachments = Attachment.objects.filter(
            course=course,
            lesson_content__isnull=True,
        )

        assert attachments.count() == len(course_data["attachments"])

        attachment = attachments.get()

        assert Path(attachment.file.name).stem.startswith("syllabus")
        assert Path(attachment.file.name).suffix == ".pdf"

        expected_directory = f"courses/{instructor.pk}/{course.pk}/attachments/"
        assert Path(attachment.file.name).parent.as_posix() == (
            expected_directory.rstrip("/")
        )

    def test_create_course_creates_sections(
        self,
        instructor,
        course_data,
    ):
        course = CourseService(instructor).create(course_data)

        sections = list(course.sections.all())

        assert len(sections) == 1

        section = sections[0]

        assert section.title == "Django Fundamentals"
        assert section.description == "Learn the fundamentals of Django."
        assert section.order == 1
        assert section.duration == timedelta(hours=4)

    def test_create_course_creates_lessons(
        self,
        instructor,
        course_data,
    ):
        course = CourseService(instructor).create(course_data)

        section = course.sections.get()

        lessons = list(section.lessons.order_by("order"))

        assert len(lessons) == 5

        assert lessons[0].title == "Introduction to Django"
        assert lessons[0].order == 1
        assert lessons[0].duration == timedelta(minutes=30)
        assert lessons[0].is_published is True
        assert lessons[0].is_preview is True

        assert lessons[1].title == "Django Models"
        assert lessons[1].order == 2
        assert lessons[1].duration == timedelta(minutes=45)
        assert lessons[1].is_published is True
        assert lessons[1].is_preview is False

        assert lessons[2].title == "Django Files"
        assert lessons[2].order == 3
        assert lessons[2].duration == timedelta(minutes=25)
        assert lessons[2].is_published is False

    def test_create_course_creates_completion_criteria(
        self,
        instructor,
        course_data,
    ):
        course = CourseService(instructor).create(course_data)

        lessons = list(
            Lesson.objects.filter(
                section__course=course,
            ).order_by("order")
        )

        criteria = [lesson.completion_criteria for lesson in lessons]

        assert criteria[0].criteria_type == (
            LessonCompletionCriteria.CriteriaType.MANUAL
        )
        assert criteria[0].video_watch_percentage is None
        assert criteria[0].quiz_passing_score is None

        assert criteria[1].criteria_type == (
            LessonCompletionCriteria.CriteriaType.WATCH_VIDEO
        )
        assert criteria[1].video_watch_percentage == 80
        assert criteria[1].quiz_passing_score is None

        assert criteria[2].criteria_type == (
            LessonCompletionCriteria.CriteriaType.READ_ARTICLE
        )
        assert criteria[2].video_watch_percentage is None
        assert criteria[2].quiz_passing_score is None

        assert criteria[3].criteria_type == (
            LessonCompletionCriteria.CriteriaType.PASS_QUIZ
        )
        assert criteria[3].quiz_passing_score == 70
        assert criteria[3].video_watch_percentage is None

        assert criteria[4].criteria_type == (
            LessonCompletionCriteria.CriteriaType.SUBMIT_ASSIGNMENT
        )
        assert criteria[4].video_watch_percentage is None
        assert criteria[4].quiz_passing_score is None

    def test_create_course_creates_article_content(
        self,
        instructor,
        course_data,
    ):
        course = CourseService(instructor).create(course_data)

        lesson = Lesson.objects.get(
            section__course=course,
            title="Introduction to Django",
        )

        content = lesson.content

        assert content.content_type == LessonContent.Type.ARTICLE

        article = content.article

        assert article.body == "Django is a Python web framework."

    def test_create_course_creates_article_content_attachment(
        self,
        instructor,
        course_data,
    ):
        course = CourseService(instructor).create(course_data)

        lesson = Lesson.objects.get(
            section__course=course,
            title="Introduction to Django",
        )

        content = lesson.content

        attachments = content.attachments.all()

        assert attachments.count() == 1

        attachment = attachments.get()

        assert attachment.course_id == course.pk
        assert attachment.lesson_content_id == content.pk
        assert Path(attachment.file.name).stem.startswith("reference")
        assert Path(attachment.file.name).suffix == ".pdf"

        expected_directory = (
            f"courses/{instructor.pk}/{course.pk}/"
            f"lesson_contents/{content.pk}/attachments"
        )

        assert Path(attachment.file.name).parent.as_posix() == (expected_directory)

    def test_create_course_creates_video_content_from_url(
        self,
        instructor,
        course_data,
    ):
        course = CourseService(instructor).create(course_data)

        lesson = Lesson.objects.get(
            section__course=course,
            title="Django Models",
        )

        video = lesson.content.video

        assert video.source == VideoContent.Source.URL
        assert video.external_url == ("https://example.com/django-models.mp4")
        assert not video.video_file
        assert video.text == "Video transcript text"
        assert video.transcript == "Full transcript"

    def test_create_course_creates_video_captions(
        self,
        instructor,
        course_data,
    ):
        course = CourseService(instructor).create(course_data)

        lesson = Lesson.objects.get(
            section__course=course,
            title="Django Models",
        )

        video = lesson.content.video

        captions = list(video.captions.order_by("language"))

        assert len(captions) == 2

        english = next(caption for caption in captions if caption.language == "en")
        persian = next(caption for caption in captions if caption.language == "fa")

        assert english.label == "English"
        assert english.file_format == VideoCaption.Format.VTT
        assert english.is_default is True

        assert persian.label == "Persian"
        assert persian.file_format == VideoCaption.Format.VTT
        assert persian.is_default is False

    def test_create_course_creates_video_content_from_file(
        self,
        instructor,
        course_data,
    ):
        data = deepcopy(course_data)

        video_file = SimpleUploadedFile(
            "uploaded-video.mp4",
            b"video",
            content_type="video/mp4",
        )

        video_data = data["sections"][0]["lessons"][1]["content"]["video"]

        video_data["external_url"] = ""
        video_data["video_file"] = video_file
        video_data["captions"] = []

        course = CourseService(instructor).create(data)

        lesson = Lesson.objects.get(
            section__course=course,
            title="Django Models",
        )

        video = lesson.content.video

        assert video.source == VideoContent.Source.FILE
        assert video.external_url == ""
        assert video.video_file

        assert Path(video.video_file.name).stem.startswith("uploaded-video")
        assert Path(video.video_file.name).suffix == ".mp4"

    def test_create_course_creates_file_content(
        self,
        instructor,
        course_data,
    ):
        course = CourseService(instructor).create(course_data)

        lesson = Lesson.objects.get(
            section__course=course,
            title="Django Files",
        )

        file_content = lesson.content.file

        assert file_content.file
        assert file_content.file_url == ""

        assert Path(file_content.file.name).stem.startswith("material")
        assert Path(file_content.file.name).suffix == ".pdf"

        expected_directory = (
            f"courses/{instructor.pk}/{course.pk}/"
            f"lesson_contents/{lesson.content.pk}/file"
        )

        assert Path(file_content.file.name).parent.as_posix() == (expected_directory)

    def test_create_course_creates_quiz_content(
        self,
        instructor,
        course_data,
    ):
        course = CourseService(instructor).create(course_data)

        lesson = Lesson.objects.get(
            section__course=course,
            title="Django Quiz",
        )

        quiz = lesson.content.quiz

        assert quiz.instructions == "Answer all questions."
        assert quiz.passing_score == 70
        assert quiz.time_limit == 30
        assert quiz.max_attempts == 3
        assert quiz.shuffle_questions is True
        assert quiz.shuffle_choices is True
        assert quiz.show_correct_answers is True

    def test_create_course_creates_all_quiz_question_types(
        self,
        instructor,
        course_data,
    ):
        course = CourseService(instructor).create(course_data)

        quiz = QuizContent.objects.get(
            content__lesson__section__course=course,
            content__lesson__title="Django Quiz",
        )

        questions = list(quiz.questions.order_by("order"))

        assert len(questions) == 4

        assert questions[0].question_type == (Question.Type.SINGLE_CHOICE)
        assert questions[1].question_type == (Question.Type.MULTIPLE_CHOICE)
        assert questions[2].question_type == (Question.Type.TRUE_FALSE)
        assert questions[3].question_type == (Question.Type.SHORT_ANSWER)

    def test_create_course_creates_question_metadata(
        self,
        instructor,
        course_data,
    ):
        course = CourseService(instructor).create(course_data)

        quiz = QuizContent.objects.get(
            content__lesson__section__course=course,
            content__lesson__title="Django Quiz",
        )

        question = quiz.questions.get(order=1)

        assert question.text == "Which language is Django written in?"
        assert question.question_type == Question.Type.SINGLE_CHOICE
        assert question.difficulty == Question.Difficulty.EASY
        assert question.points == 2
        assert question.explanation == ("Django is written in Python.")
        assert question.is_required is True
        assert question.estimated_time == timedelta(minutes=1)

    def test_create_course_creates_single_choice_options(
        self,
        instructor,
        course_data,
    ):
        course = CourseService(instructor).create(course_data)

        question = Question.objects.get(
            quiz__content__lesson__section__course=course,
            order=1,
        )

        choices = list(question.choices.order_by("order"))

        assert len(choices) == 3

        assert choices[0].text == "Python"
        assert choices[0].is_correct is True
        assert choices[0].order == 1

        assert choices[1].text == "Java"
        assert choices[1].is_correct is False
        assert choices[1].order == 2

        assert choices[2].text == "Go"
        assert choices[2].is_correct is False
        assert choices[2].order == 3

    def test_create_course_creates_multiple_choice_options(
        self,
        instructor,
        course_data,
    ):
        course = CourseService(instructor).create(course_data)

        question = Question.objects.get(
            quiz__content__lesson__section__course=course,
            order=2,
        )

        choices = list(question.choices.order_by("order"))

        assert len(choices) == 3

        assert choices[0].text == "Django"
        assert choices[0].is_correct is True

        assert choices[1].text == "Flask"
        assert choices[1].is_correct is True

        assert choices[2].text == "Laravel"
        assert choices[2].is_correct is False

        assert [choice.order for choice in choices] == [1, 2, 3]

    def test_create_course_creates_boolean_answer(
        self,
        instructor,
        course_data,
    ):
        course = CourseService(instructor).create(course_data)

        question = Question.objects.get(
            quiz__content__lesson__section__course=course,
            order=3,
        )

        boolean_answer = question.boolean_answer

        assert isinstance(boolean_answer, BooleanAnswer)
        assert boolean_answer.answer is True

    def test_create_course_creates_short_answers(
        self,
        instructor,
        course_data,
    ):
        course = CourseService(instructor).create(course_data)

        question = Question.objects.get(
            quiz__content__lesson__section__course=course,
            order=4,
        )

        answers = list(
            question.accepted_answers.order_by("id").values_list("answer", flat=True)
        )

        assert answers == ["Python", "python"]

    def test_create_assignment_content(
        self,
        instructor,
        course_data,
    ):
        course = CourseService(instructor).create(course_data)

        lesson = Lesson.objects.get(
            section__course=course,
            title="Final Assignment",
        )

        assignment = lesson.content.assignment

        assert assignment.instructions == "Build a Django project."
        assert assignment.passing_score == 80
        assert assignment.max_score == 100
        assert assignment.due_date is None
        assert assignment.allow_late_submission is True
        assert assignment.max_attempts == 2
        assert assignment.accepted_file_types == ".zip,.pdf"
        assert assignment.max_file_size_mb == 25

    def test_create_course_creates_features(
        self,
        instructor,
        course_data,
    ):
        course = CourseService(instructor).create(course_data)

        features = list(course.features.values("icon", "text"))

        assert len(features) == 2

        assert {(feature["icon"], feature["text"]) for feature in features} == {
            ("video", "12 hours of video content"),
            ("certificate", "Certificate of completion"),
        }

    def test_create_target_audiences(
        self,
        instructor,
        course_data,
    ):
        course = CourseService(instructor).create(course_data)

        audiences = list(course.target_audiences.order_by("order"))

        assert len(audiences) == 2
        assert [audience.order for audience in audiences] == [1, 2]
        assert [audience.description for audience in audiences] == [
            "Python developers",
            "Web developers",
        ]

    def test_create_prerequisites(
        self,
        instructor,
        course_data,
    ):
        course = CourseService(instructor).create(course_data)

        prerequisites = list(course.prerequisites.order_by("order"))

        assert len(prerequisites) == 2
        assert [item.order for item in prerequisites] == [1, 2]
        assert [item.description for item in prerequisites] == [
            "Basic Python knowledge",
            "Basic programming knowledge",
        ]

    def test_create_learning_outcomes(
        self,
        instructor,
        course_data,
    ):
        course = CourseService(instructor).create(course_data)

        outcomes = list(course.learning_outcomes.order_by("order"))

        assert len(outcomes) == 2
        assert {outcome.description for outcome in outcomes} == {
            "Build Django applications",
            "Use Django ORM effectively",
        }

    def test_create_learning_outcomes_does_not_duplicate_existing_values(
        self,
        instructor,
        course_data,
    ):
        data = deepcopy(course_data)

        data["learning_outcomes"] = [
            {"description": "Build Django applications"},
            {"description": "Build Django applications"},
            {"description": "Use Django ORM effectively"},
        ]

        course = CourseService(instructor).create(data)

        outcomes = list(
            course.learning_outcomes.values_list(
                "description",
                flat=True,
            )
        )

        assert outcomes.count("Build Django applications") == 1
        assert outcomes.count("Use Django ORM effectively") == 1
        assert len(outcomes) == 2

    def test_create_course_with_empty_collections(
        self,
        instructor,
        course_data,
    ):
        data = deepcopy(course_data)

        data["tags"] = []
        data["attachments"] = []
        data["features"] = []
        data["target_audiences"] = []
        data["prerequisites"] = []
        data["learning_outcomes"] = []

        for section in data["sections"]:
            for lesson in section["lessons"]:
                lesson["content"]["attachments"] = []

        course = CourseService(instructor).create(data)

        assert course.tags.count() == 0
        assert course.attachments.count() == 0
        assert course.features.count() == 0
        assert course.target_audiences.count() == 0
        assert course.prerequisites.count() == 0
        assert course.learning_outcomes.count() == 0

        assert (
            Attachment.objects.filter(
                lesson_content__lesson__section__course=course,
            ).count()
            == 0
        )

    def test_create_course_rolls_back_when_later_operation_fails(
        self,
        instructor,
        course_data,
    ):
        data = deepcopy(course_data)

        with patch.object(
            CourseService,
            "_create_outcomes",
            side_effect=ValidationError("Outcome creation failed"),
        ):
            with pytest.raises(
                ValidationError,
                match="Outcome creation failed",
            ):
                CourseService(instructor).create(data)

        assert not Course.objects.filter(
            title=data["title"],
            owner=instructor,
        ).exists()

        assert not Section.objects.filter(
            course__owner=instructor,
            course__title=data["title"],
        ).exists()

        assert not Lesson.objects.filter(
            section__course__owner=instructor,
            section__course__title=data["title"],
        ).exists()

    def test_create_course_rolls_back_when_attachment_creation_fails(
        self,
        instructor,
        course_data,
    ):
        data = deepcopy(course_data)

        with patch.object(
            CourseService,
            "_create_course_attachments",
            side_effect=ValidationError("Attachment creation failed"),
        ):
            with pytest.raises(
                ValidationError,
                match="Attachment creation failed",
            ):
                CourseService(instructor).create(data)

        assert not Course.objects.filter(
            title=data["title"],
            owner=instructor,
        ).exists()

        assert not Attachment.objects.filter(
            course__owner=instructor,
        ).exists()

    def test_create_course_rolls_back_when_section_creation_fails(
        self,
        instructor,
        course_data,
    ):
        data = deepcopy(course_data)

        with patch.object(
            CourseService,
            "_create_sections",
            side_effect=ValidationError("Section creation failed"),
        ):
            with pytest.raises(
                ValidationError,
                match="Section creation failed",
            ):
                CourseService(instructor).create(data)

        assert not Course.objects.filter(
            title=data["title"],
            owner=instructor,
        ).exists()

    def test_create_course_does_not_create_partial_course_on_failure(
        self,
        instructor,
        course_data,
    ):
        data = deepcopy(course_data)

        with patch.object(
            CourseService,
            "_create_outcomes",
            side_effect=ValidationError("Forced failure"),
        ):
            with pytest.raises(
                ValidationError,
                match="Forced failure",
            ):
                CourseService(instructor).create(data)

        assert (
            Course.objects.filter(
                owner=instructor,
            ).count()
            == 0
        )

        assert (
            Section.objects.filter(
                course__owner=instructor,
            ).count()
            == 0
        )

        assert (
            Lesson.objects.filter(
                section__course__owner=instructor,
            ).count()
            == 0
        )

        assert (
            LessonContent.objects.filter(
                lesson__section__course__owner=instructor,
            ).count()
            == 0
        )

        assert (
            QuizContent.objects.filter(
                content__lesson__section__course__owner=instructor,
            ).count()
            == 0
        )

        assert (
            Assignment.objects.filter(
                content__lesson__section__course__owner=instructor,
            ).count()
            == 0
        )

        assert (
            Tag.objects.filter(
                courses__owner=instructor,
            ).count()
            == 0
        )
