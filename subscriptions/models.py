from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from .choices import BillingPeriod, SubscriptionStatus


class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True, db_index=True)
    description = models.TextField(blank=True, default='')
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    billing_period = models.CharField(
        max_length=10,
        choices=BillingPeriod.choices,
        default=BillingPeriod.MONTHLY
    )
    max_transactions = models.IntegerField(
        default=500,
        help_text="Max transactions allowed per month (-1 for unlimited)"
    )
    max_budgets = models.IntegerField(
        default=5,
        help_text="Max active budgets allowed (-1 for unlimited)"
    )
    max_goals = models.IntegerField(
        default=3,
        help_text="Max financial goals allowed (-1 for unlimited)"
    )
    max_categories = models.IntegerField(
        default=20,
        help_text="Max custom categories allowed (-1 for unlimited)"
    )
    max_recurring_transactions = models.IntegerField(
        default=5,
        help_text="Max recurring transaction rules allowed (-1 for unlimited)"
    )
    max_import_size = models.IntegerField(
        default=100,
        help_text="Max rows allowed per CSV import (-1 for unlimited)"
    )
    features = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscription_plans'
        ordering = ['price', 'name']
        verbose_name = 'Subscription Plan'
        verbose_name_plural = 'Subscription Plans'

    def __str__(self):
        return f"{self.name} ({self.code.upper()}) - {self.price}/{self.billing_period.lower()}"


class UserSubscription(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscription'
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name='user_subscriptions'
    )
    status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.ACTIVE
    )
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    auto_renew = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_subscriptions'
        ordering = ['-created_at']
        verbose_name = 'User Subscription'
        verbose_name_plural = 'User Subscriptions'

    @property
    def is_expired(self):
        if self.end_date and timezone.now() > self.end_date:
            return True
        return False

    @property
    def effective_status(self):
        if self.status == SubscriptionStatus.ACTIVE and self.is_expired:
            return SubscriptionStatus.EXPIRED
        return self.status

    def __str__(self):
        return f"{self.user} - {self.plan.name} ({self.effective_status})"
