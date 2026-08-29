from django.urls import path

from . import views

app_name = "certification"
urlpatterns = [
    path(
        "verify/<certificate_number>/",
        views.CerficationVerify.as_view(),
        name="verify_certificate",
    )
]
