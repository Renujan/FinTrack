from django.urls import path
from .views import (
    CategoryListCreateView,
    CategoryDetailView,
    TransactionListCreateView,
    TransactionDetailView,
    BudgetListCreateView,
    BudgetDetailView,
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
    path('analytics/summary/', DashboardSummaryAPIView.as_view(), name='analytics-summary'),
    path('analytics/trends/', FinancialTrendsAPIView.as_view(), name='analytics-trends'),
    path('analytics/monthly/', MonthlySummaryAPIView.as_view(), name='analytics-monthly'),
    path('analytics/categories/', CategoryAnalyticsAPIView.as_view(), name='analytics-categories'),
    path('analytics/comparison/', PeriodComparisonAPIView.as_view(), name='analytics-comparison'),
    path('analytics/budgets/', BudgetAnalyticsAPIView.as_view(), name='analytics-budgets'),
]


