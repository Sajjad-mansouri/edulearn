from django.views.generic.base import TemplateView

from accounts.mixins import InstructorRequiredMixin


class CourseCreateTemplateView(InstructorRequiredMixin, TemplateView):
    template_name = "instructors/create_course.html"


class InstructorCourse(InstructorRequiredMixin, TemplateView):
    template_name = "instructors/instructor_courses.html"


class Students(InstructorRequiredMixin, TemplateView):
    template_name = "instructors/students.html"


class Assignments(InstructorRequiredMixin, TemplateView):
    template_name = "instructors/assignments.html"


class CourseUpateTemplateView(InstructorRequiredMixin, TemplateView):
    template_name = "instructors/update_course.html"


class InstructorAnalytics(InstructorRequiredMixin, TemplateView):
    template_name = "instructors/analytics.html"


class InstructorRevenue(InstructorRequiredMixin, TemplateView):
    template_name = "instructors/revenue.html"


class InstructorCoursePreview(InstructorRequiredMixin, TemplateView):
    template_name = "instructors/course_preview.html"
