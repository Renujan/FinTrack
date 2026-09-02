import csv
import io
import json
import logging
import uuid
from datetime import datetime, date, timedelta
from decimal import Decimal
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction as db_transaction
from django.utils import timezone
from django.utils.text import slugify

from transactions.models import DataExport
from transactions.choices import ExportStatus, ExportType, ExportFormat
from transactions.audit_services import AuditLogService

logger = logging.getLogger(__name__)

DEFAULT_RETENTION_DAYS = 7


class DataExportService:
    """
    Business service layer managing generation, filtering, file storage,
    and retention of user financial data exports.
    """

    @classmethod
    def create_export(cls, user, export_type=ExportType.FULL_FINANCIAL_DATA, format=ExportFormat.JSON, filters=None, name=None, request=None):
        """
        Creates and processes a new financial data export operation.
        """
        filters = filters or {}
        default_name = f"{export_type.replace('_', ' ').title()} Export ({format.upper()})"
        export_name = (name or default_name).strip()

        expires_at = timezone.now() + timedelta(days=DEFAULT_RETENTION_DAYS)

        export_obj = DataExport.objects.create(
            user=user,
            name=export_name,
            export_type=export_type,
            format=format,
            status=ExportStatus.PENDING,
            filters=filters,
            expires_at=expires_at,
        )

        AuditLogService.log_export_created(user=user, resource_id=export_obj.id, metadata={'export_type': export_type, 'format': format}, request=request)
        return export_obj

    @classmethod
    def save_export_file(cls, export_obj, file_bytes, extension):
        """
        Saves generated export file bytes to DataExport file field.
        """
        slug_name = slugify(export_obj.name) or 'financial_export'
        file_name = f"{slug_name}_{export_obj.id}.{extension}"
        content_file = ContentFile(file_bytes, name=file_name)

        export_obj.file.save(file_name, content_file, save=False)
        export_obj.file_name = file_name
        export_obj.file_size = len(file_bytes)

    @classmethod
    def cleanup_expired_exports(cls):
        """
        Finds all exports past their expiration date, deletes physical files,
        and marks their status as EXPIRED.
        """
        expired_qs = DataExport.objects.filter(
            expires_at__lt=timezone.now()
        ).exclude(status=ExportStatus.EXPIRED)

        count = 0
        for export_obj in expired_qs.iterator():
            export_obj.mark_expired()
            count += 1

        logger.info(f"Cleaned up {count} expired financial data exports.")
        return count
