from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, OpenApiResponse
from finance_tracker.throttling import AnalyticsRateThrottle
from .services import AnalyticsService, parse_and_validate_date_range


@extend_schema(
    tags=['Analytics'],
    summary='Dashboard Overview Summary',
    description='Returns income, expense, net savings, and category distribution overview for the specified date range.',
    parameters=[
        OpenApiParameter(name='start_date', type=OpenApiTypes.DATE, description='Start date filter (YYYY-MM-DD)'),
        OpenApiParameter(name='end_date', type=OpenApiTypes.DATE, description='End date filter (YYYY-MM-DD)'),
    ],
    responses={
        200: OpenApiResponse(description='Dashboard summary metrics'),
        400: OpenApiResponse(description='Invalid date format or range'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class DashboardSummaryAPIView(APIView):
    """
    Returns an overall financial summary for the authenticated user.
    Supports optional date filtering via start_date and end_date.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnalyticsRateThrottle]

    def get(self, request, *args, **kwargs):
        start_date, end_date = parse_and_validate_date_range(request.query_params)
        summary = AnalyticsService.get_summary(request.user, start_date, end_date)
        return Response(summary, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Analytics'],
    summary='Financial Trends Aggregation',
    description='Returns time-series income, expense, and net balance trends grouped by daily, weekly, or monthly periods.',
    parameters=[
        OpenApiParameter(name='start_date', type=OpenApiTypes.DATE, description='Start date filter (YYYY-MM-DD)'),
        OpenApiParameter(name='end_date', type=OpenApiTypes.DATE, description='End date filter (YYYY-MM-DD)'),
        OpenApiParameter(name='group_by', type=OpenApiTypes.STR, enum=['daily', 'weekly', 'monthly'], description='Grouping granularity'),
    ],
    responses={
        200: OpenApiResponse(description='Financial trends array'),
        400: OpenApiResponse(description='Invalid parameters'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class FinancialTrendsAPIView(APIView):
    """
    Returns income, expense, and net balance trend data grouped by period (daily, weekly, monthly).
    Supports optional start_date, end_date, and group_by parameters.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnalyticsRateThrottle]

    def get(self, request, *args, **kwargs):
        start_date, end_date = parse_and_validate_date_range(request.query_params)
        group_by = request.query_params.get('group_by') or request.query_params.get('period') or 'monthly'
        trends = AnalyticsService.get_trends(request.user, start_date, end_date, group_by=group_by)
        return Response(trends, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Analytics'],
    summary='Monthly Chronological Summary',
    description='Returns monthly aggregated financial performance metrics for historical analysis.',
    parameters=[
        OpenApiParameter(name='start_date', type=OpenApiTypes.DATE, description='Start date filter (YYYY-MM-DD)'),
        OpenApiParameter(name='end_date', type=OpenApiTypes.DATE, description='End date filter (YYYY-MM-DD)'),
    ],
    responses={
        200: OpenApiResponse(description='Monthly summary dataset'),
        400: OpenApiResponse(description='Invalid date parameters'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class MonthlySummaryAPIView(APIView):
    """
    Returns financial summaries grouped chronologically by month.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnalyticsRateThrottle]

    def get(self, request, *args, **kwargs):
        start_date, end_date = parse_and_validate_date_range(request.query_params)
        monthly = AnalyticsService.get_monthly_summary(request.user, start_date, end_date)
        return Response(monthly, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Analytics'],
    summary='Category Spending Analytics',
    description='Returns percentage breakdown and total spending by category for expense transactions.',
    parameters=[
        OpenApiParameter(name='start_date', type=OpenApiTypes.DATE, description='Start date filter (YYYY-MM-DD)'),
        OpenApiParameter(name='end_date', type=OpenApiTypes.DATE, description='End date filter (YYYY-MM-DD)'),
        OpenApiParameter(name='limit', type=OpenApiTypes.INT, description='Limit top N categories'),
    ],
    responses={
        200: OpenApiResponse(description='Category analytics breakdown'),
        400: OpenApiResponse(description='Invalid parameters'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class CategoryAnalyticsAPIView(APIView):
    """
    Returns category spending breakdown for expense transactions.
    Supports limit parameter for top spending categories.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnalyticsRateThrottle]

    def get(self, request, *args, **kwargs):
        start_date, end_date = parse_and_validate_date_range(request.query_params)
        limit = request.query_params.get('limit')
        categories = AnalyticsService.get_category_analytics(request.user, start_date, end_date, limit=limit)
        return Response(categories, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Analytics'],
    summary='Period Comparison Analysis',
    description='Compares income, expense, and net savings between the selected period and the preceding equal period.',
    parameters=[
        OpenApiParameter(name='start_date', type=OpenApiTypes.DATE, description='Start date filter (YYYY-MM-DD)'),
        OpenApiParameter(name='end_date', type=OpenApiTypes.DATE, description='End date filter (YYYY-MM-DD)'),
    ],
    responses={
        200: OpenApiResponse(description='Period comparison metrics'),
        400: OpenApiResponse(description='Invalid parameters'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class PeriodComparisonAPIView(APIView):
    """
    Compares financial metrics between selected period and previous period of equal length.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnalyticsRateThrottle]

    def get(self, request, *args, **kwargs):
        start_date, end_date = parse_and_validate_date_range(request.query_params)
        comparison = AnalyticsService.get_period_comparison(request.user, start_date, end_date)
        return Response(comparison, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Analytics'],
    summary='Budget Progress & Utilization Analytics',
    description='Returns budget utilization rates, warning indicators, and remaining limits.',
    parameters=[
        OpenApiParameter(name='start_date', type=OpenApiTypes.DATE, description='Start date filter (YYYY-MM-DD)'),
        OpenApiParameter(name='end_date', type=OpenApiTypes.DATE, description='End date filter (YYYY-MM-DD)'),
    ],
    responses={
        200: OpenApiResponse(description='Budget analytics report'),
        400: OpenApiResponse(description='Invalid parameters'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class BudgetAnalyticsAPIView(APIView):
    """
    Returns budget-related financial analytics integrating Day 7 budget calculation logic.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnalyticsRateThrottle]

    def get(self, request, *args, **kwargs):
        start_date, end_date = parse_and_validate_date_range(request.query_params)
        budgets = AnalyticsService.get_budget_analytics(request.user, start_date, end_date)
        return Response(budgets, status=status.HTTP_200_OK)

