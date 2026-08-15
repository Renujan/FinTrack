from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Object-level permission enforcement to only allow owners of an object to access, edit, or delete it.
    Prevents unauthorized cross-user modifications and object access.
    """

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        return hasattr(obj, 'user') and obj.user == request.user
