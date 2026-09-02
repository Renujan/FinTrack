from django.contrib import admin
from .models import Category, Transaction, Budget, RecurringTransaction, RecurringTransactionExecution, FinancialGoal, Notification, DataBackup, DataImport, DataExport


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user', 'created_at', 'updated_at')
    list_filter = ('user',)
    search_fields = ('name', 'user__email', 'user__username')


@admin.register(RecurringTransaction)
class RecurringTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user', 'category', 'amount', 'transaction_type', 'frequency', 'interval', 'next_run_date', 'last_run_date', 'is_active', 'created_at')
    list_filter = ('transaction_type', 'frequency', 'is_active', 'user', 'category')
    search_fields = ('name', 'description', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'last_run_date')


@admin.register(RecurringTransactionExecution)
class RecurringTransactionExecutionAdmin(admin.ModelAdmin):
    list_display = ('id', 'recurring_transaction', 'status', 'scheduled_for', 'executed_at', 'transaction')
    list_filter = ('status', 'executed_at')
    search_fields = ('recurring_transaction__name', 'recurring_transaction__user__email', 'error_message')
    readonly_fields = ('executed_at',)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'category', 'transaction_type', 'amount', 'date', 'created_at')
    list_filter = ('transaction_type', 'user', 'category')
    search_fields = ('description', 'user__email')


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user', 'category', 'amount', 'period', 'start_date', 'end_date', 'created_at')
    list_filter = ('period', 'user', 'category')
    search_fields = ('name', 'user__email')


@admin.register(FinancialGoal)
class FinancialGoalAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user', 'category', 'target_amount', 'target_date', 'is_active', 'created_at')
    list_filter = ('is_active', 'user', 'category')
    search_fields = ('name', 'description', 'user__email')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'user', 'notification_type', 'is_read', 'created_at', 'read_at')
    list_filter = ('notification_type', 'is_read', 'user')
    search_fields = ('title', 'message', 'user__email')
    readonly_fields = ('created_at', 'read_at')


@admin.register(DataBackup)
class DataBackupAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user', 'status', 'backup_type', 'file_size', 'record_count', 'created_at', 'completed_at', 'expires_at')
    list_filter = ('status', 'backup_type', 'created_at')
    search_fields = ('name', 'user__email', 'user__username')
    readonly_fields = ('created_at', 'completed_at', 'file_size', 'record_count')


@admin.register(DataImport)
class DataImportAdmin(admin.ModelAdmin):
    list_display = ('id', 'file_name', 'user', 'status', 'total_rows', 'successful_rows', 'failed_rows', 'skipped_rows', 'duplicate_rows', 'created_at', 'completed_at')
    list_filter = ('status', 'created_at')
    search_fields = ('file_name', 'user__email', 'user__username')
    readonly_fields = ('created_at', 'completed_at', 'total_rows', 'successful_rows', 'failed_rows', 'skipped_rows', 'duplicate_rows')


@admin.register(DataExport)
class DataExportAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user', 'export_type', 'format', 'status', 'record_count', 'file_size', 'created_at', 'completed_at', 'expires_at')
    list_filter = ('status', 'export_type', 'format', 'created_at')
    search_fields = ('name', 'user__email', 'user__username')
    readonly_fields = ('created_at', 'completed_at', 'file_size', 'record_count')




