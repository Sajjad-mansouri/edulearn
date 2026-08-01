from rest_framework.generics import ListAPIView

from courses.models import Category

from .serializers import (
    CategorySerializer,
)


class CategoriesApiView(ListAPIView):
    serializer_class = CategorySerializer
    queryset = Category.objects.all()


class SubcategoriesApiView(ListAPIView):
    serializer_class = CategorySerializer

    def get_queryset(self):
        category_slug = self.kwargs.get("categorySlug")
        return Category.objects.filter(parent__slug=category_slug)
