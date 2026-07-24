import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from curriculums.models import ArticleContent
from curriculums.tests.factories import (
    ArticleContentFactory,
    LessonContentFactory,
)


@pytest.mark.django_db
class TestArticleContentModel:
    """Tests for the ArticleContent model."""

    @pytest.fixture
    def content(self):
        return LessonContentFactory()

    def test_create_article_content(self, content):
        """An article content can be created."""
        article = ArticleContent.objects.create(
            content=content,
            body="# Introduction\n\nThis is the article body.",
            estimated_read_time=8,
        )

        assert article.content == content
        assert article.body == "# Introduction\n\nThis is the article body."
        assert article.estimated_read_time == 8

    def test_string_representation(self):
        """The string representation should return the lesson content title."""
        article = ArticleContentFactory()

        assert str(article) == article.content.title

    def test_estimated_read_time_is_optional(self, content):
        """Estimated read time is optional."""
        article = ArticleContent.objects.create(
            content=content,
            body="Article body",
        )

        assert article.estimated_read_time is None

    def test_body_is_required(self, content):
        """Article body cannot be empty."""
        article = ArticleContent(
            content=content,
            body="",
        )

        with pytest.raises(ValidationError) as exc:
            article.full_clean()

        assert "body" in exc.value.message_dict

    def test_body_cannot_contain_only_whitespace(self, content):
        """Article body cannot contain only whitespace."""
        article = ArticleContent(
            content=content,
            body="   \n\t   ",
        )

        with pytest.raises(ValidationError) as exc:
            article.full_clean()

        assert "body" in exc.value.message_dict

    def test_valid_article_passes_validation(self, content):
        """A valid article passes model validation."""
        article = ArticleContent(
            content=content,
            body="This is a valid article.",
            estimated_read_time=5,
        )

        article.full_clean()

    def test_content_can_have_only_one_article(self, content):
        """Each lesson content can have only one article."""
        ArticleContentFactory(content=content)

        with pytest.raises(IntegrityError):
            ArticleContentFactory(content=content)

    def test_deleting_content_deletes_article(self):
        """Deleting lesson content cascades to its article."""
        content = LessonContentFactory()

        article = ArticleContentFactory(
            content=content,
        )

        content.delete()

        assert not ArticleContent.objects.filter(
            pk=article.pk,
        ).exists()
