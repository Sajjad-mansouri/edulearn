from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404

from courses.models import Course

from .models import Enrollment


class EnrollmentOrOwnerRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        enrollment_id = kwargs.get("enrollment_id")
        if enrollment_id:
            try:
                self.enrollment = Enrollment.objects.select_related("course").get(
                    id=enrollment_id,
                    user=request.user,
                    status__in=[Enrollment.Status.ACTIVE, Enrollment.Status.COMPLETED],
                )
            except Enrollment.DoesNotExist:
                raise Http404() from None

        else:
            course_id = kwargs.get("course_id")
            if course_id:
                try:
                    Course.objects.filter(id=course_id, owner=request.user)
                    self.enrollment = None
                except Course.DoesNotExist:
                    raise Http404() from None
            else:
                raise Http404()
        return super().dispatch(request, *args, **kwargs)
