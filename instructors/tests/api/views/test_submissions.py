import io
import zipfile
from unittest.mock import MagicMock, patch

from django.urls import resolve, reverse
from rest_framework import status
from rest_framework.test import APIClient

from instructors.api.views import BulkDownloadView, SubmissionDownloadView


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


class TestBulkDownloadView:
    def test_unauthenticated_user_cannot_download_submissions(self):
        # Arrange
        client = APIClient()
        url = reverse("instructor_api:bulk-download")

        # Act
        response = client.get(url)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_student_cannot_download_submissions(
        self,
        student_user,
    ):
        # Arrange
        client = APIClient()
        client.force_authenticate(user=student_user)

        url = reverse("instructor_api:bulk-download")

        # Act
        response = client.get(url, {"ids": "1,2"})

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_instructor_can_access_bulk_download_endpoint(
        self,
        instructor_user,
    ):
        # Arrange
        client = APIClient()
        client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:bulk-download")

        # Act
        response = client.get(url)

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            "error": "No submission IDs provided",
        }

    def test_missing_ids_returns_bad_request(
        self,
        instructor_user,
    ):
        # Arrange
        client = APIClient()
        client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:bulk-download")

        # Act
        response = client.get(url)

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            "error": "No submission IDs provided",
        }

    def test_empty_ids_parameter_returns_bad_request(
        self,
        instructor_user,
    ):
        # Arrange
        client = APIClient()
        client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:bulk-download")

        # Act
        response = client.get(url, {"ids": ""})

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            "error": "No submission IDs provided",
        }

    def test_whitespace_only_ids_returns_bad_request(
        self,
        instructor_user,
    ):
        # Arrange
        client = APIClient()
        client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:bulk-download")

        # Act
        response = client.get(url, {"ids": "   "})

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data == {
            "error": "No submissions found",
        }

    def test_nonexistent_submission_ids_return_not_found(
        self,
        instructor_user,
    ):
        # Arrange
        client = APIClient()
        client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:bulk-download")

        # Act
        response = client.get(
            url,
            {"ids": "999999999,999999998"},
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data == {
            "error": "No submissions found",
        }

    def test_duplicate_ids_are_accepted(
        self,
        instructor_user,
    ):
        # Arrange
        client = APIClient()
        client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:bulk-download")

        submission = MagicMock()
        submission.id = 10
        submission.enrollment.user.username = "student"
        submission.files.all.return_value = []

        mock_queryset = MagicMock()
        mock_queryset.exists.return_value = True
        mock_queryset.__iter__.return_value = iter([submission])

        with patch(
            "instructors.api.views.AssignmentSubmission.objects.filter",
            return_value=mock_queryset,
        ) as filter_mock:
            # Act
            response = client.get(
                url,
                {"ids": "10,10,10"},
            )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        filter_mock.assert_called_once()

        filter_kwargs = filter_mock.call_args.kwargs
        assert filter_kwargs["id__in"] == [10, 10, 10]

    def test_ids_are_parsed_as_integers(
        self,
        instructor_user,
    ):
        # Arrange
        client = APIClient()
        client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:bulk-download")

        mock_queryset = MagicMock()
        mock_queryset.exists.return_value = False

        with patch(
            "instructors.api.views.AssignmentSubmission.objects.filter",
            return_value=mock_queryset,
        ) as filter_mock:
            # Act
            response = client.get(
                url,
                {"ids": "10, 20, 30"},
            )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        filter_kwargs = filter_mock.call_args.kwargs
        assert filter_kwargs["id__in"] == [10, 20, 30]

    def test_blank_items_between_ids_are_ignored(
        self,
        instructor_user,
    ):
        # Arrange
        client = APIClient()
        client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:bulk-download")

        mock_queryset = MagicMock()
        mock_queryset.exists.return_value = False

        with patch(
            "instructors.api.views.AssignmentSubmission.objects.filter",
            return_value=mock_queryset,
        ) as filter_mock:
            # Act
            response = client.get(
                url,
                {"ids": "10,,20, ,30"},
            )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        filter_kwargs = filter_mock.call_args.kwargs
        assert filter_kwargs["id__in"] == [10, 20, 30]

    def test_queryset_prefetches_files(
        self,
        instructor_user,
    ):
        # Arrange
        client = APIClient()
        client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:bulk-download")

        mock_queryset = MagicMock()
        mock_queryset.exists.return_value = False

        with patch(
            "instructors.api.views.AssignmentSubmission.objects.filter",
            return_value=mock_queryset,
        ):
            # Act
            client.get(url, {"ids": "10"})

        # Assert
        mock_queryset.prefetch_related.assert_called_once_with("files")

    def test_single_submission_with_single_file_returns_zip(
        self,
        instructor_user,
    ):
        # Arrange
        client = APIClient()
        client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:bulk-download")

        submission = MagicMock()
        submission.id = 10
        submission.enrollment.user.username = "student"
        submission.files.all.return_value = [
            self._submission_file(
                "answer.txt",
                b"answer content",
            ),
        ]

        queryset = self._queryset([submission])

        with patch(
            "instructors.api.views.AssignmentSubmission.objects.filter",
            return_value=queryset,
        ):
            # Act
            response = client.get(url, {"ids": "10"})

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "application/zip"
        assert (
            response["Content-Disposition"]
            == 'attachment; filename="bulk_submissions.zip"'
        )

    def test_single_submission_zip_contains_file(
        self,
        instructor_user,
    ):
        # Arrange
        client = APIClient()
        client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:bulk-download")

        submission = MagicMock()
        submission.id = 10
        submission.enrollment.user.username = "student"
        submission.files.all.return_value = [
            self._submission_file(
                "answer.txt",
                b"answer content",
            ),
        ]

        queryset = self._queryset([submission])

        with patch(
            "instructors.api.views.AssignmentSubmission.objects.filter",
            return_value=queryset,
        ):
            # Act
            response = client.get(url, {"ids": "10"})

        # Assert
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            assert archive.namelist() == [
                "student_10/answer.txt",
            ]
            assert archive.read("student_10/answer.txt") == (b"answer content")

    def test_submission_folder_replaces_spaces_in_username(
        self,
        instructor_user,
    ):
        # Arrange
        client = APIClient()
        client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:bulk-download")

        submission = MagicMock()
        submission.id = 25
        submission.enrollment.user.username = "student user"
        submission.files.all.return_value = [
            self._submission_file(
                "answer.txt",
                b"answer",
            ),
        ]

        queryset = self._queryset([submission])

        with patch(
            "instructors.api.views.AssignmentSubmission.objects.filter",
            return_value=queryset,
        ):
            # Act
            response = client.get(url, {"ids": "25"})

        # Assert
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            assert archive.namelist() == [
                "student_user_25/answer.txt",
            ]

    def test_multiple_submissions_are_added_to_separate_folders(
        self,
        instructor_user,
    ):
        # Arrange
        client = APIClient()
        client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:bulk-download")

        first_submission = MagicMock()
        first_submission.id = 10
        first_submission.enrollment.user.username = "student_one"
        first_submission.files.all.return_value = [
            self._submission_file(
                "answer.txt",
                b"first answer",
            ),
        ]

        second_submission = MagicMock()
        second_submission.id = 20
        second_submission.enrollment.user.username = "student_two"
        second_submission.files.all.return_value = [
            self._submission_file(
                "solution.py",
                b"print('second')",
            ),
        ]

        queryset = self._queryset(
            [
                first_submission,
                second_submission,
            ]
        )

        with patch(
            "instructors.api.views.AssignmentSubmission.objects.filter",
            return_value=queryset,
        ):
            # Act
            response = client.get(
                url,
                {"ids": "10,20"},
            )

        # Assert
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            assert archive.namelist() == [
                "student_one_10/answer.txt",
                "student_two_20/solution.py",
            ]

            assert archive.read("student_one_10/answer.txt") == b"first answer"

            assert archive.read("student_two_20/solution.py") == b"print('second')"

    def test_multiple_files_for_same_submission_are_in_same_folder(
        self,
        instructor_user,
    ):
        # Arrange
        client = APIClient()
        client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:bulk-download")

        submission = MagicMock()
        submission.id = 50
        submission.enrollment.user.username = "student"
        submission.files.all.return_value = [
            self._submission_file(
                "answer.txt",
                b"answer",
            ),
            self._submission_file(
                "code.py",
                b"print('hello')",
            ),
            self._submission_file(
                "notes.md",
                b"# notes",
            ),
        ]

        queryset = self._queryset([submission])

        with patch(
            "instructors.api.views.AssignmentSubmission.objects.filter",
            return_value=queryset,
        ):
            # Act
            response = client.get(url, {"ids": "50"})

        # Assert
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            assert archive.namelist() == [
                "student_50/answer.txt",
                "student_50/code.py",
                "student_50/notes.md",
            ]

            assert archive.read("student_50/answer.txt") == b"answer"

            assert archive.read("student_50/code.py") == b"print('hello')"

            assert archive.read("student_50/notes.md") == b"# notes"

    def test_empty_submission_file_list_still_returns_empty_zip(
        self,
        instructor_user,
    ):
        # Arrange
        client = APIClient()
        client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:bulk-download")

        submission = MagicMock()
        submission.id = 60
        submission.enrollment.user.username = "student"
        submission.files.all.return_value = []

        queryset = self._queryset([submission])

        with patch(
            "instructors.api.views.AssignmentSubmission.objects.filter",
            return_value=queryset,
        ):
            # Act
            response = client.get(url, {"ids": "60"})

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "application/zip"

        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            assert archive.namelist() == []

    def test_file_read_is_called_for_each_submission_file(
        self,
        instructor_user,
    ):
        # Arrange
        client = APIClient()
        client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:bulk-download")

        first_file = self._submission_file(
            "first.txt",
            b"first",
        )
        second_file = self._submission_file(
            "second.txt",
            b"second",
        )

        submission = MagicMock()
        submission.id = 70
        submission.enrollment.user.username = "student"
        submission.files.all.return_value = [
            first_file,
            second_file,
        ]

        queryset = self._queryset([submission])

        with patch(
            "instructors.api.views.AssignmentSubmission.objects.filter",
            return_value=queryset,
        ):
            # Act
            response = client.get(url, {"ids": "70"})

        # Assert
        assert response.status_code == status.HTTP_200_OK
        first_file.file.read.assert_called_once_with()
        second_file.file.read.assert_called_once_with()

    def test_zip_preserves_file_content(
        self,
        instructor_user,
    ):
        # Arrange
        client = APIClient()
        client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:bulk-download")

        content = b"\x00\x01\x02binary\xffcontent"

        submission = MagicMock()
        submission.id = 80
        submission.enrollment.user.username = "student"
        submission.files.all.return_value = [
            self._submission_file(
                "binary.dat",
                content,
            ),
        ]

        queryset = self._queryset([submission])

        with patch(
            "instructors.api.views.AssignmentSubmission.objects.filter",
            return_value=queryset,
        ):
            # Act
            response = client.get(url, {"ids": "80"})

        # Assert
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            assert archive.read("student_80/binary.dat") == content

    def test_bulk_download_url_resolves_to_correct_view(self):
        # Arrange
        url = reverse("instructor_api:bulk-download")

        # Act
        match = resolve(url)

        # Assert
        assert match.func.view_class is BulkDownloadView

    def test_bulk_download_url_has_no_parameters(self):
        # Arrange
        url = reverse("instructor_api:bulk-download")

        # Act
        match = resolve(url)

        # Assert
        assert match.kwargs == {}

    def test_bulk_download_url_uses_expected_path(self):
        # Arrange
        url = reverse("instructor_api:bulk-download")

        # Act
        normalized_url = url.rstrip("/")

        # Assert
        assert normalized_url.endswith("/assignments/bulk-download")

    def test_post_method_is_not_supported(
        self,
        instructor_user,
    ):
        # Arrange
        client = APIClient()
        client.force_authenticate(user=instructor_user)

        url = reverse("instructor_api:bulk-download")

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

        url = reverse("instructor_api:bulk-download")

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

        url = reverse("instructor_api:bulk-download")

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

        url = reverse("instructor_api:bulk-download")

        # Act
        response = client.delete(url)

        # Assert
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    @staticmethod
    def _submission_file(
        filename,
        content,
    ):
        submission_file = MagicMock()
        submission_file.file_name = filename
        submission_file.file.read.return_value = content
        return submission_file

    @staticmethod
    def _queryset(submissions):
        queryset = MagicMock()
        queryset.exists.return_value = True
        queryset.prefetch_related.return_value = queryset
        queryset.__iter__.return_value = iter(submissions)
        return queryset
