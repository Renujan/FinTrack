from decimal import Decimal
from django.db.models import Sum, Count, Q, Value
from django.db.models.functions import Coalesce
from transactions.choices import TransactionType
from transactions.models import Transaction


class BalanceSummaryMixin:
    """
    Mixin providing transaction-based balance summary calculations.
    Distinguishes transaction-calculated balance from external bank account balances.
    """

    @classmethod
    def get_balance_summary(cls, user):
        """
        Calculates user's lifetime total income, total expenses, net balance, and transaction counts.
        Clarifies transaction-based balance context.
        """
        qs = Transaction.objects.filter(user=user)

        income_filter = Q(transaction_type=TransactionType.INCOME)
        expense_filter = Q(transaction_type=TransactionType.EXPENSE)

        metrics = qs.aggregate(
            total_income=Coalesce(Sum('amount', filter=income_filter), Value(Decimal('0.00'))),
            total_expenses=Coalesce(Sum('amount', filter=expense_filter), Value(Decimal('0.00'))),
            transaction_count=Count('id'),
            income_count=Count('id', filter=income_filter),
            expense_count=Count('id', filter=expense_filter),
        )

        total_income = metrics['total_income']
        total_expenses = metrics['total_expenses']
        current_balance = total_income - total_expenses

        return {
            'total_income': f"{total_income:.2f}",
            'total_expenses': f"{total_expenses:.2f}",
            'current_balance': f"{current_balance:.2f}",
            'transaction_count': metrics['transaction_count'],
            'income_transaction_count': metrics['income_count'],
            'expense_transaction_count': metrics['expense_count'],
            'balance_type': 'transaction_based',
            'note': 'Calculated strictly from recorded income and expense transactions. Distinguish from live bank account balance.',
        }
