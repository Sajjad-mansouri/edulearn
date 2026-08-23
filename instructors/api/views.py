import io
import zipfile

from django.contrib.auth import get_user_model
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import (
    GenericAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from assessments.models import AssignmentSubmission
from courses.models import Course
from normalizers.course import normalize_course_data

from .serializers import (
    AssignmentSubmissionSerializer,
    CourseSerializer,
    GradeSerializer,
    InstructorCourseSerializer,
    InstructorDashboardSerializer,
    InstructorFilterCoursesSerializer,
)
from .services import CourseService, CourseUpdateService

User = get_user_model()


class CourseBuilder(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        course_status = kwargs.get("course_status")
        course_data, _ = normalize_course_data(request.data)

        serializer = CourseSerializer(data=course_data)
        serializer.is_valid(raise_exception=False)
        course = CourseService(instructor=request.user).create(
            serializer.validated_data
        )
        if course_status == Course.Status.SUBMITTED:
            course.status = Course.Status.SUBMITTED
            course.review_status = Course.ReviewStatus.PENDING
            course.save()
        return Response(serializer.data)


class CourseUpdateApiView(GenericAPIView):
    permission_classes = [AllowAny]

    def patch(self, request, *args, **kwargs):
        course_status = kwargs.get("course_status")
        course_data, deleted_ids_dict = normalize_course_data(request.data)

        course = self.get_object()
        serializer = CourseSerializer(instance=course, data=course_data, partial=True)
        serializer.is_valid(raise_exception=False)

        course = CourseUpdateService(
            course=course, deleted_ids_dict=deleted_ids_dict
        ).update(serializer.validated_data)
        if course_status == Course.Status.SUBMITTED:
            course.status = Course.Status.SUBMITTED
            course.review_status = Course.ReviewStatus.PENDING
            course.save()
        return Response(serializer.data)

    def get_queryset(self):
        return Course.objects.filter(owner=self.request.user)


class CourseApiView(RetrieveAPIView):
    serializer_class = CourseSerializer

    def get_queryset(self):
        return Course.objects.filter(owner=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        return Response(serializer.data)


class InstructorCoursesApiView(ListAPIView):
    serializer_class = InstructorCourseSerializer

    def get_queryset(self):
        return Course.objects.filter(owner=self.request.user)


class InstructorStudentsApiView(RetrieveAPIView):
    serializer_class = InstructorDashboardSerializer

    def get_object(self):
        return self.request.user


class InstructorAssignmentsApiView(ListAPIView):
    serializer_class = AssignmentSubmissionSerializer

    def get_queryset(self):
        return AssignmentSubmission.objects.filter(
            enrollment__course__owner=self.request.user
        )


class GradeAssignmentApiView(UpdateAPIView):
    serializer_class = GradeSerializer

    def get_queryset(self):
        return AssignmentSubmission.objects.filter(
            enrollment__course__owner=self.request.user
        )


class SubmissionDownloadView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, id):
        submission = get_object_or_404(AssignmentSubmission, pk=id)
        files = submission.files.all()

        if not files.exists():
            return Response(
                {"error": "No files found for this submission"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if files.count() == 1:
            file_obj = files.first()
            file_handle = file_obj.file.open("rb")
            response = FileResponse(
                file_handle, content_type="application/octet-stream"
            )
            response["Content-Disposition"] = (
                f'attachment; filename="{file_obj.file_name}"'
            )
            return response
        else:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for file_obj in files:
                    file_content = file_obj.file.read()
                    zip_file.writestr(file_obj.file_name, file_content)

            zip_buffer.seek(0)
            response = HttpResponse(
                zip_buffer.getvalue(), content_type="application/zip"
            )
            response["Content-Disposition"] = (
                f'attachment; filename="submission_{id}_files.zip"'
            )
            return response


class BulkDownloadView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        ids = request.GET.get("ids", "")

        if not ids:
            return Response(
                {"error": "No submission IDs provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        id_list = [int(id.strip()) for id in ids.split(",") if id.strip()]
        submissions = AssignmentSubmission.objects.filter(
            id__in=id_list
        ).prefetch_related("files")

        if not submissions.exists():
            return Response(
                {"error": "No submissions found"}, status=status.HTTP_404_NOT_FOUND
            )

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for submission in submissions:
                folder_name = f"{submission.enrollment.user.username.replace(' ', '_')}_{submission.id}"
                for file_obj in submission.files.all():
                    file_path = f"{folder_name}/{file_obj.file_name}"
                    file_content = file_obj.file.read()
                    zip_file.writestr(file_path, file_content)

        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer.getvalue(), content_type="application/zip")
        response["Content-Disposition"] = 'attachment; filename="bulk_submissions.zip"'
        return response


class InstructorFilterCoursesApiView(RetrieveAPIView):
    serializer_class = InstructorFilterCoursesSerializer

    def get_object(self):
        return self.request.user
