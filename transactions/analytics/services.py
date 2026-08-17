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
