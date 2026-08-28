from decimal import Decimal
from django.db.models import Sum, Count, Avg, Q, Value
from django.db.models.functions import Coalesce
from rest_framework import serializers
from transactions.choices import TransactionType
from transactions.models import Transaction
from transactions.analytics.services import AnalyticsService
from .overview import IncomeExpenseOverviewMixin


class SpendingInsightsMixin:
    """
    Mixin providing spending insights and top category breakdowns based on actual user financial data.
    """

    @classmethod
    def get_top_categories(cls, user, limit=5, start_date=None, end_date=None):
        """
        Retrieves user's top spending categories for expense transactions.
        Supports optional limit parameter (bounded 1 to 20, default 5).
        """
        try:
            limit_int = int(limit)
            if limit_int < 1:
                limit_int = 5
            elif limit_int > 20:
                limit_int = 20
        except (ValueError, TypeError):
            limit_int = 5

        categories_data = AnalyticsService.get_category_analytics(
            user=user,
            start_date=start_date,
            end_date=end_date,
            limit=limit_int
        )

        top_categories = []
        for cat in categories_data:
            top_categories.append({
                'category': cat['category'],
                'category_id': cat['category_id'],
                'spent': cat['spent'],
                'percentage': cat['percentage_of_total'],
                'transaction_count': cat['transaction_count'],
            })

        return top_categories

    @classmethod
    def get_spending_insights(cls, user, start_date=None, end_date=None):
        """
        Calculates key spending insights for user's expense transactions:
        highest spending category, largest recent expense, average expense,
        spending change percentage, and expense transaction count.
        """
        qs = Transaction.objects.filter(
            user=user,
            transaction_type=TransactionType.EXPENSE
        )
        if start_date:
            qs = qs.filter(date__gte=start_date)
        if end_date:
            qs = qs.filter(date__lte=end_date)

        expense_stats = qs.aggregate(
            expense_count=Count('id'),
            avg_expense=Coalesce(Avg('amount'), Value(Decimal('0.00'))),
            total_spent=Coalesce(Sum('amount'), Value(Decimal('0.00'))),
        )

        # 1. Highest Spending Category
        top_cat_list = cls.get_top_categories(user, limit=1, start_date=start_date, end_date=end_date)
        highest_category = top_cat_list[0] if top_cat_list else None

        # 2. Largest Recent Expense
        largest_txn = qs.select_related('category').order_by('-amount', '-date').first()
        largest_recent_expense = None
        if largest_txn:
            title = largest_txn.description if largest_txn.description else (largest_txn.category.name if largest_txn.category else "Expense")
            largest_recent_expense = {
                'id': largest_txn.id,
                'title': title,
                'description': largest_txn.description or "",
                'amount': f"{largest_txn.amount:.2f}",
                'category_name': largest_txn.category.name if largest_txn.category else "Uncategorized",
                'date': largest_txn.date.strftime('%Y-%m-%d'),
            }

        # 3. Spending Change Percentage vs Previous Period
        overview_data = IncomeExpenseOverviewMixin.get_income_expense_overview(
            user=user,
            start_date=start_date,
            end_date=end_date
        )
        spending_change_pct = overview_data.get('expense_percentage_change', '0.00')

        return {
            'highest_spending_category': highest_category,
            'largest_recent_expense': largest_recent_expense,
            'average_expense': f"{expense_stats['avg_expense']:.2f}",
            'spending_change_percentage': spending_change_pct,
            'expense_transaction_count': expense_stats['expense_count'],
            'total_expenses_amount': f"{expense_stats['total_spent']:.2f}",
        }
