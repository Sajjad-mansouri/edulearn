import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from courses.models import CourseFeedback, CourseFeedbackInteraction
from enrollments.models import Enrollment


@pytest.fixture
def enrollment(test_user, course):
    return Enrollment.objects.create(
        user=test_user,
        course=course,
    )


@pytest.fixture
def another_enrollment(another_user, course):
    return Enrollment.objects.create(
        user=another_user,
        course=course,
    )


@pytest.mark.django_db
class TestCourseFeedbackCreation:
    def test_feedback_can_be_created_with_required_fields(
        self,
        enrollment,
    ):
        feedback = CourseFeedback.objects.create(
            enrollment=enrollment,
            rating=5,
        )

        assert feedback.pk is not None
        assert feedback.enrollment == enrollment
        assert feedback.rating == 5
        assert feedback.title == ""
        assert feedback.comment == ""
        assert feedback.is_public is True

    def test_feedback_can_be_created_with_all_fields(
        self,
        enrollment,
    ):
        feedback = CourseFeedback.objects.create(
            enrollment=enrollment,
            rating=4,
            title="Very useful course",
            comment="The course was well structured and practical.",
            is_public=False,
        )

        assert feedback.enrollment == enrollment
        assert feedback.rating == 4
        assert feedback.title == "Very useful course"
        assert feedback.comment == "The course was well structured and practical."
        assert feedback.is_public is False

    def test_feedback_default_is_public_is_true(
        self,
        enrollment,
    ):
        feedback = CourseFeedback.objects.create(
            enrollment=enrollment,
            rating=5,
        )

        assert feedback.is_public is True

    def test_feedback_reverse_relation_exists(
        self,
        enrollment,
    ):
        feedback = CourseFeedback.objects.create(
            enrollment=enrollment,
            rating=5,
        )

        assert enrollment.feedback == feedback


@pytest.mark.django_db
class TestCourseFeedbackStringRepresentation:
    def test_str_uses_full_name_when_available(
        self,
        enrollment,
    ):
        user = enrollment.user
        user.first_name = "Test"
        user.last_name = "User"
        user.save(update_fields=["first_name", "last_name"])

        feedback = CourseFeedback.objects.create(
            enrollment=enrollment,
            rating=5,
        )

        assert str(feedback) == (
            f"Test User feedback for {enrollment.course.title} (5/5)"
        )

    def test_str_uses_username_when_full_name_is_empty(
        self,
        enrollment,
    ):
        user = enrollment.user
        user.first_name = ""
        user.last_name = ""
        user.save(update_fields=["first_name", "last_name"])

        feedback = CourseFeedback.objects.create(
            enrollment=enrollment,
            rating=4,
        )

        assert str(feedback) == (
            f"{user.username} feedback for {enrollment.course.title} (4/5)"
        )

    @pytest.mark.parametrize("rating", [1, 2, 3, 4, 5])
    def test_str_contains_correct_rating(
        self,
        enrollment,
        rating,
    ):
        feedback = CourseFeedback.objects.create(
            enrollment=enrollment,
            rating=rating,
        )

        assert f"{rating}/5" in str(feedback)

    def test_str_contains_course_title(
        self,
        enrollment,
    ):
        feedback = CourseFeedback.objects.create(
            enrollment=enrollment,
            rating=5,
        )

        assert enrollment.course.title in str(feedback)


