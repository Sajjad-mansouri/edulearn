from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from courses.models import Course
from enrollments.models import Enrollment
from instructors.api.serializers import TransactionSerializer
from instructors.api.views import InstructorTransactionsPagination
from payments.models import Payment

pytestmark = pytest.mark.django_db


class TestInstructorTransactionsApiView:
    @pytest.fixture
    def url(self):
        return reverse("instructor_api:transactions")

    def create_payment(
        self,
        enrollment,
        *,
        amount=Decimal("100.00"),
        status=Payment.Status.SUCCEEDED,
        paid_at=None,
        refunded_at=None,
    ):
        return Payment.objects.create(
            enrollment=enrollment,
            amount=amount,
            status=status,
            paid_at=paid_at,
            refunded_at=refunded_at,
        )

    def test_unauthenticated_user_cannot_access_transactions(
        self,
        api_client,
        url,
    ):
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_non_instructor_user_cannot_access_transactions(
        self,
        api_client,
        student_user,
        url,
    ):
        api_client.force_authenticate(user=student_user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == (
            "You must be an instructor to access this resource."
        )

    def test_instructor_can_access_transactions(
        self,
        api_client,
        instructor_user,
        instructor_enrollment,
        url,
    ):
        self.create_payment(
            instructor_enrollment,
            amount=Decimal("150.00"),
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert len(response.data["results"]) == 1

    def test_transactions_are_limited_to_authenticated_instructor_courses(
        self,
        api_client,
        instructor_user,
        instructor_enrollment,
        student_user,
        url,
    ):
        instructor_payment = self.create_payment(
            instructor_enrollment,
            amount=Decimal("150.00"),
        )

        other_course = Course.objects.create(
            owner=student_user,
            title="Other Instructor Course",
            slug="other-instructor-course",
        )
        other_enrollment = Enrollment.objects.create(
            user=student_user,
            course=other_course,
        )
        other_payment = self.create_payment(
            other_enrollment,
            amount=Decimal("300.00"),
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

        transaction_ids = {
            transaction["id"] for transaction in response.data["results"]
        }

        assert str(instructor_payment.id) in transaction_ids
        assert str(other_payment.id) not in transaction_ids

    def test_instructor_cannot_see_payment_from_another_instructor(
        self,
        api_client,
        instructor_user,
        instructor_enrollment,
        url,
    ):
        another_instructor = type(instructor_user).objects.create_user(
            username="another_instructor",
            email="another_instructor@example.com",
            password="test-password",
        )

        other_student = type(instructor_user).objects.create_user(
            username="other_student",
            email="other_student@example.com",
            password="test-password",
        )

        other_course = Course.objects.create(
            owner=another_instructor,
            title="Other Instructor Course",
            slug="other-instructor-course",
        )
        other_enrollment = Enrollment.objects.create(
            user=other_student,
            course=other_course,
        )

        own_payment = self.create_payment(
            instructor_enrollment,
            amount=Decimal("100.00"),
        )
        other_payment = self.create_payment(
            other_enrollment,
            amount=Decimal("500.00"),
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

        returned_ids = {transaction["id"] for transaction in response.data["results"]}

        assert str(own_payment.id) in returned_ids
        assert str(other_payment.id) not in returned_ids

    def test_no_transactions_returns_empty_paginated_response(
        self,
        api_client,
        instructor_user,
        url,
    ):
        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0
        assert response.data["results"] == []
        assert response.data["next"] is None
        assert response.data["previous"] is None

    def test_default_page_size_is_ten(
        self,
        api_client,
        instructor_user,
        instructor_enrollment,
        url,
    ):
        for _ in range(11):
            self.create_payment(
                instructor_enrollment,
                amount=Decimal("100.00"),
            )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 11
        assert len(response.data["results"]) == 10
        assert response.data["next"] is not None
        assert response.data["previous"] is None

    def test_page_size_query_parameter_changes_page_size(
        self,
        api_client,
        instructor_user,
        instructor_enrollment,
        url,
    ):
        for _ in range(15):
            self.create_payment(
                instructor_enrollment,
                amount=Decimal("100.00"),
            )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(
            url,
            {"page_size": 5},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 15
        assert len(response.data["results"]) == 5
        assert response.data["next"] is not None

    def test_page_size_cannot_exceed_maximum_page_size(
        self,
        api_client,
        instructor_user,
        instructor_enrollment,
        url,
    ):
        for _ in range(101):
            self.create_payment(
                instructor_enrollment,
                amount=Decimal("100.00"),
            )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(
            url,
            {"page_size": 101},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 101
        assert len(response.data["results"]) == 100
        assert response.data["next"] is not None

    def test_second_page_returns_remaining_transactions(
        self,
        api_client,
        instructor_user,
        instructor_enrollment,
        url,
    ):
        payments = [
            self.create_payment(
                instructor_enrollment,
                amount=Decimal("100.00"),
            )
            for _ in range(15)
        ]

        api_client.force_authenticate(user=instructor_user)

        first_response = api_client.get(
            url,
            {"page_size": 10},
        )
        second_response = api_client.get(
            url,
            {
                "page_size": 10,
                "page": 2,
            },
        )

        assert first_response.status_code == status.HTTP_200_OK
        assert second_response.status_code == status.HTTP_200_OK

        assert first_response.data["count"] == 15
        assert second_response.data["count"] == 15

        assert len(first_response.data["results"]) == 10
        assert len(second_response.data["results"]) == 5

        first_ids = {
            transaction["id"] for transaction in first_response.data["results"]
        }
        second_ids = {
            transaction["id"] for transaction in second_response.data["results"]
        }

        assert first_ids.isdisjoint(second_ids)

        all_ids = {str(payment.id) for payment in payments}

        assert first_ids | second_ids == all_ids

    def test_transactions_are_ordered_by_updated_at_descending(
        self,
        api_client,
        instructor_user,
        instructor_enrollment,
        url,
    ):
        older_payment = self.create_payment(
            instructor_enrollment,
            amount=Decimal("100.00"),
        )
        newer_payment = self.create_payment(
            instructor_enrollment,
            amount=Decimal("200.00"),
        )

        now = timezone.now()

        Payment.objects.filter(pk=older_payment.pk).update(
            updated_at=now - timedelta(hours=2),
        )
        Payment.objects.filter(pk=newer_payment.pk).update(
            updated_at=now - timedelta(hours=1),
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        results = response.data["results"]

        assert len(results) == 2
        assert results[0]["id"] == str(newer_payment.id)
        assert results[1]["id"] == str(older_payment.id)

    def test_transaction_contains_expected_fields(
        self,
        api_client,
        instructor_user,
        instructor_enrollment,
        url,
    ):
        self.create_payment(
            instructor_enrollment,
            amount=Decimal("250.50"),
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        transaction = response.data["results"][0]

        assert set(transaction.keys()) == {
            "id",
            "type",
            "amount",
            "date",
            "status",
            "course",
        }

    def test_transaction_contains_payment_id(
        self,
        api_client,
        instructor_user,
        instructor_enrollment,
        url,
    ):
        payment = self.create_payment(
            instructor_enrollment,
            amount=Decimal("250.50"),
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        transaction = response.data["results"][0]

        assert transaction["id"] == str(payment.id)

    def test_transaction_amount_is_serialized_with_two_decimal_places(
        self,
        api_client,
        instructor_user,
        instructor_enrollment,
        url,
    ):
        self.create_payment(
            instructor_enrollment,
            amount=Decimal("250.50"),
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        transaction = response.data["results"][0]

        assert transaction["amount"] == "250.50"

    def test_transaction_type_is_sale(
        self,
        api_client,
        instructor_user,
        instructor_enrollment,
        url,
    ):
        self.create_payment(
            instructor_enrollment,
            amount=Decimal("250.00"),
            status=Payment.Status.SUCCEEDED,
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        transaction = response.data["results"][0]

        assert transaction["type"] == "sale"

    def test_successful_transaction_uses_paid_at_as_date(
        self,
        api_client,
        instructor_user,
        instructor_enrollment,
        url,
    ):
        paid_at = timezone.now() - timedelta(days=2)

        payment = self.create_payment(
            instructor_enrollment,
            amount=Decimal("250.00"),
            status=Payment.Status.SUCCEEDED,
            paid_at=paid_at,
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        transaction = response.data["results"][0]

        assert transaction["id"] == str(payment.id)
        assert transaction["date"] == paid_at

    def test_refunded_transaction_uses_refunded_at_as_date(
        self,
        api_client,
        instructor_user,
        instructor_enrollment,
        url,
    ):
        refunded_at = timezone.now() - timedelta(days=1)

        payment = self.create_payment(
            instructor_enrollment,
            amount=Decimal("250.00"),
            status=Payment.Status.REFUNDED,
            refunded_at=refunded_at,
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        transaction = response.data["results"][0]

        assert transaction["id"] == str(payment.id)
        assert transaction["date"] == refunded_at

    def test_transaction_without_paid_or_refunded_timestamp_uses_updated_at(
        self,
        api_client,
        instructor_user,
        instructor_enrollment,
        url,
    ):
        payment = self.create_payment(
            instructor_enrollment,
            amount=Decimal("250.00"),
            status=Payment.Status.PENDING,
        )

        updated_at = timezone.now() - timedelta(hours=3)

        Payment.objects.filter(pk=payment.pk).update(
            updated_at=updated_at,
        )
        payment.refresh_from_db()

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        transaction = response.data["results"][0]

        assert transaction["id"] == str(payment.id)
        assert transaction["date"] == updated_at

    def test_course_is_serialized_from_payment_enrollment_course(
        self,
        api_client,
        instructor_user,
        instructor_course,
        instructor_enrollment,
        url,
    ):
        self.create_payment(
            instructor_enrollment,
            amount=Decimal("300.00"),
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        transaction = response.data["results"][0]

        assert transaction["course"] == instructor_course.title

    def test_multiple_transactions_from_same_course_are_returned(
        self,
        api_client,
        instructor_user,
        instructor_enrollment,
        url,
    ):
        first_payment = self.create_payment(
            instructor_enrollment,
            amount=Decimal("100.00"),
        )
        second_payment = self.create_payment(
            instructor_enrollment,
            amount=Decimal("200.00"),
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

        transaction_ids = {
            transaction["id"] for transaction in response.data["results"]
        }

        assert transaction_ids == {
            str(first_payment.id),
            str(second_payment.id),
        }

    def test_transactions_from_multiple_owned_courses_are_returned(
        self,
        api_client,
        instructor_user,
        instructor_course,
        instructor_enrollment,
        url,
    ):
        second_course = Course.objects.create(
            owner=instructor_user,
            title="Advanced Python",
            slug="advanced-python",
        )
        second_enrollment = Enrollment.objects.create(
            user=instructor_enrollment.user,
            course=second_course,
        )

        first_payment = self.create_payment(
            instructor_enrollment,
            amount=Decimal("100.00"),
        )
        second_payment = self.create_payment(
            second_enrollment,
            amount=Decimal("200.00"),
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

        transactions_by_id = {
            transaction["id"]: transaction for transaction in response.data["results"]
        }

        assert transactions_by_id[str(first_payment.id)]["course"] == (
            instructor_course.title
        )
        assert transactions_by_id[str(second_payment.id)]["course"] == (
            second_course.title
        )

    def test_failed_payment_is_returned_as_transaction(
        self,
        api_client,
        instructor_user,
        instructor_enrollment,
        url,
    ):
        payment = self.create_payment(
            instructor_enrollment,
            amount=Decimal("100.00"),
            status=Payment.Status.FAILED,
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

        transaction = response.data["results"][0]

        assert transaction["id"] == str(payment.id)
        assert transaction["status"] == Payment.Status.FAILED

    def test_refunded_payment_is_returned_as_transaction(
        self,
        api_client,
        instructor_user,
        instructor_enrollment,
        url,
    ):
        payment = self.create_payment(
            instructor_enrollment,
            amount=Decimal("100.00"),
            status=Payment.Status.REFUNDED,
            refunded_at=timezone.now(),
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

        transaction = response.data["results"][0]

        assert transaction["id"] == str(payment.id)
        assert transaction["status"] == Payment.Status.REFUNDED

    def test_pending_payment_is_returned_as_transaction(
        self,
        api_client,
        instructor_user,
        instructor_enrollment,
        url,
    ):
        payment = self.create_payment(
            instructor_enrollment,
            amount=Decimal("100.00"),
            status=Payment.Status.PENDING,
        )

        api_client.force_authenticate(user=instructor_user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

        transaction = response.data["results"][0]

        assert transaction["id"] == str(payment.id)
        assert transaction["status"] == Payment.Status.PENDING

    @pytest.mark.parametrize(
        "method",
        [
            "post",
            "put",
            "patch",
            "delete",
        ],
    )
    def test_unsupported_http_methods_return_405(
        self,
        api_client,
        instructor_user,
        url,
        method,
    ):
        api_client.force_authenticate(user=instructor_user)

        response = getattr(api_client, method)(url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_transactions_url_resolves_correctly(self):
        url = reverse("instructor_api:transactions")

        assert url.endswith("/transactions/")


class TestInstructorTransactionsPagination:
    def test_page_size_is_ten(self):
        assert InstructorTransactionsPagination.page_size == 10

    def test_page_size_query_parameter_is_page_size(self):
        assert InstructorTransactionsPagination.page_size_query_param == "page_size"

    def test_max_page_size_is_one_hundred(self):
        assert InstructorTransactionsPagination.max_page_size == 100


class TestTransactionSerializer:
    def test_serializer_contains_expected_fields(
        self,
        instructor_enrollment,
    ):
        payment = Payment.objects.create(
            enrollment=instructor_enrollment,
            amount=Decimal("125.50"),
            status=Payment.Status.SUCCEEDED,
            paid_at=timezone.now(),
        )

        serializer = TransactionSerializer(payment)

        assert set(serializer.data.keys()) == {
            "id",
            "type",
            "amount",
            "date",
            "status",
        }

    def test_get_type_returns_sale(
        self,
        instructor_enrollment,
    ):
        payment = Payment.objects.create(
            enrollment=instructor_enrollment,
            amount=Decimal("125.50"),
            status=Payment.Status.REFUNDED,
            refunded_at=timezone.now(),
        )

        serializer = TransactionSerializer(payment)

        assert serializer.data["type"] == "sale"

    def test_successful_payment_date_comes_from_paid_at(
        self,
        instructor_enrollment,
    ):
        paid_at = timezone.now() - timedelta(days=2)

        payment = Payment.objects.create(
            enrollment=instructor_enrollment,
            amount=Decimal("125.50"),
            status=Payment.Status.SUCCEEDED,
            paid_at=paid_at,
        )

        serializer = TransactionSerializer(payment)

        assert serializer.data["date"] == paid_at

    def test_refunded_payment_date_comes_from_refunded_at(
        self,
        instructor_enrollment,
    ):
        refunded_at = timezone.now() - timedelta(days=1)

        payment = Payment.objects.create(
            enrollment=instructor_enrollment,
            amount=Decimal("125.50"),
            status=Payment.Status.REFUNDED,
            refunded_at=refunded_at,
        )

        serializer = TransactionSerializer(payment)

        assert serializer.data["date"] == refunded_at

    def test_payment_without_relevant_status_timestamp_uses_updated_at(
        self,
        instructor_enrollment,
    ):
        payment = Payment.objects.create(
            enrollment=instructor_enrollment,
            amount=Decimal("125.50"),
            status=Payment.Status.PENDING,
        )

        updated_at = timezone.now() - timedelta(hours=4)

        Payment.objects.filter(pk=payment.pk).update(
            updated_at=updated_at,
        )
        payment.refresh_from_db()

        serializer = TransactionSerializer(payment)

        assert serializer.data["date"] == updated_at

    def test_course_field_is_read_only(
        self,
        instructor_enrollment,
    ):
        payment = Payment.objects.create(
            enrollment=instructor_enrollment,
            amount=Decimal("125.50"),
            status=Payment.Status.SUCCEEDED,
            paid_at=timezone.now(),
        )

        serializer = TransactionSerializer(
            payment,
            data={"course": "Modified Course"},
            partial=True,
        )

        assert serializer.is_valid()

        assert "course" not in serializer.validated_data
