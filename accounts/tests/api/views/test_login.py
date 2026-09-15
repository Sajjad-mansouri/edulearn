import pytest
from django.urls import reverse
from rest_framework import status

from accounts.models import Role

pytestmark = pytest.mark.django_db


class TestLoginApiView:
    url = reverse("accounts-api:login")

    @pytest.fixture
    def valid_payload(self):
        return {
            "username": "test_user",
            "password": "test-password",
        }

    @pytest.fixture(autouse=True)
    def disable_login_throttling(self, mocker):
        mocker.patch(
            "accounts.api.views.LoginApiView.get_throttles",
            return_value=[],
        )

    def test_login_returns_200_for_valid_credentials(
        self,
        api_client,
        test_user,
        valid_payload,
        mocker,
    ):
        mocker.patch(
            "accounts.api.views.perform_login",
            return_value={
                "access": "access-token",
                "refresh": "refresh-token",
            },
        )

        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

    def test_login_calls_perform_login_with_validated_data(
        self,
        api_client,
        test_user,
        valid_payload,
        mocker,
    ):
        perform_login = mocker.patch(
            "accounts.api.views.perform_login",
            return_value={
                "access": "access-token",
                "refresh": "refresh-token",
            },
        )

        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        perform_login.assert_called_once()

        validated_data, request = perform_login.call_args.args

        assert validated_data == valid_payload
        assert request is not None

    def test_login_passes_request_to_perform_login(
        self,
        api_client,
        test_user,
        valid_payload,
        mocker,
    ):
        perform_login = mocker.patch(
            "accounts.api.views.perform_login",
            return_value={
                "access": "access-token",
                "refresh": "refresh-token",
            },
        )

        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        _, request = perform_login.call_args.args

        assert request is not None
        assert request.method == "POST"
        assert request.user == test_user

    def test_login_response_contains_access_token(
        self,
        api_client,
        test_user,
        valid_payload,
        mocker,
    ):
        mocker.patch(
            "accounts.api.views.perform_login",
            return_value={
                "access": "access-token",
                "refresh": "refresh-token",
            },
        )

        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["access"] == "access-token"

    def test_login_response_contains_refresh_token(
        self,
        api_client,
        test_user,
        valid_payload,
        mocker,
    ):
        mocker.patch(
            "accounts.api.views.perform_login",
            return_value={
                "access": "access-token",
                "refresh": "refresh-token",
            },
        )

        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["refresh"] == "refresh-token"

    def test_login_returns_student_profile_url_for_student(
        self,
        api_client,
        test_user,
        valid_payload,
        mocker,
    ):
        student_role = Role.objects.create(
            name=Role.Roles.STUDENT,
        )
        student_role.users.add(test_user)

        mocker.patch(
            "accounts.api.views.perform_login",
            return_value={
                "access": "access-token",
                "refresh": "refresh-token",
            },
        )

        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["redirect_url"] == reverse("profiles:student_profile")

    def test_login_returns_instructor_profile_url_for_instructor(
        self,
        api_client,
        test_user,
        valid_payload,
        mocker,
    ):
        instructor_role = Role.objects.create(
            name=Role.Roles.INSTRUCTOR,
        )
        instructor_role.users.add(test_user)

        mocker.patch(
            "accounts.api.views.perform_login",
            return_value={
                "access": "access-token",
                "refresh": "refresh-token",
            },
        )

        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["redirect_url"] == reverse("profiles:instructor_profile")

    def test_login_prefers_instructor_profile_when_user_has_both_roles(
        self,
        api_client,
        test_user,
        valid_payload,
        mocker,
    ):
        student_role = Role.objects.create(
            name=Role.Roles.STUDENT,
        )
        instructor_role = Role.objects.create(
            name=Role.Roles.INSTRUCTOR,
        )

        student_role.users.add(test_user)
        instructor_role.users.add(test_user)

        mocker.patch(
            "accounts.api.views.perform_login",
            return_value={
                "access": "access-token",
                "refresh": "refresh-token",
            },
        )

        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["redirect_url"] == reverse("profiles:instructor_profile")

    def test_login_rejects_missing_username(
        self,
        api_client,
        test_user,
        mocker,
    ):
        perform_login = mocker.patch(
            "accounts.api.views.perform_login",
        )

        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            self.url,
            {
                "password": "test-password",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        perform_login.assert_not_called()

    def test_login_rejects_missing_password(
        self,
        api_client,
        test_user,
        mocker,
    ):
        perform_login = mocker.patch(
            "accounts.api.views.perform_login",
        )

        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            self.url,
            {
                "username": "test_user",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        perform_login.assert_not_called()

    def test_login_rejects_empty_username(
        self,
        api_client,
        test_user,
        mocker,
    ):
        perform_login = mocker.patch(
            "accounts.api.views.perform_login",
        )

        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            self.url,
            {
                "username": "",
                "password": "test-password",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        perform_login.assert_not_called()

    def test_login_rejects_empty_password(
        self,
        api_client,
        test_user,
        mocker,
    ):
        perform_login = mocker.patch(
            "accounts.api.views.perform_login",
        )

        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            self.url,
            {
                "username": "test_user",
                "password": "",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        perform_login.assert_not_called()

    def test_login_rejects_empty_payload(
        self,
        api_client,
        test_user,
        mocker,
    ):
        perform_login = mocker.patch(
            "accounts.api.views.perform_login",
        )

        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            self.url,
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        perform_login.assert_not_called()

    def test_login_rejects_get_request(
        self,
        api_client,
    ):
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_login_rejects_put_request(
        self,
        api_client,
    ):
        response = api_client.put(
            self.url,
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_login_rejects_patch_request(
        self,
        api_client,
    ):
        response = api_client.patch(
            self.url,
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_login_rejects_delete_request(
        self,
        api_client,
    ):
        response = api_client.delete(self.url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_login_response_contains_expected_keys(
        self,
        api_client,
        test_user,
        valid_payload,
        mocker,
    ):
        mocker.patch(
            "accounts.api.views.perform_login",
            return_value={
                "access": "access-token",
                "refresh": "refresh-token",
            },
        )

        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert set(response.data.keys()) == {
            "redirect_url",
            "access",
            "refresh",
        }

    def test_login_preserves_tokens_returned_by_service(
        self,
        api_client,
        test_user,
        valid_payload,
        mocker,
    ):
        mocker.patch(
            "accounts.api.views.perform_login",
            return_value={
                "access": "custom-access-token",
                "refresh": "custom-refresh-token",
            },
        )

        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            self.url,
            valid_payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["access"] == "custom-access-token"
        assert response.data["refresh"] == "custom-refresh-token"