@pytest.mark.django_db
class TestCourseFeedbackValidation:
    @pytest.mark.parametrize(
        "rating",
        [1, 2, 3, 4, 5],
    )
    def test_valid_rating_is_accepted(
        self,
        enrollment,
        rating,
    ):
        feedback = CourseFeedback(
            enrollment=enrollment,
            rating=rating,
        )

        feedback.full_clean()

    @pytest.mark.parametrize(
        "rating",
        [0, -1, 6, 10],
    )
    def test_rating_outside_allowed_range_is_rejected(
        self,
        enrollment,
        rating,
    ):
        feedback = CourseFeedback(
            enrollment=enrollment,
            rating=rating,
        )

        with pytest.raises(ValidationError) as exc_info:
            feedback.full_clean()

        assert "rating" in exc_info.value.message_dict

    def test_rating_is_required(
        self,
        enrollment,
    ):
        feedback = CourseFeedback(
            enrollment=enrollment,
            rating=None,
        )

        with pytest.raises(ValidationError) as exc_info:
            feedback.full_clean()

        assert "rating" in exc_info.value.message_dict

    def test_enrollment_is_required(self):
        feedback = CourseFeedback(
            enrollment=None,
            rating=5,
        )

        with pytest.raises(ValidationError) as exc_info:
            feedback.full_clean()

        assert "enrollment" in exc_info.value.message_dict

    def test_empty_title_is_valid(
        self,
        enrollment,
    ):
        feedback = CourseFeedback(
            enrollment=enrollment,
            rating=5,
            title="",
        )

        feedback.full_clean()

    def test_empty_comment_is_valid(
        self,
        enrollment,
    ):
        feedback = CourseFeedback(
            enrollment=enrollment,
            rating=5,
            comment="",
        )

        feedback.full_clean()

    def test_title_at_maximum_length_is_valid(
        self,
        enrollment,
    ):
        feedback = CourseFeedback(
            enrollment=enrollment,
            rating=5,
            title="A" * 150,
        )

        feedback.full_clean()

    def test_title_over_maximum_length_is_rejected(
        self,
        enrollment,
    ):
        feedback = CourseFeedback(
            enrollment=enrollment,
            rating=5,
            title="A" * 151,
        )

        with pytest.raises(ValidationError) as exc_info:
            feedback.full_clean()

        assert "title" in exc_info.value.message_dict

    def test_comment_accepts_long_text(
        self,
        enrollment,
    ):
        feedback = CourseFeedback(
            enrollment=enrollment,
            rating=5,
            comment="A" * 10_000,
        )

        feedback.full_clean()


@pytest.mark.django_db
class TestCourseFeedbackUniqueness:
    def test_enrollment_can_have_only_one_feedback(
        self,
        enrollment,
    ):
        CourseFeedback.objects.create(
            enrollment=enrollment,
            rating=5,
        )

        duplicate = CourseFeedback(
            enrollment=enrollment,
            rating=4,
        )

        with pytest.raises(ValidationError) as exc_info:
            duplicate.full_clean()

        assert "enrollment" in exc_info.value.message_dict

    def test_database_rejects_second_feedback_for_same_enrollment(
        self,
        enrollment,
    ):
        CourseFeedback.objects.create(
            enrollment=enrollment,
            rating=5,
        )

        with pytest.raises(IntegrityError):
            CourseFeedback.objects.create(
                enrollment=enrollment,
                rating=4,
            )

    def test_different_enrollments_can_have_feedback(
        self,
        enrollment,
        another_enrollment,
    ):
        first_feedback = CourseFeedback.objects.create(
            enrollment=enrollment,
            rating=5,
        )

        second_feedback = CourseFeedback.objects.create(
            enrollment=another_enrollment,
            rating=4,
        )

        assert first_feedback.pk != second_feedback.pk
        assert first_feedback.enrollment_id != second_feedback.enrollment_id


@pytest.mark.django_db
class TestCourseFeedbackTimestamps:
    def test_created_at_is_set_on_creation(
        self,
        enrollment,
    ):
        before = timezone.now()

        feedback = CourseFeedback.objects.create(
            enrollment=enrollment,
            rating=5,
        )

        after = timezone.now()

        assert feedback.created_at is not None
        assert before <= feedback.created_at <= after

    def test_updated_at_is_set_on_creation(
        self,
        enrollment,
    ):
        feedback = CourseFeedback.objects.create(
            enrollment=enrollment,
            rating=5,
        )

        assert feedback.updated_at is not None

    def test_created_at_does_not_change_on_update(
        self,
        enrollment,
    ):
        feedback = CourseFeedback.objects.create(
            enrollment=enrollment,
            rating=5,
        )

        original_created_at = feedback.created_at

        feedback.rating = 4
        feedback.save()

        feedback.refresh_from_db()

        assert feedback.created_at == original_created_at

    def test_updated_at_changes_on_update(
        self,
        enrollment,
    ):
        feedback = CourseFeedback.objects.create(
            enrollment=enrollment,
            rating=5,
        )

        original_updated_at = feedback.updated_at

        feedback.rating = 4
        feedback.save()

        feedback.refresh_from_db()

        assert feedback.updated_at > original_updated_at


