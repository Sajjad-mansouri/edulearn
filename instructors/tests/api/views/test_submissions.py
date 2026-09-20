import io
import zipfile
from unittest.mock import MagicMock, patch

from django.urls import resolve, reverse
from rest_framework import status
from rest_framework.test import APIClient

from instructors.api.views import SubmissionDownloadView


class TestSubmissionDownloadView:
    def test_unauthenticated_user_cannot_download_submission(
        self,
    ):
        # Arrange
        client = APIClient()
        url = reverse(
            "instructor_api:submission_download",
            kwargs={"id": 1},
        )

        # Act
        response = client.get(url)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_student_cannot_download_submission(
        self,
        student_user,
    ):
        # Arrange
        client = APIClient()
        client.force_authenticate(user=student_user)

        url = reverse(
            "instructor_api:submission_download",
            kwargs={"id": 1},
        )

        # Act
        response = client.get(url)

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_instructor_can_access_submission_download_endpoint(
        self,
        instructor_user,
    ):
        # Arrange
        client = APIClient()
        client.force_authenticate(user=instructor_user)

        url = reverse(
            "instructor_api:submission_download",
            kwargs={"id": 1},
        )

        submission = MagicMock()
        files = MagicMock()
        files.exists.return_value = False
        submission.files.all.return_value = files

        with patch(
            "instructors.api.views.get_object_or_404",
            return_value=submission,
        ):
            # Act
            response = client.get(url)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data == {"error": "No files found for this submission"}

    def test_nonexistent_submission_returns_404(
        self,
        instructor_user,
    ):
        # Arrange
        client = APIClient()
        client.force_authenticate(user=instructor_user)

        url = reverse(
            "instructor_api:submission_download",
            kwargs={"id": 999999999},
        )

        with patch(
            "instructors.api.views.get_object_or_404",
            side_effect=__import__(
                "django.http",
                fromlist=["Http404"],
            ).Http404,
        ):
            # Act
            response = client.get(url)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_submission_without_files_returns_404(
        self,
        instructor_user,
    ):
        # Arrange
        client = APIClient()
        client.force_authenticate(user=instructor_user)

        url = reverse(
            "instructor_api:submission_download",
            kwargs={"id": 10},
        )

        submission = MagicMock()
        files = MagicMock()
        files.exists.return_value = False
        submission.files.all.return_value = files

        with patch(
            "instructors.api.views.get_object_or_404",
            return_value=submission,
        ):
            # Act
            response = client.get(url)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data == {"error": "No files found for this submission"}

        files.exists.assert_called_once()

    def test_submission_without_files_does_not_attempt_file_download(
        self,
        instructor_user,
    ):
        # Arrange
        client = APIClient()
        client.force_authenticate(user=instructor_user)

        url = reverse(
            "instructor_api:submission_download",
            kwargs={"id": 10},
        )

        submission = MagicMock()
        files = MagicMock()
        files.exists.return_value = False
        submission.files.all.return_value = files

        with patch(
            "instructors.api.views.get_object_or_404",
            return_value=submission,
        ):
            # Act
            response = client.get(url)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        files.count.assert_not_called()
        files.first.assert_not_called()

    def test_single_file_returns_file_response(
        self,
        instructor_user,
    ):
        # Arrange
        client = APIClient()
        client.force_authenticate(user=instructor_user)

        url = reverse(
            "instructor_api:submission_download",
            kwargs={"id": 10},
        )

        file_content = b"assignment submission content"

        file_handle = io.BytesIO(file_content)

        submission_file = MagicMock()
        submission_file.file_name = "answer.pdf"
        submission_file.file.open.return_value = file_handle

        files = MagicMock()
        files.exists.return_value = True
        files.count.return_value = 1
        files.first.return_value = submission_file

        submission = MagicMock()
        submission.files.all.return_value = files

        with patch(
            "instructors.api.views.get_object_or_404",
            return_value=submission,
        ):
            # Act
            response = client.get(url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "application/octet-stream"
        assert response["Content-Disposition"] == 'attachment; filename="answer.pdf"'

        submission_file.file.open.assert_called_once_with("rb")

    def test_single_file_uses_file_name_for_content_disposition(
        self,
        instructor_user,
    ):
        # Arrange
        client = APIClient()
        client.force_authenticate(user=instructor_user)

        url = reverse(
            "instructor_api:submission_download",
            kwargs={"id": 20},
        )

        submission_file = MagicMock()
        submission_file.file_name = "project-final.zip"
        submission_file.file.open.return_value = io.BytesIO(b"content")

        files = MagicMock()
        files.exists.return_value = True
        files.count.return_value = 1
        files.first.return_value = submission_file

        submission = MagicMock()
        submission.files.all.return_value = files

        with patch(
            "instructors.api.views.get_object_or_404",
            return_value=submission,
        ):
            # Act
            response = client.get(url)

        # Assert
        assert (
            response["Content-Disposition"]
            == 'attachment; filename="project-final.zip"'
        )

    def test_single_file_does_not_create_zip(
        self,
        instructor_user,
    ):
        # Arrange
        client = APIClient()
        client.force_authenticate(user=instructor_user)

        url = reverse(
            "instructor_api:submission_download",
            kwargs={"id": 30},
        )

        submission_file = MagicMock()
        submission_file.file_name = "answer.txt"
        submission_file.file.open.return_value = io.BytesIO(b"answer")

        files = MagicMock()
        files.exists.return_value = True
        files.count.return_value = 1
        files.first.return_value = submission_file

        submission = MagicMock()
        submission.files.all.return_value = files

        with patch(
            "instructors.api.views.get_object_or_404",
            return_value=submission,
        ):
            # Act
            response = client.get(url)

        # Assert
        assert response["Content-Type"] == "application/octet-stream"
        assert not response["Content-Type"].startswith("application/zip")

    def test_multiple_files_return_zip_response(
        self,
        instructor_user,
    ):
        # Arrange
        client = APIClient()
        client.force_authenticate(user=instructor_user)

        submission_id = 40

        url = reverse(
            "instructor_api:submission_download",
            kwargs={"id": submission_id},
        )

        first_file = MagicMock()
        first_file.file_name = "answer.txt"
        first_file.file.read.return_value = b"first file content"

        second_file = MagicMock()
        second_file.file_name = "solution.py"
        second_file.file.read.return_value = b"print('hello')"

        files = MagicMock()
        files.exists.return_value = True
        files.count.return_value = 2
        files.__iter__.return_value = iter([first_file, second_file])

        submission = MagicMock()
        submission.files.all.return_value = files

        with patch(
            "instructors.api.views.get_object_or_404",
            return_value=submission,
        ):
            # Act
            response = client.get(url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "application/zip"
        assert (
            response["Content-Disposition"]
            == 'attachment; filename="submission_40_files.zip"'
        )

    def test_multiple_files_zip_contains_all_files(
        self,
        instructor_user,
    ):
        # Arrange
        client = APIClient()
        client.force_authenticate(user=instructor_user)

        submission_id = 41

        url = reverse(
            "instructor_api:submission_download",
            kwargs={"id": submission_id},
        )

        first_file = MagicMock()
        first_file.file_name = "answer.txt"
        first_file.file.read.return_value = b"answer content"

        second_file = MagicMock()
        second_file.file_name = "solution.py"
        second_file.file.read.return_value = b"print('solution')"

        third_file = MagicMock()
        third_file.file_name = "notes.md"
        third_file.file.read.return_value = b"# Notes"

        files = MagicMock()
        files.exists.return_value = True
        files.count.return_value = 3
        files.__iter__.return_value = iter(
            [
                first_file,
                second_file,
                third_file,
            ]
        )

        submission = MagicMock()
        submission.files.all.return_value = files

        with patch(
            "instructors.api.views.get_object_or_404",
            return_value=submission,
        ):
            # Act
            response = client.get(url)

        # Assert
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            assert archive.namelist() == [
                "answer.txt",
                "solution.py",
                "notes.md",
            ]

            assert archive.read("answer.txt") == b"answer content"
            assert archive.read("solution.py") == b"print('solution')"
            assert archive.read("notes.md") == b"# Notes"

    def test_multiple_files_read_each_file(
        self,
        instructor_user,
    ):
        # Arrange
        client = APIClient()
        client.force_authenticate(user=instructor_user)

        url = reverse(
            "instructor_api:submission_download",
            kwargs={"id": 50},
        )

        first_file = MagicMock()
        first_file.file_name = "first.txt"
        first_file.file.read.return_value = b"first"

        second_file = MagicMock()
        second_file.file_name = "second.txt"
        second_file.file.read.return_value = b"second"

        files = MagicMock()
        files.exists.return_value = True
        files.count.return_value = 2
        files.__iter__.return_value = iter([first_file, second_file])

        submission = MagicMock()
        submission.files.all.return_value = files

        with patch(
            "instructors.api.views.get_object_or_404",
            return_value=submission,
        ):
            # Act
            response = client.get(url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        first_file.file.read.assert_called_once_with()
        second_file.file.read.assert_called_once_with()

    def test_multiple_files_use_submission_id_in_zip_filename(
        self,
        instructor_user,
    ):
        # Arrange
        client = APIClient()
        client.force_authenticate(user=instructor_user)

        submission_id = 12345

        url = reverse(
            "instructor_api:submission_download",
            kwargs={"id": submission_id},
        )

        submission_file = MagicMock()
        submission_file.file_name = "answer.txt"
        submission_file.file.read.return_value = b"answer"

        second_file = MagicMock()
        second_file.file_name = "notes.txt"
        second_file.file.read.return_value = b"notes"

        files = MagicMock()
        files.exists.return_value = True
        files.count.return_value = 2
        files.__iter__.return_value = iter([submission_file, second_file])

        submission = MagicMock()
        submission.files.all.return_value = files

        with patch(
            "instructors.api.views.get_object_or_404",
            return_value=submission,
        ):
            # Act
            response = client.get(url)

        # Assert
        assert (
            response["Content-Disposition"]
            == 'attachment; filename="submission_12345_files.zip"'
        )

    def test_submission_download_url_resolves_to_correct_view(self):
        # Arrange
        url = reverse(
            "instructor_api:submission_download",
            kwargs={"id": 123},
        )

        # Act
        match = resolve(url)

        # Assert
        assert match.func.view_class is SubmissionDownloadView

    def test_submission_download_url_contains_submission_id(self):
        # Arrange
        url = reverse(
            "instructor_api:submission_download",
            kwargs={"id": 123},
        )

        # Act
        match = resolve(url)

        # Assert
        assert match.kwargs == {"id": 123}

    def test_submission_download_url_uses_expected_path(self):
        # Arrange
        url = reverse(
            "instructor_api:submission_download",
            kwargs={"id": 123},
        )

        # Act
        normalized_url = url.rstrip("/")

        # Assert
        assert normalized_url.endswith("/assignments/123/download")

    def test_post_method_is_not_supported(
        self,
        instructor_user,
    ):
        # Arrange
        client = APIClient()
        client.force_authenticate(user=instructor_user)

        url = reverse(
            "instructor_api:submission_download",
            kwargs={"id": 1},
        )

        # Act
        response = client.post(url, {})

        # Assert
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_put_method_is_not_supported(
        self,
        instructor_user,
    ):
        # Arrange
        client = APIClient()
        client.force_authenticate(user=instructor_user)

        url = reverse(
            "instructor_api:submission_download",
            kwargs={"id": 1},
        )

        # Act
        response = client.put(url, {})

        # Assert
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_patch_method_is_not_supported(
        self,
        instructor_user,
    ):
        # Arrange
        client = APIClient()
        client.force_authenticate(user=instructor_user)

        url = reverse(
            "instructor_api:submission_download",
            kwargs={"id": 1},
        )

        # Act
        response = client.patch(url, {})

        # Assert
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_delete_method_is_not_supported(
        self,
        instructor_user,
    ):
        # Arrange
        client = APIClient()
        client.force_authenticate(user=instructor_user)

        url = reverse(
            "instructor_api:submission_download",
            kwargs={"id": 1},
        )

        # Act
        response = client.delete(url)

        # Assert
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
