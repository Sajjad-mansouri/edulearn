from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer, LogoutSerializer, UserRegistrationSerializer
from .services import logout_user, perform_login, register_user

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


class LoginApiView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "login"

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tokens = perform_login(serializer.validated_data, request)

        return Response(tokens, status=status.HTTP_200_OK)


class LogoutApiView(APIView):
    def post(self, request, *args, **kwargs):
        """Logout may be done via POST."""
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        logout_user(serializer.validated_data["refresh"])
        return Response(
            {"detail": "Successfully logged out."},
            status=status.HTTP_200_OK,
        )
