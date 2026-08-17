from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .services import AnalyticsService, parse_and_validate_date_range


class DashboardSummaryAPIView(APIView):
    """
    Returns an overall financial summary for the authenticated user.
    Supports optional date filtering via start_date and end_date.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        start_date, end_date = parse_and_validate_date_range(request.query_params)
        summary = AnalyticsService.get_summary(request.user, start_date, end_date)
        return Response(summary, status=status.HTTP_200_OK)


class FinancialTrendsAPIView(APIView):
    """
    Returns income, expense, and net balance trend data grouped by period (daily, weekly, monthly).
    Supports optional start_date, end_date, and group_by parameters.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        start_date, end_date = parse_and_validate_date_range(request.query_params)
        group_by = request.query_params.get('group_by') or request.query_params.get('period') or 'monthly'
        trends = AnalyticsService.get_trends(request.user, start_date, end_date, group_by=group_by)
        return Response(trends, status=status.HTTP_200_OK)


class MonthlySummaryAPIView(APIView):
    """
    Returns financial summaries grouped chronologically by month.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        start_date, end_date = parse_and_validate_date_range(request.query_params)
        monthly = AnalyticsService.get_monthly_summary(request.user, start_date, end_date)
        return Response(monthly, status=status.HTTP_200_OK)


class CategoryAnalyticsAPIView(APIView):
    """
    Returns category spending breakdown for expense transactions.
    Supports limit parameter for top spending categories.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        start_date, end_date = parse_and_validate_date_range(request.query_params)
        limit = request.query_params.get('limit')
        categories = AnalyticsService.get_category_analytics(request.user, start_date, end_date, limit=limit)
        return Response(categories, status=status.HTTP_200_OK)


class PeriodComparisonAPIView(APIView):
    """
    Compares financial metrics between selected period and previous period of equal length.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        start_date, end_date = parse_and_validate_date_range(request.query_params)
        comparison = AnalyticsService.get_period_comparison(request.user, start_date, end_date)
        return Response(comparison, status=status.HTTP_200_OK)


class BudgetAnalyticsAPIView(APIView):
    """
    Returns budget-related financial analytics integrating Day 7 budget calculation logic.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        start_date, end_date = parse_and_validate_date_range(request.query_params)
        budgets = AnalyticsService.get_budget_analytics(request.user, start_date, end_date)
        return Response(budgets, status=status.HTTP_200_OK)
