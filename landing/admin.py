from django.contrib import admin

from .models import (
    APIEndpoint,
    Contact,
    EmailInbox,
    FeatureItem,
    HighlightEdpoint,
    SiteFeature,
    SiteHighlight,
    SocialLink,
)

admin.site.register(EmailInbox)
admin.site.register(SiteFeature)
admin.site.register(FeatureItem)
admin.site.register(SiteHighlight)
admin.site.register(HighlightEdpoint)
admin.site.register(Contact)
admin.site.register(SocialLink)
admin.site.register(APIEndpoint)
