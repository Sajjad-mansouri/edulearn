# mixins.py
from rest_framework.exceptions import NotFound

from courses.models import Course
from enrollments.models import Enrollment


class EnrollmentResolverMixin:
    """
    Resolves enrollment (or owner mode) early and attaches it to the view.
    Works with both function-based URL kwargs and DRF generic views.
    """

    enrollment = None  # type: Enrollment | None

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self._resolve_enrollment(request, **kwargs)

    def _resolve_enrollment(self, request, **kwargs):
        enrollment_id = kwargs.get("enrollment_id")
        course_id = kwargs.get("course_id")  # or whatever your lookup is
        print("_resolve_enrollment")
        if enrollment_id:
            try:
                self.enrollment = Enrollment.objects.select_related("course").get(
                    id=enrollment_id,
                    user=request.user,
                    status__in=[Enrollment.Status.ACTIVE, Enrollment.Status.COMPLETED],
                )
            except Enrollment.DoesNotExist:
                raise NotFound() from None
        elif course_id:
            # Owner path – just verify ownership exists
            if not Course.objects.filter(id=course_id, owner=request.user).exists():
                raise NotFound() from None
            self.enrollment = None
        else:
            raise NotFound()
