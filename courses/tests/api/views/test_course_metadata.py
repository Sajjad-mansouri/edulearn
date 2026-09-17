import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from courses.models.course import Course


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def course_metadata_url():
    return reverse("courses_api:metadata")


class TestCourseMetadataApiView:
    def test_authenticated_user_can_get_course_metadata(
        self,
        api_client,
        test_user,
        course_metadata_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        # Act
        response = api_client.get(course_metadata_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

    def test_response_contains_levels_and_languages(
        self,
        api_client,
        test_user,
        course_metadata_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        # Act
        response = api_client.get(course_metadata_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert set(response.data.keys()) == {
            "levels",
            "languages",
        }

    def test_levels_match_course_level_choices(
        self,
        api_client,
        test_user,
        course_metadata_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        expected_levels = [
            {
                "label": level.label,
                "value": level.value,
            }
            for level in Course.Level
        ]

        # Act
        response = api_client.get(course_metadata_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["levels"] == expected_levels

    def test_languages_match_course_language_choices(
        self,
        api_client,
        test_user,
        course_metadata_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        expected_languages = [
            {
                "label": language.label,
                "value": language.value,
            }
            for language in Course.LANGUAGE
        ]

        # Act
        response = api_client.get(course_metadata_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["languages"] == expected_languages

    def test_level_metadata_contains_label_and_value(
        self,
        api_client,
        test_user,
        course_metadata_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        # Act
        response = api_client.get(course_metadata_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        for level in response.data["levels"]:
            assert set(level.keys()) == {
                "label",
                "value",
            }

    def test_language_metadata_contains_label_and_value(
        self,
        api_client,
        test_user,
        course_metadata_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        # Act
        response = api_client.get(course_metadata_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        for language in response.data["languages"]:
            assert set(language.keys()) == {
                "label",
                "value",
            }

    def test_all_course_levels_are_included(
        self,
        api_client,
        test_user,
        course_metadata_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        expected_values = {level.value for level in Course.Level}

        # Act
        response = api_client.get(course_metadata_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        actual_values = {level["value"] for level in response.data["levels"]}

        assert actual_values == expected_values

    def test_all_course_languages_are_included(
        self,
        api_client,
        test_user,
        course_metadata_url,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        expected_values = {language.value for language in Course.LANGUAGE}

        # Act
        response = api_client.get(course_metadata_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        actual_values = {language["value"] for language in response.data["languages"]}

        assert actual_values == expected_values

    def test_unauthenticated_user_cannot_get_metadata(
        self,
        api_client,
        course_metadata_url,
    ):
        # Arrange
        # No authentication.

        # Act
        response = api_client.get(course_metadata_url)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        "http_method",
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
        test_user,
        course_metadata_url,
        http_method,
    ):
        # Arrange
        api_client.force_authenticate(user=test_user)

        method = getattr(api_client, http_method)

        # Act
        response = method(course_metadata_url)

        # Assert
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
