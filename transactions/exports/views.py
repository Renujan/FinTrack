import os
from django.http import HttpResponse, FileResponse, Http404
from django.utils import timezone
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListCreateAPIView, RetrieveDestroyAPIView
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, OpenApiResponse

from finance_tracker.throttling import ImportExportRateThrottle
from transactions.models import DataExport
from transactions.choices import ExportStatus, ExportFormat
from transactions.audit_services import AuditLogService
from transactions.exports.serializers import (
    DataExportCreateSerializer,
    DataExportListSerializer,
    DataExportDetailSerializer,
)
from transactions.exports.services import DataExportService


@extend_schema(
    tags=['Financial Data Export'],
    summary='List or Create Financial Data Exports',
    description='Retrieves export history for the authenticated user or requests a new financial data export (CSV/JSON).',
    responses={
        200: DataExportListSerializer(many=True),
        201: DataExportDetailSerializer,
        400: OpenApiResponse(description='Validation error'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class DataExportListCreateView(APIView):
    """
    GET  /api/exports/  - List authenticated user's data export history.
    POST /api/exports/  - Request a new data export operation.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ImportExportRateThrottle]

    def get(self, request, *args, **kwargs):
        qs = DataExport.objects.filter(user=request.user)

        # Filters
        export_type = request.query_params.get('export_type')
        fmt = request.query_params.get('format')
        export_status = request.query_params.get('status')

        if export_type:
            qs = qs.filter(export_type=export_type)
        if fmt:
            qs = qs.filter(format=fmt)
        if export_status:
            qs = qs.filter(status=export_status)

        # Ordering
        ordering = request.query_params.get('ordering', '-created_at')
        allowed_ordering = ['created_at', '-created_at', 'completed_at', '-completed_at', 'status', '-status', 'export_type', '-export_type']
        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)
        else:
            qs = qs.order_by('-created_at')

        serializer = DataExportListSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = DataExportCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        export_type = data.get('export_type')
        fmt = data.get('format')
        name = data.get('name')

        filters = {}
        if data.get('start_date'):
            filters['start_date'] = data['start_date'].isoformat()
        if data.get('end_date'):
            filters['end_date'] = data['end_date'].isoformat()
        if data.get('category'):
            filters['category'] = data['category']
        if data.get('transaction_type'):
            filters['transaction_type'] = data['transaction_type']

        export_obj = DataExportService.create_export(
            user=request.user,
            export_type=export_type,
            format=fmt,
            filters=filters,
            name=name,
            request=request
        )

        detail_serializer = DataExportDetailSerializer(export_obj, context={'request': request})
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=['Financial Data Export'],
    summary='Retrieve or Delete Financial Data Export',
    description='Fetches status/metadata for a specific data export or deletes it.',
    responses={
        200: DataExportDetailSerializer,
        204: OpenApiResponse(description='Data export deleted successfully'),
        404: OpenApiResponse(description='Export not found or access denied'),
    }
)
class DataExportDetailView(APIView):
    """
    GET    /api/exports/<id>/  - Get export status & metadata.
    DELETE /api/exports/<id>/  - Delete export record and file.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ImportExportRateThrottle]

    def get_object(self, pk, user):
        try:
            return DataExport.objects.get(pk=pk, user=user)
        except DataExport.DoesNotExist:
            raise Http404("Export record not found.")

    def get(self, request, pk, *args, **kwargs):
        export_obj = self.get_object(pk, request.user)
        serializer = DataExportDetailSerializer(export_obj, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk, *args, **kwargs):
        export_obj = self.get_object(pk, request.user)
        export_id = export_obj.id

        if export_obj.file:
            try:
                export_obj.file.delete(save=False)
            except Exception:
                pass

        export_obj.delete()
        AuditLogService.log_export_deleted(user=request.user, resource_id=export_id, request=request)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=['Financial Data Export'],
    summary='Download Financial Data Export File',
    description='Streams or downloads the generated export file (CSV or JSON) for a completed export operation.',
    responses={
        200: OpenApiResponse(description='File download attachment (text/csv or application/json)'),
        400: OpenApiResponse(description='Export is not ready or failed'),
        404: OpenApiResponse(description='File not found or expired'),
    }
)
class DataExportDownloadView(APIView):
    """
    GET /api/exports/<id>/download/
    Securely streams downloadable export file.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ImportExportRateThrottle]

    def get(self, request, pk, *args, **kwargs):
        try:
            export_obj = DataExport.objects.get(pk=pk, user=request.user)
        except DataExport.DoesNotExist:
            return Response({'detail': 'Export record not found.'}, status=status.HTTP_404_NOT_FOUND)

        if export_obj.is_expired:
            return Response({'detail': 'Export file has expired.'}, status=status.HTTP_410_GONE)

        if export_obj.status != ExportStatus.COMPLETED:
            return Response({
                'detail': f'Export is not ready for download. Current status: {export_obj.status}'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not export_obj.file or not os.path.exists(export_obj.file.path):
            return Response({'detail': 'Export file not found on server.'}, status=status.HTTP_404_NOT_FOUND)

        content_type = 'text/csv' if export_obj.format == ExportFormat.CSV else 'application/json'
        file_name = export_obj.file_name or f"financial_export_{export_obj.id}.{export_obj.format.lower()}"

        file_handle = open(export_obj.file.path, 'rb')
        response = FileResponse(file_handle, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'

        AuditLogService.log_export_downloaded(
            user=request.user,
            resource_id=export_obj.id,
            metadata={'file_name': file_name, 'file_size': export_obj.file_size},
            request=request
        )

        return response


@extend_schema(
    tags=['Financial Data Export'],
    summary='Trigger Expired Exports Cleanup',
    description='Triggers maintenance cleanup to mark past-due exports as EXPIRED and remove their files.',
    responses={
        200: OpenApiResponse(description='Cleanup result count'),
    }
)
class DataExportCleanupExpiredView(APIView):
    """
    POST /api/exports/cleanup-expired/
    Clean up expired exports and remove backing files.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ImportExportRateThrottle]

    def post(self, request, *args, **kwargs):
        cleaned_count = DataExportService.cleanup_expired_exports()
        return Response({
            'success': True,
            'message': f'Cleaned up {cleaned_count} expired export records.',
            'cleaned_count': cleaned_count
        }, status=status.HTTP_200_OK)
