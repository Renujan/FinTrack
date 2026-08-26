from decimal import Decimal
from django.db.models import Sum, Count, Avg, Min, Max, Value
from django.db.models.functions import Coalesce
from transactions.choices import TransactionType
from .base import get_user_transactions


class ExpenseReportMixin:
    @classmethod
    def get_expense_report(cls, user, start_date=None, end_date=None, category=None, search=None):
        """
        Generates user-scoped expense report:
        - total_expenses
        - transaction_count
        - average
        - minimum
        - maximum
        """
        qs = get_user_transactions(
            user,
            start_date=start_date,
            end_date=end_date,
            category=category,
            transaction_type=TransactionType.EXPENSE,
            search=search
        )

        metrics = qs.aggregate(
            total=Coalesce(Sum('amount'), Value(Decimal('0.00'))),
            count=Count('id'),
            avg=Coalesce(Avg('amount'), Value(Decimal('0.00'))),
            min=Coalesce(Min('amount'), Value(Decimal('0.00'))),
            max=Coalesce(Max('amount'), Value(Decimal('0.00'))),
        )

        return {
            'total_expenses': f"{metrics['total']:.2f}",
            'transaction_count': metrics['count'],
            'average': f"{metrics['avg']:.2f}",
            'minimum': f"{metrics['min']:.2f}",
            'maximum': f"{metrics['max']:.2f}",
        }
