from rest_framework.generics import RetrieveAPIView

from .serializers import ProfileSerializer, TopNavUserSerializer


class ProfileApiView(RetrieveAPIView):
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user.profile


class CurrentUserApiView(RetrieveAPIView):
    serializer_class = TopNavUserSerializer

    def get_object(self):
        return self.request.user
