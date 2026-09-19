from unittest.mock import Mock, patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from courses.models import Course


@pytest.mark.django_db
class TestCourseBuilder:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def create_course_url(self):
        return reverse(
            "instructor_api:create_course",
            kwargs={"course_status": Course.Status.DRAFT},
        )

    @pytest.fixture
    def submitted_course_url(self):
        return reverse(
            "instructor_api:create_course",
            kwargs={"course_status": Course.Status.SUBMITTED},
        )

    @pytest.fixture
    def normalized_course_data(self):
        return {
            "title": "Django REST Framework",
            "category": "django",
            "sections": [],
            "attachments": [],
            "tags": [],
        }

    @pytest.fixture
    def serializer(self):
        serializer = Mock()

        serializer.validated_data = {
            "title": "Django REST Framework",
            "category": Mock(),
            "sections": [],
            "attachments": [],
            "tags": [],
        }

        serializer.data = {
            "id": 1,
            "title": "Django REST Framework",
        }

        return serializer

    @pytest.fixture
    def created_course(self):
        return Mock()

    def test_unauthenticated_user_cannot_create_course(
        self,
        api_client,
        create_course_url,
    ):
        # Arrange
        payload = {
            "title": "Django REST Framework",
        }

        # Act
        response = api_client.post(
            create_course_url,
            data=payload,
            format="json",
        )

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_student_cannot_create_course(
        self,
        api_client,
        student_user,
        create_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        payload = {
            "title": "Django REST Framework",
        }

        # Act
        response = api_client.post(
            create_course_url,
            data=payload,
            format="json",
        )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_instructor_can_create_course(
        self,
        api_client,
        instructor_user,
        serializer,
        created_course,
        normalized_course_data,
        create_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)

        payload = {
            "title": "Django REST Framework",
        }

        with (
            patch(
                "instructors.api.views.normalize_course_data",
                return_value=(normalized_course_data, False),
            ),
            patch(
                "instructors.api.views.CourseSerializer",
                return_value=serializer,
            ),
            patch(
                "instructors.api.views.CourseService",
            ) as service_class_mock,
        ):
            service_class_mock.return_value.create.return_value = created_course

            # Act
            response = api_client.post(
                create_course_url,
                data=payload,
                format="json",
            )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        service_class_mock.assert_called_once_with(
            instructor=instructor_user,
        )

        service_class_mock.return_value.create.assert_called_once_with(
            serializer.validated_data,
        )

    def test_normalize_course_data_is_called_with_request_data(
        self,
        api_client,
        instructor_user,
        serializer,
        created_course,
        normalized_course_data,
        create_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)

        payload = {
            "title": "Django REST Framework",
            "description": "Learn Django REST Framework",
        }

        with (
            patch(
                "instructors.api.views.normalize_course_data",
                return_value=(normalized_course_data, False),
            ) as normalize_mock,
            patch(
                "instructors.api.views.CourseSerializer",
                return_value=serializer,
            ),
            patch(
                "instructors.api.views.CourseService",
            ) as service_class_mock,
        ):
            service_class_mock.return_value.create.return_value = created_course

            # Act
            response = api_client.post(
                create_course_url,
                data=payload,
                format="json",
            )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        normalize_mock.assert_called_once()

        request_data = normalize_mock.call_args.args[0]

        assert request_data["title"] == payload["title"]
        assert request_data["description"] == payload["description"]

    def test_normalized_course_data_is_passed_to_serializer(
        self,
        api_client,
        instructor_user,
        serializer,
        created_course,
        normalized_course_data,
        create_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)

        with (
            patch(
                "instructors.api.views.normalize_course_data",
                return_value=(normalized_course_data, False),
            ),
            patch(
                "instructors.api.views.CourseSerializer",
                return_value=serializer,
            ) as serializer_class_mock,
            patch(
                "instructors.api.views.CourseService",
            ) as service_class_mock,
        ):
            service_class_mock.return_value.create.return_value = created_course

            # Act
            response = api_client.post(
                create_course_url,
                data={},
                format="json",
            )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        serializer_class_mock.assert_called_once_with(
            data=normalized_course_data,
        )

    def test_serializer_is_validated_with_raise_exception_true(
        self,
        api_client,
        instructor_user,
        serializer,
        created_course,
        normalized_course_data,
        create_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)

        with (
            patch(
                "instructors.api.views.normalize_course_data",
                return_value=(normalized_course_data, False),
            ),
            patch(
                "instructors.api.views.CourseSerializer",
                return_value=serializer,
            ),
            patch(
                "instructors.api.views.CourseService",
            ) as service_class_mock,
        ):
            service_class_mock.return_value.create.return_value = created_course

            # Act
            response = api_client.post(
                create_course_url,
                data={},
                format="json",
            )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        serializer.is_valid.assert_called_once_with(
            raise_exception=True,
        )

    def test_validated_data_is_passed_to_course_service(
        self,
        api_client,
        instructor_user,
        serializer,
        created_course,
        normalized_course_data,
        create_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)

        with (
            patch(
                "instructors.api.views.normalize_course_data",
                return_value=(normalized_course_data, False),
            ),
            patch(
                "instructors.api.views.CourseSerializer",
                return_value=serializer,
            ),
            patch(
                "instructors.api.views.CourseService",
            ) as service_class_mock,
        ):
            service_class_mock.return_value.create.return_value = created_course

            # Act
            response = api_client.post(
                create_course_url,
                data={},
                format="json",
            )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        service_class_mock.return_value.create.assert_called_once_with(
            serializer.validated_data,
        )

    def test_course_service_receives_authenticated_instructor(
        self,
        api_client,
        instructor_user,
        serializer,
        created_course,
        normalized_course_data,
        create_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)

        with (
            patch(
                "instructors.api.views.normalize_course_data",
                return_value=(normalized_course_data, False),
            ),
            patch(
                "instructors.api.views.CourseSerializer",
                return_value=serializer,
            ),
            patch(
                "instructors.api.views.CourseService",
            ) as service_class_mock,
        ):
            service_class_mock.return_value.create.return_value = created_course

            # Act
            response = api_client.post(
                create_course_url,
                data={},
                format="json",
            )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        service_class_mock.assert_called_once_with(
            instructor=instructor_user,
        )

    def test_response_contains_serializer_data(
        self,
        api_client,
        instructor_user,
        serializer,
        created_course,
        normalized_course_data,
        create_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)

        with (
            patch(
                "instructors.api.views.normalize_course_data",
                return_value=(normalized_course_data, False),
            ),
            patch(
                "instructors.api.views.CourseSerializer",
                return_value=serializer,
            ),
            patch(
                "instructors.api.views.CourseService",
            ) as service_class_mock,
        ):
            service_class_mock.return_value.create.return_value = created_course

            # Act
            response = api_client.post(
                create_course_url,
                data={},
                format="json",
            )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data == serializer.data

    def test_draft_creation_does_not_change_course_status(
        self,
        api_client,
        instructor_user,
        serializer,
        created_course,
        normalized_course_data,
        create_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)

        with (
            patch(
                "instructors.api.views.normalize_course_data",
                return_value=(normalized_course_data, False),
            ),
            patch(
                "instructors.api.views.CourseSerializer",
                return_value=serializer,
            ),
            patch(
                "instructors.api.views.CourseService",
            ) as service_class_mock,
        ):
            service_class_mock.return_value.create.return_value = created_course

            # Act
            response = api_client.post(
                create_course_url,
                data={},
                format="json",
            )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        created_course.save.assert_not_called()

    def test_submitted_course_is_marked_as_submitted(
        self,
        api_client,
        instructor_user,
        serializer,
        created_course,
        normalized_course_data,
        submitted_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)

        with (
            patch(
                "instructors.api.views.normalize_course_data",
                return_value=(normalized_course_data, False),
            ),
            patch(
                "instructors.api.views.CourseSerializer",
                return_value=serializer,
            ),
            patch(
                "instructors.api.views.CourseService",
            ) as service_class_mock,
        ):
            service_class_mock.return_value.create.return_value = created_course

            # Act
            response = api_client.post(
                submitted_course_url,
                data={},
                format="json",
            )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert created_course.status == Course.Status.SUBMITTED

    def test_submitted_course_is_marked_as_pending_review(
        self,
        api_client,
        instructor_user,
        serializer,
        created_course,
        normalized_course_data,
        submitted_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)

        with (
            patch(
                "instructors.api.views.normalize_course_data",
                return_value=(normalized_course_data, False),
            ),
            patch(
                "instructors.api.views.CourseSerializer",
                return_value=serializer,
            ),
            patch(
                "instructors.api.views.CourseService",
            ) as service_class_mock,
        ):
            service_class_mock.return_value.create.return_value = created_course

            # Act
            response = api_client.post(
                submitted_course_url,
                data={},
                format="json",
            )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert created_course.review_status == Course.ReviewStatus.PENDING

    def test_submitted_course_is_saved_after_status_change(
        self,
        api_client,
        instructor_user,
        serializer,
        created_course,
        normalized_course_data,
        submitted_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)

        with (
            patch(
                "instructors.api.views.normalize_course_data",
                return_value=(normalized_course_data, False),
            ),
            patch(
                "instructors.api.views.CourseSerializer",
                return_value=serializer,
            ),
            patch(
                "instructors.api.views.CourseService",
            ) as service_class_mock,
        ):
            service_class_mock.return_value.create.return_value = created_course

            # Act
            response = api_client.post(
                submitted_course_url,
                data={},
                format="json",
            )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        created_course.save.assert_called_once_with()

    def test_course_service_failure_is_not_silently_swallowed(
        self,
        api_client,
        instructor_user,
        serializer,
        normalized_course_data,
        create_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)

        error = RuntimeError("course creation failed")

        with (
            patch(
                "instructors.api.views.normalize_course_data",
                return_value=(normalized_course_data, False),
            ),
            patch(
                "instructors.api.views.CourseSerializer",
                return_value=serializer,
            ),
            patch(
                "instructors.api.views.CourseService",
            ) as service_class_mock,
        ):
            service_class_mock.return_value.create.side_effect = error

            # Act / Assert
            with pytest.raises(
                RuntimeError,
                match="course creation failed",
            ):
                api_client.post(
                    create_course_url,
                    data={},
                    format="json",
                )

    def test_serializer_validation_error_returns_bad_request(
        self,
        api_client,
        instructor_user,
        normalized_course_data,
        create_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)

        serializer = Mock()
        serializer.is_valid.side_effect = ValidationError(
            {"title": ["This field is required."]}
        )

        with (
            patch(
                "instructors.api.views.normalize_course_data",
                return_value=(normalized_course_data, False),
            ),
            patch(
                "instructors.api.views.CourseSerializer",
                return_value=serializer,
            ),
            patch(
                "instructors.api.views.CourseService",
            ) as service_class_mock,
        ):
            # Act
            response = api_client.post(
                create_course_url,
                data={},
                format="json",
            )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        serializer.is_valid.assert_called_once_with(
            raise_exception=True,
        )

        service_class_mock.assert_not_called()

    def test_serializer_validation_error_prevents_course_creation(
        self,
        api_client,
        instructor_user,
        normalized_course_data,
        create_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)

        serializer = Mock()
        serializer.is_valid.side_effect = ValidationError(
            {"title": ["This field is required."]}
        )

        with (
            patch(
                "instructors.api.views.normalize_course_data",
                return_value=(normalized_course_data, False),
            ),
            patch(
                "instructors.api.views.CourseSerializer",
                return_value=serializer,
            ),
            patch(
                "instructors.api.views.CourseService",
            ) as service_class_mock,
        ):
            # Act
            response = api_client.post(
                create_course_url,
                data={},
                format="json",
            )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        service_class_mock.return_value.create.assert_not_called()

    def test_submitted_status_transition_happens_after_course_creation(
        self,
        api_client,
        instructor_user,
        serializer,
        created_course,
        normalized_course_data,
        submitted_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)

        with (
            patch(
                "instructors.api.views.normalize_course_data",
                return_value=(normalized_course_data, False),
            ),
            patch(
                "instructors.api.views.CourseSerializer",
                return_value=serializer,
            ),
            patch(
                "instructors.api.views.CourseService",
            ) as service_class_mock,
        ):
            service_class_mock.return_value.create.return_value = created_course

            # Act
            response = api_client.post(
                submitted_course_url,
                data={},
                format="json",
            )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        service_class_mock.return_value.create.assert_called_once_with(
            serializer.validated_data,
        )

        assert created_course.status == Course.Status.SUBMITTED
        assert created_course.review_status == Course.ReviewStatus.PENDING
        created_course.save.assert_called_once_with()
