from decimal import Decimal
from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from enrollments.models import Enrollment
from payments.exceptions import (
    CourseNotPriced,
    EnrollmentAccessDenied,
    EnrollmentAlreadyPaid,
    EnrollmentNotPayable,
    StripeSessionCreationFailed,
)
from payments.models import Payment
from payments.services.checkout import CheckoutService


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def pending_enrollment(db, test_user, course):
    course.price = Decimal("49.99")
    course.save(update_fields=["price"])

    return Enrollment.objects.create(
        user=test_user,
        course=course,
        status=Enrollment.Status.PENDING,
    )


@pytest.fixture
def payable_payment(db, enrollment):
    return Payment.objects.create(
        enrollment=enrollment,
        amount=Decimal("49.99"),
        currency="usd",
        status=Payment.Status.PENDING,
        payment_type=Payment.Type.ONE_TIME,
        stripe_checkout_session_id="cs_test_123",
        stripe_checkout_url="https://checkout.stripe.com/c/pay/cs_test_123",
    )


@pytest.fixture
def checkout_url():
    return reverse(
        "payment_api:create_checkout_session",
        kwargs={"enrollment_id": 1},
    )


@pytest.mark.django_db
class TestCreateCheckoutSessionApiView:
    def test_successful_checkout_returns_created_response(
        self,
        api_client,
        enrollment,
        payable_payment,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        url = reverse(
            "payment_api:create_checkout_session",
            kwargs={"enrollment_id": enrollment.id},
        )

        with patch.object(
            CheckoutService,
            "create_checkout_session",
            return_value=payable_payment,
        ) as mock_create_checkout:
            response = api_client.post(url)

        assert response.status_code == status.HTTP_201_CREATED

        assert response.data == {
            "id": str(payable_payment.id),
            "checkout_url": payable_payment.stripe_checkout_url,
            "amount": "49.99",
            "currency": "usd",
        }

        mock_create_checkout.assert_called_once_with(
            enrollment=enrollment,
            user=test_user,
        )

    def test_successful_checkout_does_not_accept_request_body_fields(
        self,
        api_client,
        enrollment,
        payable_payment,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        url = reverse(
            "payment_api:create_checkout_session",
            kwargs={"enrollment_id": enrollment.id},
        )

        with patch.object(
            CheckoutService,
            "create_checkout_session",
            return_value=payable_payment,
        ):
            response = api_client.post(
                url,
                data={
                    "amount": "1.00",
                    "currency": "eur",
                    "checkout_url": "https://attacker.example/checkout",
                },
                format="json",
            )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data == {
            "id": str(payable_payment.id),
            "checkout_url": payable_payment.stripe_checkout_url,
            "amount": "49.99",
            "currency": "usd",
        }

    def test_service_receives_authenticated_user(
        self,
        api_client,
        enrollment,
        payable_payment,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        url = reverse(
            "payment_api:create_checkout_session",
            kwargs={"enrollment_id": enrollment.id},
        )

        with patch.object(
            CheckoutService,
            "create_checkout_session",
            return_value=payable_payment,
        ) as mock_create_checkout:
            response = api_client.post(url)

        assert response.status_code == status.HTTP_201_CREATED

        _, kwargs = mock_create_checkout.call_args

        assert kwargs["enrollment"].id == enrollment.id
        assert kwargs["user"] == test_user

    def test_nonexistent_enrollment_returns_forbidden(
        self,
        api_client,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        url = reverse(
            "payment_api:create_checkout_session",
            kwargs={"enrollment_id": 999999},
        )

        with patch.object(
            CheckoutService,
            "create_checkout_session",
        ) as mock_create_checkout:
            response = api_client.post(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        mock_create_checkout.assert_not_called()

    def test_other_users_enrollment_is_not_accessible(
        self,
        api_client,
        another_enrollment,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        url = reverse(
            "payment_api:create_checkout_session",
            kwargs={"enrollment_id": another_enrollment.id},
        )

        with patch.object(
            CheckoutService,
            "create_checkout_session",
        ) as mock_create_checkout:
            response = api_client.post(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        mock_create_checkout.assert_not_called()

    def test_unauthenticated_user_is_denied(
        self,
        api_client,
        enrollment,
    ):
        url = reverse(
            "payment_api:create_checkout_session",
            kwargs={"enrollment_id": enrollment.id},
        )

        with patch.object(
            CheckoutService,
            "create_checkout_session",
        ) as mock_create_checkout:
            response = api_client.post(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        mock_create_checkout.assert_not_called()

    def test_pending_enrollment_is_rejected_by_is_enrolled_permission(
        self,
        api_client,
        pending_enrollment,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        url = reverse(
            "payment_api:create_checkout_session",
            kwargs={"enrollment_id": pending_enrollment.id},
        )

        with patch.object(
            CheckoutService,
            "create_checkout_session",
        ) as mock_create_checkout:
            response = api_client.post(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        mock_create_checkout.assert_not_called()

    def test_active_enrollment_reaches_checkout_service(
        self,
        api_client,
        enrollment,
        payable_payment,
        test_user,
    ):
        assert enrollment.status == Enrollment.Status.ACTIVE

        api_client.force_authenticate(user=test_user)

        url = reverse(
            "payment_api:create_checkout_session",
            kwargs={"enrollment_id": enrollment.id},
        )

        with patch.object(
            CheckoutService,
            "create_checkout_session",
            return_value=payable_payment,
        ) as mock_create_checkout:
            response = api_client.post(url)

        assert response.status_code == status.HTTP_201_CREATED

        mock_create_checkout.assert_called_once_with(
            enrollment=enrollment,
            user=test_user,
        )

    @pytest.mark.parametrize(
        ("exception", "expected_status"),
        [
            (
                EnrollmentAccessDenied("You do not have access to this enrollment."),
                status.HTTP_403_FORBIDDEN,
            ),
            (
                EnrollmentNotPayable("This enrollment is not available for payment."),
                status.HTTP_400_BAD_REQUEST,
            ),
            (
                EnrollmentAlreadyPaid("A payment for this enrollment already exists."),
                status.HTTP_409_CONFLICT,
            ),
            (
                CourseNotPriced("This course does not have a price."),
                status.HTTP_400_BAD_REQUEST,
            ),
            (
                StripeSessionCreationFailed("Unable to create the payment session."),
                status.HTTP_502_BAD_GATEWAY,
            ),
        ],
    )
    def test_checkout_service_exceptions_are_mapped_to_expected_status_codes(
        self,
        api_client,
        enrollment,
        test_user,
        exception,
        expected_status,
    ):
        api_client.force_authenticate(user=test_user)

        url = reverse(
            "payment_api:create_checkout_session",
            kwargs={"enrollment_id": enrollment.id},
        )

        with patch.object(
            CheckoutService,
            "create_checkout_session",
            side_effect=exception,
        ):
            response = api_client.post(url)

        assert response.status_code == expected_status
        assert response.data == {
            "detail": str(exception),
        }

    def test_enrollment_access_denied_returns_exception_message(
        self,
        api_client,
        enrollment,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        url = reverse(
            "payment_api:create_checkout_session",
            kwargs={"enrollment_id": enrollment.id},
        )

        exception = EnrollmentAccessDenied("You do not have access to this enrollment.")

        with patch.object(
            CheckoutService,
            "create_checkout_session",
            side_effect=exception,
        ):
            response = api_client.post(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == ("You do not have access to this enrollment.")

    def test_enrollment_not_payable_returns_bad_request(
        self,
        api_client,
        enrollment,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        url = reverse(
            "payment_api:create_checkout_session",
            kwargs={"enrollment_id": enrollment.id},
        )

        exception = EnrollmentNotPayable(
            "This enrollment is not available for payment."
        )

        with patch.object(
            CheckoutService,
            "create_checkout_session",
            side_effect=exception,
        ):
            response = api_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            "detail": "This enrollment is not available for payment.",
        }

    def test_already_paid_returns_conflict(
        self,
        api_client,
        enrollment,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        url = reverse(
            "payment_api:create_checkout_session",
            kwargs={"enrollment_id": enrollment.id},
        )

        exception = EnrollmentAlreadyPaid(
            "A payment for this enrollment already exists."
        )

        with patch.object(
            CheckoutService,
            "create_checkout_session",
            side_effect=exception,
        ):
            response = api_client.post(url)

        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.data == {
            "detail": "A payment for this enrollment already exists.",
        }

    def test_course_not_priced_returns_bad_request(
        self,
        api_client,
        enrollment,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        url = reverse(
            "payment_api:create_checkout_session",
            kwargs={"enrollment_id": enrollment.id},
        )

        exception = CourseNotPriced("This course does not have a price.")

        with patch.object(
            CheckoutService,
            "create_checkout_session",
            side_effect=exception,
        ):
            response = api_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            "detail": "This course does not have a price.",
        }

    def test_stripe_failure_returns_bad_gateway(
        self,
        api_client,
        enrollment,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        url = reverse(
            "payment_api:create_checkout_session",
            kwargs={"enrollment_id": enrollment.id},
        )

        exception = StripeSessionCreationFailed("Unable to create the payment session.")

        with patch.object(
            CheckoutService,
            "create_checkout_session",
            side_effect=exception,
        ):
            response = api_client.post(url)

        assert response.status_code == status.HTTP_502_BAD_GATEWAY
        assert response.data == {
            "detail": "Unable to create the payment session.",
        }

    def test_service_failure_does_not_expose_internal_exception_details(
        self,
        api_client,
        enrollment,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        url = reverse(
            "payment_api:create_checkout_session",
            kwargs={"enrollment_id": enrollment.id},
        )

        exception = StripeSessionCreationFailed("Unable to create the payment session.")

        with patch.object(
            CheckoutService,
            "create_checkout_session",
            side_effect=exception,
        ):
            response = api_client.post(url)

        assert response.status_code == status.HTTP_502_BAD_GATEWAY
        assert "Traceback" not in str(response.data)
        assert "stripe" not in str(response.data).lower()

    def test_get_method_is_not_allowed(
        self,
        api_client,
        enrollment,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        url = reverse(
            "payment_api:create_checkout_session",
            kwargs={"enrollment_id": enrollment.id},
        )

        with patch.object(
            CheckoutService,
            "create_checkout_session",
        ) as mock_create_checkout:
            response = api_client.get(url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        mock_create_checkout.assert_not_called()

    def test_put_method_is_not_allowed(
        self,
        api_client,
        enrollment,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        url = reverse(
            "payment_api:create_checkout_session",
            kwargs={"enrollment_id": enrollment.id},
        )

        with patch.object(
            CheckoutService,
            "create_checkout_session",
        ) as mock_create_checkout:
            response = api_client.put(url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        mock_create_checkout.assert_not_called()

    def test_patch_method_is_not_allowed(
        self,
        api_client,
        enrollment,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        url = reverse(
            "payment_api:create_checkout_session",
            kwargs={"enrollment_id": enrollment.id},
        )

        with patch.object(
            CheckoutService,
            "create_checkout_session",
        ) as mock_create_checkout:
            response = api_client.patch(url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        mock_create_checkout.assert_not_called()

    def test_delete_method_is_not_allowed(
        self,
        api_client,
        enrollment,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        url = reverse(
            "payment_api:create_checkout_session",
            kwargs={"enrollment_id": enrollment.id},
        )

        with patch.object(
            CheckoutService,
            "create_checkout_session",
        ) as mock_create_checkout:
            response = api_client.delete(url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        mock_create_checkout.assert_not_called()

    def test_post_does_not_create_payment_when_service_is_not_called(
        self,
        api_client,
        pending_enrollment,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        url = reverse(
            "payment_api:create_checkout_session",
            kwargs={"enrollment_id": pending_enrollment.id},
        )

        payment_count_before = Payment.objects.count()

        with patch.object(
            CheckoutService,
            "create_checkout_session",
        ) as mock_create_checkout:
            response = api_client.post(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        mock_create_checkout.assert_not_called()
        assert Payment.objects.count() == payment_count_before
