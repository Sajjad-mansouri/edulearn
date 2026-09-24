from datetime import timedelta

from django.core.paginator import Paginator
from django.db.models import Avg, Count, Prefetch, Q, Sum
from django.utils import timezone
from rest_framework.generics import (
    DestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
    get_object_or_404,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from courses.models import (
    Category,
    Course,
    CourseFeedback,
    CourseFeedbackInteraction,
    CourseWishlist,
)
from curriculums.models import Lesson, Section
from enrollments.api.permissions import IsStudent
from enrollments.models import Enrollment
from profiles.models import InstructorProfile

from .serializers import (
    CategorySerializer,
    CourseCurriculumSerializer,
    CourseDetailInfoSerializer,
    CourseFeedbackSerializer,
    CourseInstructorSerializer,
    CourseMetadataSerializer,
    CourseSerializer,
    FeedbackSerializer,
)
from .services import (
    get_best_seller_ids,
    get_course_filter_metadata,
    toggle_course_wishlist,
)


class CategoriesApiViews(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        categories = Category.objects.filter(parent__isnull=True).prefetch_related(
            "children"
        )

        data = [
            {
                "name": category.name,
                "slug": category.slug,
                "subcategories": [
                    {"name": child.name, "slug": child.slug}
                    for child in category.children.all()
                ],
            }
            for category in categories
        ]
        print(data)
        return Response(data)


class SubcategoriesApiView(ListAPIView):
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

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
        print(
            (
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
                    total_duration=Sum("sections__lessons__duration"),
                )
                .filter(q)
                .order_by("-published_at", "-pk")
            ).values_list("total_duration")
        )
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
                total_duration=Sum("sections__lessons__duration"),
            )
            .filter(q)
            .order_by("-published_at", "-pk")
        )

    def map_duration(self, duration):
        q = Q()

        if duration == "short":
            q = Q(duration__lte=timedelta(hours=3))
        elif duration == "medium":
            q = Q(
                duration__gt=timedelta(hours=3),
                duration__lte=timedelta(hours=10),
            )
        elif duration == "long":
            q = Q(duration__gt=timedelta(hours=10))

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
        min_rating = query_params.get("min_rating")

        if min_rating:
            try:
                min_rating = float(min_rating)
            except ValueError:
                min_rating = 0

            rating_q = Q(rating__gte=min_rating)
        else:
            rating_q = Q()

        categories = query_params.getlist("category")

        subcategories = query_params.getlist("subcategory")
        subcategories = [
            item for item in subcategories if not item.lower().startswith("all")
        ]
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


class CourseWishlistToggleApiView(APIView):
    permission_classes = [IsStudent]

    def post(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)

        is_wishlisted = toggle_course_wishlist(
            user=request.user,
            course=course,
        )

        return Response(
            {
                "is_wishlisted": is_wishlisted,
            }
        )


class CourseWishlistRemoveApiView(DestroyAPIView):
    permission_classes = [IsStudent]

    def get_queryset(self):
        return CourseWishlist.objects.filter(user=self.request.user)


class CourseWishlistStatusApiView(APIView):
    def get(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)

        is_wishlisted = CourseWishlist.objects.filter(
            course=course, user=request.user
        ).exists()

        return Response(
            {
                "is_wishlisted": is_wishlisted,
            }
        )


class CourseDetailInfoApiView(RetrieveAPIView):
    serializer_class = CourseDetailInfoSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = Course.objects.filter(status="published").annotate(
            rating=Avg("enrollments__feedback__rating"),
            total_ratings=Count("enrollments__feedback", distinct=True),
            total_students=Count("enrollments", distinct=True),
            total_duration=Sum("sections__lessons__duration"),
        )
        return qs

    def get_serializer_context(self):
        context = super().get_serializer_context()

        course = self.get_object()

        context["course_duration"] = course.sections.aggregate(
            total=Sum("lessons__duration")
        )["total"]

        return context


