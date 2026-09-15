import pytest
from django.contrib.auth import get_user_model

from accounts.models import Role
from profiles.models import InstructorProfile, Profile

User = get_user_model()


@pytest.fixture
def test_user(db):
    return User.objects.create_user(
        username="test_user",
        email="test_user@example.com",
        password="test-password",
    )


@pytest.fixture
def instructor_role(db):
    return Role.objects.create(
        name=Role.Roles.INSTRUCTOR,
    )


@pytest.fixture
def student_role(db):
    return Role.objects.create(
        name=Role.Roles.STUDENT,
    )


@pytest.fixture
def profile(db, test_user):
    return Profile.objects.create(user=test_user)


@pytest.fixture
def instructor_profile(db, profile):
    return InstructorProfile.objects.create(
        profile=profile,
        headline="Backend Developer",
        biography="Experienced software developer.",
        professional_title="Senior Developer",
        organization="Example Organization",
        years_of_experience=5,
    )


@pytest.fixture
def registration_request(request_factory, settings):
    settings.ALLOWED_HOSTS = ["testserver"]
    return request_factory.get("/accounts/register/")
