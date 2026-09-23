import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from assessments.models.assignment import Assignment
from courses.models.course import Course
from curriculums.models.lesson import Lesson
from curriculums.models.lesson_content import LessonContent
from curriculums.models.section import Section

User = get_user_model()


@pytest.fixture
def assignment_user(db):
    return User.objects.create_user(
        username="assignment_user",
        email="assignment_user@example.com",
        password="test-password",
    )


@pytest.fixture
def assignment_course(db, assignment_user):
    return Course.objects.create(
        title="Assignment Course",
        owner=assignment_user,
    )


@pytest.fixture
def assignment_section(db, assignment_course):
    return Section.objects.create(
        course=assignment_course,
        title="Assignment Section",
    )


@pytest.fixture
def assignment_lesson(db, assignment_section):
    return Lesson.objects.create(
        section=assignment_section,
        title="Assignment Lesson",
        slug="assignment-lesson",
    )


@pytest.fixture
def lesson_content(db, assignment_lesson):
    return LessonContent.objects.create(
        lesson=assignment_lesson,
        title="Assignment Content",
        content_type=LessonContent.Type.ASSIGNMENT,
        order=1,
    )


@pytest.fixture
def assignment(db, lesson_content):
    return Assignment.objects.create(
        content=lesson_content,
    )


class TestAssignmentCreation:
    def test_creates_assignment(self, assignment, lesson_content):
        assert assignment.pk is not None
        assert assignment.content == lesson_content

    def test_default_passing_score_is_seventy(self, assignment):
        assert assignment.passing_score == 70

    def test_default_max_score_is_one_hundred(self, assignment):
        assert assignment.max_score == 100

    def test_default_allow_late_submission_is_false(self, assignment):
        assert assignment.allow_late_submission is False

    def test_default_max_attempts_is_one(self, assignment):
        assert assignment.max_attempts == 1

    def test_default_max_file_size_is_fifty_mb(self, assignment):
        assert assignment.max_file_size_mb == 50

    def test_instructions_default_to_empty_string(self, assignment):
        assert assignment.instructions == ""

    def test_accepted_file_types_default_to_empty_string(self, assignment):
        assert assignment.accepted_file_types == ""

    def test_due_date_defaults_to_none(self, assignment):
        assert assignment.due_date is None

    def test_str_returns_content_title(self, assignment, lesson_content):
        assert str(assignment) == lesson_content.title


class TestAssignmentFields:
    @pytest.mark.parametrize(
        "instructions",
        [
            "",
            "Submit your completed assignment.",
            "Write a detailed explanation of your solution.",
        ],
    )
    def test_instructions_accepts_values(
        self,
        lesson_content,
        instructions,
    ):
        assignment = Assignment.objects.create(
            content=lesson_content,
            instructions=instructions,
        )

        assignment.refresh_from_db()

        assert assignment.instructions == instructions

    @pytest.mark.parametrize(
        "passing_score",
        [0, 50, 70, 100, None],
    )
    def test_passing_score_accepts_supported_values(
        self,
        lesson_content,
        passing_score,
    ):
        assignment = Assignment.objects.create(
            content=lesson_content,
            passing_score=passing_score,
        )

        assignment.refresh_from_db()

        assert assignment.passing_score == passing_score

    @pytest.mark.parametrize(
        "max_score",
        [0, 50, 100, None],
    )
    def test_max_score_accepts_supported_values(
        self,
        lesson_content,
        max_score,
    ):
        assignment = Assignment.objects.create(
            content=lesson_content,
            max_score=max_score,
        )

        assignment.refresh_from_db()

        assert assignment.max_score == max_score

    @pytest.mark.parametrize(
        "allow_late_submission",
        [True, False],
    )
    def test_allow_late_submission_accepts_boolean_values(
        self,
        lesson_content,
        allow_late_submission,
    ):
        assignment = Assignment.objects.create(
            content=lesson_content,
            allow_late_submission=allow_late_submission,
        )

        assignment.refresh_from_db()

        assert assignment.allow_late_submission is allow_late_submission

    @pytest.mark.parametrize(
        "max_attempts",
        [0, 1, 2, 10],
    )
    def test_max_attempts_accepts_non_negative_values(
        self,
        lesson_content,
        max_attempts,
    ):
        assignment = Assignment.objects.create(
            content=lesson_content,
            max_attempts=max_attempts,
        )

        assignment.refresh_from_db()

        assert assignment.max_attempts == max_attempts

    @pytest.mark.parametrize(
        "accepted_file_types",
        [
            "",
            "pdf",
            "pdf,docx",
            "pdf,docx,zip",
        ],
    )
    def test_accepted_file_types_accepts_values(
        self,
        lesson_content,
        accepted_file_types,
    ):
        assignment = Assignment.objects.create(
            content=lesson_content,
            accepted_file_types=accepted_file_types,
        )

        assignment.refresh_from_db()

        assert assignment.accepted_file_types == accepted_file_types

    @pytest.mark.parametrize(
        "max_file_size_mb",
        [1, 10, 50, 100],
    )
    def test_max_file_size_accepts_positive_values(
        self,
        lesson_content,
        max_file_size_mb,
    ):
        assignment = Assignment.objects.create(
            content=lesson_content,
            max_file_size_mb=max_file_size_mb,
        )

        assignment.refresh_from_db()

        assert assignment.max_file_size_mb == max_file_size_mb


