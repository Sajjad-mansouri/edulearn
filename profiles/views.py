# Create your views here.
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class StudentProfileView(LoginRequiredMixin, TemplateView):
    template_name = "profiles/student/profile.html"


class InstructorProfileView(LoginRequiredMixin, TemplateView):
    template_name = "profiles/instructor/profile.html"
