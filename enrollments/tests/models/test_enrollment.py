import pytest
from django.db import IntegrityError

from accounts.tests.factories import UserFactory
from courses.tests.factories import CourseFactory
from enrollments.models import Enrollment
from enrollments.tests.factories import EnrollmentFactory


@pytest.mark.django_db
class TestEnrollmentModel:
    """Tests for the Enrollment model."""

    @pytest.fixture
    def user(self):
        return UserFactory()

    @pytest.fixture
    def course(self):
        return CourseFactory()

    def test_create_enrollment(self, user, course):
        """An enrollment can be created."""
        enrollment = Enrollment.objects.create(
            user=user,
            course=course,
            status=Enrollment.Status.ACTIVE,
        )

        assert enrollment.user == user
        assert enrollment.course == course
        assert enrollment.status == Enrollment.Status.ACTIVE
        assert enrollment.enrolled_at is not None
        assert enrollment.completed_at is None

    def test_string_representation(self):
        """The string representation should include the user and course."""
        enrollment = EnrollmentFactory()

        assert str(enrollment) == (f"{enrollment.user} → {enrollment.course}")

    def test_status_defaults_to_active(self, user, course):
        """Status defaults to active."""
        enrollment = Enrollment.objects.create(
            user=user,
            course=course,
        )

        assert enrollment.status == Enrollment.Status.ACTIVE

    def test_completed_at_is_optional(self, user, course):
        """Completion date is optional."""
        enrollment = Enrollment.objects.create(
            user=user,
            course=course,
        )

        assert enrollment.completed_at is None

    def test_enrolled_at_is_set_automatically(self, user, course):
        """Enrollment date is set automatically."""
        enrollment = Enrollment.objects.create(
            user=user,
            course=course,
        )

        assert enrollment.enrolled_at is not None

    def test_user_cannot_enroll_twice_in_same_course(
        self,
        user,
        course,
    ):
        """A user cannot enroll in the same course twice."""
        EnrollmentFactory(
            user=user,
            course=course,
        )

        with pytest.raises(IntegrityError):
            EnrollmentFactory(
                user=user,
                course=course,
            )

    def test_user_can_enroll_in_multiple_courses(self, user):
        """A user can enroll in multiple courses."""
        enrollment1 = EnrollmentFactory(
            user=user,
        )

        enrollment2 = EnrollmentFactory(
            user=user,
        )

        assert set(user.enrollments.all()) == {
            enrollment1,
            enrollment2,
        }

    def test_multiple_users_can_enroll_in_same_course(self, course):
        """Multiple users can enroll in the same course."""
        enrollment1 = EnrollmentFactory(
            course=course,
        )

        enrollment2 = EnrollmentFactory(
            course=course,
        )

        assert set(course.enrollments.all()) == {
            enrollment1,
            enrollment2,
        }

    def test_deleting_user_deletes_enrollments(self):
        """Deleting a user cascades to its enrollments."""
        enrollment = EnrollmentFactory()

        user = enrollment.user

        user.delete()

        assert not Enrollment.objects.filter(
            pk=enrollment.pk,
        ).exists()

    def test_deleting_course_deletes_enrollments(self):
        """Deleting a course cascades to its enrollments."""
        enrollment = EnrollmentFactory()

        course = enrollment.course

        course.delete()

        assert not Enrollment.objects.filter(
            pk=enrollment.pk,
        ).exists()

    def test_enrollments_are_ordered_by_newest_first(self):
        """Enrollments are ordered by newest first."""
        older = EnrollmentFactory()
        newer = EnrollmentFactory()

        enrollments = list(Enrollment.objects.all())

        assert enrollments == [newer, older]
