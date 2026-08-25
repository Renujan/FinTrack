from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer
from rest_framework import serializers

from .models import SubscriptionPlan
from .serializers import (
    SubscriptionPlanSerializer,
    UserSubscriptionSerializer,
    SubscriptionUpgradeSerializer,
)
from .services import SubscriptionService


@extend_schema(
    tags=['Subscriptions'],
    summary='Retrieve Current Subscription Details',
    description='Returns authenticated user active subscription plan, status, period dates, and auto-renewal configuration.',
    responses={
        200: UserSubscriptionSerializer,
        401: OpenApiResponse(description='Authentication required'),
    }
)
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


@extend_schema(
    tags=['Subscriptions'],
    summary='Retrieve Subscription Quota & Usage',
    description='Returns consumption metrics against plan limits for transactions, categories, budgets, recurring items, and goals.',
    responses={
        200: OpenApiResponse(description='Usage metrics and plan limit breakdown'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class SubscriptionUsageView(APIView):
    """
    GET /api/subscription/usage/
    Retrieves detailed usage metrics against current subscription plan limits.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        usage_data = SubscriptionService.get_usage(request.user)
        return Response(usage_data, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Subscriptions'],
    summary='List Active Subscription Plans',
    description='Retrieves all active subscription tiers available for purchase or upgrade.',
    responses={
        200: SubscriptionPlanSerializer(many=True),
        401: OpenApiResponse(description='Authentication required'),
    }
)
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


@extend_schema(
    tags=['Subscriptions'],
    summary='Upgrade or Switch Subscription Plan',
    description='Switches the authenticated user to a target subscription plan tier (e.g. FREE, PREMIUM, PRO, ENTERPRISE).',
    request=SubscriptionUpgradeSerializer,
    responses={
        200: inline_serializer(
            name='SubscriptionUpgradeResponse',
            fields={
                'detail': serializers.CharField(),
                'subscription': UserSubscriptionSerializer(),
            }
        ),
        400: OpenApiResponse(description='Invalid plan code or validation error'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
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


@extend_schema(
    tags=['Subscriptions'],
    summary='Cancel Active Subscription',
    description='Cancels auto-renewal for the user subscription without purging historical data.',
    request=None,
    responses={
        200: inline_serializer(
            name='SubscriptionCancelResponse',
            fields={
                'detail': serializers.CharField(),
                'subscription': UserSubscriptionSerializer(),
            }
        ),
        401: OpenApiResponse(description='Authentication required'),
    }
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

