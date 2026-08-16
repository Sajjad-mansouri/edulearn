# Create your views here.
from django.views.generic import TemplateView

from .mixins import EnrollmentRequiredMixin


class CourseLearningView(EnrollmentRequiredMixin, TemplateView):
    template_name = "enrollments/course_learning.html"
