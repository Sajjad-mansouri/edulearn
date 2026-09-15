import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestRegisterInstructorApiView:
    url = reverse("accounts-api:register_instructor")

    @pytest.fixture
    def valid_payload(self):
        return {
            "educations": [],
            "experiences": [],
            "skills": [],
            "profile": {},
            "personal_info": {
                "username": "test_user",
                "email": "test_user@example.com",
                "first_name": "Test",
                "last_name": "User",
            },
            "instructor": {
                "professional_title": "Software Developer",
            },
        }

    # ------------------------------------------------------------------
    # HTTP method / authentication
    # ------------------------------------------------------------------

    def test_get_method_is_not_allowed(self, api_client):
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_put_method_is_not_allowed(
        self,
        api_client,
    ):
        response = api_client.put(
            self.url,
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_patch_method_is_not_allowed(
        self,
        api_client,
    ):
        response = api_client.patch(
            self.url,
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_delete_method_is_not_allowed(
        self,
        api_client,
    ):
        response = api_client.delete(self.url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_anonymous_user_can_submit_application(
        self,
        api_client,
        valid_payload,
        mocker,
    ):
        register_instructor = mocker.patch(
            "accounts.api.views.register_instructor",
            return_value=(
                mocker.Mock(id=10),
                mocker.Mock(application_status="pending"),
                True,
            ),
        )

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        register_instructor.assert_called_once()

    def test_authenticated_user_can_submit_application(
        self,
        api_client,
        test_user,
        valid_payload,
        mocker,
    ):
        register_instructor = mocker.patch(
            "accounts.api.views.register_instructor",
            return_value=(
                mocker.Mock(id=10),
                mocker.Mock(application_status="pending"),
                False,
            ),
        )

        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        register_instructor.assert_called_once()

    # ------------------------------------------------------------------
    # Successful registration
    # ------------------------------------------------------------------

    def test_new_application_returns_201(
        self,
        api_client,
        valid_payload,
        mocker,
    ):
        profile = mocker.Mock(id=123)
        instructor_profile = mocker.Mock(
            application_status="pending",
        )

        register_instructor = mocker.patch(
            "accounts.api.views.register_instructor",
            return_value=(
                profile,
                instructor_profile,
                True,
            ),
        )

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        assert response.data == {
            "detail": "Instructor application submitted successfully",
            "created": True,
            "application_status": "pending",
            "profile_id": 123,
        }

        register_instructor.assert_called_once()

    def test_existing_user_application_returns_200(
        self,
        api_client,
        test_user,
        valid_payload,
        mocker,
    ):
        profile = mocker.Mock(id=456)
        instructor_profile = mocker.Mock(
            application_status="pending",
        )

        register_instructor = mocker.patch(
            "accounts.api.views.register_instructor",
            return_value=(
                profile,
                instructor_profile,
                False,
            ),
        )

        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        assert response.data == {
            "detail": "Instructor application submitted successfully",
            "created": False,
            "application_status": "pending",
            "profile_id": 456,
        }

        register_instructor.assert_called_once()

    def test_response_contains_application_status(
        self,
        api_client,
        valid_payload,
        mocker,
    ):
        mocker.patch(
            "accounts.api.views.register_instructor",
            return_value=(
                mocker.Mock(id=100),
                mocker.Mock(application_status="pending"),
                True,
            ),
        )

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.data["application_status"] == "pending"

    def test_response_contains_profile_id(
        self,
        api_client,
        valid_payload,
        mocker,
    ):
        mocker.patch(
            "accounts.api.views.register_instructor",
            return_value=(
                mocker.Mock(id=987),
                mocker.Mock(application_status="pending"),
                True,
            ),
        )

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.data["profile_id"] == 987

    # ------------------------------------------------------------------
    # Service invocation
    # ------------------------------------------------------------------

    def test_service_receives_request(
        self,
        api_client,
        valid_payload,
        mocker,
    ):
        register_instructor = mocker.patch(
            "accounts.api.views.register_instructor",
            return_value=(
                mocker.Mock(id=1),
                mocker.Mock(application_status="pending"),
                True,
            ),
        )

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        request = register_instructor.call_args.kwargs["request"]

        assert request.method == "POST"
        assert request.path == self.url

    def test_service_receives_personal_info_for_anonymous_user(
        self,
        api_client,
        valid_payload,
        mocker,
    ):
        register_instructor = mocker.patch(
            "accounts.api.views.register_instructor",
            return_value=(
                mocker.Mock(id=1),
                mocker.Mock(application_status="pending"),
                True,
            ),
        )

        api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        kwargs = register_instructor.call_args.kwargs

        assert kwargs["user_data"] == {
            "username": "test_user",
            "email": "test_user@example.com",
            "first_name": "Test",
            "last_name": "User",
        }

    def test_service_receives_empty_user_data_for_authenticated_user(
        self,
        api_client,
        test_user,
        valid_payload,
        mocker,
    ):
        register_instructor = mocker.patch(
            "accounts.api.views.register_instructor",
            return_value=(
                mocker.Mock(id=1),
                mocker.Mock(application_status="pending"),
                False,
            ),
        )

        api_client.force_authenticate(user=test_user)

        api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        kwargs = register_instructor.call_args.kwargs

        assert kwargs["user_data"] == {}

    def test_service_receives_validated_profile_data(
        self,
        api_client,
        valid_payload,
        mocker,
    ):
        register_instructor = mocker.patch(
            "accounts.api.views.register_instructor",
            return_value=(
                mocker.Mock(id=1),
                mocker.Mock(application_status="pending"),
                True,
            ),
        )

        valid_payload["profile"] = {
            "website": "https://example.com",
            "country": "Azerbaijan",
            "linkedin": "https://linkedin.example/test",
            "github": "https://github.example/test",
        }

        api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        kwargs = register_instructor.call_args.kwargs

        assert kwargs["profile_data"] == {
            "website": "https://example.com",
            "country": "Azerbaijan",
            "linkedin": "https://linkedin.example/test",
            "github": "https://github.example/test",
        }

    def test_service_receives_validated_instructor_data(
        self,
        api_client,
        valid_payload,
        mocker,
    ):
        register_instructor = mocker.patch(
            "accounts.api.views.register_instructor",
            return_value=(
                mocker.Mock(id=1),
                mocker.Mock(application_status="pending"),
                True,
            ),
        )

        valid_payload["instructor"] = {
            "professional_title": "Software Developer",
            "organization": "Example Organization",
            "years_of_experience": 5,
        }

        api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        kwargs = register_instructor.call_args.kwargs

        assert kwargs["instructor_data"] == {
            "professional_title": "Software Developer",
            "organization": "Example Organization",
            "years_of_experience": 5,
        }

    # ------------------------------------------------------------------
    # Serializer validation
    # ------------------------------------------------------------------

    def test_invalid_personal_info_returns_400(
        self,
        api_client,
        valid_payload,
        mocker,
    ):
        register_instructor = mocker.patch(
            "accounts.api.views.register_instructor",
        )

        valid_payload["personal_info"] = {
            "email": "invalid-email",
        }

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "personal_info" in response.data

        register_instructor.assert_not_called()

    def test_invalid_education_returns_400(
        self,
        api_client,
        valid_payload,
        mocker,
    ):
        register_instructor = mocker.patch(
            "accounts.api.views.register_instructor",
        )

        valid_payload["educations"] = [
            {
                "invalid_field": "invalid",
            }
        ]

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "educations" in response.data

        register_instructor.assert_not_called()

    def test_invalid_experience_returns_400(
        self,
        api_client,
        valid_payload,
        mocker,
    ):
        register_instructor = mocker.patch(
            "accounts.api.views.register_instructor",
        )

        valid_payload["experiences"] = [
            {
                "invalid_field": "invalid",
            }
        ]

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "experiences" in response.data

        register_instructor.assert_not_called()

    def test_invalid_skill_returns_400(
        self,
        api_client,
        valid_payload,
        mocker,
    ):
        register_instructor = mocker.patch(
            "accounts.api.views.register_instructor",
        )

        valid_payload["skills"] = [
            {
                "invalid_field": "invalid",
            }
        ]

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "skills" in response.data

        register_instructor.assert_not_called()

    def test_invalid_profile_returns_400(
        self,
        api_client,
        valid_payload,
        mocker,
    ):
        register_instructor = mocker.patch(
            "accounts.api.views.register_instructor",
        )

        valid_payload["profile"] = {
            "website": "not-a-valid-url",
        }

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "profile" in response.data

        register_instructor.assert_not_called()

    def test_invalid_instructor_returns_400(
        self,
        api_client,
        valid_payload,
        mocker,
    ):
        register_instructor = mocker.patch(
            "accounts.api.views.register_instructor",
        )

        valid_payload["instructor"] = {}

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "instructor" in response.data

        register_instructor.assert_not_called()

    def test_multiple_serializer_errors_are_returned_together(
        self,
        api_client,
        valid_payload,
        mocker,
    ):
        register_instructor = mocker.patch(
            "accounts.api.views.register_instructor",
        )

        valid_payload["personal_info"] = {
            "email": "invalid-email",
        }
        valid_payload["profile"] = {
            "website": "invalid-url",
        }
        valid_payload["instructor"] = {}

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        assert "personal_info" in response.data
        assert "profile" in response.data
        assert "instructor" in response.data

        register_instructor.assert_not_called()

    def test_service_is_not_called_when_serializer_validation_fails(
        self,
        api_client,
        valid_payload,
        mocker,
    ):
        register_instructor = mocker.patch(
            "accounts.api.views.register_instructor",
        )

        valid_payload["instructor"] = {}

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        register_instructor.assert_not_called()

    # ------------------------------------------------------------------
    # Missing sections / defaults
    # ------------------------------------------------------------------

    def test_missing_collection_fields_default_to_empty_lists(
        self,
        api_client,
        mocker,
    ):
        register_instructor = mocker.patch(
            "accounts.api.views.register_instructor",
            return_value=(
                mocker.Mock(id=1),
                mocker.Mock(application_status="pending"),
                True,
            ),
        )

        payload = {
            "personal_info": {
                "username": "test_user",
                "email": "test_user@example.com",
            },
            "instructor": {
                "professional_title": "Software Developer",
            },
        }

        response = api_client.post(
            self.url,
            payload,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        kwargs = register_instructor.call_args.kwargs

        assert kwargs["educations_data"] == []
        assert kwargs["experiences_data"] == []
        assert kwargs["skills_data"] == []

    def test_missing_profile_defaults_to_empty_dictionary(
        self,
        api_client,
        mocker,
    ):
        register_instructor = mocker.patch(
            "accounts.api.views.register_instructor",
            return_value=(
                mocker.Mock(id=1),
                mocker.Mock(application_status="pending"),
                True,
            ),
        )

        payload = {
            "personal_info": {
                "username": "test_user",
                "email": "test_user@example.com",
            },
            "instructor": {
                "professional_title": "Software Developer",
            },
        }

        response = api_client.post(
            self.url,
            payload,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        kwargs = register_instructor.call_args.kwargs

        assert kwargs["profile_data"] == {}

    # ------------------------------------------------------------------
    # Service exceptions
    # ------------------------------------------------------------------

    def test_service_validation_error_returns_400(
        self,
        api_client,
        valid_payload,
        mocker,
    ):
        register_instructor = mocker.patch(
            "accounts.api.views.register_instructor",
        )

        register_instructor.side_effect = ValidationError(
            {
                "application": [
                    "Application cannot be submitted.",
                ],
            }
        )

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        assert response.data == {
            "detail": {
                "application": [
                    "Application cannot be submitted.",
                ],
            },
        }

    def test_service_validation_error_does_not_return_500(
        self,
        api_client,
        valid_payload,
        mocker,
    ):
        register_instructor = mocker.patch(
            "accounts.api.views.register_instructor",
        )

        register_instructor.side_effect = ValidationError(
            "Application cannot be submitted."
        )

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # ------------------------------------------------------------------
    # Unexpected exceptions
    # ------------------------------------------------------------------

    def test_unexpected_service_exception_is_not_converted_to_400(
        self,
        api_client,
        valid_payload,
        mocker,
    ):
        register_instructor = mocker.patch(
            "accounts.api.views.register_instructor",
        )

        register_instructor.side_effect = RuntimeError("Unexpected registration error.")

        with pytest.raises(RuntimeError, match="Unexpected registration error."):
            api_client.post(
                self.url,
                valid_payload,
                format="json",
            )

    # ------------------------------------------------------------------
    # Response contract
    # ------------------------------------------------------------------

    def test_response_contains_expected_keys(
        self,
        api_client,
        valid_payload,
        mocker,
    ):
        mocker.patch(
            "accounts.api.views.register_instructor",
            return_value=(
                mocker.Mock(id=100),
                mocker.Mock(application_status="pending"),
                True,
            ),
        )

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert set(response.data) == {
            "detail",
            "created",
            "application_status",
            "profile_id",
        }

    def test_created_value_is_boolean(
        self,
        api_client,
        valid_payload,
        mocker,
    ):
        mocker.patch(
            "accounts.api.views.register_instructor",
            return_value=(
                mocker.Mock(id=100),
                mocker.Mock(application_status="pending"),
                True,
            ),
        )

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.data["created"] is True

    def test_existing_application_created_value_is_false(
        self,
        api_client,
        test_user,
        valid_payload,
        mocker,
    ):
        mocker.patch(
            "accounts.api.views.register_instructor",
            return_value=(
                mocker.Mock(id=100),
                mocker.Mock(application_status="pending"),
                False,
            ),
        )

        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.data["created"] is False
