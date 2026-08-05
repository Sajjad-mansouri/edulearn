from datetime import timedelta

from django.db.models import Avg, Count, Q
from django.utils import timezone
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from courses.models import Category, Course

from .serializers import CategorySerializer, CourseSerializer
from .services import get_best_seller_ids, get_course_filter_metadata


class CategoriesApiView(ListAPIView):
    serializer_class = CategorySerializer

    def get_queryset(self):
        return Category.objects.filter(parent=None)


class SubcategoriesApiView(ListAPIView):
    serializer_class = CategorySerializer

    def get_queryset(self):
        category_slug = self.kwargs.get("categorySlug")
        return Category.objects.filter(parent__slug=category_slug)


class CourseFilterMetadataApiView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        return Response(get_course_filter_metadata())


class CoursesApiView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = CourseSerializer

    def get_queryset(self):
        q = self.get_query_q()

        return (
            Course.objects.filter(status="published")
            .select_related(
                "owner",
                "category",
                "category__parent",
            )
            .annotate(
                rating=Avg("enrollments__feedback__rating"),
                rating_count=Count("enrollments__feedback", distinct=True),
                students=Count("enrollments", distinct=True),
            )
            .filter(q)
        )

    def map_duration(self, duration):
        q = Q()
        if duration == "short":
            q = Q(duration__lte=timedelta(hours=3))
        elif duration == "medium":
            q = Q(duration__gte=timedelta(hours=3)) & Q(
                duration__lte=timedelta(hours=10)
            )
        elif duration == "long":
            q = Q(duration__gte=timedelta(hours=10))
        return q

    def get_query_q(self):
        query_params = self.request.query_params

        durations = query_params.getlist("duration")
        duration_q = Q()
        for duration in durations:
            duration_q |= self.map_duration(duration)

        languages = query_params.getlist("language")
        if languages:
            language_q = Q(language__in=languages)
        else:
            language_q = Q()

        levels = query_params.getlist("level")
        if levels:
            level_q = Q(level__in=levels)
        else:
            level_q = Q()

        price_types = query_params.getlist("price_type")
        if price_types:
            price_type_q = Q(price_type__in=price_types)
        else:
            price_type_q = Q()

        search = query_params.get("search")
        if search:
            q_search = Q(title__icontains=search) | Q(description__icontains=search)
        else:
            q_search = Q()
        try:
            min_rating = float(query_params.get("min_rating", 0))
        except ValueError:
            min_rating = 0
        rating_q = Q(rating__gte=min_rating)

        categories = query_params.getlist("category")

        subcategories = query_params.getlist("subcategory")
        subcategories = [item for item in subcategories if not item.startswith("all")]
        category_slugs = categories + subcategories
        category_q = Q(category__slug__in=category_slugs) if category_slugs else Q()

        total_q = (
            category_q
            & language_q
            & level_q
            & price_type_q
            & rating_q
            & duration_q
            & q_search
        )
        return total_q

    def get_serializer_context(self):
        context = super().get_serializer_context()

        context["best_sellers"] = get_best_seller_ids()
        context["now"] = timezone.now()

        return context
