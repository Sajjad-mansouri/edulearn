# Create your views here.
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.views.generic.base import TemplateView


class CourseCreateTemplateView(LoginRequiredMixin, TemplateView):
    template_name = "courses/create_course.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.roles.filter(name="instructor").exists():
            raise Http404()
        return super().dispatch(request, *args, **kwargs)
