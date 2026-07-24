import datetime

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from assessments.models import Assignment
from assessments.tests.factories import AssignmentFactory
from curriculums.tests.factories import LessonContentFactory


@pytest.mark.django_db
class TestAssignmentModel:
    """Tests for the Assignment model."""

    @pytest.fixture
    def content(self):
        return LessonContentFactory()

    def test_create_assignment(self, content):
        """An assignment can be created."""
        due_date = datetime.datetime(
            2030,
            1,
            1,
            12,
            0,
            tzinfo=datetime.UTC,
        )

        assignment = Assignment.objects.create(
            content=content,
            instructions="Complete the project.",
            max_score=50,
            due_date=due_date,
            allow_late_submission=True,
            max_attempts=3,
            accepted_file_types="pdf,zip",
            max_file_size_mb=100,
        )

        assert assignment.content == content
        assert assignment.instructions == "Complete the project."
        assert assignment.max_score == 50
        assert assignment.due_date == due_date
        assert assignment.allow_late_submission is True
        assert assignment.max_attempts == 3
        assert assignment.accepted_file_types == "pdf,zip"
        assert assignment.max_file_size_mb == 100

    def test_string_representation(self):
        """String representation returns lesson content title."""
        assignment = AssignmentFactory()

        assert str(assignment) == assignment.content.title

    def test_max_score_defaults_to_100(self, content):
        """Maximum score defaults to 100."""
        assignment = Assignment.objects.create(
            content=content,
            instructions="Instructions",
        )

        assert assignment.max_score == 100

    def test_due_date_is_optional(self, content):
        """Due date is optional."""
        assignment = Assignment.objects.create(
            content=content,
            instructions="Instructions",
        )

        assert assignment.due_date is None

    def test_allow_late_submission_defaults_to_false(self, content):
        """Late submissions are disabled by default."""
        assignment = Assignment.objects.create(
            content=content,
            instructions="Instructions",
        )

        assert assignment.allow_late_submission is False

    def test_max_attempts_defaults_to_one(self, content):
        """Maximum attempts defaults to one."""
        assignment = Assignment.objects.create(
            content=content,
            instructions="Instructions",
        )

        assert assignment.max_attempts == 1

    def test_accepted_file_types_defaults_to_empty(self, content):
        """Accepted file types default to empty."""
        assignment = Assignment.objects.create(
            content=content,
            instructions="Instructions",
        )

        assert assignment.accepted_file_types == ""

    def test_max_file_size_defaults_to_50(self, content):
        """Maximum file size defaults to 50 MB."""
        assignment = Assignment.objects.create(
            content=content,
            instructions="Instructions",
        )

        assert assignment.max_file_size_mb == 50

    def test_content_can_have_only_one_assignment(self, content):
        """Each lesson content can have only one assignment."""
        AssignmentFactory(content=content)

        with pytest.raises(IntegrityError):
            AssignmentFactory(content=content)

    def test_max_score_must_be_greater_than_zero(self, content):
        """Maximum score must be greater than zero."""
        assignment = Assignment(
            content=content,
            instructions="Instructions",
            max_score=0,
        )

        with pytest.raises(ValidationError):
            assignment.full_clean()

    def test_max_file_size_must_be_greater_than_zero(self, content):
        """Maximum file size must be greater than zero."""
        assignment = Assignment(
            content=content,
            instructions="Instructions",
            max_file_size_mb=0,
        )

        with pytest.raises(ValidationError):
            assignment.full_clean()

    def test_deleting_lesson_content_deletes_assignment(self):
        """Deleting lesson content cascades to assignment."""
        assignment = AssignmentFactory()

        content = assignment.content

        content.delete()

        assert not Assignment.objects.filter(
            pk=assignment.pk,
        ).exists()
