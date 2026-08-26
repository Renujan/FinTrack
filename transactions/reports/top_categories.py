from decimal import Decimal
from django.db.models import Sum, Count, Value
from django.db.models.functions import Coalesce
from rest_framework import serializers
from transactions.choices import TransactionType
from .base import get_user_transactions


class TopCategoriesReportMixin:
    @classmethod
    def get_top_categories(cls, user, start_date=None, end_date=None, limit=5):
        """
        Generates top spending categories report.
        Supports customizable integer limit (1 to 100, default 5).
        """
        try:
            limit_int = int(limit)
            if limit_int < 1 or limit_int > 100:
                raise ValueError()
        except (ValueError, TypeError):
            raise serializers.ValidationError({
                'limit': ["limit must be a positive integer between 1 and 100."]
            })

        qs = get_user_transactions(
            user,
            start_date=start_date,
            end_date=end_date,
            transaction_type=TransactionType.EXPENSE
        )

        total_expenses_val = qs.aggregate(
            total=Coalesce(Sum('amount'), Value(Decimal('0.00')))
        )['total']

        aggregated = (
            qs.values('category_id', 'category__name')
            .annotate(
                spent=Coalesce(Sum('amount'), Value(Decimal('0.00'))),
                transaction_count=Count('id')
            )
            .order_by('-spent')[:limit_int]
        )

        top_cats = []
        for row in aggregated:
            spent_amt = row['spent']
            cat_id = row['category_id']
            cat_name = row['category__name'] or "Uncategorized"

            if total_expenses_val > Decimal('0.00'):
                pct = round(float((spent_amt / total_expenses_val) * Decimal('100.0')), 2)
            else:
                pct = 0.0

            top_cats.append({
                'category': cat_name,
                'category_id': cat_id,
                'amount': f"{spent_amt:.2f}",
                'percentage': pct,
                'transaction_count': row['transaction_count'],
            })

        return {
            'top_categories': top_cats
        }
