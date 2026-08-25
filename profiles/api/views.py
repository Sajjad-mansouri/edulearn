from rest_framework import generics, mixins, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from .serializers import (
    EducationSerializer,
    ExperienceSerializer,
    LanguageSerializer,
    ProfileSerializer,
    SkillSerializer,
    SocialLinkSerializer,
    TopNavUserSerializer,
)


class ProfileApiView(generics.RetrieveAPIView):
    serializer_class = ProfileSerializer

    def get_object(self):
        print(self.request.user.profile)
        return self.request.user.profile


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


class UserInfoUpadteApiView(generics.UpdateAPIView):
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user.profile


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
        return self.request.user.profile.social_links.all()

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
