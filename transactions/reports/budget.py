from decimal import Decimal
from transactions.models import Budget
from transactions.services import BudgetCalculationService


class BudgetComparisonReportMixin:
    @classmethod
    def get_budget_comparison(cls, user, start_date=None, end_date=None):
        """
        Generates budget vs actual spending report integrating BudgetCalculationService.
        """
        qs = Budget.objects.filter(user=user).select_related('category').order_by('-start_date')
        if start_date:
            qs = qs.filter(end_date__gte=start_date)
        if end_date:
            qs = qs.filter(start_date__lte=end_date)

        budgets_list = []
        for b in qs:
            metrics = BudgetCalculationService.calculate_budget_metrics(b)
            budgets_list.append({
                'budget': b.name,
                'budget_id': b.id,
                'category': b.category.name if b.category else None,
                'is_overall': b.is_overall if hasattr(b, 'is_overall') else (b.category_id is None),
                'budget_amount': f"{b.amount:.2f}",
                'spent': f"{metrics['spent_amount']:.2f}",
                'remaining': f"{metrics['remaining_amount']:.2f}",
                'percentage_used': metrics['percentage_used'],
                'is_exceeded': metrics['is_exceeded'],
            })

        return {
            'budgets': budgets_list
        }
