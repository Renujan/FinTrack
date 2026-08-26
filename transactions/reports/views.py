from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, OpenApiResponse

from finance_tracker.throttling import AnalyticsRateThrottle
from .serializers import ReportQueryFilterSerializer
from .services import ReportService


@extend_schema(
    tags=['Financial Reports'],
    summary='Income Report',
    description='Returns total income, transaction count, average income, minimum income, and maximum income for the user.',
    parameters=[
        OpenApiParameter(name='start_date', type=OpenApiTypes.DATE, description='Start date filter (YYYY-MM-DD)'),
        OpenApiParameter(name='end_date', type=OpenApiTypes.DATE, description='End date filter (YYYY-MM-DD)'),
    ],
    responses={
        200: OpenApiResponse(description='Income report JSON object'),
        400: OpenApiResponse(description='Invalid date parameters'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class IncomeReportAPIView(APIView):
    """
    GET /api/reports/income/
    Read-only endpoint returning income summary statistics for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnalyticsRateThrottle]

    def get(self, request, *args, **kwargs):
        serializer = ReportQueryFilterSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        report = ReportService.get_income_report(
            user=request.user,
            start_date=serializer.validated_data.get('start_date'),
            end_date=serializer.validated_data.get('end_date')
        )
        return Response(report, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Financial Reports'],
    summary='Expense Report',
    description='Returns total expenses, transaction count, average expense, minimum, and maximum expense with optional category and search filters.',
    parameters=[
        OpenApiParameter(name='start_date', type=OpenApiTypes.DATE, description='Start date filter (YYYY-MM-DD)'),
        OpenApiParameter(name='end_date', type=OpenApiTypes.DATE, description='End date filter (YYYY-MM-DD)'),
        OpenApiParameter(name='category', type=OpenApiTypes.STR, description='Category ID or name filter'),
        OpenApiParameter(name='search', type=OpenApiTypes.STR, description='Search filter for description or category'),
    ],
    responses={
        200: OpenApiResponse(description='Expense report JSON object'),
        400: OpenApiResponse(description='Invalid parameters'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class ExpenseReportAPIView(APIView):
    """
    GET /api/reports/expenses/
    Read-only endpoint returning expense summary statistics for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnalyticsRateThrottle]

    def get(self, request, *args, **kwargs):
        serializer = ReportQueryFilterSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        report = ReportService.get_expense_report(
            user=request.user,
            start_date=serializer.validated_data.get('start_date'),
            end_date=serializer.validated_data.get('end_date'),
            category=serializer.validated_data.get('category'),
            search=serializer.validated_data.get('search')
        )
        return Response(report, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Financial Reports'],
    summary='Cash Flow Report',
    description='Returns total income, total expenses, net cash flow, and calculated savings rate.',
    parameters=[
        OpenApiParameter(name='start_date', type=OpenApiTypes.DATE, description='Start date filter (YYYY-MM-DD)'),
        OpenApiParameter(name='end_date', type=OpenApiTypes.DATE, description='End date filter (YYYY-MM-DD)'),
    ],
    responses={
        200: OpenApiResponse(description='Cash flow report JSON object'),
        400: OpenApiResponse(description='Invalid date parameters'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class CashFlowReportAPIView(APIView):
    """
    GET /api/reports/cash-flow/
    Read-only endpoint returning cash flow summary and savings rate for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnalyticsRateThrottle]

    def get(self, request, *args, **kwargs):
        serializer = ReportQueryFilterSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        report = ReportService.get_cash_flow_report(
            user=request.user,
            start_date=serializer.validated_data.get('start_date'),
            end_date=serializer.validated_data.get('end_date')
        )
        return Response(report, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Financial Reports'],
    summary='Category Spending Report',
    description='Returns expense breakdown per category with totals, percentage of overall expenses, and transaction count.',
    parameters=[
        OpenApiParameter(name='start_date', type=OpenApiTypes.DATE, description='Start date filter (YYYY-MM-DD)'),
        OpenApiParameter(name='end_date', type=OpenApiTypes.DATE, description='End date filter (YYYY-MM-DD)'),
        OpenApiParameter(name='category', type=OpenApiTypes.STR, description='Category ID or name filter'),
    ],
    responses={
        200: OpenApiResponse(description='Category spending report JSON object'),
        400: OpenApiResponse(description='Invalid date parameters'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class CategoryReportAPIView(APIView):
    """
    GET /api/reports/categories/
    Read-only endpoint returning category expense breakdown for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnalyticsRateThrottle]

    def get(self, request, *args, **kwargs):
        serializer = ReportQueryFilterSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        report = ReportService.get_category_report(
            user=request.user,
            start_date=serializer.validated_data.get('start_date'),
            end_date=serializer.validated_data.get('end_date'),
            category=serializer.validated_data.get('category')
        )
        return Response(report, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Financial Reports'],
    summary='Monthly Financial Report',
    description='Returns month-by-month financial summary including income, expenses, net balance, and transaction count.',
    parameters=[
        OpenApiParameter(name='start_date', type=OpenApiTypes.DATE, description='Start date filter (YYYY-MM-DD)'),
        OpenApiParameter(name='end_date', type=OpenApiTypes.DATE, description='End date filter (YYYY-MM-DD)'),
    ],
    responses={
        200: OpenApiResponse(description='Monthly report JSON object'),
        400: OpenApiResponse(description='Invalid date parameters'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class MonthlyReportAPIView(APIView):
    """
    GET /api/reports/monthly/
    Read-only endpoint returning monthly aggregated financial records for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnalyticsRateThrottle]

    def get(self, request, *args, **kwargs):
        serializer = ReportQueryFilterSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        report = ReportService.get_monthly_report(
            user=request.user,
            start_date=serializer.validated_data.get('start_date'),
            end_date=serializer.validated_data.get('end_date')
        )
        return Response(report, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Financial Reports'],
    summary='Spending Trends Report',
    description='Returns spending trends aggregated by daily, weekly, or monthly intervals.',
    parameters=[
        OpenApiParameter(name='start_date', type=OpenApiTypes.DATE, description='Start date filter (YYYY-MM-DD)'),
        OpenApiParameter(name='end_date', type=OpenApiTypes.DATE, description='End date filter (YYYY-MM-DD)'),
        OpenApiParameter(name='period', type=OpenApiTypes.STR, enum=['daily', 'weekly', 'monthly'], description='Aggregation interval (default: monthly)'),
    ],
    responses={
        200: OpenApiResponse(description='Spending trends report JSON object'),
        400: OpenApiResponse(description='Invalid parameters'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class SpendingTrendsReportAPIView(APIView):
    """
    GET /api/reports/trends/
    Read-only endpoint returning financial trends aggregated by period (daily, weekly, monthly) for the user.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnalyticsRateThrottle]

    def get(self, request, *args, **kwargs):
        serializer = ReportQueryFilterSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        period_val = serializer.validated_data.get('group_by') or serializer.validated_data.get('period') or 'monthly'

        report = ReportService.get_spending_trends(
            user=request.user,
            start_date=serializer.validated_data.get('start_date'),
            end_date=serializer.validated_data.get('end_date'),
            group_by=period_val
        )
        return Response(report, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Financial Reports'],
    summary='Budget vs Actual Report',
    description='Returns budget comparison report showing target amount, actual spent, remaining balance, percentage used, and exceeded state.',
    parameters=[
        OpenApiParameter(name='start_date', type=OpenApiTypes.DATE, description='Start date filter (YYYY-MM-DD)'),
        OpenApiParameter(name='end_date', type=OpenApiTypes.DATE, description='End date filter (YYYY-MM-DD)'),
    ],
    responses={
        200: OpenApiResponse(description='Budget vs actual report JSON object'),
        400: OpenApiResponse(description='Invalid parameters'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class BudgetComparisonReportAPIView(APIView):
    """
    GET /api/reports/budgets/
    Read-only endpoint returning budget vs actual performance comparison for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnalyticsRateThrottle]

    def get(self, request, *args, **kwargs):
        serializer = ReportQueryFilterSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        report = ReportService.get_budget_comparison(
            user=request.user,
            start_date=serializer.validated_data.get('start_date'),
            end_date=serializer.validated_data.get('end_date')
        )
        return Response(report, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Financial Reports'],
    summary='Top Spending Categories Report',
    description='Returns top expense categories by amount spent (default top 5, customizable limit up to 100).',
    parameters=[
        OpenApiParameter(name='start_date', type=OpenApiTypes.DATE, description='Start date filter (YYYY-MM-DD)'),
        OpenApiParameter(name='end_date', type=OpenApiTypes.DATE, description='End date filter (YYYY-MM-DD)'),
        OpenApiParameter(name='limit', type=OpenApiTypes.INT, description='Maximum number of categories (1-100, default: 5)'),
    ],
    responses={
        200: OpenApiResponse(description='Top categories report JSON object'),
        400: OpenApiResponse(description='Invalid parameters'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class TopCategoriesReportAPIView(APIView):
    """
    GET /api/reports/top-categories/
    Read-only endpoint returning top spending categories for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnalyticsRateThrottle]

    def get(self, request, *args, **kwargs):
        serializer = ReportQueryFilterSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        limit_val = serializer.validated_data.get('limit', 5)

        report = ReportService.get_top_categories(
            user=request.user,
            start_date=serializer.validated_data.get('start_date'),
            end_date=serializer.validated_data.get('end_date'),
            limit=limit_val
        )
        return Response(report, status=status.HTTP_200_OK)