@pytest.mark.django_db
class TestCourseFeedbackUpdate:
    def test_feedback_fields_can_be_updated(
        self,
        enrollment,
    ):
        feedback = CourseFeedback.objects.create(
            enrollment=enrollment,
            rating=3,
            title="Initial title",
            comment="Initial comment",
            is_public=True,
        )

        feedback.rating = 5
        feedback.title = "Updated title"
        feedback.comment = "Updated comment"
        feedback.is_public = False
        feedback.save()

        feedback.refresh_from_db()

        assert feedback.rating == 5
        assert feedback.title == "Updated title"
        assert feedback.comment == "Updated comment"
        assert feedback.is_public is False

    def test_rating_can_be_changed_to_valid_value(
        self,
        enrollment,
    ):
        feedback = CourseFeedback.objects.create(
            enrollment=enrollment,
            rating=2,
        )

        feedback.rating = 5
        feedback.full_clean()
        feedback.save()

        feedback.refresh_from_db()

        assert feedback.rating == 5

    def test_invalid_rating_is_rejected_during_validation(
        self,
        enrollment,
    ):
        feedback = CourseFeedback.objects.create(
            enrollment=enrollment,
            rating=5,
        )

        feedback.rating = 6

        with pytest.raises(ValidationError) as exc_info:
            feedback.full_clean()

        assert "rating" in exc_info.value.message_dict


@pytest.mark.django_db
class TestCourseFeedbackDeletion:
    def test_deleting_enrollment_deletes_feedback(
        self,
        enrollment,
    ):
        feedback = CourseFeedback.objects.create(
            enrollment=enrollment,
            rating=5,
        )

        feedback_id = feedback.pk

        enrollment.delete()

        assert not CourseFeedback.objects.filter(
            pk=feedback_id,
        ).exists()


@pytest.mark.django_db
class TestCourseFeedbackVisibility:
    def test_public_feedback_can_be_filtered(
        self,
        enrollment,
        another_enrollment,
    ):
        public_feedback = CourseFeedback.objects.create(
            enrollment=enrollment,
            rating=5,
            is_public=True,
        )

        private_feedback = CourseFeedback.objects.create(
            enrollment=another_enrollment,
            rating=3,
            is_public=False,
        )

        public_feedbacks = CourseFeedback.objects.filter(
            is_public=True,
        )

        assert list(public_feedbacks) == [public_feedback]
        assert private_feedback not in public_feedbacks

    def test_private_feedback_can_be_filtered(
        self,
        enrollment,
        another_enrollment,
    ):
        public_feedback = CourseFeedback.objects.create(
            enrollment=enrollment,
            rating=5,
            is_public=True,
        )

        private_feedback = CourseFeedback.objects.create(
            enrollment=another_enrollment,
            rating=3,
            is_public=False,
        )

        private_feedbacks = CourseFeedback.objects.filter(
            is_public=False,
        )

        assert list(private_feedbacks) == [private_feedback]
        assert public_feedback not in private_feedbacks


@pytest.mark.django_db
class TestCourseFeedbackRelations:
    def test_feedback_points_to_correct_enrollment(
        self,
        enrollment,
    ):
        feedback = CourseFeedback.objects.create(
            enrollment=enrollment,
            rating=5,
        )

        assert feedback.enrollment_id == enrollment.pk

    def test_feedback_points_to_correct_user_through_enrollment(
        self,
        enrollment,
    ):
        feedback = CourseFeedback.objects.create(
            enrollment=enrollment,
            rating=5,
        )

        assert feedback.enrollment.user == enrollment.user

    def test_feedback_points_to_correct_course_through_enrollment(
        self,
        enrollment,
    ):
        feedback = CourseFeedback.objects.create(
            enrollment=enrollment,
            rating=5,
        )

        assert feedback.enrollment.course == enrollment.course


# CourseFeedbackInteraction
@pytest.fixture
def feedback(enrollment):
    return CourseFeedback.objects.create(
        enrollment=enrollment,
        rating=5,
        title="Good course",
        comment="Very useful.",
    )


@pytest.fixture
def another_feedback(another_enrollment):
    return CourseFeedback.objects.create(
        enrollment=another_enrollment,
        rating=4,
        title="Good experience",
        comment="Well structured.",
    )


@pytest.fixture
def feedback_interaction(enrollment, feedback):
    return CourseFeedbackInteraction.objects.create(
        enrollment=enrollment,
        feedback=feedback,
    )


