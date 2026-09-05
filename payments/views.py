# Create your views here.
from django.views.generic import TemplateView

from accounts.mixins import StudentRequiredMixin


class SuccessPayment(StudentRequiredMixin, TemplateView):
    template_name = "payments/success_payment.html"


class CancelPayment(StudentRequiredMixin, TemplateView):
    template_name = "payments/cancel_payment.html"
