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
    FinancialGoalListCreateView,
    FinancialGoalDetailView,
    FinancialGoalPauseView,
    FinancialGoalResumeView,
    NotificationListView,
    NotificationDetailView,
    NotificationMarkAllReadView,
)
from .analytics.views import (
    DashboardSummaryAPIView,
    FinancialTrendsAPIView,
    MonthlySummaryAPIView,
    CategoryAnalyticsAPIView,
    PeriodComparisonAPIView,
    BudgetAnalyticsAPIView,
)

app_name = 'transactions'

urlpatterns = [
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
    path('goals/', FinancialGoalListCreateView.as_view(), name='financial-goal-list-create'),
    path('goals/<int:pk>/', FinancialGoalDetailView.as_view(), name='financial-goal-detail'),
    path('goals/<int:pk>/pause/', FinancialGoalPauseView.as_view(), name='financial-goal-pause'),
    path('goals/<int:pk>/resume/', FinancialGoalResumeView.as_view(), name='financial-goal-resume'),
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/mark-all-read/', NotificationMarkAllReadView.as_view(), name='notification-mark-all-read'),
    path('notifications/<int:pk>/', NotificationDetailView.as_view(), name='notification-detail'),


    path('analytics/summary/', DashboardSummaryAPIView.as_view(), name='analytics-summary'),
    path('analytics/trends/', FinancialTrendsAPIView.as_view(), name='analytics-trends'),
    path('analytics/monthly/', MonthlySummaryAPIView.as_view(), name='analytics-monthly'),
    path('analytics/categories/', CategoryAnalyticsAPIView.as_view(), name='analytics-categories'),
    path('analytics/comparison/', PeriodComparisonAPIView.as_view(), name='analytics-comparison'),
    path('analytics/budgets/', BudgetAnalyticsAPIView.as_view(), name='analytics-budgets'),
]



