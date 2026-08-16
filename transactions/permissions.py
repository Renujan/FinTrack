from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Object-level permission enforcement to only allow owners of Category, Transaction, or Budget
    objects to access, edit, or delete them. Prevents unauthorized cross-user access.
    """

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        return hasattr(obj, 'user') and obj.user == request.user

