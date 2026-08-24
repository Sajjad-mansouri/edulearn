# Create your views here.
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class SuccessPayment(LoginRequiredMixin, TemplateView):
    template_name = "payments/success_payment.html"


class CancelPayment(LoginRequiredMixin, TemplateView):
    template_name = "payments/cancel_payment.html"
