"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from core.views import MediaRangeView

urlpatterns = [
    path("", include("landing.urls")),
    path("api/v1/", include("landing.api.urls")),
    path("admin/", admin.site.urls),
    path("courses/", include("courses.urls")),
    path("api/v1/account/auth/", include("accounts.api.urls")),
    path("api/v1/account/", include("profiles.api.urls")),
    path("account/auth/", include("accounts.urls")),
    path("account/", include("profiles.urls")),
    path("instructor/", include("instructors.urls")),
    path("enrollment/", include("enrollments.urls")),
    path("api/v1/courses/", include("courses.api.urls")),
    path("api/v1/instructor/", include("instructors.api.urls")),
    path("api/v1/enrollment/", include("enrollments.api.urls")),
    path("api/v1/payment/", include("payments.api.urls")),
    path("payment/", include("payments.urls")),
    path("certificates/", include("certificates.urls")),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT,
    )

    urlpatterns += [
        path(
            "media/<path:path>",
            MediaRangeView.as_view(),
            name="media",
        ),
    ]
