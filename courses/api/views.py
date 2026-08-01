from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from courses.models import Category
from normalizers.course import normalize_course_data

from .serializers import CategorySerializer, CourseSerializer
from .services import CourseService


class CategoriesApiView(ListAPIView):
    serializer_class = CategorySerializer
    queryset = Category.objects.all()


class SubcategoriesApiView(ListAPIView):
    serializer_class = CategorySerializer

    def get_queryset(self):
        category_slug = self.kwargs.get("categorySlug")
        return Category.objects.filter(parent__slug=category_slug)


class CourseBuilder(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        course_data = normalize_course_data(request.data)

        print("parsed data:", course_data)
        serializer = CourseSerializer(data=course_data)
        serializer.is_valid(raise_exception=True)
        CourseService(instructor=request.user).create(serializer.validated_data)
        return Response(serializer.data)
