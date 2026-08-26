import datetime
from decimal import Decimal
from django.db.models import Sum, Count, Value, Q
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, Coalesce
from rest_framework import serializers
from transactions.choices import TransactionType
from .base import get_user_transactions


class SpendingTrendsReportMixin:
    @classmethod
    def get_spending_trends(cls, user, start_date=None, end_date=None, group_by='monthly'):
        """
        Generates spending trend reports aggregated by period (daily, weekly, monthly).
        Chronologically ordered.
        """
        group_by_lower = (group_by or 'monthly').lower()
        if group_by_lower in ('daily', 'day'):
            trunc_func = TruncDay
            fmt = '%Y-%m-%d'
            period_label = 'daily'
        elif group_by_lower in ('weekly', 'week'):
            trunc_func = TruncWeek
            fmt = '%Y-%m-%d'
            period_label = 'weekly'
        elif group_by_lower in ('monthly', 'month'):
            trunc_func = TruncMonth
            fmt = '%Y-%m'
            period_label = 'monthly'
        else:
            raise serializers.ValidationError({
                'period': [f"Invalid period parameter '{group_by}'. Allowed choices are: daily, weekly, monthly."]
            })

        qs = get_user_transactions(user, start_date=start_date, end_date=end_date)

        income_filter = Q(transaction_type=TransactionType.INCOME)
        expense_filter = Q(transaction_type=TransactionType.EXPENSE)

        aggregated = (
            qs.annotate(period_dt=trunc_func('date'))
            .values('period_dt')
            .annotate(
                income=Coalesce(Sum('amount', filter=income_filter), Value(Decimal('0.00'))),
                expenses=Coalesce(Sum('amount', filter=expense_filter), Value(Decimal('0.00'))),
                transaction_count=Count('id')
            )
            .order_by('period_dt')
        )

        trends = []
        for row in aggregated:
            p_dt = row['period_dt']
            if isinstance(p_dt, datetime.datetime):
                p_dt = p_dt.date()

            period_str = p_dt.strftime(fmt) if p_dt else ""
            inc = row['income']
            exp = row['expenses']
            net = inc - exp

            trends.append({
                'period': period_str,
                'income': f"{inc:.2f}",
                'expenses': f"{exp:.2f}",
                'net': f"{net:.2f}",
                'transaction_count': row['transaction_count'],
            })

        return {
            'period_type': period_label,
            'trends': trends,
        }
