from rest_framework import serializers

from courses.models import Course, CourseWishlist


class StudentCourseSerializer(serializers.ModelSerializer):
    difficulty = serializers.CharField(source="level")
    category = serializers.CharField(source="category.name", default="", read_only=True)
    instructor = serializers.CharField(
        source="owner", read_only=True
    )  # adjust as needed
    # The rest come from annotations
    enrollment_id = serializers.IntegerField(read_only=True)
    progress = serializers.FloatField(read_only=True)  # or IntegerField
    status = serializers.CharField(read_only=True)
    last_accessed = serializers.DateTimeField(read_only=True)
    enrolled_at = serializers.DateTimeField(read_only=True)
    rating = serializers.FloatField(read_only=True, allow_null=True)

    class Meta:
        model = Course
        fields = [
            "id",
            "enrollment_id",
            "title",
            "instructor",
            "thumbnail",
            "status",
            "progress",
            "difficulty",
            "category",
            "duration",
            "last_accessed",
            "enrolled_at",
            "rating",
            "slug",
        ]


class StudentWishlistSerializer(serializers.ModelSerializer):
    # Course fields
    title = serializers.CharField(source="course.title")
    course_id = serializers.CharField(source="course.id")
    course_slug = serializers.CharField(source="course.slug")
    difficulty = serializers.CharField(source="course.level")
    duration = serializers.CharField(source="course.duration")
    original_price = serializers.DecimalField(
        source="course.price", max_digits=10, decimal_places=2
    )
    price = serializers.SerializerMethodField()
    category = serializers.CharField(
        source="course.category.name", default="", read_only=True
    )
    instructor = serializers.CharField(source="course.owner", read_only=True)
    thumbnail = serializers.ImageField(source="course.thumbnail", read_only=True)

    # Annotated fields
    rating = serializers.FloatField(read_only=True, allow_null=True)
    rating_count = serializers.IntegerField(read_only=True, allow_null=True)

    # Wishlist field
    date_saved = serializers.DateTimeField(source="created_at")

    class Meta:
        model = CourseWishlist
        fields = [
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
        ]

    def get_price(self, obj):
        return obj.course.get_discounted_price
