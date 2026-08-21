from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .serializers import ReportDateRangeSerializer, TransactionImportFileUploadSerializer
from .services import DataExportService, FinancialReportService, TransactionImportService


class TransactionExportAPIView(APIView):
    """
    GET /api/export/transactions/
    Exports authenticated user's financial data (transactions, categories, budgets, goals, recurring) as CSV.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return DataExportService.export_transactions_csv(request.user, request.query_params)


class CategoryExportAPIView(APIView):
    """
    GET /api/export/categories/
    Exports authenticated user's category list as CSV file.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return DataExportService.export_categories_csv(request.user)


class BudgetExportAPIView(APIView):
    """
    GET /api/export/budgets/
    Exports authenticated user's budgets as CSV file.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return DataExportService.export_budgets_csv(request.user)


class FinancialGoalExportAPIView(APIView):
    """
    GET /api/export/goals/
    Exports authenticated user's financial goals as CSV file.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return DataExportService.export_goals_csv(request.user)


class RecurringTransactionExportAPIView(APIView):
    """
    GET /api/export/recurring/
    Exports authenticated user's recurring transaction schedules as CSV file.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return DataExportService.export_recurring_csv(request.user)


class FinancialReportAPIView(APIView):
    """
    GET /api/reports/financial/
    Generates a unified financial report for the authenticated user,
    including income, expenses, net balance, category breakdown, monthly totals,
    budget utilization, and goal metrics. Supports start_date and end_date.
    """
    permission_classes = [permissions.IsAuthenticated]

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


class TransactionImportAPIView(APIView):
    """
    POST /api/import/transactions/
    Imports transaction records from an uploaded CSV file for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        # Extract uploaded file from request.FILES or request.data
        file_obj = request.FILES.get('file') or request.FILES.get('csv_file')
        if not file_obj and 'file' in request.data:
            file_obj = request.data['file']

        upload_serializer = TransactionImportFileUploadSerializer(data={'file': file_obj})
        upload_serializer.is_valid(raise_exception=True)

        result = TransactionImportService.import_transactions_csv(
            user=request.user,
            file_obj=upload_serializer.validated_data['file']
        )

        status_code = status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST
        return Response(result, status=status_code)
