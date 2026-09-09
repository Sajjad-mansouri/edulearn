import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from courses.models.course import Course
from curriculums.models.article_content import ArticleContent
from curriculums.models.lesson import Lesson
from curriculums.models.lesson_content import LessonContent
from curriculums.models.section import Section


@pytest.fixture
def test_user(db):
    from django.contrib.auth import get_user_model

    User = get_user_model()

    return User.objects.create_user(
        username="test_user",
        email="test_user@example.com",
        password="test-password",
    )


@pytest.fixture
def course(db, test_user):
    return Course.objects.create(
        title="Django Development",
        owner=test_user,
    )


@pytest.fixture
def section(db, course):
    return Section.objects.create(
        course=course,
        title="Introduction",
    )


@pytest.fixture
def lesson(db, section):
    return Lesson.objects.create(
        section=section,
        title="Getting Started",
        slug="getting-started",
    )


@pytest.fixture
def lesson_content(db, lesson):
    return LessonContent.objects.create(
        lesson=lesson,
        title="Getting Started Article",
        content_type=LessonContent.Type.ARTICLE,
        order=1,
    )


@pytest.mark.django_db
class TestArticleContentModel:
    def test_create_article_content(self, lesson_content):
        article = ArticleContent.objects.create(
            content=lesson_content,
            body="# Introduction\n\nThis is an article.",
            estimated_read_time=10,
        )

        assert article.pk is not None
        assert article.content == lesson_content
        assert article.body == "# Introduction\n\nThis is an article."
        assert article.estimated_read_time == 10

    def test_create_article_content_without_estimated_read_time(
        self,
        lesson_content,
    ):
        article = ArticleContent.objects.create(
            content=lesson_content,
            body="Article body.",
        )

        assert article.estimated_read_time is None

    def test_str_returns_content_title(self, lesson_content):
        article = ArticleContent.objects.create(
            content=lesson_content,
            body="Article body.",
        )

        assert str(article) == lesson_content.title

    def test_reverse_content_relation(self, lesson_content):
        article = ArticleContent.objects.create(
            content=lesson_content,
            body="Article body.",
        )

        assert lesson_content.article == article

    def test_content_is_required(self):
        article = ArticleContent(
            body="Article body.",
        )

        with pytest.raises(ValidationError) as exc_info:
            article.full_clean()

        assert "content" in exc_info.value.message_dict

    def test_empty_body_is_invalid(self, lesson_content):
        article = ArticleContent(
            content=lesson_content,
            body="",
        )

        with pytest.raises(ValidationError) as exc_info:
            article.full_clean()

        assert exc_info.value.message_dict["body"] == ["Article body is required."]

    def test_whitespace_only_body_is_invalid(self, lesson_content):
        article = ArticleContent(
            content=lesson_content,
            body="   \n\t  ",
        )

        with pytest.raises(ValidationError) as exc_info:
            article.full_clean()

        assert exc_info.value.message_dict["body"] == ["Article body is required."]

    @pytest.mark.parametrize(
        "body",
        [
            "Article body.",
            "# Markdown heading",
            "<p>HTML content</p>",
            "Line one\nLine two",
        ],
    )
    def test_non_empty_body_is_valid(self, lesson_content, body):
        article = ArticleContent(
            content=lesson_content,
            body=body,
        )

        article.full_clean()

    def test_body_whitespace_around_content_is_allowed(
        self,
        lesson_content,
    ):
        article = ArticleContent(
            content=lesson_content,
            body="  Article body.  ",
        )

        article.full_clean()

        assert article.body == "  Article body.  "

    def test_estimated_read_time_can_be_null(self, lesson_content):
        article = ArticleContent(
            content=lesson_content,
            body="Article body.",
            estimated_read_time=None,
        )

        article.full_clean()

        assert article.estimated_read_time is None

    @pytest.mark.parametrize(
        "estimated_read_time",
        [0, 1, 5, 60],
    )
    def test_estimated_read_time_accepts_valid_values(
        self,
        lesson_content,
        estimated_read_time,
    ):
        article = ArticleContent(
            content=lesson_content,
            body="Article body.",
            estimated_read_time=estimated_read_time,
        )

        article.full_clean()

        assert article.estimated_read_time == estimated_read_time

    def test_estimated_read_time_rejects_negative_value(
        self,
        lesson_content,
    ):
        article = ArticleContent(
            content=lesson_content,
            body="Article body.",
            estimated_read_time=-1,
        )

        with pytest.raises(ValidationError):
            article.full_clean()

    def test_same_content_cannot_have_two_article_contents(
        self,
        lesson_content,
    ):
        ArticleContent.objects.create(
            content=lesson_content,
            body="First article.",
        )

        second = ArticleContent(
            content=lesson_content,
            body="Second article.",
        )

        with pytest.raises(ValidationError) as exc_info:
            second.full_clean()

        assert "content" in exc_info.value.message_dict

    def test_same_content_is_unique_at_database_level(
        self,
        lesson_content,
    ):
        ArticleContent.objects.create(
            content=lesson_content,
            body="First article.",
        )

        with pytest.raises(IntegrityError):
            ArticleContent.objects.create(
                content=lesson_content,
                body="Second article.",
            )

    def test_deleting_lesson_content_deletes_article_content(
        self,
        lesson_content,
    ):
        article = ArticleContent.objects.create(
            content=lesson_content,
            body="Article body.",
        )
        article_id = article.pk

        lesson_content.delete()

        assert not ArticleContent.objects.filter(pk=article_id).exists()
