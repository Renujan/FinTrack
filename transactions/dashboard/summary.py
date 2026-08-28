from decimal import Decimal
from django.db.models import Sum, Q, Value
from django.db.models.functions import Coalesce
from transactions.choices import TransactionType
from transactions.models import Transaction


class DashboardSummaryMixin:
    """
    Mixin providing financial dashboard summary calculations.
    Aggregates user-scoped total income, total expenses, current balance, and net cash flow.
    """

    @classmethod
    def get_financial_summary(cls, user, start_date=None, end_date=None):
        """
        Calculates total income, total expenses, current balance, and net cash flow for user.
        Supports date filtering via start_date and end_date.
        Uses Decimal precision for money calculations without floating point errors.
        """
        qs = Transaction.objects.filter(user=user)
        if start_date:
            qs = qs.filter(date__gte=start_date)
        if end_date:
            qs = qs.filter(date__lte=end_date)

        income_filter = Q(transaction_type=TransactionType.INCOME)
        expense_filter = Q(transaction_type=TransactionType.EXPENSE)

        metrics = qs.aggregate(
            total_income=Coalesce(Sum('amount', filter=income_filter), Value(Decimal('0.00'))),
            total_expenses=Coalesce(Sum('amount', filter=expense_filter), Value(Decimal('0.00'))),
        )

        total_income = metrics['total_income']
        total_expenses = metrics['total_expenses']
        current_balance = total_income - total_expenses
        net_cash_flow = current_balance

        return {
            'total_income': f"{total_income:.2f}",
            'total_expenses': f"{total_expenses:.2f}",
            'current_balance': f"{current_balance:.2f}",
            'net_cash_flow': f"{net_cash_flow:.2f}",
        }
