from django.db import models
from django.utils.translation import gettext_lazy as _


class TransactionType(models.TextChoices):
    INCOME = 'INCOME', _('Income')
    EXPENSE = 'EXPENSE', _('Expense')


class BudgetPeriod(models.TextChoices):
    WEEKLY = 'WEEKLY', _('Weekly')
    MONTHLY = 'MONTHLY', _('Monthly')
    CUSTOM = 'CUSTOM', _('Custom')

    @classmethod
    def is_valid_period(cls, value):
        return value in cls.values if value else False


class RecurrenceFrequency(models.TextChoices):
    DAILY = 'DAILY', _('Daily')
    WEEKLY = 'WEEKLY', _('Weekly')
    MONTHLY = 'MONTHLY', _('Monthly')
    YEARLY = 'YEARLY', _('Yearly')
    CUSTOM = 'CUSTOM', _('Custom')

    @classmethod
    def is_valid_frequency(cls, value):
        return value in cls.values if value else False


class ExecutionStatus(models.TextChoices):
    SUCCESS = 'SUCCESS', _('Success')
    FAILED = 'FAILED', _('Failed')
    SKIPPED = 'SKIPPED', _('Skipped')

    @classmethod
    def is_valid_status(cls, value):
        return value in cls.values if value else False


class GoalStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', _('Active')
    COMPLETED = 'COMPLETED', _('Completed')
    OVERDUE = 'OVERDUE', _('Overdue')
    PAUSED = 'PAUSED', _('Paused')


class NotificationType(models.TextChoices):
    BUDGET_EXCEEDED = 'BUDGET_EXCEEDED', _('Budget Exceeded')
    BUDGET_WARNING = 'BUDGET_WARNING', _('Budget Warning')
    GOAL_COMPLETED = 'GOAL_COMPLETED', _('Goal Completed')
    GOAL_WARNING = 'GOAL_WARNING', _('Goal Warning')
    RECURRING_DUE = 'RECURRING_DUE', _('Recurring Transaction Due')
    RECURRING_GENERATED = 'RECURRING_GENERATED', _('Recurring Transaction Generated')
    RECURRING_EXPIRED = 'RECURRING_EXPIRED', _('Recurring Schedule Expired')
    RECURRING_TRANSACTION_CREATED = 'RECURRING_TRANSACTION_CREATED', _('Recurring Transaction Created')
    RECURRING_TRANSACTION_EXECUTED = 'RECURRING_TRANSACTION_EXECUTED', _('Recurring Transaction Executed')
    RECURRING_TRANSACTION_FAILED = 'RECURRING_TRANSACTION_FAILED', _('Recurring Transaction Failed')
    RECURRING_TRANSACTION_PAUSED = 'RECURRING_TRANSACTION_PAUSED', _('Recurring Transaction Paused')
    RECURRING_TRANSACTION_RESUMED = 'RECURRING_TRANSACTION_RESUMED', _('Recurring Transaction Resumed')

    @classmethod
    def is_valid_type(cls, value):
        return value in cls.values if value else False


