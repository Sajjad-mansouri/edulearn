# Create your views here.
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from .mixins import EnrollmentRequiredMixin


class CourseLearningView(EnrollmentRequiredMixin, TemplateView):
    template_name = "enrollments/course_learning.html"


class StudentCoursesView(LoginRequiredMixin, TemplateView):
    template_name = "enrollments/student_courses.html"


class StudentWishlistView(LoginRequiredMixin, TemplateView):
    template_name = "enrollments/wishlist.html"
