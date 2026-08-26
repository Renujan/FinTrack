from decimal import Decimal
from django.db.models import Sum, Count, Value
from django.db.models.functions import Coalesce
from transactions.choices import TransactionType
from .base import get_user_transactions


class CategoryReportMixin:
    @classmethod
    def get_category_report(cls, user, start_date=None, end_date=None, category=None):
        """
        Generates user-scoped category spending report for expenses:
        - category name
        - total spending
        - percentage of expenses
        - transaction count
        Sorted by total spending descending.
        """
        qs = get_user_transactions(
            user,
            start_date=start_date,
            end_date=end_date,
            category=category,
            transaction_type=TransactionType.EXPENSE
        )

        total_expenses_val = qs.aggregate(
            total=Coalesce(Sum('amount'), Value(Decimal('0.00')))
        )['total']

        aggregated = (
            qs.values('category_id', 'category__name')
            .annotate(
                total=Coalesce(Sum('amount'), Value(Decimal('0.00'))),
                transaction_count=Count('id')
            )
            .order_by('-total')
        )

        categories = []
        for row in aggregated:
            spent_amt = row['total']
            cat_id = row['category_id']
            cat_name = row['category__name'] or "Uncategorized"

            if total_expenses_val > Decimal('0.00'):
                pct = round(float((spent_amt / total_expenses_val) * Decimal('100.0')), 2)
            else:
                pct = 0.0

            categories.append({
                'category': cat_name,
                'category_id': cat_id,
                'total': f"{spent_amt:.2f}",
                'percentage': pct,
                'transaction_count': row['transaction_count'],
            })

        return {
            'categories': categories
        }
