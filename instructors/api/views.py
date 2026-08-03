from django.contrib.auth import get_user_model
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from courses.models import Course
from normalizers.course import normalize_course_data

from .serializers import (
    CourseSerializer,
    InstructorCourseSerializer,
    InstructorDashboardSerializer,
)
from .services import CourseService

User = get_user_model()


class CourseBuilder(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        course_data = normalize_course_data(request.data)

        serializer = CourseSerializer(data=course_data)
        serializer.is_valid(raise_exception=True)
        CourseService(instructor=request.user).create(serializer.validated_data)
        return Response(serializer.data)


class InstructorCoursesApiView(ListAPIView):
    serializer_class = InstructorCourseSerializer

    def get_queryset(self):
        return Course.objects.filter(owner=self.request.user)


class InstructorStudentsApiView(RetrieveAPIView):
    serializer_class = InstructorDashboardSerializer

    def get_object(self):
        return self.request.user
