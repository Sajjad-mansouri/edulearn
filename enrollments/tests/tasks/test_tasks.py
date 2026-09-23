from unittest.mock import Mock

import pytest

from enrollments.models import Enrollment
from enrollments.tasks import create_certificate_task


class TestCreateCertificateTask:
    def test_creates_certificate_for_enrollment_with_100_percent_progress(
        self,
        test_user,
        course,
        monkeypatch,
        enrollment_completion_signal_disabled,
    ):
        create_certificate = Mock()
        monkeypatch.setattr(
            "enrollments.tasks.create_certificate",
            create_certificate,
        )

        enrollment = Enrollment.objects.create(
            user=test_user,
            course=course,
            status=Enrollment.Status.COMPLETED,
            progress=100,
        )

        create_certificate_task.run(enrollment.id)

        create_certificate.assert_called_once_with(enrollment)

    @pytest.mark.parametrize(
        "progress",
        [0, 1, 50, 75, 99, 99.99],
    )
    def test_does_not_create_certificate_when_progress_is_below_100(
        self,
        test_user,
        course,
        progress,
        monkeypatch,
        enrollment_completion_signal_disabled,
    ):
        create_certificate = Mock()
        monkeypatch.setattr(
            "enrollments.tasks.create_certificate",
            create_certificate,
        )

        enrollment = Enrollment.objects.create(
            user=test_user,
            course=course,
            status=Enrollment.Status.COMPLETED,
            progress=progress,
        )

        result = create_certificate_task.run(enrollment.id)

        assert result is None
        create_certificate.assert_not_called()

    @pytest.mark.parametrize(
        "status",
        [
            Enrollment.Status.PENDING,
            Enrollment.Status.ACTIVE,
            Enrollment.Status.CANCELLED,
            Enrollment.Status.SUSPENDED,
        ],
    )
    def test_creates_certificate_when_progress_is_100_regardless_of_status(
        self,
        test_user,
        course,
        status,
        monkeypatch,
        enrollment_completion_signal_disabled,
    ):
        create_certificate = Mock()
        monkeypatch.setattr(
            "enrollments.tasks.create_certificate",
            create_certificate,
        )

        enrollment = Enrollment.objects.create(
            user=test_user,
            course=course,
            status=status,
            progress=100,
        )

        create_certificate_task.run(enrollment.id)

        create_certificate.assert_called_once_with(enrollment)

    def test_does_not_create_certificate_when_certificate_already_exists(
        self,
        test_user,
        course,
        monkeypatch,
        enrollment_completion_signal_disabled,
    ):
        create_certificate = Mock()
        monkeypatch.setattr(
            "enrollments.tasks.create_certificate",
            create_certificate,
        )

        enrollment = Enrollment.objects.create(
            user=test_user,
            course=course,
            status=Enrollment.Status.COMPLETED,
            progress=100,
        )

        # Import the actual Certificate model used by the project
        # and create the corresponding certificate here.
        #
        # Replace the import below if Certificate is exposed from
        # enrollments.models.__init__.
        from certificates.models import Certificate

        Certificate.objects.create(
            enrollment=enrollment,
        )

        create_certificate_task.run(enrollment.id)

        create_certificate.assert_not_called()

    def test_returns_without_error_when_enrollment_does_not_exist(
        self,
        db,
        monkeypatch,
        enrollment_completion_signal_disabled,
    ):
        create_certificate = Mock()
        monkeypatch.setattr(
            "enrollments.tasks.create_certificate",
            create_certificate,
        )

        result = create_certificate_task.run(999999)

        assert result is None
        create_certificate.assert_not_called()
