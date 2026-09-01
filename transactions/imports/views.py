from django.shortcuts import get_object_or_404
from rest_framework import status, permissions, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, OpenApiResponse, inline_serializer

from finance_tracker.throttling import ImportExportRateThrottle
from transactions.pagination import StandardResultsSetPagination
from transactions.models import DataImport
from transactions.audit_services import AuditLogService
from .serializers import (
    DataImportFileUploadSerializer,
    DataImportExecuteSerializer,
    DataImportSerializer,
)
from .services import DataImportService


@extend_schema(
    tags=['Financial Data Import'],
    summary='Upload & Preview Financial CSV Import',
    description='Accepts a CSV transaction file upload, validates headers and rows, performs category matching and duplicate detection, and returns a preview summary without creating transactions.',
    request=DataImportFileUploadSerializer,
    responses={
        200: inline_serializer(
            name='DataImportPreviewSuccessResponse',
            fields={
                'id': serializers.IntegerField(),
                'file_name': serializers.CharField(),
                'status': serializers.CharField(),
                'total_rows': serializers.IntegerField(),
                'valid_rows': serializers.IntegerField(),
                'invalid_rows': serializers.IntegerField(),
                'duplicate_rows': serializers.IntegerField(),
                'unmatched_categories': serializers.ListField(child=serializers.CharField()),
                'errors': serializers.ListField(child=serializers.DictField()),
                'preview_rows': serializers.ListField(child=serializers.DictField()),
            }
        ),
        400: OpenApiResponse(description='CSV file validation error'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class DataImportPreviewAPIView(APIView):
    """
    POST /api/imports/preview/
    Uploads a CSV file, parses data, validates headers and rows, identifies unmatched categories
    and duplicate rows, and creates a DataImport record in PREVIEW_READY status.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ImportExportRateThrottle]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file') or request.FILES.get('csv_file')
        if not file_obj and 'file' in request.data:
            file_obj = request.data['file']

        serializer = DataImportFileUploadSerializer(data={
            'file': file_obj,
            'create_missing_categories': request.data.get('create_missing_categories', False)
        })
        serializer.is_valid(raise_exception=True)

        result = DataImportService.generate_preview(
            user=request.user,
            file_obj=serializer.validated_data['file'],
            create_missing_categories=serializer.validated_data.get('create_missing_categories', False)
        )

        status_code = status.HTTP_200_OK if result.get('status') != 'FAILED' else status.HTTP_400_BAD_REQUEST
        return Response(result, status=status_code)


@extend_schema(
    tags=['Financial Data Import'],
    summary='Execute Financial CSV Import',
    description='Executes transaction creation for a previously previewed CSV import record. Creates valid transactions atomically while skipping duplicate/invalid rows.',
    request=DataImportExecuteSerializer,
    responses={
        200: inline_serializer(
            name='DataImportExecuteSuccessResponse',
            fields={
                'id': serializers.IntegerField(),
                'file_name': serializers.CharField(),
                'status': serializers.CharField(),
                'total_rows': serializers.IntegerField(),
                'successful_rows': serializers.IntegerField(),
                'failed_rows': serializers.IntegerField(),
                'skipped_rows': serializers.IntegerField(),
                'duplicate_rows': serializers.IntegerField(),
                'created_at': serializers.DateTimeField(),
                'completed_at': serializers.DateTimeField(),
                'error_summary': serializers.ListField(child=serializers.DictField()),
            }
        ),
        400: OpenApiResponse(description='Import execution error or already completed'),
        401: OpenApiResponse(description='Authentication required'),
        404: OpenApiResponse(description='Import record not found'),
    }
)
class DataImportExecuteAPIView(APIView):
    """
    POST /api/imports/<id>/execute/
    Executes an import record, creating transaction entries in the user dataset.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ImportExportRateThrottle]

    def post(self, request, pk, *args, **kwargs):
        serializer = DataImportExecuteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = DataImportService.execute_import(
            import_id=pk,
            user=request.user,
            options=serializer.validated_data
        )

        return Response(result, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Financial Data Import'],
    summary='List Data Imports History',
    description='Retrieves a paginated list of financial CSV import operations belonging to the authenticated user.',
    parameters=[
        OpenApiParameter(name='status', type=OpenApiTypes.STR, description='Filter by status (PREVIEW_READY, COMPLETED, FAILED, PENDING)'),
        OpenApiParameter(name='page', type=OpenApiTypes.INT, description='Page number'),
        OpenApiParameter(name='page_size', type=OpenApiTypes.INT, description='Page size'),
    ],
    responses={
        200: DataImportSerializer(many=True),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class DataImportListAPIView(APIView):
    """
    GET /api/imports/
    Returns list of import history for authenticated user with pagination and filtering.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ImportExportRateThrottle]
    pagination_class = StandardResultsSetPagination

    def get(self, request, *args, **kwargs):
        queryset = DataImport.objects.filter(user=request.user).order_by('-created_at')

        status_param = request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status__iexact=status_param.strip())

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        if page is not None:
            serializer = DataImportSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = DataImportSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Financial Data Import'],
    summary='Get Data Import Detail',
    description='Retrieves details, row statistics, and error summaries for a specific import record.',
    responses={
        200: DataImportSerializer,
        401: OpenApiResponse(description='Authentication required'),
        404: OpenApiResponse(description='Import record not found'),
    }
)
class DataImportDetailAPIView(APIView):
    """
    GET /api/imports/<id>/
    Retrieves detail of a specific import operation for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ImportExportRateThrottle]

    def get_object(self, pk, user):
        """
        Enforce strict user isolation: prevent cross-user IDOR access.
        """
        return get_object_or_404(DataImport, pk=pk, user=user)

    def get(self, request, pk, *args, **kwargs):
        import_obj = self.get_object(pk, request.user)
        serializer = DataImportSerializer(import_obj)
        data = dict(serializer.data)
        # Standardize error summary payload formatting for frontend consumption
        if 'error_summary' in data and isinstance(data['error_summary'], list):
            data['error_count'] = len(data['error_summary'])
        return Response(data, status=status.HTTP_200_OK)

    def delete(self, request, pk, *args, **kwargs):
        """
        DELETE /api/imports/<id>/
        Deletes a data import record and its uploaded CSV file.
        """
        import_obj = self.get_object(pk, request.user)
        import_id = import_obj.id
        file_name = import_obj.file_name

        if import_obj.file:
            try:
                import_obj.file.delete(save=False)
            except Exception:
                pass

        import_obj.delete()

        AuditLogService.log_action(
            user=request.user,
            action='DATA_IMPORT_DELETED',
            resource_type='DataImport',
            resource_id=str(import_id),
            metadata={'file_name': file_name}
        )

        return Response({'message': 'Data import record deleted successfully.'}, status=status.HTTP_200_OK)

