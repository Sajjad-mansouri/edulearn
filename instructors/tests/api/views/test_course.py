from unittest.mock import Mock, patch

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient, APIRequestFactory

from courses.models import Course
from instructors.api.views import CourseUpdateApiView

User = get_user_model()


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


@pytest.mark.django_db
class TestCourseUpdateApiView:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def update_course_url(self, instructor_course):
        return reverse(
            "instructor_api:update_course",
            kwargs={
                "pk": instructor_course.pk,
                "course_status": Course.Status.DRAFT,
            },
        )

    @pytest.fixture
    def submitted_update_course_url(self, instructor_course):
        return reverse(
            "instructor_api:update_course",
            kwargs={
                "pk": instructor_course.pk,
                "course_status": Course.Status.SUBMITTED,
            },
        )

    @pytest.fixture
    def normalized_course_data(self):
        return {
            "title": "Updated Django Course",
        }

    @pytest.fixture
    def deleted_ids_dict(self):
        return {
            "learning_outcomes": [10, 11],
            "prerequisites": [20],
            "target_audiences": [],
            "features": [30],
            "sections": [],
        }

    @pytest.fixture
    def serializer(self):
        serializer = Mock()

        serializer.validated_data = {
            "title": "Updated Django Course",
        }

        serializer.data = {
            "id": 1,
            "title": "Updated Django Course",
        }

        return serializer

    @pytest.fixture
    def updated_course(self, instructor_course):
        return instructor_course

    @pytest.fixture
    def another_instructor(self, db):
        return User.objects.create_user(
            username="another_instructor",
            email="another_instructor@example.com",
            password="test-password",
        )

    @pytest.fixture
    def another_instructor_course(self, another_instructor):
        return Course.objects.create(
            owner=another_instructor,
            title="Another Instructor Course",
            slug="another-instructor-course",
        )

    def test_unauthenticated_user_cannot_update_course(
        self,
        api_client,
        update_course_url,
    ):
        # Arrange
        payload = {
            "title": "Updated title",
        }

        # Act
        response = api_client.patch(
            update_course_url,
            data=payload,
            format="json",
        )

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_student_cannot_update_course(
        self,
        api_client,
        student_user,
        update_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=student_user)

        payload = {
            "title": "Updated title",
        }

        # Act
        response = api_client.patch(
            update_course_url,
            data=payload,
            format="json",
        )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_instructor_can_update_owned_course(
        self,
        api_client,
        instructor_user,
        instructor_course,
        serializer,
        updated_course,
        normalized_course_data,
        deleted_ids_dict,
        update_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)

        with (
            patch(
                "instructors.api.views.normalize_course_data",
                return_value=(
                    normalized_course_data,
                    deleted_ids_dict,
                ),
            ),
            patch(
                "instructors.api.views.CourseSerializer",
                return_value=serializer,
            ) as serializer_class_mock,
            patch(
                "instructors.api.views.CourseUpdateService",
            ) as service_class_mock,
        ):
            service_class_mock.return_value.update.return_value = updated_course

            # Act
            response = api_client.patch(
                update_course_url,
                data={"title": "Updated title"},
                format="json",
            )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        serializer_class_mock.assert_called_once_with(
            instance=instructor_course,
            data=normalized_course_data,
            partial=True,
        )

        serializer.is_valid.assert_called_once_with(
            raise_exception=True,
        )

        service_class_mock.assert_called_once_with(
            course=instructor_course,
            deleted_ids_dict=deleted_ids_dict,
        )

        service_class_mock.return_value.update.assert_called_once_with(
            serializer.validated_data,
        )

    def test_normalize_course_data_receives_request_data(
        self,
        api_client,
        instructor_user,
        serializer,
        updated_course,
        normalized_course_data,
        deleted_ids_dict,
        update_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)

        payload = {
            "title": "Updated title",
            "description": "Updated description",
        }

        with (
            patch(
                "instructors.api.views.normalize_course_data",
                return_value=(
                    normalized_course_data,
                    deleted_ids_dict,
                ),
            ) as normalize_mock,
            patch(
                "instructors.api.views.CourseSerializer",
                return_value=serializer,
            ),
            patch(
                "instructors.api.views.CourseUpdateService",
            ) as service_class_mock,
        ):
            service_class_mock.return_value.update.return_value = updated_course

            # Act
            response = api_client.patch(
                update_course_url,
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
        instructor_course,
        serializer,
        updated_course,
        normalized_course_data,
        deleted_ids_dict,
        update_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)

        with (
            patch(
                "instructors.api.views.normalize_course_data",
                return_value=(
                    normalized_course_data,
                    deleted_ids_dict,
                ),
            ),
            patch(
                "instructors.api.views.CourseSerializer",
                return_value=serializer,
            ) as serializer_class_mock,
            patch(
                "instructors.api.views.CourseUpdateService",
            ) as service_class_mock,
        ):
            service_class_mock.return_value.update.return_value = updated_course

            # Act
            response = api_client.patch(
                update_course_url,
                data={},
                format="json",
            )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        serializer_class_mock.assert_called_once_with(
            instance=instructor_course,
            data=normalized_course_data,
            partial=True,
        )

    def test_serializer_is_partial(
        self,
        api_client,
        instructor_user,
        instructor_course,
        serializer,
        updated_course,
        normalized_course_data,
        deleted_ids_dict,
        update_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)

        with (
            patch(
                "instructors.api.views.normalize_course_data",
                return_value=(
                    normalized_course_data,
                    deleted_ids_dict,
                ),
            ),
            patch(
                "instructors.api.views.CourseSerializer",
                return_value=serializer,
            ) as serializer_class_mock,
            patch(
                "instructors.api.views.CourseUpdateService",
            ) as service_class_mock,
        ):
            service_class_mock.return_value.update.return_value = updated_course

            # Act
            response = api_client.patch(
                update_course_url,
                data={},
                format="json",
            )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        _, serializer_kwargs = serializer_class_mock.call_args

        assert serializer_kwargs["partial"] is True

    def test_serializer_is_validated_with_raise_exception_true(
        self,
        api_client,
        instructor_user,
        serializer,
        updated_course,
        normalized_course_data,
        deleted_ids_dict,
        update_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)

        with (
            patch(
                "instructors.api.views.normalize_course_data",
                return_value=(
                    normalized_course_data,
                    deleted_ids_dict,
                ),
            ),
            patch(
                "instructors.api.views.CourseSerializer",
                return_value=serializer,
            ),
            patch(
                "instructors.api.views.CourseUpdateService",
            ) as service_class_mock,
        ):
            service_class_mock.return_value.update.return_value = updated_course

            # Act
            response = api_client.patch(
                update_course_url,
                data={},
                format="json",
            )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        serializer.is_valid.assert_called_once_with(
            raise_exception=True,
        )

    def test_deleted_ids_are_passed_to_update_service(
        self,
        api_client,
        instructor_user,
        serializer,
        updated_course,
        normalized_course_data,
        deleted_ids_dict,
        update_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)

        with (
            patch(
                "instructors.api.views.normalize_course_data",
                return_value=(
                    normalized_course_data,
                    deleted_ids_dict,
                ),
            ),
            patch(
                "instructors.api.views.CourseSerializer",
                return_value=serializer,
            ),
            patch(
                "instructors.api.views.CourseUpdateService",
            ) as service_class_mock,
        ):
            service_class_mock.return_value.update.return_value = updated_course

            # Act
            response = api_client.patch(
                update_course_url,
                data={},
                format="json",
            )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        service_class_mock.assert_called_once_with(
            course=updated_course,
            deleted_ids_dict=deleted_ids_dict,
        )

    def test_validated_data_is_passed_to_update_service(
        self,
        api_client,
        instructor_user,
        serializer,
        updated_course,
        normalized_course_data,
        deleted_ids_dict,
        update_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)

        with (
            patch(
                "instructors.api.views.normalize_course_data",
                return_value=(
                    normalized_course_data,
                    deleted_ids_dict,
                ),
            ),
            patch(
                "instructors.api.views.CourseSerializer",
                return_value=serializer,
            ),
            patch(
                "instructors.api.views.CourseUpdateService",
            ) as service_class_mock,
        ):
            service_class_mock.return_value.update.return_value = updated_course

            # Act
            response = api_client.patch(
                update_course_url,
                data={},
                format="json",
            )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        service_class_mock.return_value.update.assert_called_once_with(
            serializer.validated_data,
        )

    def test_course_update_service_receives_original_course(
        self,
        api_client,
        instructor_user,
        instructor_course,
        serializer,
        normalized_course_data,
        deleted_ids_dict,
        update_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)

        with (
            patch(
                "instructors.api.views.normalize_course_data",
                return_value=(
                    normalized_course_data,
                    deleted_ids_dict,
                ),
            ),
            patch(
                "instructors.api.views.CourseSerializer",
                return_value=serializer,
            ),
            patch(
                "instructors.api.views.CourseUpdateService",
            ) as service_class_mock,
        ):
            service_class_mock.return_value.update.return_value = instructor_course

            # Act
            response = api_client.patch(
                update_course_url,
                data={},
                format="json",
            )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        service_class_mock.assert_called_once_with(
            course=instructor_course,
            deleted_ids_dict=deleted_ids_dict,
        )

    def test_response_contains_serializer_data(
        self,
        api_client,
        instructor_user,
        serializer,
        updated_course,
        normalized_course_data,
        deleted_ids_dict,
        update_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)

        with (
            patch(
                "instructors.api.views.normalize_course_data",
                return_value=(
                    normalized_course_data,
                    deleted_ids_dict,
                ),
            ),
            patch(
                "instructors.api.views.CourseSerializer",
                return_value=serializer,
            ),
            patch(
                "instructors.api.views.CourseUpdateService",
            ) as service_class_mock,
        ):
            service_class_mock.return_value.update.return_value = updated_course

            # Act
            response = api_client.patch(
                update_course_url,
                data={},
                format="json",
            )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data == serializer.data

    def test_non_submitted_update_does_not_change_submission_status(
        self,
        api_client,
        instructor_user,
        instructor_course,
        serializer,
        normalized_course_data,
        deleted_ids_dict,
        update_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)

        original_status = instructor_course.status
        original_review_status = instructor_course.review_status

        with (
            patch(
                "instructors.api.views.normalize_course_data",
                return_value=(
                    normalized_course_data,
                    deleted_ids_dict,
                ),
            ),
            patch(
                "instructors.api.views.CourseSerializer",
                return_value=serializer,
            ),
            patch(
                "instructors.api.views.CourseUpdateService",
            ) as service_class_mock,
        ):
            service_class_mock.return_value.update.return_value = instructor_course

            # Act
            response = api_client.patch(
                update_course_url,
                data={},
                format="json",
            )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        instructor_course.refresh_from_db()

        assert instructor_course.status == original_status
        assert instructor_course.review_status == original_review_status

    def test_submitted_update_sets_submitted_status(
        self,
        api_client,
        instructor_user,
        instructor_course,
        serializer,
        normalized_course_data,
        deleted_ids_dict,
        submitted_update_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)

        with (
            patch(
                "instructors.api.views.normalize_course_data",
                return_value=(
                    normalized_course_data,
                    deleted_ids_dict,
                ),
            ),
            patch(
                "instructors.api.views.CourseSerializer",
                return_value=serializer,
            ),
            patch(
                "instructors.api.views.CourseUpdateService",
            ) as service_class_mock,
        ):
            service_class_mock.return_value.update.return_value = instructor_course

            # Act
            response = api_client.patch(
                submitted_update_course_url,
                data={},
                format="json",
            )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        instructor_course.refresh_from_db()

        assert instructor_course.status == Course.Status.SUBMITTED

    def test_submitted_update_sets_pending_review_status(
        self,
        api_client,
        instructor_user,
        instructor_course,
        serializer,
        normalized_course_data,
        deleted_ids_dict,
        submitted_update_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)

        with (
            patch(
                "instructors.api.views.normalize_course_data",
                return_value=(
                    normalized_course_data,
                    deleted_ids_dict,
                ),
            ),
            patch(
                "instructors.api.views.CourseSerializer",
                return_value=serializer,
            ),
            patch(
                "instructors.api.views.CourseUpdateService",
            ) as service_class_mock,
        ):
            service_class_mock.return_value.update.return_value = instructor_course

            # Act
            response = api_client.patch(
                submitted_update_course_url,
                data={},
                format="json",
            )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        instructor_course.refresh_from_db()

        assert instructor_course.review_status == Course.ReviewStatus.PENDING

    def test_submitted_update_persists_both_status_changes(
        self,
        api_client,
        instructor_user,
        instructor_course,
        serializer,
        normalized_course_data,
        deleted_ids_dict,
        submitted_update_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)

        with (
            patch(
                "instructors.api.views.normalize_course_data",
                return_value=(
                    normalized_course_data,
                    deleted_ids_dict,
                ),
            ),
            patch(
                "instructors.api.views.CourseSerializer",
                return_value=serializer,
            ),
            patch(
                "instructors.api.views.CourseUpdateService",
            ) as service_class_mock,
        ):
            service_class_mock.return_value.update.return_value = instructor_course

            # Act
            response = api_client.patch(
                submitted_update_course_url,
                data={},
                format="json",
            )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        instructor_course.refresh_from_db()

        assert instructor_course.status == Course.Status.SUBMITTED
        assert instructor_course.review_status == Course.ReviewStatus.PENDING

    def test_serializer_validation_error_returns_bad_request(
        self,
        api_client,
        instructor_user,
        normalized_course_data,
        deleted_ids_dict,
        update_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)

        serializer = Mock()
        serializer.is_valid.side_effect = ValidationError(
            {
                "title": ["This field is invalid."],
            }
        )

        with (
            patch(
                "instructors.api.views.normalize_course_data",
                return_value=(
                    normalized_course_data,
                    deleted_ids_dict,
                ),
            ),
            patch(
                "instructors.api.views.CourseSerializer",
                return_value=serializer,
            ),
            patch(
                "instructors.api.views.CourseUpdateService",
            ) as service_class_mock,
        ):
            # Act
            response = api_client.patch(
                update_course_url,
                data={"title": "Invalid"},
                format="json",
            )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        serializer.is_valid.assert_called_once_with(
            raise_exception=True,
        )

        service_class_mock.assert_not_called()

    def test_serializer_validation_error_prevents_update_service(
        self,
        api_client,
        instructor_user,
        normalized_course_data,
        deleted_ids_dict,
        update_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)

        serializer = Mock()
        serializer.is_valid.side_effect = ValidationError(
            {
                "title": ["This field is invalid."],
            }
        )

        with (
            patch(
                "instructors.api.views.normalize_course_data",
                return_value=(
                    normalized_course_data,
                    deleted_ids_dict,
                ),
            ),
            patch(
                "instructors.api.views.CourseSerializer",
                return_value=serializer,
            ),
            patch(
                "instructors.api.views.CourseUpdateService",
            ) as service_class_mock,
        ):
            # Act
            response = api_client.patch(
                update_course_url,
                data={"title": "Invalid"},
                format="json",
            )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        service_class_mock.return_value.update.assert_not_called()

    def test_course_service_exception_is_not_silently_swallowed(
        self,
        api_client,
        instructor_user,
        serializer,
        normalized_course_data,
        deleted_ids_dict,
        update_course_url,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)

        error = RuntimeError("course update failed")

        with (
            patch(
                "instructors.api.views.normalize_course_data",
                return_value=(
                    normalized_course_data,
                    deleted_ids_dict,
                ),
            ),
            patch(
                "instructors.api.views.CourseSerializer",
                return_value=serializer,
            ),
            patch(
                "instructors.api.views.CourseUpdateService",
            ) as service_class_mock,
        ):
            service_class_mock.return_value.update.side_effect = error

            # Act / Assert
            with pytest.raises(
                RuntimeError,
                match="course update failed",
            ):
                api_client.patch(
                    update_course_url,
                    data={"title": "Updated"},
                    format="json",
                )

    def test_course_not_owned_by_instructor_returns_not_found(
        self,
        api_client,
        instructor_user,
        another_instructor_course,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)

        url = reverse(
            "instructor_api:update_course",
            kwargs={
                "pk": another_instructor_course.pk,
                "course_status": Course.Status.DRAFT,
            },
        )

        with patch(
            "instructors.api.views.CourseUpdateService",
        ) as service_class_mock:
            # Act
            response = api_client.patch(
                url,
                data={"title": "Attempted takeover"},
                format="json",
            )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        service_class_mock.assert_not_called()

    def test_instructor_cannot_update_course_owned_by_another_user(
        self,
        api_client,
        instructor_user,
        another_instructor_course,
    ):
        # Arrange
        api_client.force_authenticate(user=instructor_user)

        original_title = another_instructor_course.title

        url = reverse(
            "instructor_api:update_course",
            kwargs={
                "pk": another_instructor_course.pk,
                "course_status": Course.Status.DRAFT,
            },
        )

        # Act
        response = api_client.patch(
            url,
            data={"title": "Unauthorized modification"},
            format="json",
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

        another_instructor_course.refresh_from_db()

        assert another_instructor_course.title == original_title

    def test_get_queryset_returns_only_courses_owned_by_request_user(
        self,
        instructor_user,
        instructor_course,
        another_instructor_course,
    ):
        # Arrange
        view = self._build_view(instructor_user)

        # Act
        queryset = view.get_queryset()

        # Assert
        assert instructor_course in queryset
        assert another_instructor_course not in queryset

    @staticmethod
    def _build_view(user):
        factory = APIRequestFactory()
        request = factory.patch("/courses/update/")

        request.user = user

        view = CourseUpdateApiView()
        view.request = request

        return view
