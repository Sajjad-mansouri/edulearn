from rest_framework import generics, mixins, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from .serializers import (
    EducationSerializer,
    ExperienceSerializer,
    InstructorProfileSerializer,
    InstructorProfileUpdateSerializer,
    LanguageSerializer,
    ProfileSerializer,
    SkillSerializer,
    SocialLinkSerializer,
    StudentProfileSerializer,
    StudentProfileUpdateSerializer,
    TopNavUserSerializer,
    UserUpdateSerializer,
)


class ProfileApiView(generics.RetrieveAPIView):
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user.profile


class StudentProfileApiView(generics.RetrieveAPIView):
    serializer_class = StudentProfileSerializer

    def get_object(self):
        return self.request.user.profile.student_profile


class CurrentUserApiView(generics.RetrieveAPIView):
    serializer_class = TopNavUserSerializer

    def get_object(self):
        return self.request.user


class SkillViewSet(mixins.CreateModelMixin, mixins.DestroyModelMixin, GenericViewSet):
    serializer_class = SkillSerializer

    def get_queryset(self):
        return self.request.user.profile.skills.all()

    def perform_create(self, serializer):
        serializer.save(profile=self.request.user.profile)

    @action(detail=False, methods=["delete"])
    def delete(self, request):
        skill_name = request.data.get("name")

        if not skill_name:
            return Response(
                {"error": "Skill name is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        skill = get_object_or_404(self.get_queryset(), name=skill_name)
        skill.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class StudentProfileUpdateView(generics.UpdateAPIView):
    serializer_class = StudentProfileUpdateSerializer

    def get_object(self):
        return self.request.user.profile.student_profile

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data)
        serializer.is_valid(raise_exception=True)

        self.perform_update(serializer)
        serializer = StudentProfileSerializer(request.user.profile.student_profile)
        return Response(serializer.data)

    def perform_update(self, serializer):
        # This is where we update BOTH models in one request
        user_serializer = UserUpdateSerializer(
            self.request.user, data=self.request.data, partial=True
        )
        user_serializer.is_valid(raise_exception=True)
        user_serializer.save()
        profile_serializer = ProfileSerializer(
            self.request.user.profile, data=self.request.data, partial=True
        )
        profile_serializer.is_valid(raise_exception=True)
        profile_serializer.save()
        serializer.save()
        return user_serializer, profile_serializer, serializer


class InstructorProfileApiView(generics.RetrieveAPIView):
    serializer_class = InstructorProfileSerializer

    def get_object(self):
        return self.request.user.profile.instructor_profile


class InstructorProfileUpdateView(generics.UpdateAPIView):
    serializer_class = InstructorProfileUpdateSerializer

    def get_object(self):
        return self.request.user.profile.instructor_profile

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=False)
        print("error", serializer.errors)

        self.perform_update(serializer)
        serializer = InstructorProfileSerializer(
            request.user.profile.instructor_profile
        )
        return Response(serializer.data)

    def perform_update(self, serializer):
        # This is where we update BOTH models in one request
        user_serializer = UserUpdateSerializer(
            self.request.user, data=self.request.data, partial=True
        )
        user_serializer.is_valid(raise_exception=True)
        user_serializer.save()
        profile_serializer = ProfileSerializer(
            self.request.user.profile, data=self.request.data, partial=True
        )
        profile_serializer.is_valid(raise_exception=True)
        profile_serializer.save()
        serializer.save()
        return user_serializer, profile_serializer, serializer


class ProfileEducationViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    serializer_class = EducationSerializer

    def get_queryset(self):
        return self.request.user.profile.educations.all()

    def perform_create(self, serializer):
        serializer.save(profile=self.request.user.profile)


class ProfileExperienceViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    serializer_class = ExperienceSerializer

    def get_queryset(self):
        return self.request.user.profile.experiences.all()

    def perform_create(self, serializer):
        serializer.save(profile=self.request.user.profile)


class ProfileSocialLinkViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    serializer_class = SocialLinkSerializer

    def get_queryset(self):
        print(self.request.data)
        return self.request.user.profile.social_links.all()

    def create(self, request, *args, **kwargs):
        print(request.data)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(profile=self.request.user.profile)


class ProfileLanguageViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    serializer_class = LanguageSerializer

    def get_queryset(self):
        return self.request.user.profile.languages.all()

    def perform_create(self, serializer):
        serializer.save(profile=self.request.user.profile)
