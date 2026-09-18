from datetime import timedelta
from decimal import Decimal

from django.db.models import Avg, Subquery
from django.utils import timezone

from courses.models.course import Course
from courses.models.feedback import CourseFeedback
from enrollments.api.serializers.student import StudentCourseSerializer
from enrollments.models import Enrollment


def get_annotated_student_course(course, user):
    enrollment = Enrollment.objects.filter(
        user=user,
        course=course,
    )

    return (
        Course.objects.filter(pk=course.pk)
        .annotate(
            rating=Avg("enrollments__feedback__rating"),
            enrollment_id=Subquery(
                enrollment.values("id")[:1],
            ),
            progress=Subquery(
                enrollment.values("progress")[:1],
            ),
            enrollment_status=Subquery(
                enrollment.values("status")[:1],
            ),
            last_accessed=Subquery(
                enrollment.values("last_activity_at")[:1],
            ),
            enrolled_at=Subquery(
                enrollment.values("enrolled_at")[:1],
            ),
        )
        .get()
    )


class TestStudentCourseSerializer:
    def test_exposes_exact_fields(self, course, test_user):
        annotated_course = get_annotated_student_course(
            course,
            test_user,
        )

        serializer = StudentCourseSerializer(annotated_course)

        assert set(serializer.data) == {
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
        }

    def test_serializes_course_id(self, course, test_user):
        annotated_course = get_annotated_student_course(
            course,
            test_user,
        )

        serializer = StudentCourseSerializer(annotated_course)

        assert serializer.data["id"] == course.id

    def test_serializes_enrollment_id_from_annotation(self, enrollment):
        annotated_course = get_annotated_student_course(
            enrollment.course,
            enrollment.user,
        )

        serializer = StudentCourseSerializer(annotated_course)

        assert serializer.data["enrollment_id"] == enrollment.id

    def test_serializes_null_enrollment_id_when_not_enrolled(
        self,
        course,
        test_user,
    ):
        annotated_course = get_annotated_student_course(
            course,
            test_user,
        )

        serializer = StudentCourseSerializer(annotated_course)

        assert serializer.data["enrollment_id"] is None

    def test_serializes_course_title(self, course, test_user):
        annotated_course = get_annotated_student_course(
            course,
            test_user,
        )

        serializer = StudentCourseSerializer(annotated_course)

        assert serializer.data["title"] == course.title

    def test_serializes_instructor_as_course_owner(
        self,
        course,
        test_user,
    ):
        annotated_course = get_annotated_student_course(
            course,
            test_user,
        )

        serializer = StudentCourseSerializer(annotated_course)

        assert serializer.data["instructor"] == str(course.owner)

    def test_serializes_course_status(self, course, test_user):
        course.status = Course.Status.PUBLISHED
        course.save()

        annotated_course = get_annotated_student_course(
            course,
            test_user,
        )

        serializer = StudentCourseSerializer(annotated_course)

        assert serializer.data["status"] == Course.Status.PUBLISHED

    def test_serializes_progress_from_enrollment_annotation(
        self,
        enrollment,
    ):
        enrollment.progress = Decimal("62.50")
        enrollment.save()

        annotated_course = get_annotated_student_course(
            enrollment.course,
            enrollment.user,
        )

        serializer = StudentCourseSerializer(annotated_course)

        assert serializer.data["progress"] == 62.5

    def test_serializes_zero_progress(
        self,
        enrollment,
    ):
        enrollment.progress = Decimal("0.00")
        enrollment.save()

        annotated_course = get_annotated_student_course(
            enrollment.course,
            enrollment.user,
        )

        serializer = StudentCourseSerializer(annotated_course)

        assert serializer.data["progress"] == 0.0

    def test_serializes_null_progress_when_not_enrolled(
        self,
        course,
        test_user,
    ):
        annotated_course = get_annotated_student_course(
            course,
            test_user,
        )

        serializer = StudentCourseSerializer(annotated_course)

        assert serializer.data["progress"] is None

    def test_serializes_difficulty_from_course_level(
        self,
        course,
        test_user,
    ):
        course.level = Course.Level.ADVANCED
        course.save()

        annotated_course = get_annotated_student_course(
            course,
            test_user,
        )

        serializer = StudentCourseSerializer(annotated_course)

        assert serializer.data["difficulty"] == Course.Level.ADVANCED

    def test_serializes_beginner_difficulty(
        self,
        course,
        test_user,
    ):
        course.level = Course.Level.BEGINNER
        course.save()

        annotated_course = get_annotated_student_course(
            course,
            test_user,
        )

        serializer = StudentCourseSerializer(annotated_course)

        assert serializer.data["difficulty"] == Course.Level.BEGINNER

    def test_serializes_intermediate_difficulty(
        self,
        course,
        test_user,
    ):
        course.level = Course.Level.INTERMEDIATE
        course.save()

        annotated_course = get_annotated_student_course(
            course,
            test_user,
        )

        serializer = StudentCourseSerializer(annotated_course)

        assert serializer.data["difficulty"] == Course.Level.INTERMEDIATE

    def test_serializes_category_name(
        self,
        course,
        test_user,
        category,
    ):
        annotated_course = get_annotated_student_course(
            course,
            test_user,
        )

        serializer = StudentCourseSerializer(annotated_course)

        assert serializer.data["category"] == category.name

    def test_serializes_empty_category_when_course_has_no_category(
        self,
        course,
        test_user,
    ):
        course.category = None
        course.save()

        annotated_course = get_annotated_student_course(
            course,
            test_user,
        )

        serializer = StudentCourseSerializer(annotated_course)

        assert serializer.data["category"] == ""

    def test_serializes_duration(
        self,
        course,
        test_user,
    ):
        course.duration = timedelta(
            hours=2,
            minutes=30,
        )
        course.save()

        annotated_course = get_annotated_student_course(
            course,
            test_user,
        )

        serializer = StudentCourseSerializer(annotated_course)

        assert serializer.data["duration"] == "02:30:00"

    def test_serializes_null_duration(
        self,
        course,
        test_user,
    ):
        course.duration = None
        course.save()

        annotated_course = get_annotated_student_course(
            course,
            test_user,
        )

        serializer = StudentCourseSerializer(annotated_course)

        assert serializer.data["duration"] is None

    def test_serializes_last_accessed_from_enrollment_annotation(
        self,
        enrollment,
    ):
        last_accessed = timezone.now()

        enrollment.last_activity_at = last_accessed
        enrollment.save()

        annotated_course = get_annotated_student_course(
            enrollment.course,
            enrollment.user,
        )

        serializer = StudentCourseSerializer(annotated_course)

        expected = serializer.fields["last_accessed"].to_representation(last_accessed)

        assert serializer.data["last_accessed"] == expected

    def test_serializes_null_last_accessed(
        self,
        enrollment,
    ):
        enrollment.last_activity_at = None
        enrollment.save()

        annotated_course = get_annotated_student_course(
            enrollment.course,
            enrollment.user,
        )

        serializer = StudentCourseSerializer(annotated_course)

        assert serializer.data["last_accessed"] is None

    def test_serializes_enrolled_at_from_enrollment_annotation(
        self,
        enrollment,
    ):
        annotated_course = get_annotated_student_course(
            enrollment.course,
            enrollment.user,
        )

        serializer = StudentCourseSerializer(annotated_course)

        expected = serializer.fields["enrolled_at"].to_representation(
            enrollment.enrolled_at
        )

        assert serializer.data["enrolled_at"] == expected

    def test_serializes_null_enrolled_at_when_not_enrolled(
        self,
        course,
        test_user,
    ):
        annotated_course = get_annotated_student_course(
            course,
            test_user,
        )

        serializer = StudentCourseSerializer(annotated_course)

        assert serializer.data["enrolled_at"] is None

    def test_serializes_rating_from_annotation(
        self,
        enrollment,
    ):
        CourseFeedback.objects.create(
            enrollment=enrollment,
            rating=4,
            title="Good course",
            comment="Useful course.",
        )

        annotated_course = get_annotated_student_course(
            enrollment.course,
            enrollment.user,
        )

        serializer = StudentCourseSerializer(annotated_course)

        assert serializer.data["rating"] == 4.0

    def test_serializes_null_rating_when_course_has_no_feedback(
        self,
        enrollment,
    ):
        annotated_course = get_annotated_student_course(
            enrollment.course,
            enrollment.user,
        )

        serializer = StudentCourseSerializer(annotated_course)

        assert serializer.data["rating"] is None

    def test_serializes_slug(
        self,
        course,
        test_user,
    ):
        annotated_course = get_annotated_student_course(
            course,
            test_user,
        )

        serializer = StudentCourseSerializer(annotated_course)

        assert serializer.data["slug"] == course.slug

    def test_serializes_thumbnail_without_thumbnail(
        self,
        course,
        test_user,
    ):
        course.thumbnail = None
        course.save()

        annotated_course = get_annotated_student_course(
            course,
            test_user,
        )

        serializer = StudentCourseSerializer(annotated_course)

        assert serializer.data["thumbnail"] in ("", None)

    def test_does_not_expose_unlisted_course_fields(
        self,
        course,
        test_user,
    ):
        annotated_course = get_annotated_student_course(
            course,
            test_user,
        )

        serializer = StudentCourseSerializer(annotated_course)

        data = serializer.data

        assert "owner" not in data
        assert "category_id" not in data
        assert "description" not in data
        assert "subtitle" not in data
        assert "price" not in data
        assert "price_type" not in data
        assert "review_status" not in data
        assert "visibility" not in data
        assert "enrollment_status" not in data

    def test_annotated_enrollment_status_is_available_but_serializer_uses_course_status(
        self,
        enrollment,
    ):
        enrollment.status = Enrollment.Status.COMPLETED
        enrollment.save()

        enrollment.course.status = Course.Status.PUBLISHED
        enrollment.course.save()

        annotated_course = get_annotated_student_course(
            enrollment.course,
            enrollment.user,
        )

        serializer = StudentCourseSerializer(annotated_course)

        assert annotated_course.enrollment_status == (Enrollment.Status.COMPLETED)
        assert serializer.data["status"] == Course.Status.PUBLISHED

    def test_read_only_fields(self):
        serializer = StudentCourseSerializer()

        assert serializer.fields["instructor"].read_only is True
        assert serializer.fields["category"].read_only is True
        assert serializer.fields["enrollment_id"].read_only is True
        assert serializer.fields["progress"].read_only is True
        assert serializer.fields["status"].read_only is True
        assert serializer.fields["last_accessed"].read_only is True
        assert serializer.fields["enrolled_at"].read_only is True
        assert serializer.fields["rating"].read_only is True

    def test_rating_allows_null(self):
        serializer = StudentCourseSerializer()

        assert serializer.fields["rating"].allow_null is True

    def test_difficulty_is_not_read_only(self):
        serializer = StudentCourseSerializer()

        assert serializer.fields["difficulty"].read_only is False

    def test_category_is_read_only(self):
        serializer = StudentCourseSerializer()

        assert serializer.fields["category"].read_only is True

    def test_instructor_is_read_only(self):
        serializer = StudentCourseSerializer()

        assert serializer.fields["instructor"].read_only is True

    def test_annotation_fields_are_read_only(self):
        serializer = StudentCourseSerializer()

        assert serializer.fields["enrollment_id"].read_only is True
        assert serializer.fields["progress"].read_only is True
        assert serializer.fields["status"].read_only is True
        assert serializer.fields["last_accessed"].read_only is True
        assert serializer.fields["enrolled_at"].read_only is True
        assert serializer.fields["rating"].read_only is True
