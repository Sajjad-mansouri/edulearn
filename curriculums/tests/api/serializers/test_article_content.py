from unittest.mock import Mock

import pytest

from curriculums.api.serializers import ArticleContenttSerializer
from curriculums.models.article_content import ArticleContent


@pytest.mark.django_db
class TestArticleContenttSerializer:
    def test_declares_expected_fields(self):
        serializer = ArticleContenttSerializer()

        assert set(serializer.fields) == {
            "id",
            "body",
            "estimated_read_time",
        }

    def test_id_is_optional(self):
        serializer = ArticleContenttSerializer()

        assert serializer.fields["id"].required is False

    def test_id_is_not_read_only(self):
        serializer = ArticleContenttSerializer()

        assert serializer.fields["id"].read_only is False

    def test_body_is_not_required_by_serializer(self):
        serializer = ArticleContenttSerializer()

        assert serializer.fields["body"].required is False

    def test_estimated_read_time_is_not_required(self):
        serializer = ArticleContenttSerializer()

        assert serializer.fields["estimated_read_time"].required is False

    def test_id_uses_integer_field(self):
        serializer = ArticleContenttSerializer()

        assert serializer.fields["id"].__class__.__name__ == "IntegerField"

    def test_body_uses_char_field(self):
        serializer = ArticleContenttSerializer()

        assert serializer.fields["body"].__class__.__name__ == "CharField"

    def test_estimated_read_time_uses_integer_field(self):
        serializer = ArticleContenttSerializer()

        assert (
            serializer.fields["estimated_read_time"].__class__.__name__
            == "IntegerField"
        )

    def test_accepts_complete_valid_data(self):
        data = {
            "id": 10,
            "body": "# Introduction\n\nDjango is a web framework.",
            "estimated_read_time": 8,
        }

        serializer = ArticleContenttSerializer(data=data)

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["id"] == 10
        assert serializer.validated_data["body"] == data["body"]
        assert serializer.validated_data["estimated_read_time"] == 8

    def test_accepts_body_without_id(self):
        data = {
            "body": "Article content",
            "estimated_read_time": 5,
        }

        serializer = ArticleContenttSerializer(data=data)

        assert serializer.is_valid(), serializer.errors

        assert "id" not in serializer.validated_data
        assert serializer.validated_data["body"] == "Article content"
        assert serializer.validated_data["estimated_read_time"] == 5

    def test_accepts_body_without_estimated_read_time(self):
        data = {
            "body": "Article content",
        }

        serializer = ArticleContenttSerializer(data=data)

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["body"] == "Article content"
        assert "estimated_read_time" not in serializer.validated_data

    def test_accepts_empty_body(self):
        serializer = ArticleContenttSerializer(
            data={
                "body": "",
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["body"] == ""

    def test_trims_whitespace_only_body(self):
        serializer = ArticleContenttSerializer(
            data={
                "body": "   ",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["body"] == ""

    def test_trims_leading_and_trailing_whitespace_from_body(self):
        serializer = ArticleContenttSerializer(
            data={
                "body": "  Article body with surrounding whitespace  ",
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["body"] == (
            "Article body with surrounding whitespace"
        )

    def test_accepts_html_body(self):
        body = "<h1>Introduction</h1><p>This is an article.</p><strong>Django</strong>"

        serializer = ArticleContenttSerializer(
            data={"body": body},
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["body"] == body

    def test_accepts_zero_estimated_read_time(self):
        serializer = ArticleContenttSerializer(
            data={
                "body": "Article content",
                "estimated_read_time": 0,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["estimated_read_time"] == 0

    def test_accepts_positive_estimated_read_time(self):
        serializer = ArticleContenttSerializer(
            data={
                "body": "Article content",
                "estimated_read_time": 30,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["estimated_read_time"] == 30

    def test_rejects_negative_estimated_read_time(self):
        serializer = ArticleContenttSerializer(
            data={
                "body": "Article content",
                "estimated_read_time": -1,
            }
        )

        assert serializer.is_valid() is False

        assert "estimated_read_time" in serializer.errors

    def test_accepts_string_integer_estimated_read_time(self):
        serializer = ArticleContenttSerializer(
            data={
                "body": "Article content",
                "estimated_read_time": "15",
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["estimated_read_time"] == 15

    def test_rejects_non_integer_estimated_read_time(self):
        serializer = ArticleContenttSerializer(
            data={
                "body": "Article content",
                "estimated_read_time": "ten",
            }
        )

        assert serializer.is_valid() is False

        assert "estimated_read_time" in serializer.errors

    def test_rejects_decimal_estimated_read_time(self):
        serializer = ArticleContenttSerializer(
            data={
                "body": "Article content",
                "estimated_read_time": "10.5",
            }
        )

        assert serializer.is_valid() is False

        assert "estimated_read_time" in serializer.errors

    def test_accepts_id_as_integer(self):
        serializer = ArticleContenttSerializer(
            data={
                "id": 25,
                "body": "Article content",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["id"] == 25

    def test_accepts_string_integer_id(self):
        serializer = ArticleContenttSerializer(
            data={
                "id": "25",
                "body": "Article content",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["id"] == 25

    def test_rejects_non_integer_id(self):
        serializer = ArticleContenttSerializer(
            data={
                "id": "invalid",
                "body": "Article content",
            }
        )

        assert serializer.is_valid() is False

        assert "id" in serializer.errors

    def test_rejects_decimal_id(self):
        serializer = ArticleContenttSerializer(
            data={
                "id": "10.5",
                "body": "Article content",
            }
        )

        assert serializer.is_valid() is False

        assert "id" in serializer.errors

    def test_accepts_null_estimated_read_time(self):
        serializer = ArticleContenttSerializer(
            data={
                "body": "Article content",
                "estimated_read_time": None,
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["estimated_read_time"] is None

    def test_rejects_null_body(self):
        serializer = ArticleContenttSerializer(
            data={
                "body": None,
            }
        )

        assert serializer.is_valid() is False

        assert "body" in serializer.errors

    def test_partial_update_accepts_empty_data(self):
        article = Mock(spec=ArticleContent)

        serializer = ArticleContenttSerializer(
            instance=article,
            data={},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data == {}

    def test_partial_update_can_change_body(self):
        article = Mock(spec=ArticleContent)

        serializer = ArticleContenttSerializer(
            instance=article,
            data={
                "body": "Updated article body",
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["body"] == ("Updated article body")

    def test_partial_update_can_change_estimated_read_time(self):
        article = Mock(spec=ArticleContent)

        serializer = ArticleContenttSerializer(
            instance=article,
            data={
                "estimated_read_time": 12,
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["estimated_read_time"] == 12

    def test_partial_update_can_change_id(self):
        article = Mock(spec=ArticleContent)

        serializer = ArticleContenttSerializer(
            instance=article,
            data={
                "id": 20,
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["id"] == 20

    def test_serializes_id(self):
        article = Mock(spec=ArticleContent)
        article.id = 15
        article.body = "Article body"
        article.estimated_read_time = 10

        serializer = ArticleContenttSerializer(article)

        assert serializer.data["id"] == 15

    def test_serializes_body(self):
        body = "# Django\n\nArticle content."

        article = Mock(spec=ArticleContent)
        article.id = 15
        article.body = body
        article.estimated_read_time = 10

        serializer = ArticleContenttSerializer(article)

        assert serializer.data["body"] == body

    def test_serializes_estimated_read_time(self):
        article = Mock(spec=ArticleContent)
        article.id = 15
        article.body = "Article body"
        article.estimated_read_time = 10

        serializer = ArticleContenttSerializer(article)

        assert serializer.data["estimated_read_time"] == 10

    def test_serializes_null_estimated_read_time(self):
        article = Mock(spec=ArticleContent)
        article.id = 15
        article.body = "Article body"
        article.estimated_read_time = None

        serializer = ArticleContenttSerializer(article)

        assert serializer.data["estimated_read_time"] is None

    def test_serializes_empty_body(self):
        article = Mock(spec=ArticleContent)
        article.id = 15
        article.body = ""
        article.estimated_read_time = None

        serializer = ArticleContenttSerializer(article)

        assert serializer.data["body"] == ""

    def test_serializes_all_declared_fields(self):
        article = Mock(spec=ArticleContent)
        article.id = 15
        article.body = "Article body"
        article.estimated_read_time = 10

        serializer = ArticleContenttSerializer(article)

        assert set(serializer.data) == {
            "id",
            "body",
            "estimated_read_time",
        }

    def test_model_fields_not_declared_in_serializer_are_excluded(self):
        article = Mock(spec=ArticleContent)
        article.id = 15
        article.body = "Article body"
        article.estimated_read_time = 10
        article.content = Mock()

        serializer = ArticleContenttSerializer(article)

        assert "content" not in serializer.data

    def test_serializer_does_not_expose_content_field(self):
        serializer = ArticleContenttSerializer()

        assert "content" not in serializer.fields
