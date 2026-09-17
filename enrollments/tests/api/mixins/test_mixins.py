import pytest
from django.contrib.auth.models import AnonymousUser
from rest_framework.exceptions import NotFound
from rest_framework.test import APIRequestFactory

from enrollments.api.mixins import EnrollmentResolverMixin
from enrollments.models import Enrollment


class TestView(EnrollmentResolverMixin):
    def initial(self, request, *args, **kwargs):
        self.request = request
        self.args = args
        self.kwargs = kwargs
        self._resolve_enrollment(request, **kwargs)


class TestEnrollmentResolverMixin:
    @pytest.fixture
    def factory(self):
        return APIRequestFactory()

    def test_resolves_active_enrollment_for_owner(
        self,
        factory,
        test_user,
        enrollment,
    ):
        request = factory.get("/")
        request.user = test_user

        view = TestView()

        view.initial(
            request,
            enrollment_id=enrollment.id,
        )

        assert view.enrollment == enrollment
        assert view.enrollment.user == test_user
        assert view.enrollment.course == enrollment.course

    def test_resolves_completed_enrollment_for_owner(
        self,
        factory,
        test_user,
        course,
    ):
        enrollment = Enrollment.objects.create(
            user=test_user,
            course=course,
            status=Enrollment.Status.COMPLETED,
        )

        request = factory.get("/")
        request.user = test_user

        view = TestView()

        view.initial(
            request,
            enrollment_id=enrollment.id,
        )

        assert view.enrollment == enrollment

    @pytest.mark.parametrize(
        "status",
        [
            Enrollment.Status.PENDING,
            Enrollment.Status.CANCELLED,
            Enrollment.Status.SUSPENDED,
        ],
    )
    def test_does_not_resolve_ineligible_enrollment(
        self,
        factory,
        test_user,
        course,
        status,
    ):
        enrollment = Enrollment.objects.create(
            user=test_user,
            course=course,
            status=status,
        )

        request = factory.get("/")
        request.user = test_user

        view = TestView()

        with pytest.raises(NotFound):
            view.initial(
                request,
                enrollment_id=enrollment.id,
            )

    def test_does_not_resolve_another_users_enrollment(
        self,
        factory,
        test_user,
        another_user_enrollment,
    ):
        request = factory.get("/")
        request.user = test_user

        view = TestView()

        with pytest.raises(NotFound):
            view.initial(
                request,
                enrollment_id=another_user_enrollment.id,
            )

    def test_nonexistent_enrollment_raises_not_found(
        self,
        factory,
        test_user,
    ):
        request = factory.get("/")
        request.user = test_user

        view = TestView()

        with pytest.raises(NotFound):
            view.initial(
                request,
                enrollment_id=999999,
            )

    def test_resolves_owner_course_without_enrollment(
        self,
        factory,
        test_user,
        course,
    ):
        request = factory.get("/")
        request.user = test_user

        view = TestView()

        view.initial(
            request,
            course_id=course.id,
        )

        assert view.enrollment is None

    def test_non_owner_cannot_resolve_course(
        self,
        factory,
        another_user,
        course,
    ):
        request = factory.get("/")
        request.user = another_user

        view = TestView()

        with pytest.raises(NotFound):
            view.initial(
                request,
                course_id=course.id,
            )

    def test_nonexistent_course_raises_not_found(
        self,
        factory,
        test_user,
    ):
        request = factory.get("/")
        request.user = test_user

        view = TestView()

        with pytest.raises(NotFound):
            view.initial(
                request,
                course_id=999999,
            )

    def test_missing_resource_identifier_raises_not_found(
        self,
        factory,
        test_user,
    ):
        request = factory.get("/")
        request.user = test_user

        view = TestView()

        with pytest.raises(NotFound):
            view.initial(request)

    def test_enrollment_takes_precedence_when_both_identifiers_are_provided(
        self,
        factory,
        test_user,
        enrollment,
        another_user,
        category,
    ):
        another_course = enrollment.course.__class__.objects.create(
            title="Another Course",
            owner=another_user,
            category=category,
        )

        request = factory.get("/")
        request.user = test_user

        view = TestView()

        view.initial(
            request,
            enrollment_id=enrollment.id,
            course_id=another_course.id,
        )

        assert view.enrollment == enrollment

    def test_unauthenticated_user_cannot_resolve_enrollment(
        self,
        factory,
        enrollment,
    ):
        request = factory.get("/")
        request.user = AnonymousUser()

        view = TestView()

        with pytest.raises(NotFound):
            view.initial(
                request,
                enrollment_id=enrollment.id,
            )

    def test_unauthenticated_user_cannot_resolve_course_owner_path(
        self,
        factory,
        course,
    ):
        request = factory.get("/")
        request.user = AnonymousUser()

        view = TestView()

        with pytest.raises(NotFound):
            view.initial(
                request,
                course_id=course.id,
            )
