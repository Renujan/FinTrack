from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from .models import SubscriptionPlan, UserSubscription
from .choices import BillingPeriod, SubscriptionStatus
from .exceptions import PlanLimitReachedException


class SubscriptionService:
    @staticmethod
    def get_or_create_default_free_plan():
        """
        Retrieves or creates the default Free subscription plan with standard system limits.
        """
        plan, _ = SubscriptionPlan.objects.get_or_create(
            code='free',
            defaults={
                'name': 'Free Plan',
                'description': 'Default free plan with essential personal finance features and standard limits.',
                'price': Decimal('0.00'),
                'billing_period': BillingPeriod.MONTHLY,
                'max_transactions': 500,
                'max_budgets': 5,
                'max_goals': 3,
                'max_categories': 20,
                'max_recurring_transactions': 5,
                'max_import_size': 100,
                'features': {
                    'export_csv': True,
                    'analytics_dashboard': True,
                    'priority_support': False,
                    'advanced_reports': False,
                },
                'is_active': True,
            }
        )
        return plan

    @staticmethod
    def get_or_create_premium_plan():
        """
        Retrieves or creates the default Premium subscription plan with higher system limits.
        """
        plan, _ = SubscriptionPlan.objects.get_or_create(
            code='premium',
            defaults={
                'name': 'Premium Plan',
                'description': 'Premium plan designed for power users needing higher limits and advanced capabilities.',
                'price': Decimal('19.99'),
                'billing_period': BillingPeriod.MONTHLY,
                'max_transactions': 10000,
                'max_budgets': 50,
                'max_goals': 50,
                'max_categories': 100,
                'max_recurring_transactions': 50,
                'max_import_size': 5000,
                'features': {
                    'export_csv': True,
                    'analytics_dashboard': True,
                    'priority_support': True,
                    'advanced_reports': True,
                },
                'is_active': True,
            }
        )
        return plan

    @classmethod
    def get_current_subscription(cls, user):
        """
        Gets the current user subscription. Automatically provisions a Free plan subscription
        if none exists for the authenticated user. Safely updates expired statuses.
        """
        free_plan = cls.get_or_create_default_free_plan()
        subscription, created = UserSubscription.objects.get_or_create(
            user=user,
            defaults={
                'plan': free_plan,
                'status': SubscriptionStatus.ACTIVE,
                'start_date': timezone.now(),
                'auto_renew': True
            }
        )

        # Evaluate expiration state dynamically
        if subscription.status == SubscriptionStatus.ACTIVE and subscription.is_expired:
            subscription.status = SubscriptionStatus.EXPIRED
            subscription.save(update_fields=['status'])

        return subscription

    @classmethod
    def get_current_plan(cls, user):
        """
        Returns the SubscriptionPlan for the user's active subscription.
        If subscription is EXPIRED or CANCELLED, falls back to Free plan limits.
        """
        subscription = cls.get_current_subscription(user)
        if subscription.effective_status in [SubscriptionStatus.EXPIRED, SubscriptionStatus.CANCELLED]:
            return cls.get_or_create_default_free_plan()
        return subscription.plan

    @classmethod
    def get_effective_status(cls, user):
        """
        Returns the calculated subscription status for the given user.
        """
        subscription = cls.get_current_subscription(user)
        return subscription.effective_status

    @classmethod
    def has_feature(cls, user, feature_name):
        """
        Checks if the current plan features dictionary includes the specified feature flag.
        """
        plan = cls.get_current_plan(user)
        return bool(plan.features.get(feature_name, False))

    @classmethod
    def get_usage(cls, user):
        """
        Calculates and returns complete resource usage breakdown against current plan limits.
        """
        from transactions.models import Transaction, Budget, FinancialGoal, Category, RecurringTransaction

        subscription = cls.get_current_subscription(user)
        plan = cls.get_current_plan(user)
        now = timezone.now()

        # Monthly transaction count
        txn_used = Transaction.objects.filter(
            user=user,
            date__year=now.year,
            date__month=now.month
        ).count()

        budget_used = Budget.objects.filter(user=user).count()
        goal_used = FinancialGoal.objects.filter(user=user).count()
        category_used = Category.objects.filter(user=user).count()
        recurring_used = RecurringTransaction.objects.filter(user=user).count()

        def build_metric(used, limit):
            if limit == -1:
                return {
                    "used": used,
                    "limit": -1,
                    "remaining": -1
                }
            remaining = max(0, limit - used)
            return {
                "used": used,
                "limit": limit,
                "remaining": remaining
            }

        return {
            "plan": {
                "code": plan.code,
                "name": plan.name,
                "status": subscription.effective_status,
                "billing_period": plan.billing_period,
                "price": str(plan.price),
                "auto_renew": subscription.auto_renew,
                "start_date": subscription.start_date,
                "end_date": subscription.end_date,
            },
            "usage": {
                "transactions": build_metric(txn_used, plan.max_transactions),
                "budgets": build_metric(budget_used, plan.max_budgets),
                "goals": build_metric(goal_used, plan.max_goals),
                "categories": build_metric(category_used, plan.max_categories),
                "recurring_transactions": build_metric(recurring_used, plan.max_recurring_transactions),
                "import_size": {
                    "limit": plan.max_import_size if plan.max_import_size != -1 else -1
                }
            }
        }

    @classmethod
    def check_limit(cls, user, limit_type, requested_count=1):
        """
        Validates if adding `requested_count` to current usage of `limit_type` remains within plan limits.
        Raises `PlanLimitReachedException` if limit is exceeded.
        """
        from transactions.models import Transaction, Budget, FinancialGoal, Category, RecurringTransaction

        plan = cls.get_current_plan(user)
        now = timezone.now()

        limit_mapping = {
            'transactions': plan.max_transactions,
            'budgets': plan.max_budgets,
            'goals': plan.max_goals,
            'categories': plan.max_categories,
            'recurring_transactions': plan.max_recurring_transactions,
            'import_size': plan.max_import_size,
        }

        if limit_type not in limit_mapping:
            return True

        max_limit = limit_mapping[limit_type]
        if max_limit == -1:
            return True

        if limit_type == 'transactions':
            current_usage = Transaction.objects.filter(
                user=user,
                date__year=now.year,
                date__month=now.month
            ).count()
        elif limit_type == 'budgets':
            current_usage = Budget.objects.filter(user=user).count()
        elif limit_type == 'goals':
            current_usage = FinancialGoal.objects.filter(user=user).count()
        elif limit_type == 'categories':
            current_usage = Category.objects.filter(user=user).count()
        elif limit_type == 'recurring_transactions':
            current_usage = RecurringTransaction.objects.filter(user=user).count()
        elif limit_type == 'import_size':
            current_usage = 0  # Checked per batch

        if current_usage + requested_count > max_limit:
            raise PlanLimitReachedException(
                limit_type=limit_type,
                current_usage=current_usage,
                max_allowed=max_limit
            )
        return True

    @classmethod
    def can_create_transaction(cls, user, count=1):
        return cls.check_limit(user, 'transactions', requested_count=count)

    @classmethod
    def can_create_budget(cls, user, count=1):
        return cls.check_limit(user, 'budgets', requested_count=count)

    @classmethod
    def can_create_goal(cls, user, count=1):
        return cls.check_limit(user, 'goals', requested_count=count)

    @classmethod
    def can_create_category(cls, user, count=1):
        return cls.check_limit(user, 'categories', requested_count=count)

    @classmethod
    def can_create_recurring_transaction(cls, user, count=1):
        return cls.check_limit(user, 'recurring_transactions', requested_count=count)

    @classmethod
    def can_import(cls, user, count=1):
        # Checks per-batch limit and current monthly transaction limit
        cls.check_limit(user, 'import_size', requested_count=count)
        cls.check_limit(user, 'transactions', requested_count=count)
        return True

    @classmethod
    def change_plan(cls, user, new_plan_code):
        """
        Handles safe plan transition (upgrade/downgrade).
        Does not mutate or delete existing user data.
        """
        subscription = cls.get_current_subscription(user)

        if new_plan_code == 'premium':
            target_plan = cls.get_or_create_premium_plan()
        elif new_plan_code == 'free':
            target_plan = cls.get_or_create_default_free_plan()
        else:
            try:
                target_plan = SubscriptionPlan.objects.get(code=new_plan_code, is_active=True)
            except SubscriptionPlan.DoesNotExist:
                raise ValueError(f"Subscription plan '{new_plan_code}' does not exist or is inactive.")

        subscription.plan = target_plan
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.start_date = timezone.now()
        
        # Default duration 30 days for monthly, 365 days for yearly
        days = 365 if target_plan.billing_period == BillingPeriod.YEARLY else 30
        subscription.end_date = timezone.now() + timedelta(days=days)
        subscription.auto_renew = True
        subscription.save()

        return subscription

    @classmethod
    def cancel_subscription(cls, user):
        """
        Cancels the active user subscription or sets auto_renew to False safely.
        Does not delete historical or existing user data.
        """
        subscription = cls.get_current_subscription(user)
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.auto_renew = False
        subscription.save(update_fields=['status', 'auto_renew', 'updated_at'])
        return subscription
