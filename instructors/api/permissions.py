from rest_framework import permissions

from accounts.models import Role


class IsInstructor(permissions.BasePermission):
    """
    Allows access only to instructor users.
    """

    message = "You must be an instructor to access this resource."

    def has_permission(self, request, view):
        # Check if user is authenticated first
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has instructor role
        return request.user.roles.filter(name=Role.Roles.INSTRUCTOR).exists()