@pytest.mark.django_db
class TestCourseFeedbackInteractionCreation:
    def test_interaction_can_be_created_with_required_fields(
        self,
        enrollment,
        feedback,
    ):
        interaction = CourseFeedbackInteraction.objects.create(
            enrollment=enrollment,
            feedback=feedback,
        )

        assert interaction.pk is not None
        assert interaction.enrollment == enrollment
        assert interaction.feedback == feedback
        assert interaction.liked is True

    def test_liked_defaults_to_true(
        self,
        enrollment,
        feedback,
    ):
        interaction = CourseFeedbackInteraction.objects.create(
            enrollment=enrollment,
            feedback=feedback,
        )

        assert interaction.liked is True

    def test_liked_can_be_set_to_false(
        self,
        enrollment,
        feedback,
    ):
        interaction = CourseFeedbackInteraction.objects.create(
            enrollment=enrollment,
            feedback=feedback,
            liked=False,
        )

        assert interaction.liked is False

    def test_interaction_can_be_created_with_liked_true(
        self,
        enrollment,
        feedback,
    ):
        interaction = CourseFeedbackInteraction.objects.create(
            enrollment=enrollment,
            feedback=feedback,
            liked=True,
        )

        assert interaction.liked is True


@pytest.mark.django_db
class TestCourseFeedbackInteractionStringRepresentation:
    def test_str_contains_enrollment_user_username(
        self,
        feedback_interaction,
    ):
        result = str(feedback_interaction)

        assert feedback_interaction.enrollment.user.username in result

    def test_str_contains_feedback_representation(
        self,
        feedback_interaction,
    ):
        result = str(feedback_interaction)

        assert str(feedback_interaction.feedback) in result

    def test_str_matches_expected_format(
        self,
        feedback_interaction,
    ):
        expected = (
            f"{feedback_interaction.enrollment.user.username} "
            f"like {feedback_interaction.feedback}"
        )

        assert str(feedback_interaction) == expected


@pytest.mark.django_db
class TestCourseFeedbackInteractionValidation:
    def test_valid_interaction_passes_validation(
        self,
        enrollment,
        feedback,
    ):
        interaction = CourseFeedbackInteraction(
            enrollment=enrollment,
            feedback=feedback,
            liked=True,
        )

        interaction.full_clean()

    def test_enrollment_is_required(
        self,
        feedback,
    ):
        interaction = CourseFeedbackInteraction(
            enrollment=None,
            feedback=feedback,
        )

        with pytest.raises(ValidationError) as exc_info:
            interaction.full_clean()

        assert "enrollment" in exc_info.value.message_dict

    def test_feedback_is_required(
        self,
        enrollment,
    ):
        interaction = CourseFeedbackInteraction(
            enrollment=enrollment,
            feedback=None,
        )

        with pytest.raises(ValidationError) as exc_info:
            interaction.full_clean()

        assert "feedback" in exc_info.value.message_dict


@pytest.mark.django_db
class TestCourseFeedbackInteractionRelationships:
    def test_interaction_points_to_correct_enrollment(
        self,
        feedback_interaction,
        enrollment,
    ):
        assert feedback_interaction.enrollment_id == enrollment.pk

    def test_interaction_points_to_correct_feedback(
        self,
        feedback_interaction,
        feedback,
    ):
        assert feedback_interaction.feedback_id == feedback.pk

    def test_feedback_reverse_relation_contains_interaction(
        self,
        feedback,
        feedback_interaction,
    ):
        assert (
            feedback.feedback_interactions.get(
                pk=feedback_interaction.pk,
            )
            == feedback_interaction
        )

    def test_multiple_interactions_can_reference_same_feedback(
        self,
        enrollment,
        another_enrollment,
        feedback,
    ):
        first = CourseFeedbackInteraction.objects.create(
            enrollment=enrollment,
            feedback=feedback,
            liked=True,
        )

        second = CourseFeedbackInteraction.objects.create(
            enrollment=another_enrollment,
            feedback=feedback,
            liked=False,
        )

        assert first.feedback == feedback
        assert second.feedback == feedback
        assert feedback.feedback_interactions.count() == 2

    def test_multiple_interactions_can_be_created_for_same_enrollment(
        self,
        enrollment,
        feedback,
        another_feedback,
    ):
        first = CourseFeedbackInteraction.objects.create(
            enrollment=enrollment,
            feedback=feedback,
        )

        second = CourseFeedbackInteraction.objects.create(
            enrollment=enrollment,
            feedback=another_feedback,
        )

        assert first.enrollment == enrollment
        assert second.enrollment == enrollment
        assert (
            CourseFeedbackInteraction.objects.filter(
                enrollment=enrollment,
            ).count()
            == 2
        )


