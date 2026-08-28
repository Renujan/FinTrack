import datetime
from decimal import Decimal
from django.db.models import Sum, Q, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from transactions.choices import TransactionType
from transactions.models import Transaction


class IncomeExpenseOverviewMixin:
    """
    Mixin providing income and expense overview comparisons.
    Compares current period vs previous period metrics with safe percentage change calculations.
    """

    @staticmethod
    def calculate_percentage_change(current_val, previous_val):
        """
        Calculates percentage change safely. Prevents division-by-zero errors.
        Returns a formatted float string or safe default.
        """
        curr = Decimal(str(current_val))
        prev = Decimal(str(previous_val))

        if prev == Decimal('0.00'):
            if curr > Decimal('0.00'):
                return "100.00"
            elif curr < Decimal('0.00'):
                return "-100.00"
            else:
                return "0.00"

        change = ((curr - prev) / abs(prev)) * Decimal('100')
        return f"{change:.2f}"

    @classmethod
    def get_income_expense_overview(cls, user, start_date=None, end_date=None):
        """
        Calculates dashboard income and expense totals for current period vs previous period.
        Supports custom date ranges or defaults to Current Month vs Previous Month.
        """
        today = timezone.now().date()

        if start_date and end_date:
            curr_start = start_date
            curr_end = end_date
            period_type = 'custom'
        elif start_date and not end_date:
            curr_start = start_date
            curr_end = today
            period_type = 'custom'
        elif not start_date and end_date:
            curr_end = end_date
            curr_start = curr_end.replace(day=1)
            period_type = 'custom'
        else:
            curr_start = today.replace(day=1)
            curr_end = today
            period_type = 'monthly'

        if curr_start > curr_end:
            curr_start, curr_end = curr_end, curr_start

        days_count = (curr_end - curr_start).days + 1
        prev_end = curr_start - datetime.timedelta(days=1)
        prev_start = prev_end - datetime.timedelta(days=days_count - 1)

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
        prev_inc = prev_metrics['income']
        prev_exp = prev_metrics['expenses']

        income_change = cls.calculate_percentage_change(curr_inc, prev_inc)
        expense_change = cls.calculate_percentage_change(curr_exp, prev_exp)

        return {
            'period_type': period_type,
            'current_period': {
                'start_date': curr_start.strftime('%Y-%m-%d'),
                'end_date': curr_end.strftime('%Y-%m-%d'),
                'income': f"{curr_inc:.2f}",
                'expenses': f"{curr_exp:.2f}",
            },
            'previous_period': {
                'start_date': prev_start.strftime('%Y-%m-%d'),
                'end_date': prev_end.strftime('%Y-%m-%d'),
                'income': f"{prev_inc:.2f}",
                'expenses': f"{prev_exp:.2f}",
            },
            'income_percentage_change': income_change,
            'expense_percentage_change': expense_change,
        }

    @classmethod
    def get_income_summary(cls, user, start_date=None, end_date=None):
        """
        Returns standalone income summary for dashboard display.
        """
        overview = cls.get_income_expense_overview(user, start_date=start_date, end_date=end_date)
        return {
            'current_period_income': overview['current_period']['income'],
            'previous_period_income': overview['previous_period']['income'],
            'income_percentage_change': overview['income_percentage_change'],
            'period_type': overview['period_type'],
            'start_date': overview['current_period']['start_date'],
            'end_date': overview['current_period']['end_date'],
        }

    @classmethod
    def get_expense_summary(cls, user, start_date=None, end_date=None):
        """
        Returns standalone expense summary for dashboard display.
        """
        overview = cls.get_income_expense_overview(user, start_date=start_date, end_date=end_date)
        return {
            'current_period_expenses': overview['current_period']['expenses'],
            'previous_period_expenses': overview['previous_period']['expenses'],
            'expense_percentage_change': overview['expense_percentage_change'],
            'period_type': overview['period_type'],
            'start_date': overview['current_period']['start_date'],
            'end_date': overview['current_period']['end_date'],
        }