class TestAssignmentOptionalFields:
    def test_due_date_can_be_set(
        self,
        lesson_content,
    ):
        due_date = timezone.now()

        assignment = Assignment.objects.create(
            content=lesson_content,
            due_date=due_date,
        )

        assignment.refresh_from_db()

        assert assignment.due_date == due_date

    def test_due_date_can_be_null(self, assignment):
        assignment.due_date = None
        assignment.save()

        assignment.refresh_from_db()

        assert assignment.due_date is None

    def test_passing_score_can_be_null(self, lesson_content):
        assignment = Assignment.objects.create(
            content=lesson_content,
            passing_score=None,
        )

        assignment.refresh_from_db()

        assert assignment.passing_score is None

    def test_max_score_can_be_null(self, lesson_content):
        assignment = Assignment.objects.create(
            content=lesson_content,
            max_score=None,
        )

        assignment.refresh_from_db()

        assert assignment.max_score is None


class TestAssignmentRequiredFields:
    def test_content_is_required(self):
        assignment = Assignment()

        with pytest.raises(ValidationError) as exc_info:
            Assignment._meta.get_field("content").validate(
                assignment.content_id,
                assignment,
            )

        assert exc_info.value.messages

    def test_max_file_size_is_required(self, lesson_content):
        assignment = Assignment(
            content=lesson_content,
            max_file_size_mb=None,
        )

        with pytest.raises(ValidationError) as exc_info:
            Assignment._meta.get_field("max_file_size_mb").validate(
                assignment.max_file_size_mb,
                assignment,
            )

        assert exc_info.value.messages

    def test_max_attempts_is_required(self, lesson_content):
        assignment = Assignment(
            content=lesson_content,
            max_attempts=None,
        )

        with pytest.raises(ValidationError) as exc_info:
            Assignment._meta.get_field("max_attempts").validate(
                assignment.max_attempts,
                assignment,
            )

        assert exc_info.value.messages


