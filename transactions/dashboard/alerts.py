import datetime
from django.utils import timezone
from transactions.choices import GoalStatus
from transactions.models import Budget, FinancialGoal, RecurringTransaction, Notification
from transactions.services import BudgetCalculationService, GoalCalculationService


class DashboardAlertsMixin:
    """
    Mixin providing dashboard financial alerts aggregated from live user system data.
    Summarizes budget warnings, goal milestones, subscription limits, and upcoming recurring dues.
    """

    @classmethod
    def get_dashboard_alerts(cls, user):
        """
        Aggregates active financial alerts for the user:
        - BUDGET_EXCEEDED
        - BUDGET_NEAR_LIMIT
        - GOAL_COMPLETED
        - GOAL_NEAR_COMPLETION
        - SUBSCRIPTION_LIMIT_NEAR
        - RECURRING_DUE
        Returns structured list of alert objects suitable for dashboard UI components.
        """
        today = timezone.now().date()
        alerts = []

        # 1. Budget Alerts
        budgets_qs = Budget.objects.filter(user=user).select_related('category')
        for b in budgets_qs:
            metrics = BudgetCalculationService.calculate_budget_metrics(b)
            spent = metrics['spent_amount']
            budget_amt = b.amount
            pct = metrics['percentage_used']
            is_exc = metrics['is_exceeded']

            if is_exc:
                alerts.append({
                    'type': 'BUDGET_EXCEEDED',
                    'message': f"You have exceeded your budget '{b.name}'. Spent ${spent:.2f} of ${budget_amt:.2f} ({pct}%).",
                    'severity': 'danger',
                    'category': 'budget',
                    'metadata': {
                        'budget_id': b.id,
                        'budget_name': b.name,
                        'spent_amount': str(spent),
                        'budget_amount': str(budget_amt),
                        'percentage_used': pct,
                    }
                })
            elif pct >= 80.0:
                alerts.append({
                    'type': 'BUDGET_NEAR_LIMIT',
                    'message': f"Your budget '{b.name}' is close to its limit ({pct}% used). Spent ${spent:.2f} of ${budget_amt:.2f}.",
                    'severity': 'warning',
                    'category': 'budget',
                    'metadata': {
                        'budget_id': b.id,
                        'budget_name': b.name,
                        'spent_amount': str(spent),
                        'budget_amount': str(budget_amt),
                        'percentage_used': pct,
                    }
                })

        # 2. Financial Goal Alerts
        goals_qs = FinancialGoal.objects.filter(user=user, is_active=True).select_related('category')
        for g in goals_qs:
            metrics = GoalCalculationService.calculate_goal_metrics(g)
            current = metrics['current_amount']
            target = g.target_amount
            pct = metrics['percentage_complete']
            is_comp = metrics['is_completed']

            if is_comp:
                alerts.append({
                    'type': 'GOAL_COMPLETED',
                    'message': f"Congratulations! You reached your savings goal of ${target:.2f} for '{g.name}'.",
                    'severity': 'success',
                    'category': 'goal',
                    'metadata': {
                        'goal_id': g.id,
                        'goal_name': g.name,
                        'target_amount': str(target),
                        'current_amount': str(current),
                        'percentage_complete': pct,
                    }
                })
            elif pct >= 80.0:
                alerts.append({
                    'type': 'GOAL_NEAR_COMPLETION',
                    'message': f"Your goal '{g.name}' is near completion ({pct}% reached, ${current:.2f} of ${target:.2f}).",
                    'severity': 'info',
                    'category': 'goal',
                    'metadata': {
                        'goal_id': g.id,
                        'goal_name': g.name,
                        'target_amount': str(target),
                        'current_amount': str(current),
                        'percentage_complete': pct,
                    }
                })

        # 3. Subscription Limit Alerts
        try:
            from subscriptions.services import SubscriptionService
            usage_data = SubscriptionService.get_usage(user)
            plan_name = usage_data['plan']['name']
            usage_metrics = usage_data.get('usage', {})

            for limit_key, metric in usage_metrics.items():
                if isinstance(metric, dict) and metric.get('limit') not in (None, -1):
                    used = metric.get('used', 0)
                    limit = metric.get('limit', 1)
                    if limit > 0:
                        pct = (used / limit) * 100
                        if pct >= 80.0:
                            alerts.append({
                                'type': 'SUBSCRIPTION_LIMIT_NEAR',
                                'message': f"You are using {pct:.0f}% of your {plan_name} {limit_key} limit ({used}/{limit}).",
                                'severity': 'warning',
                                'category': 'subscription',
                                'metadata': {
                                    'resource': limit_key,
                                    'used': used,
                                    'limit': limit,
                                    'plan_name': plan_name,
                                }
                            })
        except Exception:
            pass

        # 4. Recurring Transaction Dues (Next 3 Days)
        due_window = today + datetime.timedelta(days=3)
        due_schedules = RecurringTransaction.objects.filter(
            user=user,
            is_active=True,
            next_run_date__lte=due_window
        ).select_related('category')

        for rec in due_schedules:
            alerts.append({
                'type': 'RECURRING_DUE',
                'message': f"Recurring transaction '{rec.name}' of ${rec.amount:.2f} is due on {rec.next_run_date}.",
                'severity': 'info',
                'category': 'recurring',
                'metadata': {
                    'recurring_id': rec.id,
                    'schedule_name': rec.name,
                    'amount': str(rec.amount),
                    'next_run_date': rec.next_run_date.strftime('%Y-%m-%d'),
                }
            })

        return alerts
