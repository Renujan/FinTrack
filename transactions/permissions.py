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
        owner = getattr(obj, 'user', None)
        return owner is not None and owner == request.user


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission enforcement allowing read access for owners and restricting write/delete.
    """

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        owner = getattr(obj, 'user', None)
        if owner is None or owner != request.user:
            return False
        return True


