from django.urls import path

from . import views

urlpatterns = [
    path("site-info/", views.LandingPageInfo.as_view(), name="landing_page_info"),
    path("message/", views.ContactMessage.as_view(), name="contact_message"),
]
