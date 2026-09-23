from types import SimpleNamespace

import pytest
from django.test import RequestFactory
from rest_framework import serializers

from courses.api.serializers.feedback import (
    CourseFeedbackSerializer,
    FeedbackSerializer,
)
from courses.models import CourseFeedback, CourseFeedbackInteraction
from enrollments.models import Enrollment
from profiles.models import Profile


@pytest.fixture
def profile(test_user):
    return Profile.objects.create(user=test_user)


@pytest.fixture
def another_profile(another_user):
    return Profile.objects.create(user=another_user)


@pytest.fixture
def enrollment(db, test_user, course):
    return Enrollment.objects.create(
        user=test_user,
        course=course,
    )


@pytest.fixture
def another_enrollment(db, another_user, course):
    return Enrollment.objects.create(
        user=another_user,
        course=course,
    )


@pytest.fixture
def feedback(enrollment):
    return CourseFeedback.objects.create(
        enrollment=enrollment,
        rating=5,
        title="Course feedback",
        comment="Useful course.",
        is_public=True,
    )


@pytest.fixture
def another_feedback(another_enrollment):
    return CourseFeedback.objects.create(
        enrollment=another_enrollment,
        rating=4,
        title="Another feedback",
        comment="Good course.",
        is_public=True,
    )


@pytest.fixture
def request_factory():
    return RequestFactory()


@pytest.fixture
def authenticated_request(request_factory, test_user):
    request = request_factory.get("/courses/reviews/")
    request.user = test_user
    return request


@pytest.fixture
def another_authenticated_request(request_factory, another_user):
    request = request_factory.get("/courses/reviews/")
    request.user = another_user
    return request


@pytest.fixture
def anonymous_request(request_factory):
    request = request_factory.get("/courses/reviews/")
    request.user = SimpleNamespace(is_anonymous=True)
    return request


