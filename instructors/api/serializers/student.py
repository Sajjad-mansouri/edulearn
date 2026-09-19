from django.contrib.auth import get_user_model
from django.db.models import Avg
from rest_framework import serializers

from enrollments.models import Enrollment

User = get_user_model()


class InstructorStudentSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(source="profile.avatar", read_only=True)

    name = serializers.SerializerMethodField()
    enrolled_courses = serializers.SerializerMethodField()
    overall_progress = serializers.SerializerMethodField()
    last_active = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    avg_rating = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "name",
            "email",
            "avatar",
            "enrolled_courses",
            "overall_progress",
            "last_active",
            "status",
            "avg_rating",
        ]

    def get_enrollments(self, obj):
        instructor = self.context["request"].user
        return Enrollment.objects.filter(course__owner=instructor, user=obj.id)

    def get_name(self, obj):
        return obj.get_full_name()

    def get_enrolled_courses(self, obj):
        enrollments = self.get_enrollments(obj)

        return [
            {"name": enrollment.course.title, "progress": enrollment.progress}
            for enrollment in enrollments
        ]

    def get_overall_progress(self, obj):
        enrollments = self.get_enrollments(obj)
        if not enrollments.exists():
            return 0

        return round(sum(e.progress for e in enrollments) / enrollments.count())

    def get_last_active(self, obj):
        enrollments = self.get_enrollments(obj)
        last = enrollments.order_by("-last_activity_at").first()
        return last.last_activity_at if last else None

    def get_status(self, obj):
        last = self.get_enrollments(obj).order_by("-last_activity_at").first()

        return last.activity_status if last else "not_started"

    def get_avg_rating(self, obj):
        enrollments = self.get_enrollments(obj)
        avg = enrollments.aggregate(avg_rating=Avg("feedback__rating"))["avg_rating"]
        return round(avg, 2) if avg is not None else None


class InstructorStatisticSerializer(serializers.ModelSerializer):
    average_course_rating = serializers.SerializerMethodField()
    total_students = serializers.SerializerMethodField()
    courses = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["average_course_rating", "total_students", "courses"]

    def get_enrollments(self, obj):
        instructor = self.context["request"].user
        return Enrollment.objects.filter(course__owner=instructor)

    def get_average_course_rating(self, obj):
        enrollments = self.get_enrollments(obj)
        avg = enrollments.aggregate(avg_rating=Avg("feedback__rating"))["avg_rating"]
        return round(avg, 2) if avg is not None else None

    def get_total_students(self, obj):
        enrollments = self.get_enrollments(obj)
        return enrollments.count()

    def get_courses(self, obj):
        return {course.slug: course.title for course in obj.owned_courses.all()}


class InstructorDashboardSerializer(serializers.Serializer):
    statistics = serializers.SerializerMethodField()
    students = serializers.SerializerMethodField()

    def get_statistics(self, obj):
        return InstructorStatisticSerializer(obj, context=self.context).data

    def get_students(self, obj):
        students = User.objects.filter(enrollments__course__owner=obj).distinct()

        return InstructorStudentSerializer(
            students, many=True, context=self.context
        ).data
