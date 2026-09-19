from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
from django.db.models import Avg
from rest_framework import serializers

from instructors.api.serializers.student import (
    InstructorDashboardSerializer,
    InstructorStatisticSerializer,
    InstructorStudentSerializer,
)


@pytest.mark.django_db
class TestInstructorStudentSerializer:
    def _serializer_request(self, instructor_user):
        request = Mock()
        request.user = instructor_user
        return request

    def _serializer(self, instructor_user, instance=None):
        kwargs = {
            "context": {
                "request": self._serializer_request(instructor_user),
            },
        }

        if instance is not None:
            kwargs["instance"] = instance

        return InstructorStudentSerializer(**kwargs)

    def test_serializer_has_expected_fields(self):
        serializer = InstructorStudentSerializer()

        assert set(serializer.fields) == {
            "id",
            "name",
            "email",
            "avatar",
            "enrolled_courses",
            "overall_progress",
            "last_active",
            "status",
            "avg_rating",
        }

    def test_id_is_read_only(self):
        serializer = InstructorStudentSerializer()

        assert serializer.fields["id"].read_only is True

    def test_name_is_read_only_method_field(self):
        serializer = InstructorStudentSerializer()

        assert serializer.fields["name"].read_only is True

    def test_enrolled_courses_is_read_only_method_field(self):
        serializer = InstructorStudentSerializer()

        assert serializer.fields["enrolled_courses"].read_only is True

    def test_overall_progress_is_read_only_method_field(self):
        serializer = InstructorStudentSerializer()

        assert serializer.fields["overall_progress"].read_only is True

    def test_last_active_is_read_only_method_field(self):
        serializer = InstructorStudentSerializer()

        assert serializer.fields["last_active"].read_only is True

    def test_status_is_read_only_method_field(self):
        serializer = InstructorStudentSerializer()

        assert serializer.fields["status"].read_only is True

    def test_avg_rating_is_read_only_method_field(self):
        serializer = InstructorStudentSerializer()

        assert serializer.fields["avg_rating"].read_only is True

    def test_avatar_is_image_field(self):
        serializer = InstructorStudentSerializer()

        assert isinstance(
            serializer.fields["avatar"],
            serializers.ImageField,
        )

    def test_avatar_is_read_only(self):
        serializer = InstructorStudentSerializer()

        assert serializer.fields["avatar"].read_only is True

    def test_avatar_uses_profile_avatar_source(self):
        serializer = InstructorStudentSerializer()

        assert serializer.fields["avatar"].source == "profile.avatar"

    def test_get_name_returns_full_name(self, student_user):
        student_user.first_name = "John"
        student_user.last_name = "Doe"
        student_user.save(
            update_fields=["first_name", "last_name"],
        )

        serializer = InstructorStudentSerializer()

        assert serializer.get_name(student_user) == "John Doe"

    def test_get_name_returns_empty_string_without_name(
        self,
        student_user,
    ):
        student_user.first_name = ""
        student_user.last_name = ""
        student_user.save(
            update_fields=["first_name", "last_name"],
        )

        serializer = InstructorStudentSerializer()

        assert serializer.get_name(student_user) == ""

    def test_get_enrollments_requires_request_context(
        self,
        student_user,
    ):
        serializer = InstructorStudentSerializer()

        with pytest.raises(KeyError):
            serializer.get_enrollments(student_user)

    def test_serializer_requires_request_context_for_method_fields(
        self,
        student_user,
    ):
        serializer = InstructorStudentSerializer(
            instance=student_user,
        )

        with pytest.raises(KeyError):
            _ = serializer.data

    def test_serializer_does_not_accept_method_fields_as_input(
        self,
        instructor_user,
    ):
        serializer = InstructorStudentSerializer(
            data={
                "email": "different@example.com",
                "name": "Injected Name",
                "enrolled_courses": [],
                "overall_progress": 100,
                "last_active": None,
                "status": "completed",
                "avg_rating": 5.0,
            },
            context={
                "request": self._serializer_request(instructor_user),
            },
        )

        assert serializer.is_valid(), serializer.errors

        assert "name" not in serializer.validated_data
        assert "enrolled_courses" not in serializer.validated_data
        assert "overall_progress" not in serializer.validated_data
        assert "last_active" not in serializer.validated_data
        assert "status" not in serializer.validated_data
        assert "avg_rating" not in serializer.validated_data

    def test_serializer_email_is_writable(
        self,
        student_user,
    ):
        serializer = InstructorStudentSerializer(
            data={
                "email": "different@example.com",
            },
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["email"] == ("different@example.com")

    def test_get_enrolled_courses_returns_empty_list_without_enrollments(
        self,
        instructor_user,
        student_user,
    ):
        serializer = self._serializer(instructor_user)

        assert serializer.get_enrolled_courses(student_user) == []

    def test_get_overall_progress_returns_zero_without_enrollments(
        self,
        instructor_user,
        student_user,
    ):
        serializer = self._serializer(instructor_user)

        assert serializer.get_overall_progress(student_user) == 0

    def test_get_last_active_returns_none_without_enrollments(
        self,
        instructor_user,
        student_user,
    ):
        serializer = self._serializer(instructor_user)

        assert serializer.get_last_active(student_user) is None

    def test_get_avg_rating_returns_none_without_feedback(
        self,
        instructor_user,
        student_user,
    ):
        serializer = self._serializer(instructor_user)

        assert serializer.get_avg_rating(student_user) is None

    def test_get_status_returns_not_started_without_enrollments(
        self,
        instructor_user,
        student_user,
    ):
        serializer = self._serializer(instructor_user)

        assert serializer.get_status(student_user) == "not_started"

    def test_serializer_id_matches_user(
        self,
        instructor_user,
        student_user,
    ):
        serializer = self._serializer(
            instructor_user,
            instance=student_user,
        )

        assert serializer.data["id"] == student_user.pk

    def test_serializer_email_matches_user(
        self,
        instructor_user,
        student_user,
    ):
        serializer = self._serializer(
            instructor_user,
            instance=student_user,
        )

        assert serializer.data["email"] == student_user.email

    def test_serializer_name_matches_user_full_name(
        self,
        instructor_user,
        student_user,
    ):
        student_user.first_name = "John"
        student_user.last_name = "Smith"
        student_user.save(
            update_fields=["first_name", "last_name"],
        )

        serializer = self._serializer(
            instructor_user,
            instance=student_user,
        )

        assert serializer.data["name"] == "John Smith"

    def test_serializer_returns_zero_progress_without_enrollments(
        self,
        instructor_user,
        student_user,
    ):
        serializer = self._serializer(
            instructor_user,
            instance=student_user,
        )

        assert serializer.data["overall_progress"] == 0

    def test_serializer_returns_empty_courses_without_enrollments(
        self,
        instructor_user,
        student_user,
    ):
        serializer = self._serializer(
            instructor_user,
            instance=student_user,
        )

        assert serializer.data["enrolled_courses"] == []

    def test_serializer_returns_none_last_active_without_enrollments(
        self,
        instructor_user,
        student_user,
    ):
        serializer = self._serializer(
            instructor_user,
            instance=student_user,
        )

        assert serializer.data["last_active"] is None

    def test_serializer_returns_not_started_without_enrollments(
        self,
        instructor_user,
        student_user,
    ):
        serializer = self._serializer(
            instructor_user,
            instance=student_user,
        )

        assert serializer.data["status"] == "not_started"

    def test_serializer_returns_none_rating_without_feedback(
        self,
        instructor_user,
        student_user,
    ):
        serializer = self._serializer(
            instructor_user,
            instance=student_user,
        )

        assert serializer.data["avg_rating"] is None

    def test_serializer_output_contains_expected_fields(
        self,
        instructor_user,
        student_user,
    ):
        serializer = self._serializer(
            instructor_user,
            instance=student_user,
        )

        assert set(serializer.data.keys()) == {
            "id",
            "name",
            "email",
            "avatar",
            "enrolled_courses",
            "overall_progress",
            "last_active",
            "status",
            "avg_rating",
        }


@pytest.mark.django_db
class TestInstructorStatisticSerializer:
    def _serializer_request(self, instructor_user):
        request = Mock()
        request.user = instructor_user
        return request

    def _serializer(self, instructor_user):
        return InstructorStatisticSerializer(
            context={"request": self._serializer_request(instructor_user)}
        )

    def test_serializer_has_expected_fields(self):
        serializer = InstructorStatisticSerializer()

        assert set(serializer.fields) == {
            "average_course_rating",
            "total_students",
            "courses",
        }

    def test_average_course_rating_is_method_field(self):
        serializer = InstructorStatisticSerializer()

        field = serializer.fields["average_course_rating"]

        assert isinstance(field, serializers.SerializerMethodField)
        assert field.read_only is True

    def test_total_students_is_method_field(self):
        serializer = InstructorStatisticSerializer()

        field = serializer.fields["total_students"]

        assert isinstance(field, serializers.SerializerMethodField)
        assert field.read_only is True

    def test_courses_is_method_field(self):
        serializer = InstructorStatisticSerializer()

        field = serializer.fields["courses"]

        assert isinstance(field, serializers.SerializerMethodField)
        assert field.read_only is True

    def test_get_enrollments_requires_request_context(self, instructor_user):
        serializer = InstructorStatisticSerializer()

        with pytest.raises(KeyError):
            serializer.get_enrollments(instructor_user)

    def test_get_enrollments_filters_by_request_instructor(
        self,
        instructor_user,
        student_user,
    ):
        serializer = self._serializer(instructor_user)
        queryset = Mock()

        with patch(
            "instructors.api.serializers.student.Enrollment.objects.filter",
            return_value=queryset,
        ) as filter_mock:
            result = serializer.get_enrollments(student_user)

        assert result is queryset
        filter_mock.assert_called_once_with(course__owner=instructor_user)

    def test_get_average_course_rating_uses_feedback_rating_average(
        self,
        instructor_user,
        student_user,
    ):
        serializer = self._serializer(instructor_user)

        enrollments = Mock()
        enrollments.aggregate.return_value = {"avg_rating": Decimal("4.666666")}

        with patch.object(
            serializer,
            "get_enrollments",
            return_value=enrollments,
        ) as get_enrollments_mock:
            result = serializer.get_average_course_rating(student_user)

        get_enrollments_mock.assert_called_once_with(student_user)
        enrollments.aggregate.assert_called_once()

        aggregate_kwargs = enrollments.aggregate.call_args.kwargs

        assert "avg_rating" in aggregate_kwargs
        assert isinstance(aggregate_kwargs["avg_rating"], Avg)
        assert result == Decimal("4.67")

    def test_get_average_course_rating_returns_none_without_ratings(
        self,
        instructor_user,
        student_user,
    ):
        serializer = self._serializer(instructor_user)

        enrollments = Mock()
        enrollments.aggregate.return_value = {"avg_rating": None}

        with patch.object(
            serializer,
            "get_enrollments",
            return_value=enrollments,
        ):
            result = serializer.get_average_course_rating(student_user)

        assert result is None

    def test_get_average_course_rating_rounds_to_two_decimal_places(
        self,
        instructor_user,
        student_user,
    ):
        serializer = self._serializer(instructor_user)

        enrollments = Mock()
        enrollments.aggregate.return_value = {"avg_rating": Decimal("3.125")}

        with patch.object(
            serializer,
            "get_enrollments",
            return_value=enrollments,
        ):
            result = serializer.get_average_course_rating(student_user)

        assert result == Decimal("3.12")

    def test_get_total_students_returns_enrollment_count(
        self,
        instructor_user,
        student_user,
    ):
        serializer = self._serializer(instructor_user)

        enrollments = Mock()
        enrollments.count.return_value = 7

        with patch.object(
            serializer,
            "get_enrollments",
            return_value=enrollments,
        ) as get_enrollments_mock:
            result = serializer.get_total_students(student_user)

        get_enrollments_mock.assert_called_once_with(student_user)
        enrollments.count.assert_called_once_with()
        assert result == 7

    def test_get_total_students_returns_zero_when_no_enrollments(
        self,
        instructor_user,
        student_user,
    ):
        serializer = self._serializer(instructor_user)

        enrollments = Mock()
        enrollments.count.return_value = 0

        with patch.object(
            serializer,
            "get_enrollments",
            return_value=enrollments,
        ):
            result = serializer.get_total_students(student_user)

        assert result == 0

    def test_get_courses_returns_slug_to_title_mapping(
        self,
        instructor_user,
    ):
        course_one = Mock(
            slug="django",
            title="Django REST Framework",
        )
        course_two = Mock(
            slug="python",
            title="Advanced Python",
        )

        student = Mock()
        student.owned_courses.all.return_value = [
            course_one,
            course_two,
        ]

        serializer = self._serializer(instructor_user)

        result = serializer.get_courses(student)

        student.owned_courses.all.assert_called_once_with()

        assert result == {
            "django": "Django REST Framework",
            "python": "Advanced Python",
        }

    def test_get_courses_returns_empty_dict_without_courses(
        self,
        instructor_user,
    ):
        student = Mock()
        student.owned_courses.all.return_value = []

        serializer = self._serializer(instructor_user)

        result = serializer.get_courses(student)

        student.owned_courses.all.assert_called_once_with()

        assert result == {}

    def test_get_courses_uses_course_slug_as_dictionary_key(
        self,
        instructor_user,
    ):
        course = Mock(
            slug="django-rest",
            title="Django REST Framework",
        )

        student = Mock()
        student.owned_courses.all.return_value = [course]

        serializer = self._serializer(instructor_user)

        result = serializer.get_courses(student)

        assert result == {
            "django-rest": "Django REST Framework",
        }

    def test_serializer_output_contains_all_statistics(
        self,
        instructor_user,
    ):
        student = Mock()

        request = self._serializer_request(instructor_user)

        serializer = InstructorStatisticSerializer(
            instance=student,
            context={"request": request},
        )

        with (
            patch.object(
                serializer,
                "get_average_course_rating",
                return_value=4.5,
            ),
            patch.object(
                serializer,
                "get_total_students",
                return_value=12,
            ),
            patch.object(
                serializer,
                "get_courses",
                return_value={
                    "django": "Django REST Framework",
                },
            ),
        ):
            data = serializer.data

        assert data == {
            "average_course_rating": 4.5,
            "total_students": 12,
            "courses": {
                "django": "Django REST Framework",
            },
        }

    def test_serializer_requires_request_context_for_average_rating(
        self,
        instructor_user,
    ):
        serializer = InstructorStatisticSerializer(
            instance=instructor_user,
        )

        with pytest.raises(KeyError):
            _ = serializer.data


@pytest.mark.django_db
class TestInstructorDashboardSerializer:
    def test_serializer_has_expected_fields(self):
        serializer = InstructorDashboardSerializer()

        assert set(serializer.fields) == {
            "statistics",
            "students",
        }

    def test_statistics_is_method_field(self):
        serializer = InstructorDashboardSerializer()

        field = serializer.fields["statistics"]

        assert isinstance(field, serializers.SerializerMethodField)
        assert field.read_only is True

    def test_students_is_method_field(self):
        serializer = InstructorDashboardSerializer()

        field = serializer.fields["students"]

        assert isinstance(field, serializers.SerializerMethodField)
        assert field.read_only is True

    def test_get_statistics_requires_no_database_queries_when_child_is_mocked(
        self,
        instructor_user,
    ):
        request = Mock()
        request.user = instructor_user

        serializer = InstructorDashboardSerializer(
            context={"request": request},
        )

        expected_statistics = {
            "average_course_rating": 4.5,
            "total_students": 10,
            "courses": {
                "django": "Django REST Framework",
            },
        }

        child_serializer = Mock()
        child_serializer.data = expected_statistics

        with patch(
            "instructors.api.serializers.student.InstructorStatisticSerializer",
            return_value=child_serializer,
        ) as serializer_class_mock:
            result = serializer.get_statistics(instructor_user)

        serializer_class_mock.assert_called_once_with(
            instructor_user,
            context={"request": request},
        )
        assert result == expected_statistics

    def test_get_statistics_passes_parent_context_to_child_serializer(
        self,
        instructor_user,
    ):
        request = Mock()
        request.user = instructor_user

        serializer = InstructorDashboardSerializer(
            context={"request": request},
        )

        child_serializer = Mock()
        child_serializer.data = {}

        with patch(
            "instructors.api.serializers.student.InstructorStatisticSerializer",
            return_value=child_serializer,
        ) as serializer_class_mock:
            serializer.get_statistics(instructor_user)

        serializer_class_mock.assert_called_once_with(
            instructor_user,
            context={"request": request},
        )

    def test_get_students_filters_students_by_instructor_courses(
        self,
        instructor_user,
    ):
        request = Mock()
        request.user = instructor_user

        serializer = InstructorDashboardSerializer(
            context={"request": request},
        )

        queryset = Mock()
        distinct_queryset = Mock()
        queryset.distinct.return_value = distinct_queryset

        with patch(
            "instructors.api.serializers.student.User.objects.filter",
            return_value=queryset,
        ) as filter_mock:
            with patch(
                "instructors.api.serializers.student.InstructorStudentSerializer"
            ) as student_serializer_class:
                student_serializer_class.return_value.data = []

                result = serializer.get_students(instructor_user)

        filter_mock.assert_called_once_with(
            enrollments__course__owner=instructor_user,
        )
        queryset.distinct.assert_called_once_with()
        student_serializer_class.assert_called_once_with(
            distinct_queryset,
            many=True,
            context={"request": request},
        )
        assert result == []

    def test_get_students_returns_serialized_students(
        self,
        instructor_user,
    ):
        request = Mock()
        request.user = instructor_user

        serializer = InstructorDashboardSerializer(
            context={"request": request},
        )

        students = [Mock(), Mock()]

        queryset = Mock()
        queryset.distinct.return_value = students

        expected_students = [
            {
                "id": 1,
                "name": "John Doe",
            },
            {
                "id": 2,
                "name": "Jane Doe",
            },
        ]

        child_serializer = Mock()
        child_serializer.data = expected_students

        with patch(
            "instructors.api.serializers.student.User.objects.filter",
            return_value=queryset,
        ):
            with patch(
                "instructors.api.serializers.student.InstructorStudentSerializer",
                return_value=child_serializer,
            ):
                result = serializer.get_students(instructor_user)

        assert result == expected_students

    def test_get_students_uses_distinct_to_prevent_duplicate_students(
        self,
        instructor_user,
    ):
        request = Mock()
        request.user = instructor_user

        serializer = InstructorDashboardSerializer(
            context={"request": request},
        )

        queryset = Mock()
        distinct_queryset = Mock()
        queryset.distinct.return_value = distinct_queryset

        child_serializer = Mock()
        child_serializer.data = []

        with patch(
            "instructors.api.serializers.student.User.objects.filter",
            return_value=queryset,
        ):
            with patch(
                "instructors.api.serializers.student.InstructorStudentSerializer",
                return_value=child_serializer,
            ):
                serializer.get_students(instructor_user)

        queryset.distinct.assert_called_once_with()

    def test_get_students_passes_request_context_to_student_serializer(
        self,
        instructor_user,
    ):
        request = Mock()
        request.user = instructor_user

        serializer = InstructorDashboardSerializer(
            context={"request": request},
        )

        queryset = Mock()
        queryset.distinct.return_value = []

        child_serializer = Mock()
        child_serializer.data = []

        with patch(
            "instructors.api.serializers.student.User.objects.filter",
            return_value=queryset,
        ):
            with patch(
                "instructors.api.serializers.student.InstructorStudentSerializer",
                return_value=child_serializer,
            ) as student_serializer_class:
                serializer.get_students(instructor_user)

        student_serializer_class.assert_called_once_with(
            [],
            many=True,
            context={"request": request},
        )

    def test_get_students_returns_empty_list_when_no_students(
        self,
        instructor_user,
    ):
        request = Mock()
        request.user = instructor_user

        serializer = InstructorDashboardSerializer(
            context={"request": request},
        )

        queryset = Mock()
        queryset.distinct.return_value = []

        child_serializer = Mock()
        child_serializer.data = []

        with patch(
            "instructors.api.serializers.student.User.objects.filter",
            return_value=queryset,
        ):
            with patch(
                "instructors.api.serializers.student.InstructorStudentSerializer",
                return_value=child_serializer,
            ):
                result = serializer.get_students(instructor_user)

        assert result == []

    def test_serializer_requires_context_for_statistics(
        self,
        instructor_user,
    ):
        serializer = InstructorDashboardSerializer(
            instance=instructor_user,
        )

        with pytest.raises(KeyError):
            _ = serializer.data
