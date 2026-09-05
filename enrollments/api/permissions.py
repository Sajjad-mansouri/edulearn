from rest_framework import permissions

from accounts.models import Role
from courses.models import Course
from enrollments.models import Enrollment


class IsEnrolled(permissions.BasePermission):
    """
    Allows access if user is enrolled in the course or owns it.
    """

    message = "You must be enrolled in this course or be the owner."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Get identifiers from URL kwargs
        enrollment_id = view.kwargs.get("enrollment_id")

        # Case 1: Enrollment-based access
        if enrollment_id:
            enrollment = Enrollment.objects.filter(
                id=enrollment_id, user=request.user
            ).exists()
            if enrollment:
                # Store enrollment for later use if needed
                view.enrollment = Enrollment.objects.select_related("course").get(
                    id=enrollment_id, user=request.user
                )
                return True
            return False

        # No valid identifier provided
        return False


class IsOwner(permissions.BasePermission):
    """
    Allows access if user is enrolled in the course or owns it.
    """

    message = "You must be enrolled in this course or be the owner."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        course_id = view.kwargs.get("course_id")

        if course_id:
            is_owner = Course.objects.filter(id=course_id, owner=request.user).exists()
            if is_owner:
                view.enrollment = None
                return True
            return False

        # No valid identifier provided
        return False


class IsStudent(permissions.BasePermission):
    """
    Allows access only to instructor users.
    """

    message = "You must be an instructor to access this resource."

    def has_permission(self, request, view):
        # Check if user is authenticated first
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has instructor role
        return request.user.roles.filter(name=Role.Roles.STUDENT).exists()
