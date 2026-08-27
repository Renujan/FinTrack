from rest_framework import status, generics, permissions
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer
from rest_framework import serializers

from finance_tracker.throttling import UserAuthRateThrottle
from transactions.audit_services import AuditLogService
from transactions.models import Transaction, Budget, FinancialGoal, RecurringTransaction, Notification, AuditLog
from users.models import UserProfile, UserPreference
from users.services import UserPreferenceService
from users.serializers import (
    UserProfileSerializer,
    UserPreferenceSerializer,
    PasswordChangeSerializer,
    AccountOverviewSerializer,
)


@extend_schema(
    tags=['User Profile & Account'],
    summary='Retrieve or Update Authenticated User Profile',
    description='Retrieves or updates authenticated user profile details including name, bio, phone number, and currency.',
    request=UserProfileSerializer,
    responses={
        200: UserProfileSerializer,
        400: OpenApiResponse(description='Validation error or duplicate email/username'),
        401: OpenApiResponse(description='Authentication credentials required'),
    }
)
class UserProfileDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserAuthRateThrottle]

    def get_object(self):
        user = self.request.user
        profile, _ = UserProfile.objects.get_or_create(user=user)
        return profile

    def perform_update(self, serializer):
        profile = serializer.save()
        AuditLogService.log_update(
            user=self.request.user,
            resource_type='UserProfile',
            resource_id=profile.id,
            metadata={'updated_fields': list(serializer.validated_data.keys())},
            request=self.request
        )


@extend_schema(
    tags=['User Profile & Account'],
    summary='Retrieve or Update User Account Preferences',
    description='Retrieves or updates authenticated user settings including preferred currency, date format, timezone, and notification toggles.',
    request=UserPreferenceSerializer,
    responses={
        200: UserPreferenceSerializer,
        400: OpenApiResponse(description='Invalid preference configuration values'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class UserPreferenceDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = UserPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserAuthRateThrottle]

    def get_object(self):
        user = self.request.user
        return UserPreferenceService.get_preferences(user)

    def perform_update(self, serializer):
        preferences = serializer.save()
        AuditLogService.log_update(
            user=self.request.user,
            resource_type='UserPreference',
            resource_id=preferences.id,
            metadata={'updated_fields': list(serializer.validated_data.keys())},
            request=self.request
        )


@extend_schema(
    tags=['User Profile & Account'],
    summary='Change Authenticated User Password',
    description='Securely changes account password requiring current password validation and matching password confirmation.',
    request=PasswordChangeSerializer,
    responses={
        200: inline_serializer(
            name='PasswordChangeSuccessResponse',
            fields={'message': serializers.CharField(default='Password changed successfully.')}
        ),
        400: OpenApiResponse(description='Current password incorrect or validation error'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class PasswordChangeView(generics.GenericAPIView):
    serializer_class = PasswordChangeSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserAuthRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        new_password = serializer.validated_data['new_password']
        user.set_password(new_password)
        user.save()

        AuditLogService.log_password_change(user, request=request)

        return Response(
            {"message": "Password changed successfully."},
            status=status.HTTP_200_OK
        )


@extend_schema(
    tags=['User Profile & Account'],
    summary='Retrieve Account Overview & Activity Summary',
    description='Returns comprehensive overview of current account user info, active profile, preferences, subscription tier, entity counters, and recent activity.',
    responses={
        200: AccountOverviewSerializer,
        401: OpenApiResponse(description='Authentication required'),
    }
)
class AccountOverviewView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserAuthRateThrottle]
    serializer_class = AccountOverviewSerializer

    def get_account_summary(self, user, request):
        profile, _ = UserProfile.objects.get_or_create(user=user)
        preferences = UserPreferenceService.get_preferences(user)
        sub_info = {
            'plan_name': 'Free',
            'status': 'active',
            'start_date': None,
            'end_date': None,
            'auto_renew': True,
        }
        if hasattr(user, 'subscription') and user.subscription:
            sub = user.subscription
            sub_info = {
                'plan_name': sub.plan.name if sub.plan else 'Free',
                'status': sub.effective_status,
                'start_date': sub.start_date.isoformat() if sub.start_date else None,
                'end_date': sub.end_date.isoformat() if sub.end_date else None,
                'auto_renew': sub.auto_renew,
            }
        stats = {
            'transaction_count': Transaction.objects.filter(user=user).count(),
            'budget_count': Budget.objects.filter(user=user).count(),
            'goal_count': FinancialGoal.objects.filter(user=user).count(),
            'recurring_schedule_count': RecurringTransaction.objects.filter(user=user).count(),
            'unread_notification_count': Notification.objects.filter(user=user, is_read=False).count(),
        }
        recent_logs = AuditLog.objects.filter(user=user).order_by('-timestamp')[:5]
        activity_summary = [
            {
                'action': log.action,
                'resource_type': log.resource_type,
                'resource_id': log.resource_id,
                'timestamp': log.timestamp.isoformat(),
                'ip_address': log.ip_address,
            }
            for log in recent_logs
        ]
        return {
            'user_info': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'date_joined': user.date_joined.isoformat() if user.date_joined else None,
                'is_staff': user.is_staff,
                'is_active': user.is_active,
            },
            'profile': UserProfileSerializer(profile, context={'request': request}).data,
            'preferences': UserPreferenceSerializer(preferences, context={'request': request}).data,
            'subscription': sub_info,
            'statistics': stats,
            'recent_activity': activity_summary,
        }

    def get(self, request, *args, **kwargs):
        data = self.get_account_summary(request.user, request)
        return Response(data, status=status.HTTP_200_OK)
