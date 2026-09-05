# Create your views here.
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView
from rest_framework.permissions import AllowAny

from .models import Certificate


class CerficationVerify(DetailView):
    template_name = "certificates/certificate.html"
    permission_classes = [AllowAny]

    def get_object(self):
        certificate_number = self.kwargs.get("certificate_number")
        return get_object_or_404(Certificate, certificate_number=certificate_number)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        enrollment = self.object.enrollment
        context["certificate"] = self.object
        context["student"] = enrollment.user
        context["course"] = enrollment.course
