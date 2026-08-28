from decimal import Decimal
from django.utils import timezone
from transactions.choices import GoalStatus
from transactions.models import FinancialGoal
from transactions.services import GoalCalculationService


class GoalOverviewMixin:
    """
    Mixin providing financial goal overview metrics for dashboard integration.
    Reuses GoalCalculationService for goal progress and dynamic status logic.
    """

    @classmethod
    def get_goal_overview(cls, user):
        """
        Aggregates financial goal metrics: total goals, active goals count, completed goals count,
        near completion count, total target amount, total saved amount, overall progress %.
        """
        goals_qs = FinancialGoal.objects.filter(user=user).select_related('category')
        today = timezone.now().date()

        total_goals = goals_qs.count()
        active_goals_count = 0
        completed_goals_count = 0
        near_completion_count = 0

        total_target_amount = Decimal('0.00')
        total_saved_amount = Decimal('0.00')
        goals_summary = []

        for g in goals_qs:
            metrics = GoalCalculationService.calculate_goal_metrics(g)
            current = metrics['current_amount']
            target = g.target_amount
            rem = metrics['remaining_amount']
            pct = metrics['percentage_complete']
            is_comp = metrics['is_completed']
            g_status = metrics['status']

            if g_status == GoalStatus.ACTIVE:
                active_goals_count += 1

            if is_comp:
                completed_goals_count += 1
            elif pct >= 80.0:
                near_completion_count += 1

            total_target_amount += target
            total_saved_amount += current

            days_remaining = (g.target_date - today).days if g.target_date >= today else 0

            goals_summary.append({
                'id': g.id,
                'name': g.name,
                'category_name': g.category.name if g.category else None,
                'target_amount': f"{target:.2f}",
                'current_amount': f"{current:.2f}",
                'remaining_amount': f"{rem:.2f}",
                'percentage_complete': pct,
                'status': g_status,
                'is_completed': is_comp,
                'is_near_completion': (pct >= 80.0 and not is_comp),
                'target_date': g.target_date.strftime('%Y-%m-%d'),
                'days_remaining': days_remaining,
            })

        if total_target_amount > Decimal('0.00'):
            overall_progress = round(float((total_saved_amount / total_target_amount) * 100), 2)
        else:
            overall_progress = 0.0

        return {
            'total_goals': total_goals,
            'active_goals': active_goals_count,
            'completed_goals': completed_goals_count,
            'near_completion_goals': near_completion_count,
            'total_target_amount': f"{total_target_amount:.2f}",
            'total_saved_amount': f"{total_saved_amount:.2f}",
            'overall_progress_percentage': overall_progress,
            'goals_summary': goals_summary,
        }