class TestCourseFeedbackSerializer:
    def test_declared_fields(self):
        serializer = CourseFeedbackSerializer()

        assert set(serializer.fields) == {
            "id",
            "user_name",
            "user_avatar",
            "rating",
            "comment",
            "created_at",
            "helpful_count",
            "user_has_liked",
            "is_owner",
        }

    def test_meta_fields_do_not_expose_title_or_is_public(self):
        serializer = CourseFeedbackSerializer()

        assert "title" not in serializer.fields
        assert "is_public" not in serializer.fields

    def test_helpful_count_is_read_only(self):
        serializer = CourseFeedbackSerializer()

        assert serializer.fields["helpful_count"].read_only is True

    def test_user_name_returns_enrollment_user_username(
        self,
        feedback,
        test_user,
    ):
        serializer = CourseFeedbackSerializer()

        result = serializer.get_user_name(feedback)

        assert result == test_user.username

    def test_user_avatar_returns_enrollment_user_avatar(
        self,
        feedback,
        profile,
        test_user,
    ):
        serializer = CourseFeedbackSerializer()

        result = serializer.get_user_avatar(feedback)

        assert result == test_user.avatar

    def test_user_has_liked_returns_false_for_anonymous_user(
        self,
        feedback,
        anonymous_request,
    ):
        serializer = CourseFeedbackSerializer(
            context={"request": anonymous_request},
        )

        result = serializer.get_user_has_liked(feedback)

        assert result is False

    def test_user_has_liked_returns_false_when_authenticated_user_has_no_interaction(
        self,
        feedback,
        authenticated_request,
    ):
        serializer = CourseFeedbackSerializer(
            context={"request": authenticated_request},
        )

        result = serializer.get_user_has_liked(feedback)

        assert result is False

    def test_user_has_liked_returns_true_when_authenticated_user_has_interaction(
        self,
        feedback,
        enrollment,
        authenticated_request,
    ):
        CourseFeedbackInteraction.objects.create(
            enrollment=enrollment,
            feedback=feedback,
        )

        serializer = CourseFeedbackSerializer(
            context={"request": authenticated_request},
        )

        result = serializer.get_user_has_liked(feedback)

        assert result is True

    def test_user_has_liked_returns_true_for_existing_interaction_even_when_liked_is_false(
        self,
        feedback,
        enrollment,
        authenticated_request,
    ):
        CourseFeedbackInteraction.objects.create(
            enrollment=enrollment,
            feedback=feedback,
            liked=False,
        )

        serializer = CourseFeedbackSerializer(
            context={"request": authenticated_request},
        )

        result = serializer.get_user_has_liked(feedback)

        assert result is True

    def test_user_has_liked_only_checks_interactions_for_request_user(
        self,
        feedback,
        enrollment,
        another_enrollment,
        authenticated_request,
    ):
        CourseFeedbackInteraction.objects.create(
            enrollment=another_enrollment,
            feedback=feedback,
        )

        serializer = CourseFeedbackSerializer(
            context={"request": authenticated_request},
        )

        result = serializer.get_user_has_liked(feedback)

        assert result is False

        CourseFeedbackInteraction.objects.create(
            enrollment=enrollment,
            feedback=feedback,
        )

        result = serializer.get_user_has_liked(feedback)

        assert result is True

    def test_is_owner_returns_true_for_feedback_owner(
        self,
        feedback,
        authenticated_request,
    ):
        serializer = CourseFeedbackSerializer(
            context={"request": authenticated_request},
        )

        result = serializer.get_is_owner(feedback)

        assert result is True

    def test_is_owner_returns_false_for_different_authenticated_user(
        self,
        feedback,
        another_authenticated_request,
    ):
        serializer = CourseFeedbackSerializer(
            context={"request": another_authenticated_request},
        )

        result = serializer.get_is_owner(feedback)

        assert result is False

    def test_is_owner_returns_false_for_anonymous_user(
        self,
        feedback,
        anonymous_request,
    ):
        serializer = CourseFeedbackSerializer(
            context={"request": anonymous_request},
        )

        result = serializer.get_is_owner(feedback)

        assert result is False

    def test_serializes_real_course_feedback_instance(
        self,
        feedback,
        profile,
        authenticated_request,
    ):
        feedback.helpful_count = 2

        serializer = CourseFeedbackSerializer(
            feedback,
            context={"request": authenticated_request},
        )

        data = serializer.data

        assert data["id"] == feedback.id
        assert data["user_name"] == feedback.enrollment.user.username
        assert data["user_avatar"] == feedback.enrollment.user.avatar
        assert data["rating"] == feedback.rating
        assert data["comment"] == feedback.comment
        assert data["helpful_count"] == 2
        assert data["user_has_liked"] is False
        assert data["is_owner"] is True
        assert data["created_at"] is not None

    def test_serializes_multiple_feedback_instances(
        self,
        feedback,
        another_feedback,
        profile,
        another_profile,
        authenticated_request,
    ):
        feedback.helpful_count = 1
        another_feedback.helpful_count = 0

        serializer = CourseFeedbackSerializer(
            [feedback, another_feedback],
            many=True,
            context={"request": authenticated_request},
        )

        data = serializer.data

        assert len(data) == 2
        assert data[0]["id"] == feedback.id
        assert data[1]["id"] == another_feedback.id
        assert data[0]["rating"] == feedback.rating
        assert data[1]["rating"] == another_feedback.rating

    def test_serialized_comment_matches_model_value(
        self,
        feedback,
        profile,
        authenticated_request,
    ):
        serializer = CourseFeedbackSerializer(
            feedback,
            context={"request": authenticated_request},
        )

        assert serializer.data["comment"] == feedback.comment

    def test_serializer_does_not_include_title(
        self,
        feedback,
        profile,
        authenticated_request,
    ):
        serializer = CourseFeedbackSerializer(
            feedback,
            context={"request": authenticated_request},
        )

        assert "title" not in serializer.data

    def test_serializer_does_not_include_is_public(
        self,
        feedback,
        profile,
        authenticated_request,
    ):
        serializer = CourseFeedbackSerializer(
            feedback,
            context={"request": authenticated_request},
        )

        assert "is_public" not in serializer.data

    def test_helpful_count_uses_value_present_on_instance(
        self,
        feedback,
        profile,
        authenticated_request,
    ):
        feedback.helpful_count = 7

        serializer = CourseFeedbackSerializer(
            feedback,
            context={"request": authenticated_request},
        )

        assert serializer.data["helpful_count"] == 7

    def test_helpful_count_is_not_required_for_input(
        self,
    ):
        serializer = CourseFeedbackSerializer()

        assert serializer.fields["helpful_count"].read_only is True

    def test_missing_request_context_raises_key_error(
        self,
        feedback,
    ):
        serializer = CourseFeedbackSerializer()

        with pytest.raises(KeyError):
            serializer.get_user_has_liked(feedback)

    def test_missing_request_context_raises_key_error_for_is_owner(
        self,
        feedback,
    ):
        serializer = CourseFeedbackSerializer()

        with pytest.raises(KeyError):
            serializer.get_is_owner(feedback)


