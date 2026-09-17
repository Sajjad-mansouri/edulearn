from unittest.mock import Mock

import pytest
from django.test import override_settings

from enrollments.models import Enrollment


class TestEnrollmentCompletedSignal:
    @override_settings(HOST_ASYNC_ABILITY=True)
    def test_completed_enrollment_with_100_percent_dispatches_certificate_task(
        self,
        test_user,
        course,
        monkeypatch,
    ):
        task_delay = Mock()

        monkeypatch.setattr(
            "enrollments.signals.create_certificate_task.delay",
            task_delay,
        )

        enrollment = Enrollment.objects.create(
            user=test_user,
            course=course,
            status=Enrollment.Status.COMPLETED,
            progress=100,
        )

        task_delay.assert_called_once_with(enrollment.id)

    @override_settings(HOST_ASYNC_ABILITY=False)
    def test_completed_enrollment_with_100_percent_runs_task_synchronously(
        self,
        test_user,
        course,
        monkeypatch,
    ):
        task = Mock()

        monkeypatch.setattr(
            "enrollments.signals.create_certificate_task",
            task,
        )

        enrollment = Enrollment.objects.create(
            user=test_user,
            course=course,
            status=Enrollment.Status.COMPLETED,
            progress=100,
        )

        task.assert_called_once_with(enrollment.id)

    @pytest.mark.parametrize(
        "status",
        [
            Enrollment.Status.PENDING,
            Enrollment.Status.ACTIVE,
            Enrollment.Status.CANCELLED,
            Enrollment.Status.SUSPENDED,
        ],
    )
    @override_settings(HOST_ASYNC_ABILITY=True)
    def test_non_completed_status_does_not_dispatch_certificate_task(
        self,
        test_user,
        course,
        status,
        monkeypatch,
    ):
        task_delay = Mock()

        monkeypatch.setattr(
            "enrollments.signals.create_certificate_task.delay",
            task_delay,
        )

        Enrollment.objects.create(
            user=test_user,
            course=course,
            status=status,
            progress=100,
        )

        task_delay.assert_not_called()

    @pytest.mark.parametrize(
        "progress",
        [
            0,
            1,
            50,
            75,
            99,
            99.99,
        ],
    )
    @override_settings(HOST_ASYNC_ABILITY=True)
    def test_completed_enrollment_below_100_percent_does_not_dispatch_certificate_task(
        self,
        test_user,
        course,
        progress,
        monkeypatch,
    ):
        task_delay = Mock()

        monkeypatch.setattr(
            "enrollments.signals.create_certificate_task.delay",
            task_delay,
        )

        Enrollment.objects.create(
            user=test_user,
            course=course,
            status=Enrollment.Status.COMPLETED,
            progress=progress,
        )

        task_delay.assert_not_called()

    @pytest.mark.parametrize(
        "progress",
        [
            100,
            100.0,
            100.00,
        ],
    )
    @override_settings(HOST_ASYNC_ABILITY=True)
    def test_completed_enrollment_at_100_percent_dispatches_certificate_task(
        self,
        test_user,
        course,
        progress,
        monkeypatch,
    ):
        task_delay = Mock()

        monkeypatch.setattr(
            "enrollments.signals.create_certificate_task.delay",
            task_delay,
        )

        enrollment = Enrollment.objects.create(
            user=test_user,
            course=course,
            status=Enrollment.Status.COMPLETED,
            progress=progress,
        )

        task_delay.assert_called_once_with(enrollment.id)

    @override_settings(HOST_ASYNC_ABILITY=True)
    def test_completed_enrollment_task_receives_enrollment_id(
        self,
        test_user,
        course,
        monkeypatch,
    ):
        task_delay = Mock()

        monkeypatch.setattr(
            "enrollments.signals.create_certificate_task.delay",
            task_delay,
        )

        enrollment = Enrollment.objects.create(
            user=test_user,
            course=course,
            status=Enrollment.Status.COMPLETED,
            progress=100,
        )

        assert task_delay.call_args.args == (enrollment.id,)

    @override_settings(HOST_ASYNC_ABILITY=True)
    def test_incomplete_enrollment_does_not_dispatch_certificate_task(
        self,
        test_user,
        course,
        monkeypatch,
    ):
        task_delay = Mock()

        monkeypatch.setattr(
            "enrollments.signals.create_certificate_task.delay",
            task_delay,
        )

        Enrollment.objects.create(
            user=test_user,
            course=course,
            status=Enrollment.Status.ACTIVE,
            progress=50,
        )

        task_delay.assert_not_called()

    @override_settings(HOST_ASYNC_ABILITY=True)
    def test_completed_enrollment_with_zero_progress_does_not_dispatch_certificate_task(
        self,
        test_user,
        course,
        monkeypatch,
    ):
        task_delay = Mock()

        monkeypatch.setattr(
            "enrollments.signals.create_certificate_task.delay",
            task_delay,
        )

        Enrollment.objects.create(
            user=test_user,
            course=course,
            status=Enrollment.Status.COMPLETED,
            progress=0,
        )

        task_delay.assert_not_called()

    @override_settings(HOST_ASYNC_ABILITY=True)
    def test_completed_enrollment_with_decimal_progress_below_100_does_not_dispatch_task(
        self,
        test_user,
        course,
        monkeypatch,
    ):
        task_delay = Mock()

        monkeypatch.setattr(
            "enrollments.signals.create_certificate_task.delay",
            task_delay,
        )

        Enrollment.objects.create(
            user=test_user,
            course=course,
            status=Enrollment.Status.COMPLETED,
            progress=99.99,
        )

        task_delay.assert_not_called()

    @override_settings(HOST_ASYNC_ABILITY=False)
    def test_non_completed_enrollment_does_not_run_task_synchronously(
        self,
        test_user,
        course,
        monkeypatch,
    ):
        task = Mock()

        monkeypatch.setattr(
            "enrollments.signals.create_certificate_task",
            task,
        )

        Enrollment.objects.create(
            user=test_user,
            course=course,
            status=Enrollment.Status.ACTIVE,
            progress=100,
        )

        task.assert_not_called()

    @override_settings(HOST_ASYNC_ABILITY=False)
    def test_completed_enrollment_below_100_does_not_run_task_synchronously(
        self,
        test_user,
        course,
        monkeypatch,
    ):
        task = Mock()

        monkeypatch.setattr(
            "enrollments.signals.create_certificate_task",
            task,
        )

        Enrollment.objects.create(
            user=test_user,
            course=course,
            status=Enrollment.Status.COMPLETED,
            progress=99.99,
        )

        task.assert_not_called()
