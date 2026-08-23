from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import SubscriptionPlan
from .serializers import (
    SubscriptionPlanSerializer,
    UserSubscriptionSerializer,
    SubscriptionUpgradeSerializer,
)
from .services import SubscriptionService


class SubscriptionDetailView(APIView):
    """
    GET /api/subscription/
    Retrieves the authenticated user's current subscription details.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        subscription = SubscriptionService.get_current_subscription(request.user)
        serializer = UserSubscriptionSerializer(subscription)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SubscriptionUsageView(APIView):
    """
    GET /api/subscription/usage/
    Retrieves detailed usage metrics against current subscription plan limits.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        usage_data = SubscriptionService.get_usage(request.user)
        return Response(usage_data, status=status.HTTP_200_OK)


class SubscriptionPlanListView(generics.ListAPIView):
    """
    GET /api/subscription/plans/
    Lists all active subscription plans available in the system.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SubscriptionPlanSerializer

    def get_queryset(self):
        # Ensure default plans exist before listing
        SubscriptionService.get_or_create_default_free_plan()
        SubscriptionService.get_or_create_premium_plan()
        return SubscriptionPlan.objects.filter(is_active=True).order_by('price')


class SubscriptionUpgradeView(APIView):
    """
    POST /api/subscription/upgrade/
    Safely upgrades or downgrades the user's subscription plan.
    Note: Payment gateway integration is intentionally not implemented in Day 14.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = SubscriptionUpgradeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        plan_code = serializer.validated_data['plan_code']
        updated_sub = SubscriptionService.change_plan(request.user, plan_code)
        
        response_serializer = UserSubscriptionSerializer(updated_sub)
        return Response(
            {
                'detail': f"Successfully updated subscription to '{updated_sub.plan.name}'.",
                'subscription': response_serializer.data
            },
            status=status.HTTP_200_OK
        )


class SubscriptionCancelView(APIView):
    """
    POST /api/subscription/cancel/
    Cancels the user's active subscription safely without deleting user financial data.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        cancelled_sub = SubscriptionService.cancel_subscription(request.user)
        response_serializer = UserSubscriptionSerializer(cancelled_sub)
        return Response(
            {
                'detail': "Subscription cancelled successfully. Your existing data remains intact.",
                'subscription': response_serializer.data
            },
            status=status.HTTP_200_OK
        )
