from unittest.mock import patch

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.test import APIRequestFactory

from courses.api.views import CourseFilterMetadataApiView


class TestCourseFilterMetadataApiView:
    def test_get_returns_course_filter_metadata(self):
        metadata = {
            "categories": [],
            "languages": [],
            "levels": [],
            "price_types": [],
        }

        factory = APIRequestFactory()
        request = factory.get("/courses/filter-metadata/")

        with patch(
            "courses.api.views.get_course_filter_metadata",
            return_value=metadata,
        ) as mock_get_metadata:
            response = CourseFilterMetadataApiView.as_view()(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == metadata
        mock_get_metadata.assert_called_once_with()

    def test_get_allows_anonymous_users(self):
        factory = APIRequestFactory()
        request = factory.get("/courses/filter-metadata/")

        with patch(
            "courses.api.views.get_course_filter_metadata",
            return_value={},
        ):
            response = CourseFilterMetadataApiView.as_view()(request)

        assert response.status_code == status.HTTP_200_OK

    def test_get_returns_empty_metadata_when_service_returns_empty_data(self):
        factory = APIRequestFactory()
        request = factory.get("/courses/filter-metadata/")

        with patch(
            "courses.api.views.get_course_filter_metadata",
            return_value={},
        ) as mock_get_metadata:
            response = CourseFilterMetadataApiView.as_view()(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {}
        mock_get_metadata.assert_called_once_with()

    def test_permission_classes_allow_any(self):
        assert CourseFilterMetadataApiView.permission_classes == [AllowAny]
