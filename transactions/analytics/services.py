import datetime
from decimal import Decimal
from django.db.models import Sum, Count, Avg, Q, Value
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, Coalesce
from rest_framework import serializers
from transactions.choices import TransactionType
from transactions.models import Transaction, Budget
from transactions.services import BudgetCalculationService


def parse_and_validate_analytics_filters(params):
    """
    Parses and validates common query parameters for analytics endpoints:
    start_date, end_date, category, transaction_type, limit.
    """
    errors = {}
    parsed_start = None
    parsed_end = None
    category = params.get('category')
    transaction_type = params.get('transaction_type')
    limit_val = params.get('limit')

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

    if transaction_type and transaction_type.upper() not in [TransactionType.INCOME, TransactionType.EXPENSE]:
        errors['transaction_type'] = [f"Invalid transaction_type. Choice must be {TransactionType.INCOME} or {TransactionType.EXPENSE}."]

    parsed_limit = None
    if limit_val is not None:
        try:
            parsed_limit = int(limit_val)
            if parsed_limit <= 0 or parsed_limit > 100:
                errors['limit'] = ["limit must be a positive integer between 1 and 100."]
        except (ValueError, TypeError):
            errors['limit'] = ["limit must be a valid integer."]

    if errors:
        raise serializers.ValidationError(errors)

    return parsed_start, parsed_end, category, transaction_type, parsed_limit


def parse_and_validate_date_range(params):
    """
    Parses and validates start_date and end_date query parameters.
    Maintained for backward compatibility.
    """
    parsed_start, parsed_end, _, _, _ = parse_and_validate_analytics_filters(params)
    return parsed_start, parsed_end


