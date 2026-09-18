from datetime import timedelta
from decimal import Decimal

from django.db.models import Avg, Count

from courses.models import Course, CourseFeedback, CourseWishlist
from enrollments.api.serializers.student import StudentWishlistSerializer


def get_annotated_wishlist(wishlist):
    return (
        CourseWishlist.objects.filter(pk=wishlist.pk)
        .select_related(
            "course",
            "course__category",
            "course__owner",
        )
        .annotate(
            rating=Avg("course__enrollments__feedback__rating"),
            rating_count=Count(
                "course__enrollments__feedback",
                distinct=True,
            ),
        )
        .get()
    )


class TestStudentWishlistSerializer:
    def test_serializes_expected_fields(self, test_user, course):
        wishlist = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )

        serializer = StudentWishlistSerializer(wishlist)

        assert set(serializer.data) == {
            "id",
            "title",
            "instructor",
            "thumbnail",
            "rating",
            "rating_count",
            "difficulty",
            "duration",
            "price",
            "original_price",
            "category",
            "date_saved",
            "course_id",
            "course_slug",
        }

    def test_serializes_wishlist_id(self, test_user, course):
        wishlist = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )

        serializer = StudentWishlistSerializer(wishlist)

        assert serializer.data["id"] == wishlist.id

    def test_serializes_course_title(self, test_user, course):
        wishlist = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )

        serializer = StudentWishlistSerializer(wishlist)

        assert serializer.data["title"] == course.title

    def test_serializes_course_id_as_string(self, test_user, course):
        wishlist = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )

        serializer = StudentWishlistSerializer(wishlist)

        assert serializer.data["course_id"] == str(course.id)

    def test_serializes_course_slug(self, test_user, course):
        wishlist = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )

        serializer = StudentWishlistSerializer(wishlist)

        assert serializer.data["course_slug"] == course.slug

    def test_serializes_difficulty_from_course_level(
        self,
        test_user,
        course,
    ):
        wishlist = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )

        serializer = StudentWishlistSerializer(wishlist)

        assert serializer.data["difficulty"] == course.level

    def test_serializes_duration_from_course(self, test_user, course):
        course.duration = timedelta(hours=2, minutes=30)
        course.save()

        wishlist = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )

        serializer = StudentWishlistSerializer(wishlist)

        expected = serializer.fields["duration"].to_representation(course.duration)

        assert serializer.data["duration"] == expected

    def test_serializes_null_duration(self, test_user, course):
        course.duration = None
        course.save()

        wishlist = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )

        serializer = StudentWishlistSerializer(wishlist)

        assert serializer.data["duration"] is None

    def test_serializes_original_price(self, test_user, course):
        course.price = Decimal("149.99")
        course.save()

        wishlist = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )

        serializer = StudentWishlistSerializer(wishlist)

        expected = serializer.fields["original_price"].to_representation(course.price)

        assert serializer.data["original_price"] == expected

    def test_serializes_null_original_price_for_free_course(
        self,
        test_user,
        course,
    ):
        course.price = None
        course.save()

        wishlist = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )

        serializer = StudentWishlistSerializer(wishlist)

        assert serializer.data["original_price"] is None

    def test_serializes_discounted_price(self, test_user, course):
        course.price = Decimal("149.99")
        course.save()

        wishlist = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )

        serializer = StudentWishlistSerializer(wishlist)

        assert serializer.data["price"] == course.get_discounted_price

    def test_serializes_category_name(
        self,
        test_user,
        course,
        category,
    ):
        course.category = category
        course.save()

        wishlist = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )

        serializer = StudentWishlistSerializer(wishlist)

        assert serializer.data["category"] == category.name

    def test_serializes_empty_category_when_course_has_no_category(
        self,
        test_user,
        course,
    ):
        course.category = None
        course.save()

        wishlist = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )

        serializer = StudentWishlistSerializer(wishlist)

        assert serializer.data["category"] == ""

    def test_serializes_instructor_from_course_owner(
        self,
        test_user,
        course,
    ):
        wishlist = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )

        serializer = StudentWishlistSerializer(wishlist)

        assert serializer.data["instructor"] == str(course.owner)

    def test_serializes_thumbnail_without_thumbnail(
        self,
        test_user,
        course,
    ):
        course.thumbnail = None
        course.save()

        wishlist = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )

        serializer = StudentWishlistSerializer(wishlist)

        assert serializer.data["thumbnail"] is None

    def test_serializes_rating_from_annotation(
        self,
        test_user,
        course,
        enrollment,
    ):
        CourseFeedback.objects.create(
            enrollment=enrollment,
            rating=4,
        )

        wishlist = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )
        wishlist = get_annotated_wishlist(wishlist)

        serializer = StudentWishlistSerializer(wishlist)

        assert serializer.data["rating"] == 4.0

    def test_serializes_rating_count_from_annotation(
        self,
        test_user,
        course,
        enrollment,
    ):
        CourseFeedback.objects.create(
            enrollment=enrollment,
            rating=4,
        )

        wishlist = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )
        wishlist = get_annotated_wishlist(wishlist)

        serializer = StudentWishlistSerializer(wishlist)

        assert serializer.data["rating_count"] == 1

    def test_serializes_null_rating_when_course_has_no_feedback(
        self,
        test_user,
        course,
    ):
        wishlist = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )
        wishlist = get_annotated_wishlist(wishlist)

        serializer = StudentWishlistSerializer(wishlist)

        assert serializer.data["rating"] is None

    def test_serializes_zero_rating_count_when_course_has_no_feedback(
        self,
        test_user,
        course,
    ):
        wishlist = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )
        wishlist = get_annotated_wishlist(wishlist)

        serializer = StudentWishlistSerializer(wishlist)

        assert serializer.data["rating_count"] == 0

    def test_serializes_date_saved_from_created_at(
        self,
        test_user,
        course,
    ):
        wishlist = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )

        serializer = StudentWishlistSerializer(wishlist)

        expected = serializer.fields["date_saved"].to_representation(
            wishlist.created_at
        )

        assert serializer.data["date_saved"] == expected

    def test_serializes_rating_and_rating_count_for_annotated_wishlist(
        self,
        test_user,
        course,
        enrollment,
    ):
        CourseFeedback.objects.create(
            enrollment=enrollment,
            rating=5,
        )

        wishlist = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )
        wishlist = get_annotated_wishlist(wishlist)

        assert wishlist.rating == 5
        assert wishlist.rating_count == 1

        serializer = StudentWishlistSerializer(wishlist)

        assert serializer.data["rating"] == 5.0
        assert serializer.data["rating_count"] == 1

    def test_uses_course_level_for_difficulty(
        self,
        test_user,
        course,
    ):
        course.level = Course.Level.ADVANCED
        course.save()

        wishlist = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )

        serializer = StudentWishlistSerializer(wishlist)

        assert serializer.data["difficulty"] == Course.Level.ADVANCED

    def test_exposes_course_information_not_wishlist_user(
        self,
        test_user,
        course,
    ):
        wishlist = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )

        serializer = StudentWishlistSerializer(wishlist)

        assert "user" not in serializer.data
        assert "course" not in serializer.data

    def test_does_not_expose_created_at_directly(
        self,
        test_user,
        course,
    ):
        wishlist = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )

        serializer = StudentWishlistSerializer(wishlist)

        assert "created_at" not in serializer.data
        assert "date_saved" in serializer.data

    def test_annotated_rating_is_read_only(self):
        serializer = StudentWishlistSerializer()

        assert serializer.fields["rating"].read_only is True
        assert serializer.fields["rating"].allow_null is True

    def test_annotated_rating_count_is_read_only(self):
        serializer = StudentWishlistSerializer()

        assert serializer.fields["rating_count"].read_only is True
        assert serializer.fields["rating_count"].allow_null is True

    def test_category_is_read_only(self):
        serializer = StudentWishlistSerializer()

        assert serializer.fields["category"].read_only is True

    def test_instructor_is_read_only(self):
        serializer = StudentWishlistSerializer()

        assert serializer.fields["instructor"].read_only is True

    def test_thumbnail_is_read_only(self):
        serializer = StudentWishlistSerializer()

        assert serializer.fields["thumbnail"].read_only is True

    def test_price_is_serializer_method_field(self):
        serializer = StudentWishlistSerializer()

        assert isinstance(
            serializer.fields["price"],
            serializer.fields["price"].__class__,
        )

    def test_wishlist_unique_per_user_and_course(
        self,
        test_user,
        course,
    ):
        CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )

        duplicate = CourseWishlist(
            user=test_user,
            course=course,
        )

        from django.db import IntegrityError

        try:
            duplicate.save()
        except IntegrityError:
            pass
        else:
            raise AssertionError(
                "A user must not be able to wishlist the same course twice."
            )

    def test_different_users_can_wishlist_same_course(
        self,
        test_user,
        another_user,
        course,
    ):
        first_wishlist = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )
        second_wishlist = CourseWishlist.objects.create(
            user=another_user,
            course=course,
        )

        assert first_wishlist.pk != second_wishlist.pk
        assert first_wishlist.course_id == second_wishlist.course_id
