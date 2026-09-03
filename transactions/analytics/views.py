from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, OpenApiResponse

from finance_tracker.throttling import AnalyticsRateThrottle
from transactions.audit_services import AuditLogService
from .services import FinancialAnalyticsService, parse_and_validate_analytics_filters
from .serializers import SummaryAnalyticsSerializer, IncomeExpenseAnalyticsSerializer, CategoryAnalyticsItemSerializer


@extend_schema(
    tags=['Analytics'],
    summary='Dashboard Summary Metrics',
    description='Returns overall total income, total expenses, net balance, savings rate, and transaction count for the authenticated user.',
    parameters=[
        OpenApiParameter(name='start_date', type=OpenApiTypes.DATE, description='Start date filter (YYYY-MM-DD)'),
        OpenApiParameter(name='end_date', type=OpenApiTypes.DATE, description='End date filter (YYYY-MM-DD)'),
    ],
    responses={
        200: OpenApiResponse(response=SummaryAnalyticsSerializer, description='Dashboard summary metrics'),
        400: OpenApiResponse(description='Invalid filter parameters'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class DashboardSummaryAPIView(APIView):
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
    parameters=[
        OpenApiParameter(name='start_date', type=OpenApiTypes.DATE, description='Start date filter (YYYY-MM-DD)'),
        OpenApiParameter(name='end_date', type=OpenApiTypes.DATE, description='End date filter (YYYY-MM-DD)'),
    ],
    responses={
        200: OpenApiResponse(response=IncomeExpenseAnalyticsSerializer, description='Income and expense totals'),
        400: OpenApiResponse(description='Invalid filter parameters'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class IncomeExpenseAnalyticsAPIView(APIView):
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
    parameters=[
        OpenApiParameter(name='start_date', type=OpenApiTypes.DATE, description='Start date filter (YYYY-MM-DD)'),
        OpenApiParameter(name='end_date', type=OpenApiTypes.DATE, description='End date filter (YYYY-MM-DD)'),
        OpenApiParameter(name='limit', type=OpenApiTypes.INT, description='Limit top N categories (1-100)'),
    ],
    responses={
        200: OpenApiResponse(response=CategoryAnalyticsItemSerializer(many=True), description='Category spending breakdown'),
        400: OpenApiResponse(description='Invalid filter parameters'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class CategoryAnalyticsAPIView(APIView):
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
