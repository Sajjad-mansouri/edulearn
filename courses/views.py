from django.views.generic.base import TemplateView


class CourseCatalog(TemplateView):
    template_name = "courses/catalog.html"
