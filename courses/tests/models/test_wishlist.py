import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from courses.models.wishlist import CourseWishlist


@pytest.mark.django_db
class TestCourseWishlistModel:
    def test_create_wishlist(self, test_user, course):
        wishlist = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )

        assert wishlist.pk is not None
        assert wishlist.user == test_user
        assert wishlist.course == course

    def test_str_returns_user_and_course(self, test_user, course):
        wishlist = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )

        assert str(wishlist) == f"{test_user} → {course}"

    def test_created_at_is_set_automatically(self, test_user, course):
        before = timezone.now()

        wishlist = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )

        after = timezone.now()

        assert wishlist.created_at is not None
        assert before <= wishlist.created_at <= after

    def test_user_is_required(self, course):
        wishlist = CourseWishlist(course=course)

        with pytest.raises(ValidationError):
            wishlist.full_clean()

    def test_course_is_required(self, test_user):
        wishlist = CourseWishlist(user=test_user)

        with pytest.raises(ValidationError):
            wishlist.full_clean()

    def test_same_user_cannot_wishlist_same_course_twice(
        self,
        test_user,
        course,
    ):
        CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )

        with pytest.raises(IntegrityError):
            CourseWishlist.objects.create(
                user=test_user,
                course=course,
            )

    def test_different_users_can_wishlist_same_course(
        self,
        test_user,
        another_user,
        course,
    ):
        first = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )
        second = CourseWishlist.objects.create(
            user=another_user,
            course=course,
        )

        assert first.pk != second.pk
        assert CourseWishlist.objects.filter(course=course).count() == 2

    def test_same_user_can_wishlist_different_courses(
        self,
        test_user,
        course,
        category,
    ):
        another_course = course.__class__.objects.create(
            title="Another Course",
            owner=test_user,
            category=category,
        )

        first = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )
        second = CourseWishlist.objects.create(
            user=test_user,
            course=another_course,
        )

        assert first.pk != second.pk
        assert CourseWishlist.objects.filter(user=test_user).count() == 2

    def test_deleting_user_deletes_wishlist_entries(
        self,
        test_user,
        course,
    ):
        wishlist = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )
        wishlist_id = wishlist.pk

        test_user.delete()

        assert not CourseWishlist.objects.filter(pk=wishlist_id).exists()

    def test_deleting_course_deletes_wishlist_entries(
        self,
        test_user,
        course,
    ):
        wishlist = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )
        wishlist_id = wishlist.pk

        course.delete()

        assert not CourseWishlist.objects.filter(pk=wishlist_id).exists()

    def test_reverse_user_relation(self, test_user, course):
        wishlist = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )

        assert wishlist in test_user.course_wishlists.all()

    def test_reverse_course_relation(self, test_user, course):
        wishlist = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )

        assert wishlist in course.wishlisted_by.all()

    def test_default_queryset_ordering_is_newest_first(
        self,
        test_user,
        course,
        another_user,
    ):
        first = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )

        second = CourseWishlist.objects.create(
            user=another_user,
            course=course,
        )

        first.created_at = first.created_at - timezone.timedelta(days=1)
        first.save(update_fields=["created_at"])

        wishlists = list(CourseWishlist.objects.all())

        assert wishlists == [second, first]

    def test_filter_by_user(self, test_user, another_user, course):
        first = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )
        CourseWishlist.objects.create(
            user=another_user,
            course=course,
        )

        result = CourseWishlist.objects.filter(user=test_user)

        assert list(result) == [first]

    def test_filter_by_course(self, test_user, another_user, course):
        first = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )
        second = CourseWishlist.objects.create(
            user=another_user,
            course=course,
        )

        result = CourseWishlist.objects.filter(course=course)

        assert list(result) == [second, first]

    def test_user_index_exists(self):
        indexes = CourseWishlist._meta.indexes

        assert any(index.fields == ["user", "-created_at"] for index in indexes)

    def test_course_index_exists(self):
        indexes = CourseWishlist._meta.indexes

        assert any(index.fields == ["course"] for index in indexes)

    def test_unique_user_course_constraint_exists(self):
        constraints = CourseWishlist._meta.constraints

        assert any(
            constraint.name == "unique_user_course_wishlist"
            for constraint in constraints
        )

    def test_created_at_is_not_changed_when_wishlist_is_updated(
        self,
        test_user,
        course,
    ):
        wishlist = CourseWishlist.objects.create(
            user=test_user,
            course=course,
        )
        original_created_at = wishlist.created_at

        wishlist.save()

        wishlist.refresh_from_db()

        assert wishlist.created_at == original_created_at
