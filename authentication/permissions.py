"""
Authentication Custom Permissions module.
Provides granular permission enforcement for authentication and user account management.
"""
from rest_framework import permissions


class IsSelfOrAdmin(permissions.BasePermission):
    """
    Permission check to allow users to modify only their own account records,
    or administrative superusers.
    """

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        return obj == request.user or request.user.is_staff
