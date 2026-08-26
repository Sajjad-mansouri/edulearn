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
    path("profile/", views.ProfileApiView.as_view(), name="profile"),
    path(
        "student/profile/",
        views.StudentProfileApiView.as_view(),
        name="student_profile",
    ),
    path("current-user/", views.CurrentUserApiView.as_view(), name="current_user"),
    path(
        "profile/student/update/",
        views.StudentProfileUpdateView.as_view(),
        name="update_student_profile",
    ),
    path(
        "instructor/profile/",
        views.InstructorProfileApiView.as_view(),
        name="instructor_profile",
    ),
    path(
        "profile/instructor/update/",
        views.InstructorProfileUpdateView.as_view(),
        name="update_instructor_profile",
    ),
]