@pytest.mark.django_db
class TestCourseFeedbackInteractionUpdate:
    def test_liked_can_be_changed(
        self,
        feedback_interaction,
    ):
        feedback_interaction.liked = False
        feedback_interaction.save()

        feedback_interaction.refresh_from_db()

        assert feedback_interaction.liked is False

    def test_liked_can_be_changed_back_to_true(
        self,
        feedback_interaction,
    ):
        feedback_interaction.liked = False
        feedback_interaction.save()

        feedback_interaction.liked = True
        feedback_interaction.save()

        feedback_interaction.refresh_from_db()

        assert feedback_interaction.liked is True

    def test_enrollment_can_be_changed(
        self,
        feedback_interaction,
        another_enrollment,
    ):
        feedback_interaction.enrollment = another_enrollment
        feedback_interaction.save()

        feedback_interaction.refresh_from_db()

        assert feedback_interaction.enrollment_id == another_enrollment.pk

    def test_feedback_can_be_changed(
        self,
        feedback_interaction,
        another_feedback,
    ):
        feedback_interaction.feedback = another_feedback
        feedback_interaction.save()

        feedback_interaction.refresh_from_db()

        assert feedback_interaction.feedback_id == another_feedback.pk


@pytest.mark.django_db
class TestCourseFeedbackInteractionTimestamps:
    def test_created_at_is_set_on_creation(
        self,
        enrollment,
        feedback,
    ):
        before = timezone.now()

        interaction = CourseFeedbackInteraction.objects.create(
            enrollment=enrollment,
            feedback=feedback,
        )

        after = timezone.now()

        assert interaction.created_at is not None
        assert before <= interaction.created_at <= after

    def test_created_at_does_not_change_on_update(
        self,
        feedback_interaction,
    ):
        original_created_at = feedback_interaction.created_at

        feedback_interaction.liked = False
        feedback_interaction.save()

        feedback_interaction.refresh_from_db()

        assert feedback_interaction.created_at == original_created_at


@pytest.mark.django_db
class TestCourseFeedbackInteractionDeletion:
    def test_deleting_enrollment_deletes_interaction(
        self,
        feedback_interaction,
        enrollment,
    ):
        interaction_id = feedback_interaction.pk

        enrollment.delete()

        assert not CourseFeedbackInteraction.objects.filter(
            pk=interaction_id,
        ).exists()

    def test_deleting_feedback_deletes_interaction(
        self,
        feedback_interaction,
        feedback,
    ):
        interaction_id = feedback_interaction.pk

        feedback.delete()

        assert not CourseFeedbackInteraction.objects.filter(
            pk=interaction_id,
        ).exists()


@pytest.mark.django_db
class TestCourseFeedbackInteractionQuerying:
    def test_can_filter_liked_interactions(
        self,
        enrollment,
        another_enrollment,
        feedback,
        another_feedback,
    ):
        liked = CourseFeedbackInteraction.objects.create(
            enrollment=enrollment,
            feedback=feedback,
            liked=True,
        )

        not_liked = CourseFeedbackInteraction.objects.create(
            enrollment=another_enrollment,
            feedback=another_feedback,
            liked=False,
        )

        liked_interactions = CourseFeedbackInteraction.objects.filter(
            liked=True,
        )

        assert list(liked_interactions) == [liked]
        assert not_liked not in liked_interactions

    def test_can_filter_not_liked_interactions(
        self,
        enrollment,
        another_enrollment,
        feedback,
        another_feedback,
    ):
        liked = CourseFeedbackInteraction.objects.create(
            enrollment=enrollment,
            feedback=feedback,
            liked=True,
        )

        not_liked = CourseFeedbackInteraction.objects.create(
            enrollment=another_enrollment,
            feedback=another_feedback,
            liked=False,
        )

        not_liked_interactions = CourseFeedbackInteraction.objects.filter(
            liked=False,
        )

        assert list(not_liked_interactions) == [not_liked]
        assert liked not in not_liked_interactions
