from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404

from .models import Role


class InstructorRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        if not request.user.roles.filter(name=Role.Roles.INSTRUCTOR).exists():
            raise Http404()

        return super().dispatch(request, *args, **kwargs)


class StudentRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        if not request.user.roles.filter(name=Role.Roles.STUDENT).exists():
            raise Http404()

        return super().dispatch(request, *args, **kwargs)
