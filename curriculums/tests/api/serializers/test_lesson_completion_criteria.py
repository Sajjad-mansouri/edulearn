import pytest

from curriculums.api.serializers import CompletionCriteraSerializer
from curriculums.models import LessonCompletionCriteria


class TestCompletionCriteraSerializerFields:
    def test_contains_expected_fields(self):
        serializer = CompletionCriteraSerializer()

        assert list(serializer.fields) == [
            "criteria_type",
            "quiz_passing_score",
            "video_watch_percentage",
        ]

    def test_criteria_type_is_not_required(self):
        serializer = CompletionCriteraSerializer()

        assert serializer.fields["criteria_type"].required is False

    def test_quiz_passing_score_is_not_required(self):
        serializer = CompletionCriteraSerializer()

        assert serializer.fields["quiz_passing_score"].required is False

    def test_video_watch_percentage_is_not_required(self):
        serializer = CompletionCriteraSerializer()

        assert serializer.fields["video_watch_percentage"].required is False

    def test_quiz_passing_score_allows_null(self):
        serializer = CompletionCriteraSerializer()

        assert serializer.fields["quiz_passing_score"].allow_null is True

    def test_video_watch_percentage_allows_null(self):
        serializer = CompletionCriteraSerializer()

        assert serializer.fields["video_watch_percentage"].allow_null is True

    def test_does_not_expose_lesson_field(self):
        serializer = CompletionCriteraSerializer()

        assert "lesson" not in serializer.fields

    def test_does_not_expose_created_at_field(self):
        serializer = CompletionCriteraSerializer()

        assert "created_at" not in serializer.fields

    def test_does_not_expose_updated_at_field(self):
        serializer = CompletionCriteraSerializer()

        assert "updated_at" not in serializer.fields


