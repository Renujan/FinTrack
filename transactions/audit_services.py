import logging
from .choices import AuditAction
from .models import AuditLog

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """
    Safely extract client IP address from request headers (HTTP_X_FORWARDED_FOR)
    or REMOTE_ADDR fallback.
    """
    if not request:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class AuditLogService:
    """
    Reusable service layer for creating audit trail records across operations.
    Fails silently with error logging to prevent interrupting financial transactions.
    """

    @staticmethod
    def log_action(user=None, action=None, resource_type='', resource_id='', ip_address=None, metadata=None, request=None):
        """
        Record an audit log entry.
        """
        try:
            if request:
                if not user and hasattr(request, 'user') and request.user.is_authenticated:
                    user = request.user
                if not ip_address:
                    ip_address = get_client_ip(request)

            if user and not getattr(user, 'is_authenticated', False):
                user = None

            clean_metadata = dict(metadata) if isinstance(metadata, dict) else {}
            # Shield sensitive keys
            for key in ['password', 'token', 'refresh', 'access', 'secret', 'key']:
                clean_metadata.pop(key, None)

            audit_log = AuditLog.objects.create(
                user=user,
                action=action,
                resource_type=str(resource_type),
                resource_id=str(resource_id) if resource_id is not None else '',
                ip_address=ip_address,
                metadata=clean_metadata
            )
            return audit_log
        except Exception as e:
            logger.error(f"Audit log entry creation failed: {e}", exc_info=True)
            return None

    @classmethod
    def log_create(cls, user, resource_type, resource_id='', metadata=None, request=None):
        return cls.log_action(user=user, action=AuditAction.CREATE, resource_type=resource_type, resource_id=resource_id, metadata=metadata, request=request)

    @classmethod
    def log_update(cls, user, resource_type, resource_id='', metadata=None, request=None):
        return cls.log_action(user=user, action=AuditAction.UPDATE, resource_type=resource_type, resource_id=resource_id, metadata=metadata, request=request)

    @classmethod
    def log_delete(cls, user, resource_type, resource_id='', metadata=None, request=None):
        return cls.log_action(user=user, action=AuditAction.DELETE, resource_type=resource_type, resource_id=resource_id, metadata=metadata, request=request)

    @classmethod
    def log_import(cls, user, resource_type, resource_id='', metadata=None, request=None):
        return cls.log_action(user=user, action=AuditAction.IMPORT, resource_type=resource_type, resource_id=resource_id, metadata=metadata, request=request)

    @classmethod
    def log_export(cls, user, resource_type, resource_id='', metadata=None, request=None):
        return cls.log_action(user=user, action=AuditAction.EXPORT, resource_type=resource_type, resource_id=resource_id, metadata=metadata, request=request)

    @classmethod
    def log_login(cls, user, ip_address=None, metadata=None, request=None):
        user_id = getattr(user, 'id', '') if user else ''
        return cls.log_action(user=user, action=AuditAction.LOGIN, resource_type='User', resource_id=user_id, ip_address=ip_address, metadata=metadata, request=request)

    @classmethod
    def log_logout(cls, user, ip_address=None, metadata=None, request=None):
        user_id = getattr(user, 'id', '') if user else ''
        return cls.log_action(user=user, action=AuditAction.LOGOUT, resource_type='User', resource_id=user_id, ip_address=ip_address, metadata=metadata, request=request)

    @classmethod
    def log_password_change(cls, user, ip_address=None, metadata=None, request=None):
        user_id = getattr(user, 'id', '') if user else ''
        return cls.log_action(user=user, action=AuditAction.PASSWORD_CHANGE, resource_type='User', resource_id=user_id, ip_address=ip_address, metadata=metadata, request=request)

    @classmethod
    def log_backup_created(cls, user, resource_id='', metadata=None, request=None):
        return cls.log_action(user=user, action=AuditAction.BACKUP_CREATED, resource_type='DataBackup', resource_id=resource_id, metadata=metadata, request=request)

    @classmethod
    def log_backup_downloaded(cls, user, resource_id='', metadata=None, request=None):
        return cls.log_action(user=user, action=AuditAction.BACKUP_DOWNLOADED, resource_type='DataBackup', resource_id=resource_id, metadata=metadata, request=request)

    @classmethod
    def log_backup_deleted(cls, user, resource_id='', metadata=None, request=None):
        return cls.log_action(user=user, action=AuditAction.BACKUP_DELETED, resource_type='DataBackup', resource_id=resource_id, metadata=metadata, request=request)

    @classmethod
    def log_restore_validated(cls, user, metadata=None, request=None):
        return cls.log_action(user=user, action=AuditAction.RESTORE_VALIDATED, resource_type='DataBackup', resource_id='', metadata=metadata, request=request)
