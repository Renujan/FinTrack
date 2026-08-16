from decimal import Decimal
from django.db.models import Sum, Q
from .choices import TransactionType
from .models import Transaction


class BudgetCalculationService:
    """
    Service layer to calculate financial usage and status metrics for budgets.
    Calculates spent_amount, remaining_amount, percentage_used, and is_exceeded.
    Budget consumption is based ONLY on EXPENSE transactions belonging to the budget's user
    within the budget date range [start_date, end_date].
    """

    @staticmethod
    def get_budget_transactions(budget):
        """
        Returns the queryset of expense transactions contributing to a budget's spending.
        """
        filters = Q(
            user=budget.user,
            transaction_type=TransactionType.EXPENSE,
            date__gte=budget.start_date,
            date__lte=budget.end_date
        )
        if budget.category_id is not None:
            filters &= Q(category_id=budget.category_id)
        return Transaction.objects.filter(filters)

    @classmethod
    def calculate_spent_amount(cls, budget):
        """
        Calculates total expense spending for a specific budget instance.
        """
        result = cls.get_budget_transactions(budget).aggregate(total=Sum('amount'))
        total_spent = result['total'] if result['total'] is not None else Decimal('0.00')
        return total_spent


    @classmethod
    def calculate_budget_metrics(cls, budget):
        """
        Calculates all usage metrics for a budget.
        Returns a dictionary containing spent_amount, remaining_amount, percentage_used, is_exceeded.
        """
        spent_amount = cls.calculate_spent_amount(budget)
        budget_amount = budget.amount

        remaining_amount = budget_amount - spent_amount

        if budget_amount > Decimal('0.00'):
            percentage_used = round(float((spent_amount / budget_amount) * 100), 2)
        else:
            percentage_used = 0.0

        is_exceeded = spent_amount > budget_amount

        return {
            'budget_amount': budget_amount,
            'spent_amount': spent_amount,
            'remaining_amount': remaining_amount,
            'percentage_used': percentage_used,
            'is_exceeded': is_exceeded,
        }