class TestAssignmentValidation:
    def test_valid_max_score_passes_clean(self, lesson_content):
        assignment = Assignment(
            content=lesson_content,
            max_score=100,
        )

        assignment.full_clean()

    def test_zero_max_score_is_allowed_by_current_clean_method(
        self,
        lesson_content,
    ):
        assignment = Assignment(
            content=lesson_content,
            max_score=0,
        )

        assignment.clean()

        assert assignment.max_score == 0

    def test_negative_max_score_is_rejected_by_positive_field(
        self,
        lesson_content,
    ):
        assignment = Assignment(
            content=lesson_content,
            max_score=-1,
        )

        with pytest.raises(ValidationError) as exc_info:
            assignment.full_clean()

        assert "max_score" in exc_info.value.message_dict

    def test_clean_rejects_negative_max_score_if_reached_directly(
        self,
        lesson_content,
    ):
        assignment = Assignment(
            content=lesson_content,
            max_score=-1,
        )

        with pytest.raises(ValidationError) as exc_info:
            assignment.clean()

        assert "max_score" in exc_info.value.message_dict
        assert (
            "Passing score must be greater than zero."
            in exc_info.value.message_dict["max_score"]
        )

    def test_valid_max_file_size_passes_clean(self, lesson_content):
        assignment = Assignment(
            content=lesson_content,
            max_file_size_mb=50,
        )

        assignment.full_clean()

    def test_max_file_size_of_zero_is_rejected(
        self,
        lesson_content,
    ):
        assignment = Assignment(
            content=lesson_content,
            max_file_size_mb=0,
        )

        with pytest.raises(ValidationError) as exc_info:
            assignment.full_clean()

        assert "max_file_size_mb" in exc_info.value.message_dict
        assert (
            "Maximum file size must be greater than zero."
            in exc_info.value.message_dict["max_file_size_mb"]
        )

    def test_negative_max_file_size_is_rejected_by_positive_field(
        self,
        lesson_content,
    ):
        assignment = Assignment(
            content=lesson_content,
            max_file_size_mb=-1,
        )

        with pytest.raises(ValidationError) as exc_info:
            assignment.full_clean()

        assert "max_file_size_mb" in exc_info.value.message_dict


class TestAssignmentRelationship:
    def test_content_has_reverse_assignment_relation(
        self,
        assignment,
        lesson_content,
    ):
        assert lesson_content.assignment == assignment

    def test_content_is_one_to_one(self, assignment, lesson_content):
        assert assignment.content_id == lesson_content.pk

    def test_second_assignment_cannot_use_same_content(
        self,
        assignment,
        lesson_content,
    ):
        duplicate = Assignment(
            content=lesson_content,
        )

        with pytest.raises(IntegrityError):
            duplicate.save()

    def test_deleting_content_cascades_to_assignment(
        self,
        assignment,
        lesson_content,
    ):
        assignment_id = assignment.pk

        lesson_content.delete()

        assert not Assignment.objects.filter(pk=assignment_id).exists()


class TestAssignmentPersistence:
    def test_updates_instructions(
        self,
        assignment,
    ):
        assignment.instructions = "Updated instructions."
        assignment.save()

        assignment.refresh_from_db()

        assert assignment.instructions == "Updated instructions."

    def test_updates_passing_score(
        self,
        assignment,
    ):
        assignment.passing_score = 80
        assignment.save()

        assignment.refresh_from_db()

        assert assignment.passing_score == 80

    def test_updates_max_score(
        self,
        assignment,
    ):
        assignment.max_score = 120
        assignment.save()

        assignment.refresh_from_db()

        assert assignment.max_score == 120

    def test_updates_due_date(
        self,
        assignment,
    ):
        due_date = timezone.now()
        assignment.due_date = due_date
        assignment.save()

        assignment.refresh_from_db()

        assert assignment.due_date == due_date

    def test_updates_allow_late_submission(
        self,
        assignment,
    ):
        assignment.allow_late_submission = True
        assignment.save()

        assignment.refresh_from_db()

        assert assignment.allow_late_submission is True

    def test_updates_max_attempts(
        self,
        assignment,
    ):
        assignment.max_attempts = 3
        assignment.save()

        assignment.refresh_from_db()

        assert assignment.max_attempts == 3

    def test_updates_accepted_file_types(
        self,
        assignment,
    ):
        assignment.accepted_file_types = "pdf,docx"
        assignment.save()

        assignment.refresh_from_db()

        assert assignment.accepted_file_types == "pdf,docx"

    def test_updates_max_file_size(
        self,
        assignment,
    ):
        assignment.max_file_size_mb = 100
        assignment.save()

        assignment.refresh_from_db()

        assert assignment.max_file_size_mb == 100
