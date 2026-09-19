import io
import zipfile
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import DecimalField, F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import (
    DestroyAPIView,
    GenericAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from assessments.models import AssignmentSubmission
from courses.models import Course
from normalizers.course import normalize_course_data
from payments.models import Payment

from .permissions import IsInstructor
from .serializers import (
    AnalyticFilterCoursesSerializer,
    AnalyticSerializer,
    AssignmentSubmissionSerializer,
    CourseSerializer,
    GradeSerializer,
    InstructorCourseSerializer,
    InstructorCourseSubmissionSerializer,
    InstructorDashboardSerializer,
    InstructorFilterCoursesSerializer,
    RevenueSerializer,
    TransactionSerializer,
)
from .services import (
    AnalyticService,
    CourseService,
    CourseUpdateService,
    RevenueService,
)

User = get_user_model()


class CourseBuilder(APIView):
    permission_classes = [IsInstructor]

    def post(self, request, *args, **kwargs):
        course_status = kwargs.get("course_status")
        course_data, _ = normalize_course_data(request.data)

        serializer = CourseSerializer(data=course_data)
        serializer.is_valid(raise_exception=True)
        print(serializer.errors)
        course = CourseService(instructor=request.user).create(
            serializer.validated_data
        )
        if course_status == Course.Status.SUBMITTED:
            course.status = Course.Status.SUBMITTED
            course.review_status = Course.ReviewStatus.PENDING
            course.save()
        return Response(serializer.data)


class CourseUpdateApiView(GenericAPIView):
    permission_classes = [IsInstructor]

    def patch(self, request, *args, **kwargs):
        course_status = kwargs.get("course_status")
        course_data, deleted_ids_dict = normalize_course_data(request.data)
        course = self.get_object()
        serializer = CourseSerializer(instance=course, data=course_data, partial=True)
        serializer.is_valid(raise_exception=True)

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
    permission_classes = [IsInstructor]

    def get_queryset(self):
        return Course.objects.filter(owner=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        return Response(serializer.data)


class InstructorCoursesApiView(ListAPIView):
    serializer_class = InstructorCourseSerializer
    permission_classes = [IsInstructor]

    def get_queryset(self):
        return (
            Course.objects.filter(owner=self.request.user)
            .annotate(
                revenue=Coalesce(
                    Sum(
                        "enrollments__payments__amount",
                        filter=Q(
                            enrollments__payments__status=Payment.Status.SUCCEEDED
                        ),
                    ),
                    Value(Decimal("0.00")),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                )
                - Coalesce(
                    Sum(
                        "enrollments__payments__amount",
                        filter=Q(enrollments__payments__status=Payment.Status.REFUNDED),
                    ),
                    Value(Decimal("0.00")),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                )
            )
            .order_by("-last_updated", "-pk")
        )


class InstructorStudentsApiView(RetrieveAPIView):
    serializer_class = InstructorDashboardSerializer
    permission_classes = [IsInstructor]

    def get_object(self):
        return self.request.user


class InstructorAssignmentsApiView(ListAPIView):
    serializer_class = AssignmentSubmissionSerializer
    permission_classes = [IsInstructor]

    def get_queryset(self):
        return AssignmentSubmission.objects.filter(
            enrollment__course__owner=self.request.user
        )


class GradeAssignmentApiView(UpdateAPIView):
    serializer_class = GradeSerializer
    permission_classes = [IsInstructor]

    def get_queryset(self):
        return AssignmentSubmission.objects.filter(
            enrollment__course__owner=self.request.user
        )

    def perform_update(self, serializer):
        serializer.save()


class SubmissionDownloadView(APIView):
    permission_classes = [IsInstructor]

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
    permission_classes = [IsInstructor]

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
    permission_classes = [IsInstructor]

    def get_object(self):
        return self.request.user


class InstructorAnalyticsApiView(APIView):
    permission_classes = [IsInstructor]

    def get(self, request, *args, **kwargs):
        period = kwargs.get("period") or request.query_params.get("period") or "30"
        course_slug = request.query_params.get(
            "course_slug"
        ) or request.query_params.get("course")

        service = AnalyticService(
            instructor=request.user,
            period=period,
            course_slug=course_slug,
        )
        analytics_data = service.get_analytics()
        serializer = AnalyticSerializer(data=analytics_data)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class InstructorAnalyticsCoursesApiView(ListAPIView):
    serializer_class = AnalyticFilterCoursesSerializer
    pagination_class = None
    permission_classes = [IsInstructor]

    def get_queryset(self):
        return Course.objects.filter(owner=self.request.user)


class InstructorRevenueApiView(APIView):
    permission_classes = [IsInstructor]

    def get(self, request, *args, **kwargs):
        period = request.query_params.get("period", "30")
        period = str(period).lower().strip()

        if period not in RevenueService.ALLOWED_PERIODS:
            raise ValidationError(
                {
                    "period": (
                        f"Invalid period. Allowed values: "
                        f"{', '.join(sorted(RevenueService.ALLOWED_PERIODS))}"
                    )
                }
            )

        service = RevenueService(
            instructor=request.user,
            period=period,
        )
        revenue_data = service.get_revenue()

        serializer = RevenueSerializer(revenue_data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class InstructorTransactionsPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class InstructorTransactionsApiView(ListAPIView):
    permission_classes = [IsInstructor]
    serializer_class = TransactionSerializer
    pagination_class = InstructorTransactionsPagination

    def get_queryset(self):
        return (
            Payment.objects.filter(enrollment__course__owner=self.request.user)
            .annotate(course=F("enrollment__course__title"))
            .select_related("enrollment__course")
            .order_by("-updated_at")  # or -paid_at / -created_at
        )


class CourseDeleteApiView(DestroyAPIView):
    permission_classes = [IsInstructor]

    def get_queryset(self):
        return Course.objects.filter(
            Q(owner=self.request.user)
            & ~Q(
                review_status__in=[
                    Course.ReviewStatus.PENDING,
                    Course.ReviewStatus.UNDER_REVIEW,
                ]
            )
        )


class CourseSubmitApiView(APIView):
    permission_classes = [IsInstructor]

    def post(self, request, course_id):
        courses = Course.objects.filter(
            Q(owner=request.user)
            & Q(
                review_status__in=[
                    Course.ReviewStatus.NOT_SUBMITTED,
                    Course.ReviewStatus.CHANGES_REQUESTED,
                ]
            )
        )
        course = get_object_or_404(courses, id=course_id)
        serializer = InstructorCourseSubmissionSerializer(
            course,
            {
                "review_status": Course.ReviewStatus.PENDING,
                "status": Course.Status.SUBMITTED,
            },
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


class CoursePublishApiView(APIView):
    permission_classes = [IsInstructor]

    def post(self, request, course_id):
        courses = Course.objects.filter(
            Q(owner=request.user)
            & Q(review_status=Course.ReviewStatus.APPROVED)
            & Q(status=Course.Status.SUBMITTED)
        )

        course = get_object_or_404(courses, id=course_id)
        serializer = InstructorCourseSubmissionSerializer(
            course, {"status": Course.Status.PUBLISHED}, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)
