from django.urls import path

from . import views

app_name = "payment_api"
urlpatterns = [
    path(
        "enrollments/<int:enrollment_id>/checkout/",
        views.CreateCheckoutSessionApiView.as_view(),
        name="create_checkout_session",
    ),
    path(
        "webhooks/stripe/",
        views.StripeWebhookApiView.as_view(),
        name="stripe-webhook",
    ),
]
