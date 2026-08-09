from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView

from courses.models import Course


class CourseCatalog(TemplateView):
    template_name = "courses/catalog.html"


class CourseDetailView(DetailView):
    template_name = "courses/course_detail.html"

    def get_queryset(self):
        return Course.objects.filter(status=Course.Status.PUBLISHED)
