from rest_framework import status, permissions, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, OpenApiResponse, inline_serializer

from finance_tracker.throttling import ImportExportRateThrottle, AnalyticsRateThrottle
from transactions.audit_services import AuditLogService
from .serializers import ReportDateRangeSerializer, TransactionImportFileUploadSerializer
from .services import DataExportService, FinancialReportService, TransactionImportService


@extend_schema(
    tags=['Import & Export'],
    summary='Export Transactions CSV',
    description='Generates and streams a downloadable CSV file containing transactions filtered by optional parameters.',
    parameters=[
        OpenApiParameter(name='start_date', type=OpenApiTypes.DATE, description='Start date filter (YYYY-MM-DD)'),
        OpenApiParameter(name='end_date', type=OpenApiTypes.DATE, description='End date filter (YYYY-MM-DD)'),
        OpenApiParameter(name='category', type=OpenApiTypes.INT, description='Category ID filter'),
        OpenApiParameter(name='transaction_type', type=OpenApiTypes.STR, enum=['income', 'expense'], description='Transaction type filter'),
    ],
    responses={
        200: OpenApiResponse(description='CSV File Download (text/csv)'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class TransactionExportAPIView(APIView):
    """
    GET /api/export/transactions/
    Exports authenticated user's financial data (transactions, categories, budgets, goals, recurring) as CSV.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ImportExportRateThrottle]

    def get(self, request, *args, **kwargs):
        response_obj = DataExportService.export_transactions_csv(request.user, request.query_params)
        AuditLogService.log_export(request.user, 'Transaction', metadata={'export_format': 'csv'}, request=request)
        return response_obj


@extend_schema(
    tags=['Import & Export'],
    summary='Export Categories CSV',
    description='Exports a CSV file of all custom and system categories for the authenticated user.',
    responses={
        200: OpenApiResponse(description='CSV File Download (text/csv)'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class CategoryExportAPIView(APIView):
    """
    GET /api/export/categories/
    Exports authenticated user's category list as CSV file.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ImportExportRateThrottle]

    def get(self, request, *args, **kwargs):
        response_obj = DataExportService.export_categories_csv(request.user)
        AuditLogService.log_export(request.user, 'Category', metadata={'export_format': 'csv'}, request=request)
        return response_obj


@extend_schema(
    tags=['Import & Export'],
    summary='Export Budgets CSV',
    description='Exports a CSV file of all category budgets and progress metrics.',
    responses={
        200: OpenApiResponse(description='CSV File Download (text/csv)'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class BudgetExportAPIView(APIView):
    """
    GET /api/export/budgets/
    Exports authenticated user's budgets as CSV file.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ImportExportRateThrottle]

    def get(self, request, *args, **kwargs):
        response_obj = DataExportService.export_budgets_csv(request.user)
        AuditLogService.log_export(request.user, 'Budget', metadata={'export_format': 'csv'}, request=request)
        return response_obj


@extend_schema(
    tags=['Import & Export'],
    summary='Export Financial Goals CSV',
    description='Exports a CSV file of all financial goal targets and completion percentages.',
    responses={
        200: OpenApiResponse(description='CSV File Download (text/csv)'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class FinancialGoalExportAPIView(APIView):
    """
    GET /api/export/goals/
    Exports authenticated user's financial goals as CSV file.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ImportExportRateThrottle]

    def get(self, request, *args, **kwargs):
        response_obj = DataExportService.export_goals_csv(request.user)
        AuditLogService.log_export(request.user, 'Goal', metadata={'export_format': 'csv'}, request=request)
        return response_obj


@extend_schema(
    tags=['Import & Export'],
    summary='Export Recurring Schedules CSV',
    description='Exports a CSV file of all automated recurring transaction schedules.',
    responses={
        200: OpenApiResponse(description='CSV File Download (text/csv)'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class RecurringTransactionExportAPIView(APIView):
    """
    GET /api/export/recurring/
    Exports authenticated user's recurring transaction schedules as CSV file.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ImportExportRateThrottle]

    def get(self, request, *args, **kwargs):
        response_obj = DataExportService.export_recurring_csv(request.user)
        AuditLogService.log_export(request.user, 'RecurringTransaction', metadata={'export_format': 'csv'}, request=request)
        return response_obj


@extend_schema(
    tags=['Reports'],
    summary='Unified Financial Report',
    description='Generates a consolidated financial report including totals, category breakdown, monthly distribution, budgets, and goal progress.',
    parameters=[
        OpenApiParameter(name='start_date', type=OpenApiTypes.DATE, description='Start date filter (YYYY-MM-DD)'),
        OpenApiParameter(name='end_date', type=OpenApiTypes.DATE, description='End date filter (YYYY-MM-DD)'),
    ],
    responses={
        200: OpenApiResponse(description='Unified financial report JSON structure'),
        400: OpenApiResponse(description='Invalid date range parameters'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class FinancialReportAPIView(APIView):
    """
    GET /api/reports/financial/
    Generates a unified financial report for the authenticated user,
    including income, expenses, net balance, category breakdown, monthly totals,
    budget utilization, and goal metrics. Supports start_date and end_date.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnalyticsRateThrottle]

    def get(self, request, *args, **kwargs):
        serializer = ReportDateRangeSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        start_date = serializer.validated_data.get('start_date')
        end_date = serializer.validated_data.get('end_date')

        report_data = FinancialReportService.get_financial_report(
            user=request.user,
            start_date=start_date,
            end_date=end_date
        )

        return Response(report_data, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Import & Export'],
    summary='Bulk Import Transactions CSV',
    description='Accepts a multipart CSV file upload and imports transaction records into the user dataset with field validation.',
    request=TransactionImportFileUploadSerializer,
    responses={
        200: inline_serializer(
            name='TransactionImportSuccessResponse',
            fields={
                'success': serializers.BooleanField(default=True),
                'imported_count': serializers.IntegerField(),
                'errors': serializers.ListField(child=serializers.CharField(), default=[]),
            }
        ),
        400: OpenApiResponse(description='CSV parsing or row validation error'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class TransactionImportAPIView(APIView):
    """
    POST /api/import/transactions/
    Imports transaction records from an uploaded CSV file for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ImportExportRateThrottle]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file') or request.FILES.get('csv_file')
        if not file_obj and 'file' in request.data:
            file_obj = request.data['file']

        upload_serializer = TransactionImportFileUploadSerializer(data={'file': file_obj})
        upload_serializer.is_valid(raise_exception=True)

        result = TransactionImportService.import_transactions_csv(
            user=request.user,
            file_obj=upload_serializer.validated_data['file']
        )

        if result.get('success'):
            AuditLogService.log_import(
                user=request.user,
                resource_type='Transaction',
                metadata={'imported_count': result.get('imported_count', 0)},
                request=request
            )

        status_code = status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST
        return Response(result, status=status_code)

