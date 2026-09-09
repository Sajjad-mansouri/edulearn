# signals.py
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Enrollment
from .tasks import create_certificate_task


@receiver(post_save, sender=Enrollment)
def enrollment_completed(sender, instance: Enrollment, created, **kwargs):
    # Only when it just became completed
    if instance.status == Enrollment.Status.COMPLETED and instance.progress >= 100:
        # Prevent duplicate certificates (reverse OneToOne)
        if not hasattr(instance, "certificate"):
            if settings.HOST_ASYNC_ABILITY:
                create_certificate_task.delay(instance.id)
            else:
                create_certificate_task(instance.id)