class AuditAction(models.TextChoices):
    CREATE = 'CREATE', _('Create')
    UPDATE = 'UPDATE', _('Update')
    DELETE = 'DELETE', _('Delete')
    IMPORT = 'IMPORT', _('Import')
    EXPORT = 'EXPORT', _('Export')
    LOGIN = 'LOGIN', _('Login')
    LOGOUT = 'LOGOUT', _('Logout')
    PASSWORD_CHANGE = 'PASSWORD_CHANGE', _('Password Change')
    BACKUP_CREATED = 'BACKUP_CREATED', _('Backup Created')
    BACKUP_DOWNLOADED = 'BACKUP_DOWNLOADED', _('Backup Downloaded')
    BACKUP_DELETED = 'BACKUP_DELETED', _('Backup Deleted')
    RESTORE_VALIDATED = 'RESTORE_VALIDATED', _('Restore Validated')
    RECURRING_TRANSACTION_CREATED = 'RECURRING_TRANSACTION_CREATED', _('Recurring Transaction Created')
    RECURRING_TRANSACTION_UPDATED = 'RECURRING_TRANSACTION_UPDATED', _('Recurring Transaction Updated')
    RECURRING_TRANSACTION_PAUSED = 'RECURRING_TRANSACTION_PAUSED', _('Recurring Transaction Paused')
    RECURRING_TRANSACTION_RESUMED = 'RECURRING_TRANSACTION_RESUMED', _('Recurring Transaction Resumed')
    RECURRING_TRANSACTION_EXECUTED = 'RECURRING_TRANSACTION_EXECUTED', _('Recurring Transaction Executed')
    RECURRING_TRANSACTION_DELETED = 'RECURRING_TRANSACTION_DELETED', _('Recurring Transaction Deleted')
    DATA_IMPORT_CREATED = 'DATA_IMPORT_CREATED', _('Data Import Created')
    DATA_IMPORT_PREVIEWED = 'DATA_IMPORT_PREVIEWED', _('Data Import Previewed')
    DATA_IMPORT_EXECUTED = 'DATA_IMPORT_EXECUTED', _('Data Import Executed')
    DATA_IMPORT_FAILED = 'DATA_IMPORT_FAILED', _('Data Import Failed')
    DATA_IMPORT_DELETED = 'DATA_IMPORT_DELETED', _('Data Import Deleted')
    DATA_EXPORT_CREATED = 'DATA_EXPORT_CREATED', _('Data Export Created')
    DATA_EXPORT_COMPLETED = 'DATA_EXPORT_COMPLETED', _('Data Export Completed')
    DATA_EXPORT_DOWNLOADED = 'DATA_EXPORT_DOWNLOADED', _('Data Export Downloaded')
    DATA_EXPORT_DELETED = 'DATA_EXPORT_DELETED', _('Data Export Deleted')
    DATA_EXPORT_FAILED = 'DATA_EXPORT_FAILED', _('Data Export Failed')

    @classmethod
    def is_valid_action(cls, value):
        return value in cls.values if value else False


class BackupStatus(models.TextChoices):
    PENDING = 'PENDING', _('Pending')
    PROCESSING = 'PROCESSING', _('Processing')
    COMPLETED = 'COMPLETED', _('Completed')
    FAILED = 'FAILED', _('Failed')
    EXPIRED = 'EXPIRED', _('Expired')

    @classmethod
    def is_valid_status(cls, value):
        return value in cls.values if value else False


class BackupType(models.TextChoices):
    FULL = 'FULL', _('Full Backup')
    TRANSACTIONS = 'TRANSACTIONS', _('Transactions & Categories')
    SELECTED_DATA = 'SELECTED_DATA', _('Selected Data')

    @classmethod
    def is_valid_type(cls, value):
        return value in cls.values if value else False


class ImportStatus(models.TextChoices):
    PENDING = 'PENDING', _('Pending')
    PROCESSING = 'PROCESSING', _('Processing')
    PREVIEW_READY = 'PREVIEW_READY', _('Preview Ready')
    COMPLETED = 'COMPLETED', _('Completed')
    FAILED = 'FAILED', _('Failed')

    @classmethod
    def is_valid_status(cls, value):
        return value in cls.values if value else False


class ExportStatus(models.TextChoices):
    PENDING = 'PENDING', _('Pending')
    PROCESSING = 'PROCESSING', _('Processing')
    COMPLETED = 'COMPLETED', _('Completed')
    FAILED = 'FAILED', _('Failed')
    EXPIRED = 'EXPIRED', _('Expired')

    @classmethod
    def is_valid_status(cls, value):
        return value in cls.values if value else False


class ExportType(models.TextChoices):
    TRANSACTIONS = 'TRANSACTIONS', _('Transactions')
    CATEGORIES = 'CATEGORIES', _('Categories')
    BUDGETS = 'BUDGETS', _('Budgets')
    GOALS = 'GOALS', _('Goals')
    RECURRING_TRANSACTIONS = 'RECURRING_TRANSACTIONS', _('Recurring Transactions')
    FULL_FINANCIAL_DATA = 'FULL_FINANCIAL_DATA', _('Full Financial Data')

    @classmethod
    def is_valid_type(cls, value):
        return value in cls.values if value else False


class ExportFormat(models.TextChoices):
    CSV = 'CSV', _('CSV')
    JSON = 'JSON', _('JSON')

    @classmethod
    def is_valid_format(cls, value):
        return value in cls.values if value else False





