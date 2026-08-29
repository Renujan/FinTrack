import json
import logging
from django.http import FileResponse, Http404
from rest_framework import status, generics, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from transactions.models import DataBackup
from transactions.choices import BackupStatus, BackupType
from transactions.pagination import StandardResultsSetPagination
from .serializers import (
    DataBackupSerializer,
    DataBackupCreateSerializer,
    RestoreValidationRequestSerializer,
)
from .services import BackupService
from transactions.audit_services import AuditLogService

logger = logging.getLogger(__name__)


class DataBackupListCreateView(generics.ListCreateAPIView):
    """
    GET /api/backups/ - List user backup history with metadata.
    POST /api/backups/ - Request new data backup creation.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = DataBackupSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['created_at', 'completed_at', 'status', 'file_size']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = DataBackup.objects.filter(user=self.request.user)
        status_param = self.request.query_params.get('status')
        if status_param and BackupStatus.is_valid_status(status_param.upper()):
            queryset = queryset.filter(status=status_param.upper())
        type_param = self.request.query_params.get('backup_type')
        if type_param and BackupType.is_valid_type(type_param.upper()):
            queryset = queryset.filter(backup_type=type_param.upper())
        return queryset

    @extend_schema(
        summary="List user backups",
        description="Retrieve history and metadata of user financial backups.",
        parameters=[
            OpenApiParameter('status', OpenApiTypes.STR, description="Filter by status (PENDING, PROCESSING, COMPLETED, FAILED, EXPIRED)"),
            OpenApiParameter('backup_type', OpenApiTypes.STR, description="Filter by backup type (FULL, TRANSACTIONS, SELECTED_DATA)"),
        ],
        responses={200: DataBackupSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Create financial backup",
        description="Generate a new JSON data backup for user financial records.",
        request=DataBackupCreateSerializer,
        responses={201: DataBackupSerializer}
    )
    def post(self, request, *args, **kwargs):
        serializer = DataBackupCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        try:
            backup_record = BackupService.create_backup(
                user=request.user,
                name=validated_data.get('name'),
                backup_type=validated_data.get('backup_type', BackupType.FULL),
                include_sections=validated_data.get('include_sections'),
                retention_days=validated_data.get('retention_days', 30),
                request=request
            )
            response_serializer = DataBackupSerializer(backup_record, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating backup: {e}", exc_info=True)
            return Response(
                {"error": f"Backup generation failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )


class DataBackupDetailView(generics.RetrieveDestroyAPIView):
    """
    GET /api/backups/<id>/ - Retrieve backup metadata detail and history record.
    DELETE /api/backups/<id>/ - Safely delete backup file and record.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = DataBackupSerializer
    lookup_field = 'pk'

    def get_queryset(self):
        return DataBackup.objects.filter(user=self.request.user)

    @extend_schema(
        summary="Get backup details",
        description="Retrieve metadata and download information for a specific backup record.",
        responses={200: DataBackupSerializer}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Delete backup record",
        description="Safely delete a user backup record and remove its associated file from storage.",
        responses={204: None}
    )
    def delete(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        try:
            BackupService.delete_backup(user=request.user, backup_id=pk, request=request)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error deleting backup {pk}: {e}", exc_info=True)
            return Response({"error": "Failed to delete backup."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DataBackupDownloadView(APIView):
    """
    GET /api/backups/<id>/download/ - Secure backup file download endpoint.
    Only the owner of the backup can stream and download the file. Never exposes filesystem paths.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Download backup file",
        description="Securely stream and download the JSON financial data backup file.",
        responses={200: OpenApiTypes.BINARY}
    )
    def get(self, request, pk, *args, **kwargs):
        try:
            backup = DataBackup.objects.get(pk=pk, user=request.user)
        except DataBackup.DoesNotExist:
            raise Http404("Backup not found or access denied.")

        if backup.status != BackupStatus.COMPLETED or not backup.file:
            return Response(
                {"error": "Backup file is not ready or has been removed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if backup.is_expired:
            backup.mark_expired()
            return Response(
                {"error": "Backup file has expired and is no longer available for download."},
                status=status.HTTP_410_GONE
            )

        try:
            filename = f"backup_{request.user.username}_{backup.created_at.strftime('%Y%m%d')}_{backup.id}.json"
            response = FileResponse(
                backup.file.open('rb'),
                content_type='application/json'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'

            AuditLogService.log_backup_downloaded(
                user=request.user,
                resource_id=str(backup.id),
                metadata={'name': backup.name, 'file_size': backup.file_size},
                request=request
            )
            return response
        except Exception as e:
            logger.error(f"Error streaming download for backup {pk}: {e}", exc_info=True)
            return Response({"error": "Download failed."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BackupRestoreValidateView(APIView):
    """
    POST /api/backups/validate-restore/ - Restore preparation & preview.
    Validates backup structure, format, version, and entity integrity without modifying user data.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Validate restore data",
        description="Validate a financial backup file or payload for restore preparation without altering any database records.",
        request=RestoreValidationRequestSerializer,
        responses={200: OpenApiTypes.OBJECT}
    )
    def post(self, request, *args, **kwargs):
        serializer = RestoreValidationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file_obj = serializer.validated_data.get('file')
        json_data = serializer.validated_data.get('json_data')

        payload = None
        if file_obj:
            try:
                content = file_obj.read().decode('utf-8')
                payload = json.loads(content)
            except Exception as e:
                return Response(
                    {
                        "valid": False,
                        "error": f"Failed to parse uploaded backup file: {str(e)}",
                        "validation_errors": [f"File parsing error: {str(e)}"]
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            payload = json_data

        result = BackupService.validate_restore_data(
            user=request.user,
            payload=payload,
            request=request
        )
        return Response(result, status=status.HTTP_200_OK)


class BackupCleanupExpiredView(APIView):
    """
    POST /api/backups/cleanup-expired/ - Manually trigger cleanup of expired backup records and files.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Cleanup expired backups",
        description="Process retention rules and mark expired user backups as EXPIRED while removing associated files.",
        responses={200: OpenApiTypes.OBJECT}
    )
    def post(self, request, *args, **kwargs):
        count = BackupService.cleanup_expired_backups()
        return Response(
            {
                "message": "Retention cleanup processed successfully.",
                "expired_backups_processed": count
            },
            status=status.HTTP_200_OK
        )
