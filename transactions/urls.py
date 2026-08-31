from django.urls import path
from .views import (
    CategoryListCreateView,
    CategoryDetailView,
    TransactionListCreateView,
    TransactionDetailView,
    BudgetListCreateView,
    BudgetDetailView,
    RecurringTransactionListCreateView,
    RecurringTransactionDetailView,
    RecurringTransactionPauseView,
    RecurringTransactionResumeView,
    RecurringTransactionExecuteView,
    RecurringTransactionHistoryView,
    FinancialGoalListCreateView,
    FinancialGoalDetailView,
    FinancialGoalPauseView,
    FinancialGoalResumeView,
    NotificationListView,
    NotificationDetailView,
    NotificationMarkAllReadView,
    AuditLogListView,
    AuditLogDetailView,
)
from .analytics.views import (
    DashboardSummaryAPIView,
    FinancialTrendsAPIView,
    MonthlySummaryAPIView,
    CategoryAnalyticsAPIView,
    PeriodComparisonAPIView,
    BudgetAnalyticsAPIView,
)
from .export_import.views import (
    TransactionExportAPIView,
    CategoryExportAPIView,
    BudgetExportAPIView,
    FinancialGoalExportAPIView,
    RecurringTransactionExportAPIView,
    FinancialReportAPIView,
    TransactionImportAPIView,
)
from .reports.views import (
    IncomeReportAPIView,
    ExpenseReportAPIView,
    CashFlowReportAPIView,
    CategoryReportAPIView,
    MonthlyReportAPIView,
    SpendingTrendsReportAPIView,
    BudgetComparisonReportAPIView,
    TopCategoriesReportAPIView,
)
from .dashboard.views import (
    DashboardAPIView,
    DashboardSummaryDetailAPIView,
    DashboardRecentTransactionsAPIView,
    DashboardBudgetsAPIView,
    DashboardGoalsAPIView,
    DashboardInsightsAPIView,
    DashboardAlertsAPIView,
)
from .backups.views import (
    DataBackupListCreateView,
    DataBackupDetailView,
    DataBackupDownloadView,
    BackupRestoreValidateView,
    BackupCleanupExpiredView,
)

app_name = 'transactions'

