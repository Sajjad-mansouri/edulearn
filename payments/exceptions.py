class PaymentError(Exception):
    """Base exception for payment domain errors."""

    pass


class EnrollmentAccessDenied(PaymentError):
    """Raised when the user does not own the enrollment."""

    pass


class EnrollmentNotPayable(PaymentError):
    """Raised when the enrollment is not in a payable state."""

    pass


class EnrollmentAlreadyPaid(PaymentError):
    """Raised when a successful payment already exists for the enrollment."""

    pass


class CourseNotPriced(PaymentError):
    """Raised when the course has no valid price."""

    pass


class StripeSessionCreationFailed(PaymentError):
    """Raised when Stripe fails to create a checkout session."""

    pass
