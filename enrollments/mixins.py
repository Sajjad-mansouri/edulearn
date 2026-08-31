from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404

from accounts.models import Role

from .models import Enrollment


class EnrollmentRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        enrollment_id = kwargs.get("enrollment_id")
        print("enrollment_id", enrollment_id)
        if enrollment_id:
            try:
                self.enrollment = Enrollment.objects.select_related("course").get(
                    id=enrollment_id, user=request.user
                )
            except Enrollment.DoesNotExist:
                raise Http404() from None

        else:
            try:
                self.request.user.roles.get(name=Role.Roles.INSTRUCTOR)
                self.enrollment = None
            except Role.DoesNotExist:
                raise Http404() from None

        return super().dispatch(request, *args, **kwargs)
