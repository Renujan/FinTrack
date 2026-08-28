from .summary import DashboardSummaryMixin
from .overview import IncomeExpenseOverviewMixin
from .balance import BalanceSummaryMixin
from .cash_flow import CashFlowOverviewMixin
from .recent import RecentTransactionsMixin
from .budgets import BudgetOverviewMixin
from .goals import GoalOverviewMixin
from .insights import SpendingInsightsMixin
from .alerts import DashboardAlertsMixin
from .comparison import MonthlyComparisonMixin


class DashboardService(
    DashboardSummaryMixin,
    IncomeExpenseOverviewMixin,
    BalanceSummaryMixin,
    CashFlowOverviewMixin,
    RecentTransactionsMixin,
    BudgetOverviewMixin,
    GoalOverviewMixin,
    SpendingInsightsMixin,
    DashboardAlertsMixin,
    MonthlyComparisonMixin,
):
    """
    Unified Financial Dashboard Aggregation Service.
    Aggregates user-scoped financial data into optimized dashboard responses.
    Reduces multiple frontend API requests into clean, consolidated endpoints.
    """

    @classmethod
    def get_dashboard_summary(cls, user, start_date=None, end_date=None, recent_limit=5, top_cat_limit=5):
        """
        Aggregates complete financial dashboard payload into a single optimized dictionary response.
        """
        return {
            'financial_summary': cls.get_financial_summary(user, start_date=start_date, end_date=end_date),
            'income_expense_overview': cls.get_income_expense_overview(user, start_date=start_date, end_date=end_date),
            'balance_summary': cls.get_balance_summary(user),
            'cash_flow_summary': cls.get_cash_flow_summary(user, start_date=start_date, end_date=end_date),
            'recent_transactions': cls.get_recent_transactions(user, limit=recent_limit),
            'budget_overview': cls.get_budget_overview(user),
            'goal_overview': cls.get_goal_overview(user),
            'spending_insights': cls.get_spending_insights(user, start_date=start_date, end_date=end_date),
            'top_categories': cls.get_top_categories(user, limit=top_cat_limit, start_date=start_date, end_date=end_date),
            'monthly_comparison': cls.get_monthly_comparison(user),
            'alerts': cls.get_dashboard_alerts(user),
        }
