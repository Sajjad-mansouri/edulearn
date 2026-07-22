from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"skills", views.SkillViewSet, basename="skill")
router.register(r"educations", views.ProfileEducationViewSet, basename="education")
router.register(r"experiences", views.ProfileExperienceViewSet, basename="experience")
router.register(r"social-links", views.ProfileSocialLinkViewSet, basename="social_link")
router.register(r"languages", views.ProfileLanguageViewSet, basename="language")


urlpatterns = router.urls


app_name = "profile-api"
urlpatterns += [
    path("profile/", views.ProfileApiView.as_view(), name="student_profile"),
    path("current-user/", views.CurrentUserApiView.as_view(), name="current_user"),
    path(
        "basic-info/update/", views.UserInfoUpadteApiView.as_view(), name="update_user"
    ),
]
