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

from transactions.models import DataExport, Transaction, Category, Budget, FinancialGoal, RecurringTransaction
from transactions.choices import ExportStatus, ExportType, ExportFormat
from transactions.audit_services import AuditLogService
from transactions.services import BudgetCalculationService, GoalCalculationService

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
    def collect_export_data(cls, user, export_type, filters=None):
        """
        Collects and filters user financial data based on export_type.
        Returns a tuple of (data_dict_or_list, total_record_count).
        """
        filters = filters or {}
        start_date = filters.get('start_date')
        end_date = filters.get('end_date')
        category_id = filters.get('category')
        transaction_type = filters.get('transaction_type')

        if export_type == ExportType.TRANSACTIONS:
            txns_data, count = cls._collect_transactions(user, start_date, end_date, category_id, transaction_type)
            return txns_data, count

        elif export_type == ExportType.CATEGORIES:
            cats_data, count = cls._collect_categories(user)
            return cats_data, count

        elif export_type == ExportType.BUDGETS:
            budgets_data, count = cls._collect_budgets(user, category_id)
            return budgets_data, count

        elif export_type == ExportType.GOALS:
            goals_data, count = cls._collect_goals(user)
            return goals_data, count

        elif export_type == ExportType.RECURRING_TRANSACTIONS:
            recurring_data, count = cls._collect_recurring(user, category_id, transaction_type)
            return recurring_data, count

        elif export_type == ExportType.FULL_FINANCIAL_DATA:
            txns, c_txns = cls._collect_transactions(user, start_date, end_date, category_id, transaction_type)
            cats, c_cats = cls._collect_categories(user)
            budgets, c_budgets = cls._collect_budgets(user, category_id)
            goals, c_goals = cls._collect_goals(user)
            recurring, c_rec = cls._collect_recurring(user, category_id, transaction_type)

            full_data = {
                'transactions': txns,
                'categories': cats,
                'budgets': budgets,
                'goals': goals,
                'recurring_transactions': recurring,
            }
            total_count = c_txns + c_cats + c_budgets + c_goals + c_rec
            return full_data, total_count

        else:
            raise ValueError(f"Unsupported export type: {export_type}")

    @classmethod
    def _collect_transactions(cls, user, start_date=None, end_date=None, category_id=None, transaction_type=None):
        qs = Transaction.objects.filter(user=user).select_related('category').order_by('-date', '-created_at')
        if start_date:
            qs = qs.filter(date__gte=start_date)
        if end_date:
            qs = qs.filter(date__lte=end_date)
        if category_id:
            qs = qs.filter(category_id=category_id)
        if transaction_type:
            qs = qs.filter(transaction_type=transaction_type)

        txns = []
        for t in qs.iterator():
            txns.append({
                'id': t.id,
                'title': t.description,
                'description': t.description,
                'amount': str(t.amount),
                'transaction_type': t.transaction_type,
                'category_id': t.category_id,
                'category_name': t.category.name if t.category else 'Uncategorized',
                'date': t.date.isoformat() if t.date else None,
                'created_at': t.created_at.isoformat() if t.created_at else None,
            })
        return txns, len(txns)

    @classmethod
    def _collect_categories(cls, user):
        qs = Category.objects.filter(user=user).order_by('name')
        cats = []
        for c in qs.iterator():
            cats.append({
                'id': c.id,
                'name': c.name,
                'created_at': c.created_at.isoformat() if c.created_at else None,
                'updated_at': c.updated_at.isoformat() if c.updated_at else None,
            })
        return cats, len(cats)

    @classmethod
    def _collect_budgets(cls, user, category_id=None):
        qs = Budget.objects.filter(user=user).select_related('category').order_by('-start_date')
        if category_id:
            qs = qs.filter(category_id=category_id)

        budgets = []
        for b in qs.iterator():
            spent = BudgetCalculationService.calculate_spent_amount(b)
            remaining = b.amount - spent
            is_exceeded = spent > b.amount
            budgets.append({
                'id': b.id,
                'name': b.name,
                'category_id': b.category_id,
                'category_name': b.category.name if b.category else 'All Categories',
                'amount': str(b.amount),
                'period': b.period,
                'start_date': b.start_date.isoformat() if b.start_date else None,
                'end_date': b.end_date.isoformat() if b.end_date else None,
                'spent_amount': str(spent),
                'remaining_amount': str(remaining),
                'is_exceeded': is_exceeded,
                'created_at': b.created_at.isoformat() if b.created_at else None,
            })
        return budgets, len(budgets)

    @classmethod
    def _collect_goals(cls, user):
        qs = FinancialGoal.objects.filter(user=user).select_related('category').order_by('target_date')
        goals = []
        for g in qs.iterator():
            pct = GoalCalculationService.calculate_progress_percentage(g)
            goals.append({
                'id': g.id,
                'name': g.name,
                'category_id': g.category_id,
                'category_name': g.category.name if g.category else 'General',
                'target_amount': str(g.target_amount),
                'current_amount': str(g.current_amount),
                'target_date': g.target_date.isoformat() if g.target_date else None,
                'status': g.status,
                'percentage_completed': float(pct),
                'created_at': g.created_at.isoformat() if g.created_at else None,
            })
        return goals, len(goals)

    @classmethod
    def _collect_recurring(cls, user, category_id=None, transaction_type=None):
        qs = RecurringTransaction.objects.filter(user=user).select_related('category').order_by('next_run_date')
        if category_id:
            qs = qs.filter(category_id=category_id)
        if transaction_type:
            qs = qs.filter(transaction_type=transaction_type)

        recurring = []
        for r in qs.iterator():
            recurring.append({
                'id': r.id,
                'title': r.name,
                'name': r.name,
                'amount': str(r.amount),
                'transaction_type': r.transaction_type,
                'frequency': r.frequency,
                'category_id': r.category_id,
                'category_name': r.category.name if r.category else 'Uncategorized',
                'next_run_date': r.next_run_date.isoformat() if r.next_run_date else None,
                'is_active': r.is_active,
                'created_at': r.created_at.isoformat() if r.created_at else None,
            })
        return recurring, len(recurring)

    @classmethod
    def generate_csv(cls, data, export_type):
        """
        Generates CSV binary content (UTF-8 encoded) for collected data.
        """
        output = io.StringIO()
        writer = csv.writer(output)

        if export_type == ExportType.TRANSACTIONS:
            writer.writerow(['ID', 'Title', 'Amount', 'Transaction Type', 'Category', 'Date', 'Created At'])
            for row in data:
                writer.writerow([
                    row['id'], row['title'], row['amount'], row['transaction_type'],
                    row['category_name'], row['date'], row['created_at']
                ])

        elif export_type == ExportType.CATEGORIES:
            writer.writerow(['ID', 'Name', 'Created At', 'Updated At'])
            for row in data:
                writer.writerow([row['id'], row['name'], row['created_at'], row['updated_at']])

        elif export_type == ExportType.BUDGETS:
            writer.writerow(['ID', 'Name', 'Category', 'Amount', 'Period', 'Start Date', 'End Date', 'Spent Amount', 'Remaining Amount', 'Is Exceeded', 'Created At'])
            for row in data:
                writer.writerow([
                    row['id'], row['name'], row['category_name'], row['amount'], row['period'],
                    row['start_date'], row['end_date'], row['spent_amount'], row['remaining_amount'],
                    row['is_exceeded'], row['created_at']
                ])

        elif export_type == ExportType.GOALS:
            writer.writerow(['ID', 'Name', 'Target Amount', 'Current Amount', 'Target Date', 'Status', 'Percentage Completed', 'Created At'])
            for row in data:
                writer.writerow([
                    row['id'], row['name'], row['target_amount'], row['current_amount'],
                    row['target_date'], row['status'], row['percentage_completed'], row['created_at']
                ])

        elif export_type == ExportType.RECURRING_TRANSACTIONS:
            writer.writerow(['ID', 'Title', 'Amount', 'Transaction Type', 'Frequency', 'Category', 'Next Run Date', 'Is Active', 'Created At'])
            for row in data:
                writer.writerow([
                    row['id'], row['title'], row['amount'], row['transaction_type'],
                    row['frequency'], row['category_name'], row['next_run_date'], row['is_active'], row['created_at']
                ])

        elif export_type == ExportType.FULL_FINANCIAL_DATA:
            # Multi-section CSV export
            writer.writerow(['=== CATEGORIES ==='])
            writer.writerow(['ID', 'Name', 'Created At', 'Updated At'])
            for row in data.get('categories', []):
                writer.writerow([row['id'], row['name'], row['created_at'], row['updated_at']])
            writer.writerow([])

            writer.writerow(['=== TRANSACTIONS ==='])
            writer.writerow(['ID', 'Title', 'Amount', 'Transaction Type', 'Category', 'Date', 'Created At'])
            for row in data.get('transactions', []):
                writer.writerow([
                    row['id'], row['title'], row['amount'], row['transaction_type'],
                    row['category_name'], row['date'], row['created_at']
                ])
            writer.writerow([])

            writer.writerow(['=== BUDGETS ==='])
            writer.writerow(['ID', 'Name', 'Category', 'Amount', 'Period', 'Start Date', 'End Date', 'Spent Amount', 'Remaining Amount', 'Is Exceeded', 'Created At'])
            for row in data.get('budgets', []):
                writer.writerow([
                    row['id'], row['name'], row['category_name'], row['amount'], row['period'],
                    row['start_date'], row['end_date'], row['spent_amount'], row['remaining_amount'],
                    row['is_exceeded'], row['created_at']
                ])
            writer.writerow([])

            writer.writerow(['=== FINANCIAL GOALS ==='])
            writer.writerow(['ID', 'Name', 'Target Amount', 'Current Amount', 'Target Date', 'Status', 'Percentage Completed', 'Created At'])
            for row in data.get('goals', []):
                writer.writerow([
                    row['id'], row['name'], row['target_amount'], row['current_amount'],
                    row['target_date'], row['status'], row['percentage_completed'], row['created_at']
                ])
            writer.writerow([])

            writer.writerow(['=== RECURRING TRANSACTIONS ==='])
            writer.writerow(['ID', 'Title', 'Amount', 'Transaction Type', 'Frequency', 'Category', 'Next Run Date', 'Is Active', 'Created At'])
            for row in data.get('recurring_transactions', []):
                writer.writerow([
                    row['id'], row['title'], row['amount'], row['transaction_type'],
                    row['frequency'], row['category_name'], row['next_run_date'], row['is_active'], row['created_at']
                ])

        return output.getvalue().encode('utf-8')

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
