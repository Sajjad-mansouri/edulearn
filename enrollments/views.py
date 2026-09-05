# Create your views here.
from django.views.generic import TemplateView

from accounts.mixins import StudentRequiredMixin

from .mixins import EnrollmentOrOwnerRequiredMixin


class CourseLearningView(EnrollmentOrOwnerRequiredMixin, TemplateView):
    template_name = "enrollments/course_learning.html"


class StudentCoursesView(StudentRequiredMixin, TemplateView):
    template_name = "enrollments/student_courses.html"


class StudentWishlistView(StudentRequiredMixin, TemplateView):
    template_name = "enrollments/wishlist.html"


class StudentCertificatesView(StudentRequiredMixin, TemplateView):
    template_name = "enrollments/certificates.html"
