from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, OpenApiResponse

from finance_tracker.throttling import AnalyticsRateThrottle
from transactions.audit_services import AuditLogService
from .services import FinancialAnalyticsService, parse_and_validate_analytics_filters, parse_and_validate_date_range
from .serializers import (
    SummaryAnalyticsSerializer,
    IncomeExpenseAnalyticsSerializer,
    CategoryAnalyticsItemSerializer,
    IncomeCategoryAnalyticsItemSerializer,
    DailyTrendItemSerializer,
    MonthlyTrendItemSerializer,
    TrendItemSerializer,
    PeriodComparisonSerializer,
    BudgetAnalyticsSerializer,
    RecentTransactionAnalyticsSerializer,
)


common_analytics_parameters = [
    OpenApiParameter(name='start_date', type=OpenApiTypes.DATE, description='Start date filter (YYYY-MM-DD)'),
    OpenApiParameter(name='end_date', type=OpenApiTypes.DATE, description='End date filter (YYYY-MM-DD)'),
    OpenApiParameter(name='category', type=OpenApiTypes.STR, description='Filter by category ID or name'),
    OpenApiParameter(name='transaction_type', type=OpenApiTypes.STR, enum=['INCOME', 'EXPENSE'], description='Filter by transaction type'),
]


@extend_schema(
    tags=['Analytics'],
    summary='Dashboard Summary Metrics',
    description='Returns overall total income, total expenses, net balance, savings rate, and transaction count for the authenticated user.',
    parameters=common_analytics_parameters,
    responses={
        200: OpenApiResponse(response=SummaryAnalyticsSerializer, description='Dashboard summary metrics'),
        400: OpenApiResponse(description='Invalid filter parameters'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class DashboardSummaryAPIView(APIView):
    """
    Returns financial dashboard summary metrics for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnalyticsRateThrottle]

    def get(self, request, *args, **kwargs):
        start_date, end_date, category, transaction_type, _ = parse_and_validate_analytics_filters(request.query_params)
        summary = FinancialAnalyticsService.get_summary(
            user=request.user,
            start_date=start_date,
            end_date=end_date,
            category=category,
            transaction_type=transaction_type
        )
        AuditLogService.log_analytics_viewed(request.user, metadata={'endpoint': 'summary'}, request=request)
        return Response(summary, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Analytics'],
    summary='Income & Expense Analytics',
    description='Returns income, expenses, net balance, savings rate, and transaction counts for selected date range and filters.',
    parameters=common_analytics_parameters,
    responses={
        200: OpenApiResponse(response=IncomeExpenseAnalyticsSerializer, description='Income and expense totals'),
        400: OpenApiResponse(description='Invalid filter parameters'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class IncomeExpenseAnalyticsAPIView(APIView):
    """
    Returns income and expense totals for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnalyticsRateThrottle]

    def get(self, request, *args, **kwargs):
        start_date, end_date, category, transaction_type, _ = parse_and_validate_analytics_filters(request.query_params)
        data = FinancialAnalyticsService.get_income_expense_totals(
            user=request.user,
            start_date=start_date,
            end_date=end_date,
            category=category,
            transaction_type=transaction_type
        )
        AuditLogService.log_analytics_viewed(request.user, metadata={'endpoint': 'income-expenses'}, request=request)
        return Response(data, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Analytics'],
    summary='Category Spending Analytics',
    description='Returns spending breakdown by category for expense transactions including amounts, percentages, and transaction counts.',
    parameters=common_analytics_parameters + [
        OpenApiParameter(name='limit', type=OpenApiTypes.INT, description='Limit top N categories (1-100)'),
    ],
    responses={
        200: OpenApiResponse(response=CategoryAnalyticsItemSerializer(many=True), description='Category spending breakdown'),
        400: OpenApiResponse(description='Invalid filter parameters'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class CategoryAnalyticsAPIView(APIView):
    """
    Returns spending breakdown by category for expense transactions.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnalyticsRateThrottle]

    def get(self, request, *args, **kwargs):
        start_date, end_date, category, _, limit = parse_and_validate_analytics_filters(request.query_params)
        categories = FinancialAnalyticsService.get_category_breakdown(
            user=request.user,
            start_date=start_date,
            end_date=end_date,
            category=category,
            limit=limit
        )
        AuditLogService.log_analytics_viewed(request.user, metadata={'endpoint': 'categories'}, request=request)
        return Response(categories, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Analytics'],
    summary='Income Category Analytics',
    description='Returns income breakdown by category for income transactions including amounts, percentages, and transaction counts.',
    parameters=common_analytics_parameters + [
        OpenApiParameter(name='limit', type=OpenApiTypes.INT, description='Limit top N categories (1-100)'),
    ],
    responses={
        200: OpenApiResponse(response=IncomeCategoryAnalyticsItemSerializer(many=True), description='Income category breakdown'),
        400: OpenApiResponse(description='Invalid filter parameters'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class IncomeCategoryAnalyticsAPIView(APIView):
    """
    Returns income breakdown by category for income transactions.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnalyticsRateThrottle]

    def get(self, request, *args, **kwargs):
        start_date, end_date, category, _, limit = parse_and_validate_analytics_filters(request.query_params)
        income_categories = FinancialAnalyticsService.get_income_breakdown(
            user=request.user,
            start_date=start_date,
            end_date=end_date,
            category=category,
            limit=limit
        )
        AuditLogService.log_analytics_viewed(request.user, metadata={'endpoint': 'income-categories'}, request=request)
        return Response(income_categories, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Analytics'],
    summary='Daily Financial Trends',
    description='Returns daily aggregated income, expense, and net balance trends for historical analysis.',
    parameters=common_analytics_parameters,
    responses={
        200: OpenApiResponse(response=DailyTrendItemSerializer(many=True), description='Daily trend metrics'),
        400: OpenApiResponse(description='Invalid filter parameters'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class DailyTrendsAPIView(APIView):
    """
    Returns daily financial trends aggregated using database Date truncation.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnalyticsRateThrottle]

    def get(self, request, *args, **kwargs):
        start_date, end_date, category, _, _ = parse_and_validate_analytics_filters(request.query_params)
        daily = FinancialAnalyticsService.get_daily_trends(
            user=request.user,
            start_date=start_date,
            end_date=end_date,
            category=category
        )
        AuditLogService.log_analytics_viewed(request.user, metadata={'endpoint': 'daily'}, request=request)
        return Response(daily, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Analytics'],
    summary='Monthly Financial Trends',
    description='Returns monthly aggregated income, expense, and net balance trends across year boundaries.',
    parameters=common_analytics_parameters,
    responses={
        200: OpenApiResponse(response=MonthlyTrendItemSerializer(many=True), description='Monthly trend metrics'),
        400: OpenApiResponse(description='Invalid filter parameters'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class MonthlyTrendsAPIView(APIView):
    """
    Returns monthly financial trends aggregated across year boundaries.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnalyticsRateThrottle]

    def get(self, request, *args, **kwargs):
        start_date, end_date, category, _, _ = parse_and_validate_analytics_filters(request.query_params)
        monthly = FinancialAnalyticsService.get_monthly_trends(
            user=request.user,
            start_date=start_date,
            end_date=end_date,
            category=category
        )
        AuditLogService.log_analytics_viewed(request.user, metadata={'endpoint': 'monthly'}, request=request)
        return Response(monthly, status=status.HTTP_200_OK)


MonthlySummaryAPIView = MonthlyTrendsAPIView


@extend_schema(
    tags=['Analytics'],
    summary='Financial Trends Aggregation',
    description='Returns income, expense, and net balance trends grouped by daily, weekly, or monthly granularity.',
    parameters=common_analytics_parameters + [
        OpenApiParameter(name='group_by', type=OpenApiTypes.STR, enum=['daily', 'weekly', 'monthly'], description='Grouping granularity'),
    ],
    responses={
        200: OpenApiResponse(response=TrendItemSerializer(many=True), description='Financial trends array'),
        400: OpenApiResponse(description='Invalid parameters'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class FinancialTrendsAPIView(APIView):
    """
    Returns income, expense, and net balance trend data grouped by period (daily, weekly, monthly).
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnalyticsRateThrottle]

    def get(self, request, *args, **kwargs):
        start_date, end_date, category, _, _ = parse_and_validate_analytics_filters(request.query_params)
        group_by = request.query_params.get('group_by') or request.query_params.get('period') or 'monthly'
        trends = FinancialAnalyticsService.get_trends(
            user=request.user,
            start_date=start_date,
            end_date=end_date,
            group_by=group_by,
            category=category
        )
        AuditLogService.log_analytics_viewed(request.user, metadata={'endpoint': 'trends'}, request=request)
        return Response(trends, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Analytics'],
    summary='Budget Performance Analytics',
    description='Returns budget progress, spent amounts, remaining limits, percentage used, and exceed status by integrating BudgetCalculationService.',
    parameters=[
        OpenApiParameter(name='start_date', type=OpenApiTypes.DATE, description='Start date filter (YYYY-MM-DD)'),
        OpenApiParameter(name='end_date', type=OpenApiTypes.DATE, description='End date filter (YYYY-MM-DD)'),
    ],
    responses={
        200: OpenApiResponse(response=BudgetAnalyticsSerializer, description='Budget performance report'),
        400: OpenApiResponse(description='Invalid parameters'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class BudgetPerformanceAPIView(APIView):
    """
    Returns budget performance analytics integrating Day 7 budget calculations.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnalyticsRateThrottle]

    def get(self, request, *args, **kwargs):
        start_date, end_date, _, _, _ = parse_and_validate_analytics_filters(request.query_params)
        budgets = FinancialAnalyticsService.get_budget_performance(
            user=request.user,
            start_date=start_date,
            end_date=end_date
        )
        AuditLogService.log_analytics_viewed(request.user, metadata={'endpoint': 'budget-performance'}, request=request)
        return Response(budgets, status=status.HTTP_200_OK)


BudgetAnalyticsAPIView = BudgetPerformanceAPIView


@extend_schema(
    tags=['Analytics'],
    summary='Top Spending Categories',
    description='Returns highest spending expense categories up to requested limit.',
    parameters=common_analytics_parameters + [
        OpenApiParameter(name='limit', type=OpenApiTypes.INT, description='Limit top N categories (default: 5, max: 100)'),
    ],
    responses={
        200: OpenApiResponse(response=CategoryAnalyticsItemSerializer(many=True), description='Top spending categories breakdown'),
        400: OpenApiResponse(description='Invalid limit parameter'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class TopCategoriesAnalyticsAPIView(APIView):
    """
    Returns top spending categories for expense transactions.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnalyticsRateThrottle]

    def get(self, request, *args, **kwargs):
        start_date, end_date, category, _, limit = parse_and_validate_analytics_filters(request.query_params)
        limit = limit or 5
        top_categories = FinancialAnalyticsService.get_top_categories(
            user=request.user,
            limit=limit,
            start_date=start_date,
            end_date=end_date
        )
        AuditLogService.log_analytics_viewed(request.user, metadata={'endpoint': 'top-categories'}, request=request)
        return Response(top_categories, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Analytics'],
    summary='Recent Dashboard Transactions',
    description='Returns a limited list of authenticated user recent transactions.',
    parameters=[
        OpenApiParameter(name='limit', type=OpenApiTypes.INT, description='Number of recent transactions (default: 5, max: 100)'),
    ],
    responses={
        200: OpenApiResponse(response=RecentTransactionAnalyticsSerializer(many=True), description='Recent transaction list'),
        400: OpenApiResponse(description='Invalid limit parameter'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class RecentTransactionsAnalyticsAPIView(APIView):
    """
    Returns authenticated user's recent transactions.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnalyticsRateThrottle]

    def get(self, request, *args, **kwargs):
        _, _, _, _, limit = parse_and_validate_analytics_filters(request.query_params)
        limit = limit or 5
        recent = FinancialAnalyticsService.get_recent_transactions(request.user, limit=limit)
        AuditLogService.log_analytics_viewed(request.user, metadata={'endpoint': 'recent-transactions'}, request=request)
        return Response(recent, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Analytics'],
    summary='Period Comparison Analysis',
    description='Compares income, expense, and net savings between the selected period and the preceding equal period.',
    parameters=[
        OpenApiParameter(name='start_date', type=OpenApiTypes.DATE, description='Start date filter (YYYY-MM-DD)'),
        OpenApiParameter(name='end_date', type=OpenApiTypes.DATE, description='End date filter (YYYY-MM-DD)'),
    ],
    responses={
        200: OpenApiResponse(response=PeriodComparisonSerializer, description='Period comparison metrics'),
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
        comparison = FinancialAnalyticsService.get_period_comparison(request.user, start_date, end_date)
        AuditLogService.log_analytics_viewed(request.user, metadata={'endpoint': 'comparison'}, request=request)
        return Response(comparison, status=status.HTTP_200_OK)