urlpatterns = [
    path('backups/', DataBackupListCreateView.as_view(), name='backup-list-create'),
    path('backups/<int:pk>/', DataBackupDetailView.as_view(), name='backup-detail'),
    path('backups/<int:pk>/download/', DataBackupDownloadView.as_view(), name='backup-download'),
    path('backups/validate-restore/', BackupRestoreValidateView.as_view(), name='backup-validate-restore'),
    path('backups/cleanup-expired/', BackupCleanupExpiredView.as_view(), name='backup-cleanup-expired'),

    path('categories/', CategoryListCreateView.as_view(), name='category-list-create'),
    path('categories/<int:pk>/', CategoryDetailView.as_view(), name='category-detail'),
    path('transactions/', TransactionListCreateView.as_view(), name='transaction-list-create'),
    path('transactions/<int:pk>/', TransactionDetailView.as_view(), name='transaction-detail'),
    path('budgets/', BudgetListCreateView.as_view(), name='budget-list-create'),
    path('budgets/<int:pk>/', BudgetDetailView.as_view(), name='budget-detail'),
    path('recurring-transactions/', RecurringTransactionListCreateView.as_view(), name='recurring-transaction-list-create'),
    path('recurring-transactions/<int:pk>/', RecurringTransactionDetailView.as_view(), name='recurring-transaction-detail'),
    path('recurring-transactions/<int:pk>/pause/', RecurringTransactionPauseView.as_view(), name='recurring-transaction-pause'),
    path('recurring-transactions/<int:pk>/resume/', RecurringTransactionResumeView.as_view(), name='recurring-transaction-resume'),
    path('recurring-transactions/<int:pk>/execute/', RecurringTransactionExecuteView.as_view(), name='recurring-transaction-execute'),
    path('recurring-transactions/<int:pk>/history/', RecurringTransactionHistoryView.as_view(), name='recurring-transaction-history'),
    path('goals/', FinancialGoalListCreateView.as_view(), name='financial-goal-list-create'),
    path('goals/<int:pk>/', FinancialGoalDetailView.as_view(), name='financial-goal-detail'),
    path('goals/<int:pk>/pause/', FinancialGoalPauseView.as_view(), name='financial-goal-pause'),
    path('goals/<int:pk>/resume/', FinancialGoalResumeView.as_view(), name='financial-goal-resume'),
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/mark-all-read/', NotificationMarkAllReadView.as_view(), name='notification-mark-all-read'),
    path('notifications/<int:pk>/', NotificationDetailView.as_view(), name='notification-detail'),

    path('audit-logs/', AuditLogListView.as_view(), name='audit-log-list'),
    path('audit-logs/<int:pk>/', AuditLogDetailView.as_view(), name='audit-log-detail'),

    path('analytics/summary/', DashboardSummaryAPIView.as_view(), name='analytics-summary'),
    path('analytics/trends/', FinancialTrendsAPIView.as_view(), name='analytics-trends'),
    path('analytics/monthly/', MonthlySummaryAPIView.as_view(), name='analytics-monthly'),
    path('analytics/categories/', CategoryAnalyticsAPIView.as_view(), name='analytics-categories'),
    path('analytics/comparison/', PeriodComparisonAPIView.as_view(), name='analytics-comparison'),
    path('analytics/budgets/', BudgetAnalyticsAPIView.as_view(), name='analytics-budgets'),

    path('export/transactions/', TransactionExportAPIView.as_view(), name='export-transactions'),
    path('export/categories/', CategoryExportAPIView.as_view(), name='export-categories'),
    path('export/budgets/', BudgetExportAPIView.as_view(), name='export-budgets'),
    path('export/goals/', FinancialGoalExportAPIView.as_view(), name='export-goals'),
    path('export/recurring/', RecurringTransactionExportAPIView.as_view(), name='export-recurring'),

    path('reports/financial/', FinancialReportAPIView.as_view(), name='reports-financial'),
    path('reports/income/', IncomeReportAPIView.as_view(), name='reports-income'),
    path('reports/expenses/', ExpenseReportAPIView.as_view(), name='reports-expenses'),
    path('reports/cash-flow/', CashFlowReportAPIView.as_view(), name='reports-cash-flow'),
    path('reports/categories/', CategoryReportAPIView.as_view(), name='reports-categories'),
    path('reports/monthly/', MonthlyReportAPIView.as_view(), name='reports-monthly'),
    path('reports/trends/', SpendingTrendsReportAPIView.as_view(), name='reports-trends'),
    path('reports/budgets/', BudgetComparisonReportAPIView.as_view(), name='reports-budgets'),
    path('reports/top-categories/', TopCategoriesReportAPIView.as_view(), name='reports-top-categories'),

    path('import/transactions/', TransactionImportAPIView.as_view(), name='import-transactions'),

    path('dashboard/', DashboardAPIView.as_view(), name='dashboard-overview'),
    path('dashboard/summary/', DashboardSummaryDetailAPIView.as_view(), name='dashboard-summary'),
    path('dashboard/recent-transactions/', DashboardRecentTransactionsAPIView.as_view(), name='dashboard-recent-transactions'),
    path('dashboard/budgets/', DashboardBudgetsAPIView.as_view(), name='dashboard-budgets'),
    path('dashboard/goals/', DashboardGoalsAPIView.as_view(), name='dashboard-goals'),
    path('dashboard/insights/', DashboardInsightsAPIView.as_view(), name='dashboard-insights'),
    path('dashboard/alerts/', DashboardAlertsAPIView.as_view(), name='dashboard-alerts'),
]