class TestCompletionCriteraSerializerCriteriaType:
    @pytest.mark.parametrize(
        "criteria_type",
        [
            LessonCompletionCriteria.CriteriaType.MANUAL,
            LessonCompletionCriteria.CriteriaType.WATCH_VIDEO,
            LessonCompletionCriteria.CriteriaType.READ_ARTICLE,
            LessonCompletionCriteria.CriteriaType.PASS_QUIZ,
            LessonCompletionCriteria.CriteriaType.SUBMIT_ASSIGNMENT,
        ],
    )
    def test_accepts_valid_criteria_type(self, criteria_type):
        serializer = CompletionCriteraSerializer(data={"criteria_type": criteria_type})

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["criteria_type"] == criteria_type

    def test_rejects_invalid_criteria_type(self):
        serializer = CompletionCriteraSerializer(
            data={"criteria_type": "invalid_criteria"}
        )

        assert not serializer.is_valid()
        assert "criteria_type" in serializer.errors

    @pytest.mark.parametrize(
        "criteria_type",
        [
            "",
            None,
        ],
    )
    def test_rejects_empty_criteria_type(self, criteria_type):
        serializer = CompletionCriteraSerializer(data={"criteria_type": criteria_type})

        assert not serializer.is_valid()
        assert "criteria_type" in serializer.errors

    def test_accepts_criteria_type_as_string(self):
        serializer = CompletionCriteraSerializer(
            data={
                "criteria_type": "manual",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["criteria_type"] == "manual"

    def test_uses_model_default_when_criteria_type_is_omitted(self):
        serializer = CompletionCriteraSerializer(
            data={
                "video_watch_percentage": None,
                "quiz_passing_score": None,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert "criteria_type" not in serializer.validated_data


class TestCompletionCriteraSerializerQuizPassingScore:
    @pytest.mark.parametrize(
        "score",
        [
            0,
            1,
            50,
            70,
            100,
        ],
    )
    def test_accepts_valid_integer_quiz_passing_score(self, score):
        serializer = CompletionCriteraSerializer(
            data={
                "criteria_type": LessonCompletionCriteria.CriteriaType.PASS_QUIZ,
                "quiz_passing_score": score,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["quiz_passing_score"] == score

    def test_accepts_quiz_passing_score_as_numeric_string(self):
        serializer = CompletionCriteraSerializer(
            data={
                "criteria_type": LessonCompletionCriteria.CriteriaType.PASS_QUIZ,
                "quiz_passing_score": "75",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["quiz_passing_score"] == 75

    def test_accepts_null_quiz_passing_score(self):
        serializer = CompletionCriteraSerializer(
            data={
                "criteria_type": LessonCompletionCriteria.CriteriaType.MANUAL,
                "quiz_passing_score": None,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["quiz_passing_score"] is None

    def test_omits_quiz_passing_score_when_not_provided(self):
        serializer = CompletionCriteraSerializer(
            data={
                "criteria_type": LessonCompletionCriteria.CriteriaType.MANUAL,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert "quiz_passing_score" not in serializer.validated_data

    @pytest.mark.parametrize(
        "score",
        [
            -1,
            -10,
        ],
    )
    def test_rejects_negative_quiz_passing_score(self, score):
        serializer = CompletionCriteraSerializer(
            data={
                "criteria_type": LessonCompletionCriteria.CriteriaType.PASS_QUIZ,
                "quiz_passing_score": score,
            }
        )

        assert not serializer.is_valid()
        assert "quiz_passing_score" in serializer.errors

    @pytest.mark.parametrize(
        "score",
        [
            "not-a-number",
            "75.5",
            True,
        ],
    )
    def test_rejects_invalid_quiz_passing_score(self, score):
        serializer = CompletionCriteraSerializer(
            data={
                "criteria_type": LessonCompletionCriteria.CriteriaType.PASS_QUIZ,
                "quiz_passing_score": score,
            }
        )

        assert not serializer.is_valid()
        assert "quiz_passing_score" in serializer.errors


class TestCompletionCriteraSerializerVideoWatchPercentage:
    @pytest.mark.parametrize(
        "percentage",
        [
            0,
            1,
            25,
            50,
            99,
            100,
        ],
    )
    def test_accepts_valid_integer_video_watch_percentage(self, percentage):
        serializer = CompletionCriteraSerializer(
            data={
                "criteria_type": LessonCompletionCriteria.CriteriaType.WATCH_VIDEO,
                "video_watch_percentage": percentage,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["video_watch_percentage"] == percentage

    def test_accepts_video_watch_percentage_as_numeric_string(self):
        serializer = CompletionCriteraSerializer(
            data={
                "criteria_type": LessonCompletionCriteria.CriteriaType.WATCH_VIDEO,
                "video_watch_percentage": "80",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["video_watch_percentage"] == 80

    def test_accepts_null_video_watch_percentage(self):
        serializer = CompletionCriteraSerializer(
            data={
                "criteria_type": LessonCompletionCriteria.CriteriaType.MANUAL,
                "video_watch_percentage": None,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["video_watch_percentage"] is None

    def test_omits_video_watch_percentage_when_not_provided(self):
        serializer = CompletionCriteraSerializer(
            data={
                "criteria_type": LessonCompletionCriteria.CriteriaType.MANUAL,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert "video_watch_percentage" not in serializer.validated_data

    @pytest.mark.parametrize(
        "percentage",
        [
            -1,
            -10,
        ],
    )
    def test_rejects_negative_video_watch_percentage(self, percentage):
        serializer = CompletionCriteraSerializer(
            data={
                "criteria_type": LessonCompletionCriteria.CriteriaType.WATCH_VIDEO,
                "video_watch_percentage": percentage,
            }
        )

        assert not serializer.is_valid()
        assert "video_watch_percentage" in serializer.errors

    @pytest.mark.parametrize(
        "percentage",
        [
            "not-a-number",
            "75.5",
            True,
        ],
    )
    def test_rejects_invalid_video_watch_percentage(self, percentage):
        serializer = CompletionCriteraSerializer(
            data={
                "criteria_type": LessonCompletionCriteria.CriteriaType.WATCH_VIDEO,
                "video_watch_percentage": percentage,
            }
        )

        assert not serializer.is_valid()
        assert "video_watch_percentage" in serializer.errors


class TestCompletionCriteraSerializerCriteriaCombinations:
    def test_accepts_manual_without_specific_criteria(self):
        serializer = CompletionCriteraSerializer(
            data={
                "criteria_type": LessonCompletionCriteria.CriteriaType.MANUAL,
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["criteria_type"] == (
            LessonCompletionCriteria.CriteriaType.MANUAL
        )

    def test_accepts_read_article_without_specific_criteria(self):
        serializer = CompletionCriteraSerializer(
            data={
                "criteria_type": LessonCompletionCriteria.CriteriaType.READ_ARTICLE,
            }
        )

        assert serializer.is_valid(), serializer.errors

    def test_accepts_submit_assignment_without_specific_criteria(self):
        serializer = CompletionCriteraSerializer(
            data={
                "criteria_type": (
                    LessonCompletionCriteria.CriteriaType.SUBMIT_ASSIGNMENT
                ),
            }
        )

        assert serializer.is_valid(), serializer.errors

    def test_accepts_watch_video_with_watch_percentage(self):
        serializer = CompletionCriteraSerializer(
            data={
                "criteria_type": LessonCompletionCriteria.CriteriaType.WATCH_VIDEO,
                "video_watch_percentage": 80,
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data == {
            "criteria_type": LessonCompletionCriteria.CriteriaType.WATCH_VIDEO,
            "video_watch_percentage": 80,
        }

    def test_accepts_pass_quiz_with_passing_score(self):
        serializer = CompletionCriteraSerializer(
            data={
                "criteria_type": LessonCompletionCriteria.CriteriaType.PASS_QUIZ,
                "quiz_passing_score": 70,
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data == {
            "criteria_type": LessonCompletionCriteria.CriteriaType.PASS_QUIZ,
            "quiz_passing_score": 70,
        }

    def test_serializer_does_not_apply_watch_video_model_clean_rules(self):
        serializer = CompletionCriteraSerializer(
            data={
                "criteria_type": LessonCompletionCriteria.CriteriaType.WATCH_VIDEO,
                "video_watch_percentage": 0,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["video_watch_percentage"] == 0

    def test_serializer_does_not_apply_pass_quiz_model_clean_rules(self):
        serializer = CompletionCriteraSerializer(
            data={
                "criteria_type": LessonCompletionCriteria.CriteriaType.PASS_QUIZ,
                "quiz_passing_score": 0,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["quiz_passing_score"] == 0

    def test_accepts_both_specific_fields(self):
        serializer = CompletionCriteraSerializer(
            data={
                "criteria_type": LessonCompletionCriteria.CriteriaType.WATCH_VIDEO,
                "video_watch_percentage": 80,
                "quiz_passing_score": 70,
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["video_watch_percentage"] == 80
        assert serializer.validated_data["quiz_passing_score"] == 70

    @pytest.mark.parametrize(
        "criteria_type",
        [
            LessonCompletionCriteria.CriteriaType.MANUAL,
            LessonCompletionCriteria.CriteriaType.READ_ARTICLE,
            LessonCompletionCriteria.CriteriaType.SUBMIT_ASSIGNMENT,
        ],
    )
    def test_accepts_specific_fields_for_other_criteria_types(
        self,
        criteria_type,
    ):
        serializer = CompletionCriteraSerializer(
            data={
                "criteria_type": criteria_type,
                "video_watch_percentage": 80,
                "quiz_passing_score": 70,
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["video_watch_percentage"] == 80
        assert serializer.validated_data["quiz_passing_score"] == 70


class TestCompletionCriteraSerializerSerialization:
    def test_serializes_all_fields(self):
        instance = LessonCompletionCriteria(
            criteria_type=LessonCompletionCriteria.CriteriaType.WATCH_VIDEO,
            video_watch_percentage=80,
            quiz_passing_score=None,
        )

        serializer = CompletionCriteraSerializer(instance=instance)

        assert serializer.data == {
            "criteria_type": LessonCompletionCriteria.CriteriaType.WATCH_VIDEO,
            "quiz_passing_score": None,
            "video_watch_percentage": 80,
        }

    def test_serializes_manual_criteria(self):
        instance = LessonCompletionCriteria(
            criteria_type=LessonCompletionCriteria.CriteriaType.MANUAL,
            video_watch_percentage=None,
            quiz_passing_score=None,
        )

        serializer = CompletionCriteraSerializer(instance=instance)

        assert serializer.data == {
            "criteria_type": LessonCompletionCriteria.CriteriaType.MANUAL,
            "quiz_passing_score": None,
            "video_watch_percentage": None,
        }

    def test_serializes_read_article_criteria(self):
        instance = LessonCompletionCriteria(
            criteria_type=LessonCompletionCriteria.CriteriaType.READ_ARTICLE,
        )

        serializer = CompletionCriteraSerializer(instance=instance)

        assert serializer.data["criteria_type"] == (
            LessonCompletionCriteria.CriteriaType.READ_ARTICLE
        )
        assert serializer.data["quiz_passing_score"] is None
        assert serializer.data["video_watch_percentage"] is None

    def test_serializes_pass_quiz_criteria(self):
        instance = LessonCompletionCriteria(
            criteria_type=LessonCompletionCriteria.CriteriaType.PASS_QUIZ,
            quiz_passing_score=75,
            video_watch_percentage=None,
        )

        serializer = CompletionCriteraSerializer(instance=instance)

        assert serializer.data == {
            "criteria_type": LessonCompletionCriteria.CriteriaType.PASS_QUIZ,
            "quiz_passing_score": 75,
            "video_watch_percentage": None,
        }

    def test_serializes_submit_assignment_criteria(self):
        instance = LessonCompletionCriteria(
            criteria_type=(LessonCompletionCriteria.CriteriaType.SUBMIT_ASSIGNMENT),
            quiz_passing_score=None,
            video_watch_percentage=None,
        )

        serializer = CompletionCriteraSerializer(instance=instance)

        assert serializer.data == {
            "criteria_type": (LessonCompletionCriteria.CriteriaType.SUBMIT_ASSIGNMENT),
            "quiz_passing_score": None,
            "video_watch_percentage": None,
        }

    def test_serializes_zero_values(self):
        instance = LessonCompletionCriteria(
            criteria_type=LessonCompletionCriteria.CriteriaType.MANUAL,
            quiz_passing_score=0,
            video_watch_percentage=0,
        )

        serializer = CompletionCriteraSerializer(instance=instance)

        assert serializer.data["quiz_passing_score"] == 0
        assert serializer.data["video_watch_percentage"] == 0


class TestCompletionCriteraSerializerPartialUpdates:
    def test_partial_update_accepts_empty_data(self):
        instance = LessonCompletionCriteria(
            criteria_type=LessonCompletionCriteria.CriteriaType.MANUAL,
        )

        serializer = CompletionCriteraSerializer(
            instance=instance,
            data={},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data == {}

    def test_partial_update_accepts_criteria_type(self):
        instance = LessonCompletionCriteria(
            criteria_type=LessonCompletionCriteria.CriteriaType.MANUAL,
        )

        serializer = CompletionCriteraSerializer(
            instance=instance,
            data={
                "criteria_type": (LessonCompletionCriteria.CriteriaType.READ_ARTICLE),
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["criteria_type"] == (
            LessonCompletionCriteria.CriteriaType.READ_ARTICLE
        )

    def test_partial_update_accepts_quiz_passing_score(self):
        instance = LessonCompletionCriteria(
            criteria_type=LessonCompletionCriteria.CriteriaType.PASS_QUIZ,
            quiz_passing_score=60,
        )

        serializer = CompletionCriteraSerializer(
            instance=instance,
            data={"quiz_passing_score": 80},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["quiz_passing_score"] == 80

    def test_partial_update_accepts_video_watch_percentage(self):
        instance = LessonCompletionCriteria(
            criteria_type=LessonCompletionCriteria.CriteriaType.WATCH_VIDEO,
            video_watch_percentage=60,
        )

        serializer = CompletionCriteraSerializer(
            instance=instance,
            data={"video_watch_percentage": 90},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["video_watch_percentage"] == 90

    def test_partial_update_accepts_null_quiz_passing_score(self):
        instance = LessonCompletionCriteria(
            criteria_type=LessonCompletionCriteria.CriteriaType.PASS_QUIZ,
            quiz_passing_score=70,
        )

        serializer = CompletionCriteraSerializer(
            instance=instance,
            data={"quiz_passing_score": None},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["quiz_passing_score"] is None

    def test_partial_update_accepts_null_video_watch_percentage(self):
        instance = LessonCompletionCriteria(
            criteria_type=LessonCompletionCriteria.CriteriaType.WATCH_VIDEO,
            video_watch_percentage=80,
        )

        serializer = CompletionCriteraSerializer(
            instance=instance,
            data={"video_watch_percentage": None},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["video_watch_percentage"] is None


class TestCompletionCriteraSerializerFullPayloads:
    def test_validates_complete_watch_video_payload(self):
        data = {
            "criteria_type": LessonCompletionCriteria.CriteriaType.WATCH_VIDEO,
            "video_watch_percentage": 90,
            "quiz_passing_score": None,
        }

        serializer = CompletionCriteraSerializer(data=data)

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data == data

    def test_validates_complete_pass_quiz_payload(self):
        data = {
            "criteria_type": LessonCompletionCriteria.CriteriaType.PASS_QUIZ,
            "quiz_passing_score": 80,
            "video_watch_percentage": None,
        }

        serializer = CompletionCriteraSerializer(data=data)

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data == data

    def test_validates_complete_manual_payload(self):
        data = {
            "criteria_type": LessonCompletionCriteria.CriteriaType.MANUAL,
            "quiz_passing_score": None,
            "video_watch_percentage": None,
        }

        serializer = CompletionCriteraSerializer(data=data)

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data == data
