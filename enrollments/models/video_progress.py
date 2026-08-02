from decimal import Decimal

from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from .lesson_content_progress import LessonContentProgress


class VideoProgress(models.Model):
    lesson_content_progress = models.OneToOneField(
        LessonContentProgress,
        on_delete=models.CASCADE,
        related_name="video_progress",
        verbose_name=_("Lesson Content Progress"),
    )

    watched_seconds = models.PositiveIntegerField(
        _("Watched Seconds"),
        default=0,
        help_text=_("Total watched video time in seconds."),
    )

    class Meta:
        verbose_name = _("Video Progress")
        verbose_name_plural = _("Video Progress")

    def __str__(self):
        return (
            f"{self.lesson_content_progress.enrollment.user} - "
            f"{self.lesson_content_progress.content.title}"
        )

    @property
    def duration_seconds(self):
        """
        Get video duration from Video model.
        """
        return self.lesson_content_progress.content.video.duration

    @property
    def watched_percentage(self):
        """
        Calculate watched percentage dynamically.
        """
        if not self.duration_seconds:
            return Decimal("0")

        return (
            Decimal(self.watched_seconds)
            * Decimal("100")
            / Decimal(self.duration_seconds)
        )

    @transaction.atomic
    def update_progress(self, watched_seconds):
        """
        Update video progress.

        watched_seconds:
            Current playback position sent by the video player.
        """

        if watched_seconds < 0:
            watched_seconds = 0

        if self.duration_seconds:
            watched_seconds = min(
                watched_seconds,
                self.duration_seconds,
            )

        # Keep the highest watched position
        self.watched_seconds = max(
            self.watched_seconds,
            watched_seconds,
        )

        self.save(
            update_fields=[
                "watched_seconds",
            ]
        )

        self.sync_content_progress()

    def sync_content_progress(self):
        """
        Sync video progress with LessonContentProgress.
        """

        content_progress = self.lesson_content_progress

        if self.watched_percentage >= Decimal("90"):
            content_progress.mark_completed()

        elif content_progress.status == (LessonContentProgress.Status.NOT_STARTED):
            content_progress.mark_started()
