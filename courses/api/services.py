from django.conf import settings
from django.db.models import Count

from courses.models import Course, CourseWishlist

from .selectors import (
    get_category_options,
    get_duration_options,
    get_language_options,
    get_level_options,
    get_price_options,
    get_rating_options,
)


def get_course_filter_metadata():
    return {
        "categories": get_category_options(),
        "languages": get_language_options(),
        "levels": get_level_options(),
        "prices": get_price_options(),
        "durations": get_duration_options(),
        "ratings": get_rating_options(),
    }


def get_best_seller_ids():
    return set(
        Course.objects.filter(
            status=Course.Status.PUBLISHED, price_type=Course.PriceType.PAID
        )
        .annotate(students_count=Count("enrollments"))
        .order_by("-students_count")
        .values_list("id", flat=True)[: settings.BEST_SELLERS_COUNT]
    )


def toggle_course_wishlist(*, user, course):
    wishlist, created = CourseWishlist.objects.get_or_create(
        user=user,
        course=course,
    )

    if created:
        return True

    wishlist.delete()
    return False
