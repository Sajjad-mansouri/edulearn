from django.db import models


class EmailInbox(models.Model):
    name = models.CharField(max_length=150)
    subject = models.CharField(max_length=250, blank=True)
    email = models.EmailField(max_length=150)
    message = models.TextField()


class SiteFeature(models.Model):
    title = models.CharField()


class AbstractBaseItem(models.Model):
    title = models.CharField(max_length=250)
    description = models.TextField()
    icon = models.CharField(max_length=250)
    color = models.CharField(max_length=100)


class FeatureItem(AbstractBaseItem):
    feature = models.ForeignKey(
        SiteFeature, on_delete=models.CASCADE, related_name="items"
    )
    image = models.ImageField(upload_to="landing/feature/")


class SiteHighlight(AbstractBaseItem):
    pass


class HighlightEdpoint(models.Model):
    highlight = models.ForeignKey(
        SiteHighlight, on_delete=models.CASCADE, related_name="endpoints"
    )
    end_point = models.CharField()


class Contact(models.Model):
    name = models.CharField(max_length=250)
    title = models.CharField(max_length=250)
    description = models.TextField()
    email = models.EmailField()


class SocialLink(models.Model):
    contact = models.ForeignKey(
        Contact, on_delete=models.CASCADE, related_name="social_links"
    )
    platform = models.CharField(max_length=250)
    url = models.URLField()
    icon = models.CharField(max_length=250)
    username = models.CharField(max_length=250)


class APIEndpoint(models.Model):
    count = models.IntegerField(default=0)
