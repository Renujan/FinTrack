import datetime
from decimal import Decimal
from django.db.models import Sum, Q, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from transactions.choices import TransactionType
from transactions.models import Transaction
from .overview import IncomeExpenseOverviewMixin


class MonthlyComparisonMixin:
    """
    Mixin providing monthly financial comparison summary.
    Compares current month performance against previous month safely.
    """

    @classmethod
    def get_monthly_comparison(cls, user):
        """
        Calculates monthly comparison metrics:
        Current Month vs Previous Month income difference, expense difference, balance difference,
        and safe percentage changes.
        """
        today = timezone.now().date()
        curr_start = today.replace(day=1)
        curr_end = today

        # Previous month calculation
        prev_end = curr_start - datetime.timedelta(days=1)
        prev_start = prev_end.replace(day=1)

        income_filter = Q(transaction_type=TransactionType.INCOME)
        expense_filter = Q(transaction_type=TransactionType.EXPENSE)

        curr_metrics = Transaction.objects.filter(
            user=user,
            date__gte=curr_start,
            date__lte=curr_end
        ).aggregate(
            income=Coalesce(Sum('amount', filter=income_filter), Value(Decimal('0.00'))),
            expenses=Coalesce(Sum('amount', filter=expense_filter), Value(Decimal('0.00'))),
        )

        prev_metrics = Transaction.objects.filter(
            user=user,
            date__gte=prev_start,
            date__lte=prev_end
        ).aggregate(
            income=Coalesce(Sum('amount', filter=income_filter), Value(Decimal('0.00'))),
            expenses=Coalesce(Sum('amount', filter=expense_filter), Value(Decimal('0.00'))),
        )

        curr_inc = curr_metrics['income']
        curr_exp = curr_metrics['expenses']
        curr_net = curr_inc - curr_exp

        prev_inc = prev_metrics['income']
        prev_exp = prev_metrics['expenses']
        prev_net = prev_inc - prev_exp

        inc_diff = curr_inc - prev_inc
        exp_diff = curr_exp - prev_exp
        net_diff = curr_net - prev_net

        inc_pct = IncomeExpenseOverviewMixin.calculate_percentage_change(curr_inc, prev_inc)
        exp_pct = IncomeExpenseOverviewMixin.calculate_percentage_change(curr_exp, prev_exp)
        net_pct = IncomeExpenseOverviewMixin.calculate_percentage_change(curr_net, prev_net)

        return {
            'current_month': curr_start.strftime('%Y-%m'),
            'previous_month': prev_start.strftime('%Y-%m'),
            'current_income': f"{curr_inc:.2f}",
            'previous_income': f"{prev_inc:.2f}",
            'income_difference': f"{inc_diff:.2f}",
            'income_percentage_change': inc_pct,
            'current_expenses': f"{curr_exp:.2f}",
            'previous_expenses': f"{prev_exp:.2f}",
            'expense_difference': f"{exp_diff:.2f}",
            'expense_percentage_change': exp_pct,
            'current_balance': f"{curr_net:.2f}",
            'previous_balance': f"{prev_net:.2f}",
            'balance_difference': f"{net_diff:.2f}",
            'balance_percentage_change': net_pct,
        }
