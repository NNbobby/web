from rest_framework import permissions

class IsVerified(permissions.BasePermission):
    message = "Account is not verified by administration."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_verified)