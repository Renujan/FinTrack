from decimal import Decimal
from django.utils import timezone
from transactions.models import Budget
from transactions.services import BudgetCalculationService


class BudgetOverviewMixin:
    """
    Mixin providing budget overview metrics for dashboard integration.
    Reuses BudgetCalculationService for spent and limit calculations.
    """

    @classmethod
    def get_budget_overview(cls, user):
        """
        Aggregates budget metrics for user: active budgets count, exceeded budgets count,
        near-limit budgets count, overall total budgeted, total spent, and remaining amounts.
        """
        budgets_qs = Budget.objects.filter(user=user).select_related('category')
        today = timezone.now().date()

        total_budgets = budgets_qs.count()
        active_budgets_count = 0
        exceeded_budgets_count = 0
        near_limit_count = 0

        total_budgeted_amount = Decimal('0.00')
        total_spent_amount = Decimal('0.00')
        budgets_summary = []

        for b in budgets_qs:
            metrics = BudgetCalculationService.calculate_budget_metrics(b)
            spent = metrics['spent_amount']
            rem = metrics['remaining_amount']
            pct = metrics['percentage_used']
            is_exc = metrics['is_exceeded']

            if b.start_date <= today <= b.end_date:
                active_budgets_count += 1

            if is_exc:
                exceeded_budgets_count += 1
            elif pct >= 80.0:
                near_limit_count += 1

            total_budgeted_amount += b.amount
            total_spent_amount += spent

            budgets_summary.append({
                'id': b.id,
                'name': b.name,
                'category_name': b.category.name if b.category else None,
                'is_overall': b.is_overall,
                'budget_amount': f"{b.amount:.2f}",
                'spent_amount': f"{spent:.2f}",
                'remaining_amount': f"{rem:.2f}",
                'percentage_used': pct,
                'is_exceeded': is_exc,
                'is_near_limit': (pct >= 80.0 and not is_exc),
            })

        remaining_amount = total_budgeted_amount - total_spent_amount

        if total_budgeted_amount > Decimal('0.00'):
            overall_utilization = round(float((total_spent_amount / total_budgeted_amount) * 100), 2)
        else:
            overall_utilization = 0.0

        return {
            'total_budgets': total_budgets,
            'active_budgets': active_budgets_count,
            'exceeded_budgets': exceeded_budgets_count,
            'budgets_near_limit': near_limit_count,
            'total_budget_amount': f"{total_budgeted_amount:.2f}",
            'total_spent_amount': f"{total_spent_amount:.2f}",
            'remaining_amount': f"{remaining_amount:.2f}",
            'overall_utilization_percentage': overall_utilization,
            'budgets_summary': budgets_summary,
        }