class CourseDetailInstructorInfoApiView(RetrieveAPIView):
    serializer_class = CourseInstructorSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        course = get_object_or_404(
            Course,
            id=self.kwargs["course_id"],
        )

        return get_object_or_404(
            self.get_queryset(),
            profile__user__owned_courses=course,
        )

    def get_queryset(self):
        return (
            InstructorProfile.objects.select_related(
                "profile",
                "profile__user",
            )
            .prefetch_related(
                "profile__social_links",
            )
            .annotate(
                rating=Avg(
                    "profile__user__owned_courses__enrollments__feedback__rating",
                ),
                total_students=Count(
                    "profile__user__owned_courses__enrollments__user",
                    distinct=True,
                ),
                total_courses=Count(
                    "profile__user__owned_courses",
                    distinct=True,
                ),
            )
        )


class CourseDetailCurriculumApiView(ListAPIView):
    serializer_class = CourseCurriculumSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        lesson_qs = Lesson.objects.filter(content__is_main_content=True).select_related(
            "content"
        )

        return (
            Section.objects.filter(course_id=self.kwargs["course_id"])
            .annotate(
                section_duration=Sum(
                    "lessons__duration",
                ),
                lessons_count=Count(
                    "lessons",
                    distinct=True,
                ),
            )
            .prefetch_related(Prefetch("lessons", queryset=lesson_qs))
            .order_by("order")
        )


class CourseReviewListApiView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, course_id):
        per_page = 3
        page_number = request.query_params.get("page", 1)
        feedback_qs = (
            CourseFeedback.objects.filter(enrollment__course_id=course_id)
            .select_related("enrollment__user__profile")
            .annotate(helpful_count=Count("feedback_interactions"))
            .order_by("created_at")
        )

        distribution_row = (
            feedback_qs.values("rating").annotate(count=Count("id")).order_by("rating")
        )

        per_page = int(request.query_params.get("per_page", 3))
        page_number = int(request.query_params.get("page_number", 1))

        paginator = Paginator(feedback_qs, per_page)
        page_obj = paginator.get_page(page_number)
        serializer = CourseFeedbackSerializer(
            page_obj.object_list, many=True, context={"request": request}
        )
        total_pages = paginator.count
        distribution = {
            r["rating"]: round((r["count"] / total_pages) * 100)
            for r in distribution_row
        }
        for i in range(1, 6):
            distribution.setdefault(i, 0)
        data = {
            "current_page": page_obj.number,
            "per_page": per_page,
            "total_reviews": paginator.count,
            "total_pages": paginator.num_pages,
            "distribution": distribution,
            "items": serializer.data,
        }
        return Response(data)


class CourseReviewApiView(APIView):
    permission_classes = [IsStudent]

    def post(self, request, course_id):
        enrollment = get_object_or_404(
            Enrollment, user=request.user, course_id=course_id
        )

        data = {"enrollment": enrollment.id, **request.data}
        serializer = FeedbackSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class CourseReviewHelpfulApiView(APIView):
    permission_classes = [IsStudent]

    def post(self, request, course_id, review_id):
        enrollment = get_object_or_404(
            Enrollment, user=request.user, course_id=course_id
        )

        feedback = get_object_or_404(CourseFeedback, id=review_id)
        obj, created = CourseFeedbackInteraction.objects.get_or_create(
            enrollment=enrollment, feedback=feedback
        )
        user_has_liked = True
        if not created:
            obj.delete()
            user_has_liked = False

        helpful_count = feedback.feedback_interactions.aggregate(count=Count("id"))[
            "count"
        ]
        data = {"helpful_count": helpful_count, "user_has_liked": user_has_liked}
        return Response(data)


class CourseReviewDestroyApiView(DestroyAPIView):
    lookup_url_kwarg = "review_id"
    permission_classes = [IsStudent]

    def get_queryset(self):
        return CourseFeedback.objects.filter(enrollment__user=self.request.user)


class CourseMetadataApiView(APIView):
    def get(self, request, *args, **kwargs):
        serializer = CourseMetadataSerializer(Course)
        return Response(serializer.data)
