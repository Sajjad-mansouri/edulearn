# Create your views here.
from django.views.generic import TemplateView

from accounts.mixins import InstructorRequiredMixin, StudentRequiredMixin


class StudentProfileView(StudentRequiredMixin, TemplateView):
    template_name = "profiles/student/profile.html"


class InstructorProfileView(InstructorRequiredMixin, TemplateView):
    template_name = "profiles/instructor/profile.html"
