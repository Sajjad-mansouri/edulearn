from rest_framework.exceptions import NotFound

from courses.models import Course
from enrollments.models import Enrollment


class EnrollmentResolverMixin:
    """
    Resolves enrollment (or owner mode) early and attaches it to the view.
    Works with both function-based URL kwargs and DRF generic views.
    """

    enrollment = None

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self._resolve_enrollment(request, **kwargs)

    def _resolve_enrollment(self, request, **kwargs):
        if not request.user.is_authenticated:
            raise NotFound()

        enrollment_id = kwargs.get("enrollment_id")
        course_id = kwargs.get("course_id")

        if enrollment_id:
            try:
                self.enrollment = Enrollment.objects.select_related("course").get(
                    id=enrollment_id,
                    user=request.user,
                    status__in=[
                        Enrollment.Status.ACTIVE,
                        Enrollment.Status.COMPLETED,
                    ],
                )
            except Enrollment.DoesNotExist:
                raise NotFound() from None

        elif course_id:
            if not Course.objects.filter(
                id=course_id,
                owner=request.user,
            ).exists():
                raise NotFound()

            self.enrollment = None

        else:
            raise NotFound()
