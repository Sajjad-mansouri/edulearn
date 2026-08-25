from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import CreateAPIView, GenericAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from profiles.api.serializers import (
    EducationSerializer,
    ExperienceSerializer,
    SkillSerializer,
)

from .serializers import (
    CurrentUserSerializer,
    InstructorProfileSerializer,
    LoginSerializer,
    LogoutSerializer,
    PasswordResetSerializer,
    StudentRegistrationSerializer,
    UserRegisterationSerializer,
    UserRegisterProfileSerializer,
)
from .services import (
    logout_user,
    perform_login,
    register_instructor,
    register_user,
    send_password_reset_email,
)

User = get_user_model()


class RegisterApiView(CreateAPIView):
    serializer_class = StudentRegistrationSerializer
    queryset = User.objects.all()
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        data = serializer.validated_data.copy()
        register_user(data=data, role_name="student", request=self.request)


class RegisterInstructorApiView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        educations = request.data.get("educations", [])
        experiences = request.data.get("experiences", [])
        skills = request.data.get("skills", [])
        profile_info = request.data.get("profile", {})
        personal_info = request.data.get("personal_info", {})
        instructor_info = request.data.get("instructor", {})

        # ==================== User Serializer ====================
        if request.user.is_authenticated:
            user_serializer = None  # No user creation, do nothing
        else:
            user_serializer = UserRegisterationSerializer(data=personal_info)

        # ==================== Other Serializers ====================
        edu_serializer = EducationSerializer(data=educations, many=True)
        experience_serializer = ExperienceSerializer(data=experiences, many=True)
        skill_serializer = SkillSerializer(data=skills, many=True)
        profile_serializer = UserRegisterProfileSerializer(data=profile_info)
        instructor_serializer = InstructorProfileSerializer(data=instructor_info)

        # ==================== Validate All Serializers ====================
        errors = {}

        if user_serializer is not None:
            if not user_serializer.is_valid():
                errors["personal_info"] = user_serializer.errors

        if not edu_serializer.is_valid():
            errors["educations"] = edu_serializer.errors
        if not experience_serializer.is_valid():
            errors["experiences"] = experience_serializer.errors
        if not skill_serializer.is_valid():
            errors["skills"] = skill_serializer.errors
        if not profile_serializer.is_valid():
            errors["profile"] = profile_serializer.errors
        if not instructor_serializer.is_valid():
            errors["instructor"] = instructor_serializer.errors

        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            profile, instructor_profile, created = register_instructor(
                request=request,
                educations_data=edu_serializer.validated_data,
                experiences_data=experience_serializer.validated_data,
                skills_data=skill_serializer.validated_data,
                user_data=user_serializer.validated_data if user_serializer else {},
                profile_data=profile_serializer.validated_data,
                instructor_data=instructor_serializer.validated_data,
            )
        except ValidationError as e:
            return Response(
                {"detail": getattr(e, "message_dict", str(e))},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "detail": "Instructor application submitted successfully",
                "created": created,
                "application_status": instructor_profile.application_status,
                "profile_id": profile.id,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class LoginApiView(GenericAPIView):
    permission_classes = [AllowAny]
    throttle_scope = "login"

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tokens = perform_login(serializer.validated_data, request)

        return Response(tokens, status=status.HTTP_200_OK)


class LogoutApiView(GenericAPIView):
    def post(self, request, *args, **kwargs):
        """Logout may be done via POST."""
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        logout_user(serializer.validated_data["refresh"])
        return Response(
            {"detail": "Successfully logged out."},
            status=status.HTTP_200_OK,
        )


class PasswordResetApiView(RetrieveAPIView):
    serializer_class = PasswordResetSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        send_password_reset_email(
            request=request, email=serializer.validated_data["email"]
        )
        return Response(
            {
                "detail": "If an account with that email exists, a password reset link has been sent."
            },
            status=status.HTTP_200_OK,
        )


class CurrentUserApiView(RetrieveAPIView):
    serializer_class = CurrentUserSerializer

    def get_object(self):
        return self.request.user
