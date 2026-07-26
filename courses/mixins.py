from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404


class InstructorRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        if not request.user.roles.filter(name="instructor").exists():
            raise Http404()

        return super().dispatch(request, *args, **kwargs)
