from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, OpenApiResponse

from finance_tracker.throttling import AnalyticsRateThrottle
from transactions.analytics.services import parse_and_validate_date_range
from .services import DashboardService
from .serializers import (
    FinancialDashboardResponseSerializer,
    DashboardFinancialSummarySerializer,
    RecentTransactionItemSerializer,
    BudgetOverviewSerializer,
    GoalOverviewSerializer,
    SpendingInsightsSerializer,
    DashboardAlertItemSerializer,
)


@extend_schema(
    tags=['Dashboard'],
    summary='Complete Financial Dashboard Overview',
    description='Returns fully aggregated financial dashboard payload including summary, income/expense overview, cash flow, recent transactions, budgets, goals, insights, top categories, monthly comparison, and alerts.',
    parameters=[
        OpenApiParameter(name='start_date', type=OpenApiTypes.DATE, description='Start date filter (YYYY-MM-DD)'),
        OpenApiParameter(name='end_date', type=OpenApiTypes.DATE, description='End date filter (YYYY-MM-DD)'),
        OpenApiParameter(name='limit', type=OpenApiTypes.INT, description='Limit recent transactions (default: 5, max: 50)'),
    ],
    responses={
        200: OpenApiResponse(response=FinancialDashboardResponseSerializer, description='Aggregated financial dashboard summary'),
        400: OpenApiResponse(description='Invalid date parameters or limits'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class DashboardAPIView(APIView):
    """
    Primary financial dashboard endpoint.
    Aggregates financial metrics into a single optimized response payload for frontend rendering.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnalyticsRateThrottle]

    def get(self, request, *args, **kwargs):
        start_date, end_date = parse_and_validate_date_range(request.query_params)
        recent_limit = request.query_params.get('limit') or 5
        top_cat_limit = request.query_params.get('top_categories_limit') or 5

        data = DashboardService.get_dashboard_summary(
            user=request.user,
            start_date=start_date,
            end_date=end_date,
            recent_limit=recent_limit,
            top_cat_limit=top_cat_limit
        )
        return Response(data, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Dashboard'],
    summary='Financial Dashboard Summary Metrics',
    description='Returns core financial totals: income, expenses, transaction-based balance, and net cash flow.',
    parameters=[
        OpenApiParameter(name='start_date', type=OpenApiTypes.DATE, description='Start date filter (YYYY-MM-DD)'),
        OpenApiParameter(name='end_date', type=OpenApiTypes.DATE, description='End date filter (YYYY-MM-DD)'),
    ],
    responses={
        200: OpenApiResponse(description='Financial summary metrics'),
        400: OpenApiResponse(description='Invalid date parameters'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class DashboardSummaryDetailAPIView(APIView):
    """
    Returns core financial dashboard summary totals and period comparison overview.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnalyticsRateThrottle]

    def get(self, request, *args, **kwargs):
        start_date, end_date = parse_and_validate_date_range(request.query_params)
        data = {
            'financial_summary': DashboardService.get_financial_summary(request.user, start_date, end_date),
            'income_expense_overview': DashboardService.get_income_expense_overview(request.user, start_date, end_date),
            'balance_summary': DashboardService.get_balance_summary(request.user),
        }
        return Response(data, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Dashboard'],
    summary='Dashboard Recent Transactions',
    description='Returns user recent transaction entries with category details.',
    parameters=[
        OpenApiParameter(name='limit', type=OpenApiTypes.INT, description='Number of recent transactions (default: 5, max: 50)'),
    ],
    responses={
        200: OpenApiResponse(response=RecentTransactionItemSerializer(many=True), description='Recent transaction entries array'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class DashboardRecentTransactionsAPIView(APIView):
    """
    Returns authenticated user's recent transactions.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnalyticsRateThrottle]

    def get(self, request, *args, **kwargs):
        limit = request.query_params.get('limit') or 5
        recent = DashboardService.get_recent_transactions(request.user, limit=limit)
        return Response(recent, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Dashboard'],
    summary='Dashboard Budget Overview',
    description='Returns active budget status, exceeded counts, utilization rates, and remaining amounts.',
    responses={
        200: OpenApiResponse(response=BudgetOverviewSerializer, description='Budget overview summary'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class DashboardBudgetsAPIView(APIView):
    """
    Returns budget status overview for dashboard widgets.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnalyticsRateThrottle]

    def get(self, request, *args, **kwargs):
        data = DashboardService.get_budget_overview(request.user)
        return Response(data, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Dashboard'],
    summary='Dashboard Goal Overview',
    description='Returns financial goal completion metrics, overall savings progress, and near-completion goals.',
    responses={
        200: OpenApiResponse(response=GoalOverviewSerializer, description='Goal overview summary'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class DashboardGoalsAPIView(APIView):
    """
    Returns financial goals overview for dashboard widgets.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnalyticsRateThrottle]

    def get(self, request, *args, **kwargs):
        data = DashboardService.get_goal_overview(request.user)
        return Response(data, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Dashboard'],
    summary='Dashboard Spending Insights & Top Categories',
    description='Returns highest spending category, largest expense, average expense, and top spending categories breakdown.',
    parameters=[
        OpenApiParameter(name='start_date', type=OpenApiTypes.DATE, description='Start date filter (YYYY-MM-DD)'),
        OpenApiParameter(name='end_date', type=OpenApiTypes.DATE, description='End date filter (YYYY-MM-DD)'),
        OpenApiParameter(name='limit', type=OpenApiTypes.INT, description='Limit top categories (default: 5, max: 20)'),
    ],
    responses={
        200: OpenApiResponse(description='Spending insights dataset'),
        400: OpenApiResponse(description='Invalid date parameters'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class DashboardInsightsAPIView(APIView):
    """
    Returns structured spending insights and top spending categories dataset.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnalyticsRateThrottle]

    def get(self, request, *args, **kwargs):
        start_date, end_date = parse_and_validate_date_range(request.query_params)
        limit = request.query_params.get('limit') or 5
        data = {
            'spending_insights': DashboardService.get_spending_insights(request.user, start_date, end_date),
            'top_categories': DashboardService.get_top_categories(request.user, limit=limit, start_date=start_date, end_date=end_date),
        }
        return Response(data, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Dashboard'],
    summary='Dashboard Financial Alerts',
    description='Returns active financial system warnings, budget alerts, goal completion alerts, subscription limits, and due recurring schedules.',
    responses={
        200: OpenApiResponse(response=DashboardAlertItemSerializer(many=True), description='Dashboard financial alerts array'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class DashboardAlertsAPIView(APIView):
    """
    Returns active dashboard financial alerts.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnalyticsRateThrottle]

    def get(self, request, *args, **kwargs):
        alerts = DashboardService.get_dashboard_alerts(request.user)
        return Response(alerts, status=status.HTTP_200_OK)
