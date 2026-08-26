import datetime
from decimal import Decimal
from django.db.models import Sum, Count, Value, Q
from django.db.models.functions import TruncMonth, Coalesce
from transactions.choices import TransactionType
from .base import get_user_transactions


class MonthlyReportMixin:
    @classmethod
    def get_monthly_report(cls, user, start_date=None, end_date=None):
        """
        Generates monthly aggregated financial report chronologically:
        - month (YYYY-MM)
        - income
        - expenses
        - net
        - transaction_count
        """
        qs = get_user_transactions(user, start_date=start_date, end_date=end_date)

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

        reports = []
        for row in aggregated:
            m_dt = row['month_dt']
            if isinstance(m_dt, datetime.datetime):
                m_dt = m_dt.date()

            month_str = m_dt.strftime('%Y-%m') if m_dt else ""
            inc = row['income']
            exp = row['expenses']
            net = inc - exp

            reports.append({
                'month': month_str,
                'income': f"{inc:.2f}",
                'expenses': f"{exp:.2f}",
                'net': f"{net:.2f}",
                'transaction_count': row['transaction_count'],
            })

        return {
            'monthly_reports': reports
        }
