import datetime
from decimal import Decimal
from django.db.models import Sum, Count, Q, Value
from django.db.models.functions import TruncMonth, Coalesce
from transactions.choices import TransactionType
from transactions.models import Transaction


class CashFlowOverviewMixin:
    """
    Mixin providing cash flow overview aggregations suitable for financial charts.
    Aggregates monthly income, expenses, and net cash flow chronologically.
    """

    @classmethod
    def get_cash_flow_summary(cls, user, start_date=None, end_date=None, months=6):
        """
        Calculates monthly cash flow dataset for authenticated user.
        Groups transactions chronologically by month.
        """
        qs = Transaction.objects.filter(user=user)
        if start_date:
            qs = qs.filter(date__gte=start_date)
        if end_date:
            qs = qs.filter(date__lte=end_date)

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

        cash_flow_list = []
        for row in aggregated:
            m_dt = row['month_dt']
            if isinstance(m_dt, datetime.datetime):
                m_dt = m_dt.date()

            period_str = m_dt.strftime('%Y-%m') if m_dt else ""
            inc = row['income']
            exp = row['expenses']
            net = inc - exp

            cash_flow_list.append({
                'period': period_str,
                'income': f"{inc:.2f}",
                'expenses': f"{exp:.2f}",
                'net_cash_flow': f"{net:.2f}",
                'transaction_count': row['transaction_count'],
            })

        if not start_date and not end_date and len(cash_flow_list) > months:
            cash_flow_list = cash_flow_list[-months:]

        return cash_flow_list
