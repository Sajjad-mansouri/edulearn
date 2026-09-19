import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from accounts.models import Role

User = get_user_model()


@pytest.fixture
def instructor_user(db):
    user = User.objects.create_user(
        username="test_instructor",
        email="test_instructor@example.com",
        password="test-password",
    )
    role, _ = Role.objects.get_or_create(name=Role.Roles.INSTRUCTOR)
    user.roles.add(role)
    return user


@pytest.fixture
def student_user(db):
    user = User.objects.create_user(
        username="test_student",
        email="test_student@example.com",
        password="test-password",
    )
    role, _ = Role.objects.get_or_create(name=Role.Roles.STUDENT)
    user.roles.add(role)
    return user


@pytest.fixture
def instructor_urls():
    return [
        (
            "instructor:instructor_course_list",
            {},
            "instructors/instructor_courses.html",
        ),
        (
            "instructor:create_course",
            {},
            "instructors/create_course.html",
        ),
        (
            "instructor:students",
            {},
            "instructors/students.html",
        ),
        (
            "instructor:assignments",
            {},
            "instructors/assignments.html",
        ),
        (
            "instructor:update_course",
            {"slug": "test-course", "pk": 1},
            "instructors/update_course.html",
        ),
        (
            "instructor:analytics",
            {},
            "instructors/analytics.html",
        ),
        (
            "instructor:revenue",
            {},
            "instructors/revenue.html",
        ),
        (
            "instructor:course_preview",
            {"course_id": 1},
            "instructors/course_preview.html",
        ),
    ]


class TestInstructorTemplateViews:
    @pytest.mark.parametrize(
        ("url_name", "kwargs", "template_name"),
        [
            (
                "instructor:instructor_course_list",
                {},
                "instructors/instructor_courses.html",
            ),
            (
                "instructor:create_course",
                {},
                "instructors/create_course.html",
            ),
            (
                "instructor:students",
                {},
                "instructors/students.html",
            ),
            (
                "instructor:assignments",
                {},
                "instructors/assignments.html",
            ),
            (
                "instructor:update_course",
                {"slug": "test-course", "pk": 1},
                "instructors/update_course.html",
            ),
            (
                "instructor:analytics",
                {},
                "instructors/analytics.html",
            ),
            (
                "instructor:revenue",
                {},
                "instructors/revenue.html",
            ),
            (
                "instructor:course_preview",
                {"course_id": 1},
                "instructors/course_preview.html",
            ),
        ],
    )
    def test_instructor_can_access_view(
        self,
        client,
        instructor_user,
        url_name,
        kwargs,
        template_name,
    ):
        # Arrange
        client.force_login(instructor_user)
        url = reverse(url_name, kwargs=kwargs)

        # Act
        response = client.get(url)

        # Assert
        assert response.status_code == 200
        assert response.template_name == [template_name]

    @pytest.mark.parametrize(
        ("url_name", "kwargs"),
        [
            ("instructor:instructor_course_list", {}),
            ("instructor:create_course", {}),
            ("instructor:students", {}),
            ("instructor:assignments", {}),
            (
                "instructor:update_course",
                {"slug": "test-course", "pk": 1},
            ),
            ("instructor:analytics", {}),
            ("instructor:revenue", {}),
            (
                "instructor:course_preview",
                {"course_id": 1},
            ),
        ],
    )
    def test_unauthenticated_user_is_redirected_to_login(
        self,
        client,
        url_name,
        kwargs,
    ):
        # Arrange
        url = reverse(url_name, kwargs=kwargs)

        # Act
        response = client.get(url)

        # Assert
        assert response.status_code == 302

    @pytest.mark.parametrize(
        ("url_name", "kwargs"),
        [
            ("instructor:instructor_course_list", {}),
            ("instructor:create_course", {}),
            ("instructor:students", {}),
            ("instructor:assignments", {}),
            (
                "instructor:update_course",
                {"slug": "test-course", "pk": 1},
            ),
            ("instructor:analytics", {}),
            ("instructor:revenue", {}),
            (
                "instructor:course_preview",
                {"course_id": 1},
            ),
        ],
    )
    def test_non_instructor_user_cannot_access_view(
        self,
        client,
        student_user,
        url_name,
        kwargs,
    ):
        # Arrange
        client.force_login(student_user)
        url = reverse(url_name, kwargs=kwargs)

        # Act
        response = client.get(url)

        # Assert
        assert response.status_code == 404

    @pytest.mark.parametrize(
        ("url_name", "kwargs", "template_name"),
        [
            (
                "instructor:instructor_course_list",
                {},
                "instructors/instructor_courses.html",
            ),
            (
                "instructor:create_course",
                {},
                "instructors/create_course.html",
            ),
            (
                "instructor:students",
                {},
                "instructors/students.html",
            ),
            (
                "instructor:assignments",
                {},
                "instructors/assignments.html",
            ),
            (
                "instructor:update_course",
                {"slug": "test-course", "pk": 1},
                "instructors/update_course.html",
            ),
            (
                "instructor:analytics",
                {},
                "instructors/analytics.html",
            ),
            (
                "instructor:revenue",
                {},
                "instructors/revenue.html",
            ),
            (
                "instructor:course_preview",
                {"course_id": 1},
                "instructors/course_preview.html",
            ),
        ],
    )
    def test_view_uses_expected_template(
        self,
        client,
        instructor_user,
        url_name,
        kwargs,
        template_name,
    ):
        # Arrange
        client.force_login(instructor_user)
        url = reverse(url_name, kwargs=kwargs)

        # Act
        response = client.get(url)

        # Assert
        assert response.status_code == 200
        assert response.template_name == [template_name]
        assert template_name in {template.name for template in response.templates}
