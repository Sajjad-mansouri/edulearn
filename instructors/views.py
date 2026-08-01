from django.views.generic.base import TemplateView

from .mixins import InstructorRequiredMixin


class CourseCreateTemplateView(InstructorRequiredMixin, TemplateView):
    template_name = "instructors/create_course.html"


class InstructorCourse(InstructorRequiredMixin, TemplateView):
    template_name = "instructors/instructor_courses.html"