class FinancialAnalyticsService:
    """
    Dedicated service providing database-level financial analytics and aggregations.
    All operations are strictly scoped to the authenticated user.
    """

    @staticmethod
    def get_user_transactions(user, start_date=None, end_date=None, category=None, transaction_type=None):
        """
        Returns a transaction queryset scoped to the given user and optional filters.
        Optimized using select_related('category').
        """
        qs = Transaction.objects.filter(user=user).select_related('category')
        if start_date:
            qs = qs.filter(date__gte=start_date)
        if end_date:
            qs = qs.filter(date__lte=end_date)
        if category:
            if str(category).isdigit():
                qs = qs.filter(category_id=int(category))
            else:
                qs = qs.filter(category__name__iexact=str(category))
        if transaction_type:
            qs = qs.filter(transaction_type=transaction_type.upper())
        return qs

    @classmethod
    def get_summary(cls, user, start_date=None, end_date=None, category=None, transaction_type=None):
        """
        Calculates overall financial summary statistics for the dashboard.
        Returns total_income, total_expenses, net_balance, savings_rate, and transaction counts.
        """
        qs = cls.get_user_transactions(user, start_date, end_date, category, transaction_type)

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

        if total_income > Decimal('0.00'):
            savings_rate = round(float((net_balance / total_income) * Decimal('100.00')), 2)
        else:
            savings_rate = 0.0

        return {
            'total_income': round(float(total_income), 2),
            'total_expenses': round(float(total_expenses), 2),
            'net_balance': round(float(net_balance), 2),
            'savings_rate': savings_rate,
            'transaction_count': metrics['transaction_count'],
            'income_transaction_count': metrics['income_transaction_count'],
            'expense_transaction_count': metrics['expense_transaction_count'],
            'avg_income_transaction': round(float(metrics['avg_income']), 2),
            'avg_expense_transaction': round(float(metrics['avg_expense']), 2),
        }

    @classmethod
    def get_income_expense_totals(cls, user, start_date=None, end_date=None, category=None, transaction_type=None):
        """
        Returns totals and metrics for income and expense analysis.
        """
        summary = cls.get_summary(user, start_date, end_date, category, transaction_type)
        return {
            'income': summary['total_income'],
            'expenses': summary['total_expenses'],
            'net': summary['net_balance'],
            'savings_rate': summary['savings_rate'],
            'transaction_count': summary['transaction_count'],
            'income_count': summary['income_transaction_count'],
            'expense_count': summary['expense_transaction_count'],
        }

    @classmethod
    def get_net_balance(cls, user, start_date=None, end_date=None, category=None):
        """
        Calculates net balance for given user and filters.
        """
        summary = cls.get_summary(user, start_date, end_date, category)
        return summary['net_balance']

    @classmethod
    def get_savings_rate(cls, user, start_date=None, end_date=None, category=None):
        """
        Calculates savings rate percentage safely.
        """
        summary = cls.get_summary(user, start_date, end_date, category)
        return summary['savings_rate']

    @classmethod
    def get_category_breakdown(cls, user, start_date=None, end_date=None, category=None, limit=None):
        """
        Calculates category spending analytics for expense transactions.
        """
        qs = cls.get_user_transactions(user, start_date, end_date, category).filter(
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

        if limit:
            aggregated = aggregated[:limit]

        results = []
        for row in aggregated:
            cat_id = row['category_id']
            cat_name = row['category__name'] or "Uncategorized"
            spent_amt = row['spent']

            if total_expenses_val > Decimal('0.00'):
                pct = round(float((spent_amt / total_expenses_val) * Decimal('100.00')), 2)
            else:
                pct = 0.0

            results.append({
                'category': cat_name,
                'category_id': cat_id,
                'amount': round(float(spent_amt), 2),
                'spent': round(float(spent_amt), 2),
                'percentage': pct,
                'percentage_of_total': pct,
                'transaction_count': row['transaction_count'],
            })

        return results

    @classmethod
    def get_income_breakdown(cls, user, start_date=None, end_date=None, category=None, limit=None):
        """
        Calculates income breakdown by category for income transactions.
        """
        qs = cls.get_user_transactions(user, start_date, end_date, category).filter(
            transaction_type=TransactionType.INCOME
        )

        total_income_val = qs.aggregate(
            total=Coalesce(Sum('amount'), Value(Decimal('0.00')))
        )['total']

        aggregated = (
            qs.values('category_id', 'category__name')
            .annotate(
                income=Coalesce(Sum('amount'), Value(Decimal('0.00'))),
                transaction_count=Count('id')
            )
            .order_by('-income')
        )

        if limit:
            aggregated = aggregated[:limit]

        results = []
        for row in aggregated:
            cat_id = row['category_id']
            cat_name = row['category__name'] or "Uncategorized"
            inc_amt = row['income']

            if total_income_val > Decimal('0.00'):
                pct = round(float((inc_amt / total_income_val) * Decimal('100.00')), 2)
            else:
                pct = 0.0

            results.append({
                'category': cat_name,
                'category_id': cat_id,
                'amount': round(float(inc_amt), 2),
                'income': round(float(inc_amt), 2),
                'percentage': pct,
                'percentage_of_total': pct,
                'transaction_count': row['transaction_count'],
            })

        return results

    @classmethod
    def get_daily_trends(cls, user, start_date=None, end_date=None, category=None):
        """
        Returns daily income, expenses, and net balance aggregated using TruncDay.
        """
        qs = cls.get_user_transactions(user, start_date, end_date, category)

        income_filter = Q(transaction_type=TransactionType.INCOME)
        expense_filter = Q(transaction_type=TransactionType.EXPENSE)

        aggregated = (
            qs.annotate(day_dt=TruncDay('date'))
            .values('day_dt')
            .annotate(
                income=Coalesce(Sum('amount', filter=income_filter), Value(Decimal('0.00'))),
                expenses=Coalesce(Sum('amount', filter=expense_filter), Value(Decimal('0.00'))),
                transaction_count=Count('id')
            )
            .order_by('day_dt')
        )

        trends = []
        for row in aggregated:
            day_dt = row['day_dt']
            if isinstance(day_dt, datetime.datetime):
                day_dt = day_dt.date()

            date_str = day_dt.strftime('%Y-%m-%d') if day_dt else ""
            inc = row['income']
            exp = row['expenses']

            trends.append({
                'date': date_str,
                'income': round(float(inc), 2),
                'expenses': round(float(exp), 2),
                'net': round(float(inc - exp), 2),
                'transaction_count': row['transaction_count'],
            })

        return trends

    @classmethod
    def get_monthly_trends(cls, user, start_date=None, end_date=None, category=None):
        """
        Returns monthly income, expenses, and net balance aggregated using TruncMonth.
        Works across year boundaries.
        """
        qs = cls.get_user_transactions(user, start_date, end_date, category)

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

            monthly.append({
                'month': month_str,
                'income': round(float(inc), 2),
                'expenses': round(float(exp), 2),
                'net': round(float(inc - exp), 2),
                'net_balance': round(float(inc - exp), 2),
                'transaction_count': row['transaction_count'],
            })

        return monthly

    @classmethod
    def get_trends(cls, user, start_date=None, end_date=None, group_by='monthly', category=None):
        """
        Returns financial trends aggregated by period (daily, weekly, monthly).
        """
        group_by_lower = (group_by or 'monthly').lower()
        if group_by_lower in ('daily', 'day'):
            return cls.get_daily_trends(user, start_date, end_date, category)
        elif group_by_lower in ('monthly', 'month'):
            return cls.get_monthly_trends(user, start_date, end_date, category)
        elif group_by_lower in ('weekly', 'week'):
            qs = cls.get_user_transactions(user, start_date, end_date, category)
            income_filter = Q(transaction_type=TransactionType.INCOME)
            expense_filter = Q(transaction_type=TransactionType.EXPENSE)
            aggregated = (
                qs.annotate(period_dt=TruncWeek('date'))
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
                p_str = p_dt.strftime('%Y-%m-%d') if p_dt else ""
                inc = row['income']
                exp = row['expenses']
                trends.append({
                    'period': p_str,
                    'income': round(float(inc), 2),
                    'expenses': round(float(exp), 2),
                    'net': round(float(inc - exp), 2),
                    'transaction_count': row['transaction_count'],
                })
            return trends
        else:
            raise serializers.ValidationError({
                'group_by': [f"Invalid group_by parameter '{group_by}'. Allowed choices are: daily, weekly, monthly."]
            })

    @classmethod
    def get_monthly_summary(cls, user, start_date=None, end_date=None):
        """
        Returns financial summaries grouped chronologically by month.
        """
        return cls.get_monthly_trends(user, start_date, end_date)

    @classmethod
    def get_category_analytics(cls, user, start_date=None, end_date=None, limit=None):
        """
        Category spending analytics wrapper.
        """
        return cls.get_category_breakdown(user, start_date, end_date, limit=limit)

    @classmethod
    def get_top_categories(cls, user, limit=5, start_date=None, end_date=None):
        """
        Returns top spending categories.
        """
        return cls.get_category_breakdown(user, start_date, end_date, limit=limit)

    @classmethod
    def get_budget_performance(cls, user, start_date=None, end_date=None):
        """
        Calculates user-scoped budget performance metrics by integrating BudgetCalculationService.
        """
        budgets_qs = Budget.objects.filter(user=user).select_related('category')
        if start_date:
            budgets_qs = budgets_qs.filter(end_date__gte=start_date)
        if end_date:
            budgets_qs = budgets_qs.filter(start_date__lte=end_date)

        today = datetime.date.today()
        total_budgets = budgets_qs.count()
        active_budgets_count = 0
        exceeded_budgets_count = 0

        total_budgeted_amount = Decimal('0.00')
        total_budget_spending = Decimal('0.00')
        budgets_summary = []

        for b in budgets_qs:
            metrics = BudgetCalculationService.calculate_budget_metrics(b)
            if b.start_date <= today <= b.end_date:
                active_budgets_count += 1
            if metrics['is_exceeded']:
                exceeded_budgets_count += 1

            total_budgeted_amount += b.amount
            total_budget_spending += metrics['spent_amount']

            budgets_summary.append({
                'id': b.id,
                'name': b.name,
                'category_name': b.category.name if b.category else None,
                'is_overall': b.is_overall,
                'budget_amount': round(float(b.amount), 2),
                'spent_amount': round(float(metrics['spent_amount']), 2),
                'remaining_amount': round(float(metrics['remaining_amount']), 2),
                'percentage_used': metrics['percentage_used'],
                'is_exceeded': metrics['is_exceeded'],
            })

        if total_budgeted_amount > Decimal('0.00'):
            overall_utilization = round(float((total_budget_spending / total_budgeted_amount) * Decimal('100.00')), 2)
        else:
            overall_utilization = 0.0

        return {
            'total_budgets': total_budgets,
            'active_budgets_count': active_budgets_count,
            'exceeded_budgets_count': exceeded_budgets_count,
            'total_budgeted_amount': round(float(total_budgeted_amount), 2),
            'total_budget_spending': round(float(total_budget_spending), 2),
            'overall_budget_utilization': overall_utilization,
            'budgets_summary': budgets_summary,
        }

    @classmethod
    def get_budget_analytics(cls, user, start_date=None, end_date=None):
        """
        Alias for get_budget_performance.
        """
        return cls.get_budget_performance(user, start_date, end_date)

    @classmethod
    def get_recent_transactions(cls, user, limit=5):
        """
        Returns dashboard-friendly recent transactions sliced efficiently.
        """
        qs = Transaction.objects.filter(user=user).select_related('category').order_by('-date', '-created_at')[:limit]
        recent = []
        for tx in qs:
            recent.append({
                'id': tx.id,
                'title': tx.title,
                'amount': round(float(tx.amount), 2),
                'transaction_type': tx.transaction_type,
                'date': tx.date.strftime('%Y-%m-%d'),
                'category_id': tx.category.id if tx.category else None,
                'category_name': tx.category.name if tx.category else 'Uncategorized',
            })
        return recent

    @classmethod
    def get_period_comparison(cls, user, start_date=None, end_date=None):
        """
        Compares metrics with preceding equal-length period safely.
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

        curr_inc = Decimal(str(curr_summary['total_income']))
        prev_inc = Decimal(str(prev_summary['total_income']))
        curr_exp = Decimal(str(curr_summary['total_expenses']))
        prev_exp = Decimal(str(prev_summary['total_expenses']))
        curr_net = Decimal(str(curr_summary['net_balance']))
        prev_net = Decimal(str(prev_summary['net_balance']))

        def calc_change_pct(curr, prev):
            if prev == Decimal('0.00'):
                if curr > Decimal('0.00'):
                    return 100.0
                elif curr < Decimal('0.00'):
                    return -100.0
                else:
                    return 0.0
            change = ((curr - prev) / abs(prev)) * Decimal('100.00')
            return round(float(change), 2)

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


# Alias class name as required by specification
AnalyticsService = FinancialAnalyticsService
