from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.utils.http import urlsafe_base64_decode
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import UserRegistrationSerializer
from .services import confirm_registration, register_user

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


class RegisterConfirmApiView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        user = self.get_user(kwargs["uidb64"])
        token = kwargs["token"]

        if user is None:
            return Response(
                {"detail": "Invalid confirmation link."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not default_token_generator.check_token(user, token):
            return Response(
                {"detail": "Invalid confirmation link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        confirm_registration(user)
        return Response(
            {"detail": "Email verified successfully."},
            status=status.HTTP_200_OK,
        )

    def get_user(self, uidb64):
        try:
            # urlsafe_base64_decode() decodes to bytestring
            uid = urlsafe_base64_decode(uidb64).decode()
            pk = User._meta.pk.to_python(uid)
            user = User._default_manager.get(pk=pk)
        except (
            TypeError,
            ValueError,
            OverflowError,
            User.DoesNotExist,
            ValidationError,
        ):
            user = None
        return user
