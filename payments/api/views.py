import stripe
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from enrollments.api.permissions import IsEnrolled
from enrollments.models import Enrollment
from payments.api.serializers import CheckoutSessionResponseSerializer
from payments.exceptions import (
    CourseNotPriced,
    EnrollmentAccessDenied,
    EnrollmentAlreadyPaid,
    EnrollmentNotPayable,
    StripeSessionCreationFailed,
)
from payments.services.checkout import CheckoutService
from payments.services.webhook import handle_checkout_session_completed


class CreateCheckoutSessionApiView(APIView):
    permission_classes = [IsEnrolled]

    def post(self, request, enrollment_id):
        enrollment = get_object_or_404(Enrollment, id=enrollment_id, user=request.user)

        try:
            payment = CheckoutService.create_checkout_session(
                enrollment=enrollment, user=request.user
            )

        except EnrollmentAccessDenied as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)

        except EnrollmentNotPayable as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        except EnrollmentAlreadyPaid as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)

        except CourseNotPriced as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        except StripeSessionCreationFailed as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        serializer = CheckoutSessionResponseSerializer(payment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookApiView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                settings.STRIPE_WEBHOOK_SECRET,
            )
        except (ValueError, stripe.SignatureVerificationError):
            return HttpResponse(status=400)

        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            handle_checkout_session_completed(session)

        return HttpResponse(status=200)
