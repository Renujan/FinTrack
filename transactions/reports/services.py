from .income import IncomeReportMixin
from .expense import ExpenseReportMixin
from .cash_flow import CashFlowReportMixin
from .category import CategoryReportMixin
from .monthly import MonthlyReportMixin
from .trends import SpendingTrendsReportMixin
from .budget import BudgetComparisonReportMixin
from .top_categories import TopCategoriesReportMixin


class ReportService(
    IncomeReportMixin,
    ExpenseReportMixin,
    CashFlowReportMixin,
    CategoryReportMixin,
    MonthlyReportMixin,
    SpendingTrendsReportMixin,
    BudgetComparisonReportMixin,
    TopCategoriesReportMixin,
):
    """
    Unified ReportService providing comprehensive user-scoped financial reports:
    - get_income_report()
    - get_expense_report()
    - get_cash_flow_report()
    - get_category_report()
    - get_monthly_report()
    - get_budget_comparison()
    - get_spending_trends()
    - get_top_categories()

    All computations strictly isolated to the authenticated request user.
    """
    pass
