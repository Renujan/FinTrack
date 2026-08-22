from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Object-level permission enforcement to only allow owners of Category, Transaction, Budget,
    RecurringTransaction, FinancialGoal, Notification, or AuditLog objects to access, edit, or delete them.
    Prevents unauthorized cross-user access and IDOR vulnerabilities.
    """

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        return hasattr(obj, 'user') and obj.user == request.user


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission enforcement allowing read access for owners and restricting write/delete.
    """

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return hasattr(obj, 'user') and obj.user == request.user
        return hasattr(obj, 'user') and obj.user == request.user