class TestFeedbackSerializer:
    def test_declared_fields(self):
        serializer = FeedbackSerializer()

        assert set(serializer.fields) == {
            "enrollment",
            "rating",
            "comment",
        }

    def test_enrollment_field_is_model_related_field(self):
        serializer = FeedbackSerializer()

        assert isinstance(
            serializer.fields["enrollment"],
            serializers.PrimaryKeyRelatedField,
        )

    def test_serializes_course_feedback(
        self,
        feedback,
    ):
        serializer = FeedbackSerializer(feedback)

        data = serializer.data

        assert data["enrollment"] == feedback.enrollment.pk
        assert data["rating"] == feedback.rating
        assert data["comment"] == feedback.comment

    def test_title_is_not_serialized(
        self,
        feedback,
    ):
        serializer = FeedbackSerializer(feedback)

        assert "title" not in serializer.data

    def test_is_public_is_not_serialized(
        self,
        feedback,
    ):
        serializer = FeedbackSerializer(feedback)

        assert "is_public" not in serializer.data

    def test_created_at_is_not_serialized(
        self,
        feedback,
    ):
        serializer = FeedbackSerializer(feedback)

        assert "created_at" not in serializer.data

    def test_rating_validation_accepts_valid_value(
        self,
        enrollment,
    ):
        serializer = FeedbackSerializer(
            data={
                "enrollment": enrollment.pk,
                "rating": 5,
                "comment": "Useful course.",
            }
        )

        assert serializer.is_valid(), serializer.errors

    def test_rating_validation_accepts_minimum_value(
        self,
        enrollment,
    ):
        serializer = FeedbackSerializer(
            data={
                "enrollment": enrollment.pk,
                "rating": 1,
                "comment": "Course feedback.",
            }
        )

        assert serializer.is_valid(), serializer.errors

    def test_rating_validation_accepts_maximum_value(
        self,
        enrollment,
    ):
        serializer = FeedbackSerializer(
            data={
                "enrollment": enrollment.pk,
                "rating": 5,
                "comment": "Course feedback.",
            }
        )

        assert serializer.is_valid(), serializer.errors

    def test_rating_validation_rejects_value_below_minimum(
        self,
        enrollment,
    ):
        serializer = FeedbackSerializer(
            data={
                "enrollment": enrollment.pk,
                "rating": 0,
                "comment": "Course feedback.",
            }
        )

        assert serializer.is_valid() is False
        assert "rating" in serializer.errors

    def test_rating_validation_rejects_value_above_maximum(
        self,
        enrollment,
    ):
        serializer = FeedbackSerializer(
            data={
                "enrollment": enrollment.pk,
                "rating": 6,
                "comment": "Course feedback.",
            }
        )

        assert serializer.is_valid() is False
        assert "rating" in serializer.errors

    def test_comment_is_optional(
        self,
        enrollment,
    ):
        serializer = FeedbackSerializer(
            data={
                "enrollment": enrollment.pk,
                "rating": 4,
            }
        )

        assert serializer.is_valid(), serializer.errors

    def test_enrollment_is_required(
        self,
    ):
        serializer = FeedbackSerializer(
            data={
                "rating": 4,
                "comment": "Course feedback.",
            }
        )

        assert serializer.is_valid() is False
        assert "enrollment" in serializer.errors

    def test_rating_is_required(
        self,
        enrollment,
    ):
        serializer = FeedbackSerializer(
            data={
                "enrollment": enrollment.pk,
                "comment": "Course feedback.",
            }
        )

        assert serializer.is_valid() is False
        assert "rating" in serializer.errors
