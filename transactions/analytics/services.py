def parse_and_validate_date_range(params):
    """
    Parses and validates start_date and end_date query parameters.
    Returns a tuple (start_date_obj, end_date_obj).
    Raises DRF ValidationError if dates are malformed or start_date > end_date.
    """
    errors = {}
    parsed_start = None
    parsed_end = None

    start_str = params.get('start_date')
    if start_str:
        try:
            parsed_start = datetime.datetime.strptime(start_str, '%Y-%m-%d').date()
        except ValueError:
            errors['start_date'] = ["Invalid date format for start_date. Expected YYYY-MM-DD."]

    end_str = params.get('end_date')
    if end_str:
        try:
            parsed_end = datetime.datetime.strptime(end_str, '%Y-%m-%d').date()
        except ValueError:
            errors['end_date'] = ["Invalid date format for end_date. Expected YYYY-MM-DD."]

    if parsed_start and parsed_end and parsed_start > parsed_end:
        errors['start_date'] = ["start_date cannot be greater than end_date."]

    if errors:
        raise serializers.ValidationError(errors)

    return parsed_start, parsed_end


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

    @classmethod
    def get_trends(cls, user, start_date=None, end_date=None, group_by='monthly'):
        """
        Returns financial trends aggregated by period (daily, weekly, monthly).
        Chronologically ordered.
        """
        group_by_lower = (group_by or 'monthly').lower()
        if group_by_lower in ('daily', 'day'):
            trunc_func = TruncDay
            fmt = '%Y-%m-%d'
        elif group_by_lower in ('weekly', 'week'):
            trunc_func = TruncWeek
            fmt = '%Y-%m-%d'
        elif group_by_lower in ('monthly', 'month'):
            trunc_func = TruncMonth
            fmt = '%Y-%m'
        else:
            raise serializers.ValidationError({
                'group_by': [f"Invalid group_by parameter '{group_by}'. Allowed choices are: daily, weekly, monthly."]
            })

        qs = cls.get_user_transactions(user, start_date, end_date)

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
            period_dt = row['period_dt']
            if isinstance(period_dt, datetime.datetime):
                period_dt = period_dt.date()

            period_str = period_dt.strftime(fmt) if period_dt else ""
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

        return trends

    @classmethod
    def get_monthly_summary(cls, user, start_date=None, end_date=None):
        """
        Returns financial summaries grouped by month chronologically.
        """
        qs = cls.get_user_transactions(user, start_date, end_date)

        income_filter = Q(transaction_type=TransactionType.INCOME)
        expense_filter = Q(transaction_type=TransactionType.EXPENSE)

        aggregated = (
            qs.annotate(month_dt=TruncMonth('date'))
            .values('month_dt')
            .annotate(
                income=Coalesce(Sum('amount', filter=income_filter), Value(Decimal('0.00'))),
                expenses=Coalesce(Sum('amount', filter=expense_filter), Value(Decimal('0.00'))),
                transaction_count=Count('id')
            )
            .order_by('month_dt')
        )

        monthly = []
        for row in aggregated:
            m_dt = row['month_dt']
            if isinstance(m_dt, datetime.datetime):
                m_dt = m_dt.date()

            month_str = m_dt.strftime('%Y-%m') if m_dt else ""
            inc = row['income']
            exp = row['expenses']
            net = inc - exp

            monthly.append({
                'month': month_str,
                'income': f"{inc:.2f}",
                'expenses': f"{exp:.2f}",
                'net_balance': f"{net:.2f}",
                'transaction_count': row['transaction_count'],
            })

        return monthly

    @classmethod
    def get_category_analytics(cls, user, start_date=None, end_date=None, limit=None):
        """
        Calculates category spending analytics for expense transactions.
        Ordered by spending amount descending. Supports an optional limit parameter.
        """
        if limit is not None:
            try:
                limit_int = int(limit)
                if limit_int <= 0 or limit_int > 100:
                    raise ValueError()
            except (ValueError, TypeError):
                raise serializers.ValidationError({
                    'limit': ["limit must be a positive integer between 1 and 100."]
                })
        else:
            limit_int = None

        qs = cls.get_user_transactions(user, start_date, end_date).filter(
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
            .order_by('-spent')
        )

        if limit_int:
            aggregated = aggregated[:limit_int]

        results = []
        for row in aggregated:
            cat_id = row['category_id']
            cat_name = row['category__name'] or "Uncategorized"
            spent_amt = row['spent']

            if total_expenses_val > Decimal('0.00'):
                pct = round(float((spent_amt / total_expenses_val) * 100), 2)
            else:
                pct = 0.0

            results.append({
                'category': cat_name,
                'category_id': cat_id,
                'spent': f"{spent_amt:.2f}",
                'transaction_count': row['transaction_count'],
                'percentage_of_total': pct,
            })

        return results

    @classmethod
    def get_period_comparison(cls, user, start_date=None, end_date=None):
        """
        Compares financial metrics for selected period with the immediately preceding equal-length period.
        Handles zero previous values safely without division by zero.
        """
        if start_date and end_date:
            curr_start = start_date
            curr_end = end_date
        elif start_date and not end_date:
            curr_start = start_date
            curr_end = datetime.date.today()
        elif not start_date and end_date:
            curr_end = end_date
            curr_start = curr_end.replace(day=1)
        else:
            curr_end = datetime.date.today()
            curr_start = curr_end.replace(day=1)

        if curr_start > curr_end:
            curr_start, curr_end = curr_end, curr_start

        days_count = (curr_end - curr_start).days + 1
        prev_end = curr_start - datetime.timedelta(days=1)
        prev_start = prev_end - datetime.timedelta(days=days_count - 1)

        curr_summary = cls.get_summary(user, curr_start, curr_end)
        prev_summary = cls.get_summary(user, prev_start, prev_end)

        curr_inc = Decimal(curr_summary['total_income'])
        prev_inc = Decimal(prev_summary['total_income'])
        curr_exp = Decimal(curr_summary['total_expenses'])
        prev_exp = Decimal(prev_summary['total_expenses'])
        curr_net = Decimal(curr_summary['net_balance'])
        prev_net = Decimal(prev_summary['net_balance'])

        def calc_change_pct(curr, prev):
            if prev == Decimal('0.00'):
                if curr > Decimal('0.00'):
                    return "100.00"
                elif curr < Decimal('0.00'):
                    return "-100.00"
                else:
                    return "0.00"
            change = ((curr - prev) / abs(prev)) * Decimal('100')
            return f"{change:.2f}"

        return {
            'current_period': {
                'start_date': curr_start.strftime('%Y-%m-%d'),
                'end_date': curr_end.strftime('%Y-%m-%d'),
                'income': curr_summary['total_income'],
                'expenses': curr_summary['total_expenses'],
                'net_balance': curr_summary['net_balance'],
                'transaction_count': curr_summary['transaction_count'],
            },
            'previous_period': {
                'start_date': prev_start.strftime('%Y-%m-%d'),
                'end_date': prev_end.strftime('%Y-%m-%d'),
                'income': prev_summary['total_income'],
                'expenses': prev_summary['total_expenses'],
                'net_balance': prev_summary['net_balance'],
                'transaction_count': prev_summary['transaction_count'],
            },
            'income_change': calc_change_pct(curr_inc, prev_inc),
            'expense_change': calc_change_pct(curr_exp, prev_exp),
            'net_change': calc_change_pct(curr_net, prev_net),
        }
