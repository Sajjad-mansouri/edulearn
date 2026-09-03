from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from landing.models import APIEndpoint, Contact, SiteFeature, SiteHighlight

from .serializers import (
    APIEnpointSerializer,
    ContactSerializer,
    EmailInboxSerializer,
    FeatureSerializer,
    HighlightSerializer,
)
from .tasks import send_email_task


def get_current_site_address(request):
    current_site = get_current_site(request)
    site_name = current_site.name
    protocol = "https" if request.is_secure() else "http"
    site_address = f"{protocol}://{current_site.domain}"
    return site_name, site_address


def message_feedback(request, name, user_email, message):
    site_name, site_address = get_current_site_address(request)
    kwargs = {
        "site_name": site_name,
        "site_address": site_address,
        "name": name,
        "email": user_email,
        "message": message,
    }
    if settings.HOST_ASYNC_ABILITY:
        send_email_task.delay(**kwargs)
    else:
        send_email_task(**kwargs)


class ContactMessage(CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = EmailInboxSerializer

    def perform_create(self, serializer):
        instance = serializer.save()
        message_feedback(self.request, instance.name, instance.email, instance.message)


class LandingPageInfo(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        feature_qs = SiteFeature.objects.all()
        highlight_qs = SiteHighlight.objects.all()
        contact = Contact.objects.first()
        api_endpoint = APIEndpoint.objects.first()

        feature_serializer = FeatureSerializer(feature_qs, many=True)
        highlight_serializer = HighlightSerializer(highlight_qs, many=True)
        contact_serializer = ContactSerializer(contact)
        api_endpoint_serializer = APIEnpointSerializer(api_endpoint)
        print(
            {
                "features": feature_serializer.data,
                "highlights": highlight_serializer.data,
                "contact": contact_serializer.data,
            }
        )
        return Response(
            {
                "features": feature_serializer.data,
                "highlights": highlight_serializer.data,
                "contact": contact_serializer.data,
                "api_endpoints": api_endpoint_serializer.data,
            }
        )
