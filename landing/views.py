from django.views.generic import TemplateView


class LandingPage(TemplateView):
    template_name = "landing/landing.html"
