from django.contrib.auth import get_user_model
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny

from .serializers import UserRegistrationSerializer
from .services import register_user

User = get_user_model()


class RegisterApiView(CreateAPIView):
    serializer_class = UserRegistrationSerializer
    queryset = User.objects.all()
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        data = serializer.validated_data.copy()
        register_user(data=data, role_name="student", request=self.request)


class RegisterInstructorApiView(RegisterApiView):
    def perform_create(self, serializer):
        data = serializer.validated_data.copy()
        register_user(data=data, role_name="teacher", request=self.request)


class RegisterConfirmApiView(CreateAPIView):
    pass
