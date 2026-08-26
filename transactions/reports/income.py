from decimal import Decimal
from django.db.models import Sum, Count, Avg, Min, Max, Value
from django.db.models.functions import Coalesce
from transactions.choices import TransactionType
from .base import get_user_transactions


class IncomeReportMixin:
    @classmethod
    def get_income_report(cls, user, start_date=None, end_date=None):
        """
        Generates user-scoped income report:
        - total_income
        - transaction_count
        - average
        - minimum
        - maximum
        """
        qs = get_user_transactions(
            user,
            start_date=start_date,
            end_date=end_date,
            transaction_type=TransactionType.INCOME
        )

        metrics = qs.aggregate(
            total=Coalesce(Sum('amount'), Value(Decimal('0.00'))),
            count=Count('id'),
            avg=Coalesce(Avg('amount'), Value(Decimal('0.00'))),
            min=Coalesce(Min('amount'), Value(Decimal('0.00'))),
            max=Coalesce(Max('amount'), Value(Decimal('0.00'))),
        )

        return {
            'total_income': f"{metrics['total']:.2f}",
            'transaction_count': metrics['count'],
            'average': f"{metrics['avg']:.2f}",
            'minimum': f"{metrics['min']:.2f}",
            'maximum': f"{metrics['max']:.2f}",
        }
