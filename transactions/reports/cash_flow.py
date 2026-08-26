from decimal import Decimal
from django.db.models import Sum, Value, Q
from django.db.models.functions import Coalesce
from transactions.choices import TransactionType
from .base import get_user_transactions


class CashFlowReportMixin:
    @classmethod
    def get_cash_flow_report(cls, user, start_date=None, end_date=None):
        """
        Generates user-scoped cash flow report:
        - total_income
        - total_expenses
        - net_cash_flow (total_income - total_expenses)
        - savings_rate (net_cash_flow / total_income * 100, zero division safe)
        """
        qs = get_user_transactions(user, start_date=start_date, end_date=end_date)

        income_filter = Q(transaction_type=TransactionType.INCOME)
        expense_filter = Q(transaction_type=TransactionType.EXPENSE)

        metrics = qs.aggregate(
            total_income=Coalesce(Sum('amount', filter=income_filter), Value(Decimal('0.00'))),
            total_expenses=Coalesce(Sum('amount', filter=expense_filter), Value(Decimal('0.00'))),
        )

        total_income = metrics['total_income']
        total_expenses = metrics['total_expenses']
        net_cash_flow = total_income - total_expenses

        if total_income > Decimal('0.00'):
            savings_rate = round(float((net_cash_flow / total_income) * Decimal('100.0')), 2)
        else:
            savings_rate = 0.0

        return {
            'total_income': f"{total_income:.2f}",
            'total_expenses': f"{total_expenses:.2f}",
            'net_cash_flow': f"{net_cash_flow:.2f}",
            'savings_rate': savings_rate,
        }
