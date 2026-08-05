from django.db.models import Count, Prefetch, Q

from courses.models import Category, Course


def get_category_options():
    queryset = (
        Category.objects.filter(parent=None)
        .annotate(
            course_count=Count(
                "courses", filter=Q(courses__isnull=False), distinct=True
            )
            + Count(
                "children__courses",
                filter=Q(children__courses__isnull=False),
                distinct=True,
            )
        )
        .filter(course_count__gt=0)
        .prefetch_related(
            Prefetch(
                "children",
                queryset=(
                    Category.objects.annotate(
                        course_count=Count("courses", distinct=True)
                    )
                    .filter(course_count__gt=0)
                    .order_by("name")
                ),
            )
        )
        .order_by("name")
    )

    return [
        {
            "value": category.slug,
            "label": category.name,
            "count": category.course_count,
            "icon": category.icon,
            "subcategories": [
                {
                    "value": subcategory.slug,
                    "label": subcategory.name,
                    "count": subcategory.course_count,
                }
                for subcategory in category.children.all()
            ],
        }
        for category in queryset
    ]


def get_language_options():
    return [
        {
            "value": value,
            "label": label,
        }
        for value, label in Course.LANGUAGE.choices
    ]


def get_level_options():
    return [
        {
            "value": value,
            "label": label,
        }
        for value, label in Course.Level.choices
    ]


def get_price_options():
    return [
        {
            "value": "free",
            "label": "Free",
        },
        {
            "value": "paid",
            "label": "Paid",
        },
    ]


def get_duration_options():
    return [
        {"value": "short", "label": "0-3 Hours"},
        {"value": "medium", "label": "3-10 Hours"},
        {"value": "long", "label": "10+ Hours"},
    ]


def get_rating_options():
    return [
        {
            "value": 4.5,
            "label": "4.5 & above",
        },
        {
            "value": 4.0,
            "label": "4.0 & above",
        },
        {
            "value": 3.0,
            "label": "3.0 & above",
        },
    ]
