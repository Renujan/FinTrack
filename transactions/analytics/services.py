import datetime
from decimal import Decimal
from django.db.models import Sum, Count, Avg, Q, Value
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, Coalesce
from rest_framework import serializers
from transactions.choices import TransactionType
from transactions.models import Transaction, Budget
from transactions.services import BudgetCalculationService


class AnalyticsService:
    """
    Service layer providing database-level aggregation and logic for financial analytics.
    Strictly isolated by user.
    """

    @staticmethod
    def get_user_transactions(user, start_date=None, end_date=None):
        """
        Returns transaction queryset scoped to the given user and optional date range.
        """
        qs = Transaction.objects.filter(user=user)
        if start_date:
            qs = qs.filter(date__gte=start_date)
        if end_date:
            qs = qs.filter(date__lte=end_date)
        return qs

    @classmethod
    def get_summary(cls, user, start_date=None, end_date=None):
        """
        Calculates overall financial summary statistics for the user.
        """
        qs = cls.get_user_transactions(user, start_date, end_date)

        income_filter = Q(transaction_type=TransactionType.INCOME)
        expense_filter = Q(transaction_type=TransactionType.EXPENSE)

        metrics = qs.aggregate(
            total_income=Coalesce(Sum('amount', filter=income_filter), Value(Decimal('0.00'))),
            total_expenses=Coalesce(Sum('amount', filter=expense_filter), Value(Decimal('0.00'))),
            transaction_count=Count('id'),
            income_transaction_count=Count('id', filter=income_filter),
            expense_transaction_count=Count('id', filter=expense_filter),
            avg_income=Coalesce(Avg('amount', filter=income_filter), Value(Decimal('0.00'))),
            avg_expense=Coalesce(Avg('amount', filter=expense_filter), Value(Decimal('0.00'))),
        )

        total_income = metrics['total_income']
        total_expenses = metrics['total_expenses']
        net_balance = total_income - total_expenses

        return {
            'total_income': f"{total_income:.2f}",
            'total_expenses': f"{total_expenses:.2f}",
            'net_balance': f"{net_balance:.2f}",
            'transaction_count': metrics['transaction_count'],
            'income_transaction_count': metrics['income_transaction_count'],
            'expense_transaction_count': metrics['expense_transaction_count'],
            'avg_income_transaction': f"{metrics['avg_income']:.2f}",
            'avg_expense_transaction': f"{metrics['avg_expense']:.2f}",
        }
