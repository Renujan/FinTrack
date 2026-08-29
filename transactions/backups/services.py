import json
import logging
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction as db_transaction
from django.utils import timezone

from transactions.models import (
    Category,
    Transaction,
    Budget,
    FinancialGoal,
    RecurringTransaction,
    DataBackup,
)
from transactions.choices import BackupStatus, BackupType
from transactions.audit_services import AuditLogService

logger = logging.getLogger(__name__)

# JSON Backup Export Standard Schema Version
JSON_BACKUP_SCHEMA_VERSION = "1.0"


class DecimalAndDateEncoder(json.JSONEncoder):
    """
    JSON encoder for Decimal, Date, DateTime, and UUID types.
    """
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, (datetime, timezone.datetime)):
            return obj.isoformat()
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return super().default(obj)


class BackupService:
    """
    Reusable service layer for financial data backups, storage handling,
    restore validation, and retention cleanup.
    """

    FORMAT_VERSION = "1.0"
    DEFAULT_RETENTION_DAYS = 30

    @classmethod
    def collect_user_data(cls, user, backup_type=BackupType.FULL, include_sections=None):
        """
        Collect financial models and user profile/preferences strictly belonging
        to the authenticated user.
        Excludes passwords, JWT tokens, secret keys, or internal config.
        """
        if include_sections is None:
            include_sections = []

        data = {}
        section_counts = {}

        # Determine which sections to collect based on backup_type & include_sections
        should_include_all = backup_type == BackupType.FULL or not include_sections
        should_include_txns = should_include_all or backup_type == BackupType.TRANSACTIONS or 'transactions' in include_sections
        should_include_cats = should_include_txns or 'categories' in include_sections
        should_include_budgets = should_include_all or 'budgets' in include_sections
        should_include_goals = should_include_all or 'goals' in include_sections
        should_include_recurring = should_include_all or 'recurring' in include_sections
        should_include_preferences = should_include_all or 'preferences' in include_sections
        should_include_profile = should_include_all or 'profile' in include_sections

        # 1. User Categories
        if should_include_cats:
            categories_qs = Category.objects.filter(user=user).order_by('id')
            categories = [
                {
                    'id': cat.id,
                    'name': cat.name,
                    'created_at': cat.created_at.isoformat() if cat.created_at else None,
                    'updated_at': cat.updated_at.isoformat() if cat.updated_at else None,
                }
                for cat in categories_qs
            ]
            data['categories'] = categories
            section_counts['categories'] = len(categories)

        # 2. User Transactions
        if should_include_txns:
            transactions_qs = Transaction.objects.filter(user=user).select_related('category').order_by('-date', '-created_at')
            txns = [
                {
                    'id': t.id,
                    'category_id': t.category_id,
                    'category_name': t.category.name if t.category else 'Uncategorized',
                    'transaction_type': t.transaction_type,
                    'amount': str(t.amount),
                    'description': t.description or '',
                    'date': t.date.isoformat() if t.date else None,
                    'recurring_transaction_id': t.recurring_transaction_id,
                    'recurring_schedule_date': t.recurring_schedule_date.isoformat() if t.recurring_schedule_date else None,
                    'created_at': t.created_at.isoformat() if t.created_at else None,
                    'updated_at': t.updated_at.isoformat() if t.updated_at else None,
                }
                for t in transactions_qs
            ]
            data['transactions'] = txns
            section_counts['transactions'] = len(txns)

        # 3. User Budgets
        if should_include_budgets:
            budgets_qs = Budget.objects.filter(user=user).select_related('category').order_by('-start_date')
            budgets = [
                {
                    'id': b.id,
                    'category_id': b.category_id,
                    'category_name': b.category.name if b.category else None,
                    'name': b.name,
                    'amount': str(b.amount),
                    'period': b.period,
                    'start_date': b.start_date.isoformat() if b.start_date else None,
                    'end_date': b.end_date.isoformat() if b.end_date else None,
                    'created_at': b.created_at.isoformat() if b.created_at else None,
                    'updated_at': b.updated_at.isoformat() if b.updated_at else None,
                }
                for b in budgets_qs
            ]
            data['budgets'] = budgets
            section_counts['budgets'] = len(budgets)

        # 4. Financial Goals
        if should_include_goals:
            goals_qs = FinancialGoal.objects.filter(user=user).select_related('category').order_by('target_date')
            goals = [
                {
                    'id': g.id,
                    'category_id': g.category_id,
                    'category_name': g.category.name if g.category else None,
                    'name': g.name,
                    'description': g.description or '',
                    'target_amount': str(g.target_amount),
                    'target_date': g.target_date.isoformat() if g.target_date else None,
                    'is_active': g.is_active,
                    'created_at': g.created_at.isoformat() if g.created_at else None,
                    'updated_at': g.updated_at.isoformat() if g.updated_at else None,
                }
                for g in goals_qs
            ]
            data['financial_goals'] = goals
            section_counts['financial_goals'] = len(goals)

        # 5. Recurring Transactions
        if should_include_recurring:
            recurring_qs = RecurringTransaction.objects.filter(user=user).select_related('category').order_by('next_run_date')
            recurring = [
                {
                    'id': r.id,
                    'category_id': r.category_id,
                    'category_name': r.category.name if r.category else '',
                    'name': r.name,
                    'description': r.description or '',
                    'amount': str(r.amount),
                    'transaction_type': r.transaction_type,
                    'frequency': r.frequency,
                    'start_date': r.start_date.isoformat() if r.start_date else None,
                    'end_date': r.end_date.isoformat() if r.end_date else None,
                    'next_run_date': r.next_run_date.isoformat() if r.next_run_date else None,
                    'last_run_date': r.last_run_date.isoformat() if r.last_run_date else None,
                    'is_active': r.is_active,
                    'created_at': r.created_at.isoformat() if r.created_at else None,
                    'updated_at': r.updated_at.isoformat() if r.updated_at else None,
                }
                for r in recurring_qs
            ]
            data['recurring_transactions'] = recurring
            section_counts['recurring_transactions'] = len(recurring)

        # 6. User Profile
        if should_include_profile and hasattr(user, 'profile'):
            prof = user.profile
            data['user_profile'] = {
                'display_name': prof.display_name,
                'bio': prof.bio,
                'phone_number': prof.phone_number,
                'created_at': prof.created_at.isoformat() if prof.created_at else None,
            }

        # 7. User Preferences
        if should_include_preferences and hasattr(user, 'preferences'):
            pref = user.preferences
            data['user_preferences'] = {
                'currency': pref.currency,
                'currency_symbol': pref.currency_symbol,
                'default_currency': pref.default_currency,
                'date_format': pref.date_format,
                'timezone': pref.timezone,
                'language': pref.language,
                'financial_year_start_month': pref.financial_year_start_month,
                'default_transaction_type': pref.default_transaction_type,
                'budget_alerts': pref.budget_alerts,
                'goal_alerts': pref.goal_alerts,
                'recurring_transaction_alerts': pref.recurring_transaction_alerts,
                'system_notifications': pref.system_notifications,
            }

        # 8. Subscription Summary (if subscription app attached)
        if hasattr(user, 'subscription'):
            sub = user.subscription
            data['subscription_summary'] = {
                'plan_name': sub.plan.name if sub.plan else None,
                'plan_code': sub.plan.code if sub.plan else None,
                'status': sub.effective_status,
                'start_date': sub.start_date.isoformat() if sub.start_date else None,
                'end_date': sub.end_date.isoformat() if sub.end_date else None,
            }

        total_records = sum(section_counts.values())
        return data, section_counts, total_records

    @classmethod
    def serialize_backup_data(cls, user, collected_data, backup_type=BackupType.FULL):
        """
        Build JSON-structured backup object containing version metadata, timestamp,
        user basic info, and data sections.
        """
        user_info = {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'currency': getattr(user, 'currency', 'LKR'),
        }

        payload = {
            'version': cls.FORMAT_VERSION,
            'created_at': timezone.now().isoformat(),
            'backup_type': backup_type,
            'user': user_info,
            'data': collected_data,
        }

        return json.dumps(payload, cls=DecimalAndDateEncoder, indent=2)

    @classmethod
    def create_backup(cls, user, name=None, backup_type=BackupType.FULL, include_sections=None, retention_days=None, request=None):
        """
        Generate, serialize, and store a financial data backup for the user.
        """
        if not retention_days or retention_days <= 0:
            retention_days = cls.DEFAULT_RETENTION_DAYS

        now = timezone.now()
        expires_at = now + timedelta(days=retention_days)

        if not name:
            name = f"Backup-{backup_type}-{now.strftime('%Y%m%d-%H%M%S')}"

        # Create DataBackup record in PENDING / PROCESSING state
        backup_record = DataBackup.objects.create(
            user=user,
            name=name,
            status=BackupStatus.PROCESSING,
            backup_type=backup_type,
            expires_at=expires_at,
        )

        try:
            collected_data, section_counts, total_records = cls.collect_user_data(
                user=user,
                backup_type=backup_type,
                include_sections=include_sections
            )

            json_string = cls.serialize_backup_data(
                user=user,
                collected_data=collected_data,
                backup_type=backup_type
            )

            file_bytes = json_string.encode('utf-8')
            filename = f"user_{user.id}_backup_{now.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.json"

            # Save content file securely to storage
            backup_record.file.save(filename, ContentFile(file_bytes), save=False)
            backup_record.file_size = len(file_bytes)
            backup_record.record_count = total_records
            backup_record.metadata = {
                'section_counts': section_counts,
                'version': cls.FORMAT_VERSION,
                'include_sections': include_sections or [],
                'retention_days': retention_days,
            }
            backup_record.completed_at = timezone.now()
            backup_record.status = BackupStatus.COMPLETED
            backup_record.save()

            # Audit logging
            AuditLogService.log_backup_created(
                user=user,
                resource_id=str(backup_record.id),
                metadata={
                    'name': name,
                    'backup_type': backup_type,
                    'file_size': backup_record.file_size,
                    'record_count': total_records,
                    'expires_at': expires_at.isoformat(),
                },
                request=request
            )

            return backup_record

        except Exception as e:
            logger.error(f"Backup generation failed for user {user.id}: {e}", exc_info=True)
            backup_record.status = BackupStatus.FAILED
            backup_record.metadata = {'error': 'Backup generation failed'}
            backup_record.save(update_fields=['status', 'metadata'])
            raise ValueError(f"Failed to generate backup: {str(e)}")

    @classmethod
    def validate_restore_data(cls, user, payload, request=None):
        """
        Validate backup format, version, required fields, and entity data without
        modifying any existing user data in the database.
        """
        validation_errors = []
        validation_warnings = []

        if isinstance(payload, (str, bytes)):
            try:
                payload = json.loads(payload)
            except Exception as e:
                validation_errors.append(f"Invalid JSON content: {str(e)}")
                return {
                    'valid': False,
                    'version': None,
                    'supported': False,
                    'backup_type': 'UNKNOWN',
                    'summary': {},
                    'validation_errors': validation_errors,
                    'validation_warnings': validation_warnings,
                }

        if not isinstance(payload, dict):
            validation_errors.append("Backup payload must be a JSON object.")
            return {
                'valid': False,
                'version': None,
                'supported': False,
                'backup_type': 'UNKNOWN',
                'summary': {},
                'validation_errors': validation_errors,
                'validation_warnings': validation_warnings,
            }

        version = payload.get('version')
        if not version:
            validation_errors.append("Missing backup 'version' attribute.")
        elif version != cls.FORMAT_VERSION:
            validation_warnings.append(f"Backup version '{version}' differs from current format '{cls.FORMAT_VERSION}'. Compatibility may be partial.")

        backup_type = payload.get('backup_type', 'FULL')
        data = payload.get('data')

        if not isinstance(data, dict):
            validation_errors.append("Missing or invalid 'data' container in backup payload.")
            data = {}

        # Inspect data sections
        categories = data.get('categories', [])
        transactions = data.get('transactions', [])
        budgets = data.get('budgets', [])
        goals = data.get('financial_goals', [])
        recurring = data.get('recurring_transactions', [])

        existing_cat_names = set(Category.objects.filter(user=user).values_list('name', flat=True))
        backup_cat_names = {c.get('name') for c in categories if isinstance(c, dict) and c.get('name')}

        new_cats = backup_cat_names - existing_cat_names
        if new_cats:
            validation_warnings.append(f"{len(new_cats)} new category names found in backup that will be created during restoration.")

        # Validate transaction records
        invalid_txn_count = 0
        if isinstance(transactions, list):
            for t in transactions:
                if not isinstance(t, dict) or not t.get('amount') or not t.get('date') or not t.get('transaction_type'):
                    invalid_txn_count += 1
            if invalid_txn_count > 0:
                validation_errors.append(f"{invalid_txn_count} transaction records are missing required fields (amount, date, transaction_type).")

        summary = {
            'categories_count': len(categories) if isinstance(categories, list) else 0,
            'transactions_count': len(transactions) if isinstance(transactions, list) else 0,
            'budgets_count': len(budgets) if isinstance(budgets, list) else 0,
            'financial_goals_count': len(goals) if isinstance(goals, list) else 0,
            'recurring_transactions_count': len(recurring) if isinstance(recurring, list) else 0,
            'user_profile_included': 'user_profile' in data,
            'user_preferences_included': 'user_preferences' in data,
        }

        AuditLogService.log_restore_validated(
            user=user,
            metadata={
                'version': version,
                'valid': len(validation_errors) == 0,
                'summary': summary,
                'errors_count': len(validation_errors),
                'warnings_count': len(validation_warnings),
            },
            request=request
        )

        return {
            'valid': len(validation_errors) == 0,
            'version': version,
            'supported': version == cls.FORMAT_VERSION,
            'backup_type': backup_type,
            'created_at': payload.get('created_at'),
            'summary': summary,
            'validation_errors': validation_errors,
            'validation_warnings': validation_warnings,
            'note': 'Full destructive data restoration is intentionally not implemented on Day 20.'
        }

    @classmethod
    def delete_backup(cls, user, backup_id, request=None):
        """
        Verify backup ownership, remove physical file from storage safely, and
        delete database record.
        """
        try:
            backup = DataBackup.objects.get(id=backup_id, user=user)
        except DataBackup.DoesNotExist:
            raise ValueError("Backup record not found or access denied.")

        name = backup.name
        b_id = str(backup.id)

        if backup.file:
            try:
                backup.file.delete(save=False)
            except Exception as e:
                logger.warning(f"Failed to remove backup file for record {backup.id}: {e}")

        backup.delete()

        AuditLogService.log_backup_deleted(
            user=user,
            resource_id=b_id,
            metadata={'name': name},
            request=request
        )

        return True

    @classmethod
    def cleanup_expired_backups(cls):
        """
        Identify expired backups and perform retention cleanup safely.
        """
        now = timezone.now()
        expired_backups = DataBackup.objects.filter(
            expires_at__lte=now
        ).exclude(status=BackupStatus.EXPIRED)

        count = 0
        for backup in expired_backups:
            try:
                backup.mark_expired()
                count += 1
            except Exception as e:
                logger.error(f"Error marking backup {backup.id} expired: {e}")

        return count
