from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from .choices import TransactionType, BudgetPeriod, RecurrenceFrequency, GoalStatus, NotificationType


class Category(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='categories'
    )
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['name']
        indexes = [
            models.Index(fields=['user', 'name'], name='idx_cat_user_name'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'name'],
                name='unique_user_category'
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.user})"


class RecurringTransaction(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recurring_transactions'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='recurring_transactions'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default='')
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    transaction_type = models.CharField(
        max_length=10,
        choices=TransactionType.choices
    )
    frequency = models.CharField(
        max_length=10,
        choices=RecurrenceFrequency.choices
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    next_run_date = models.DateField()
    last_run_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['next_run_date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active', 'next_run_date'], name='idx_rec_user_act_next'),
            models.Index(fields=['user', 'category'], name='idx_rec_user_category'),
            models.Index(fields=['user', 'transaction_type'], name='idx_rec_user_type'),
            models.Index(fields=['user', 'frequency'], name='idx_rec_user_freq'),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name='recurring_amount_positive'
            ),
            models.CheckConstraint(
                condition=models.Q(end_date__isnull=True) | models.Q(end_date__gte=models.F('start_date')),
                name='recurring_start_lte_end_date'
            )
        ]

    def __str__(self):
        return f"{self.name} - {self.frequency} - {self.amount} ({self.user})"


class Transaction(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='transactions'
    )
    recurring_transaction = models.ForeignKey(
        RecurringTransaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_transactions'
    )
    recurring_schedule_date = models.DateField(null=True, blank=True)
    transaction_type = models.CharField(
        max_length=10,
        choices=TransactionType.choices
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    description = models.TextField(blank=True, default='')
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'date'], name='idx_txn_user_date'),
            models.Index(fields=['user', 'transaction_type'], name='idx_txn_user_type'),
            models.Index(fields=['user', 'category'], name='idx_txn_user_category'),
            models.Index(fields=['user', 'amount'], name='idx_txn_user_amount'),
            models.Index(fields=['user', 'created_at'], name='idx_txn_user_created'),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name='transaction_amount_positive'
            ),
            models.UniqueConstraint(
                fields=['recurring_transaction', 'recurring_schedule_date'],
                name='unique_recurring_occurrence'
            )
        ]

    def __str__(self):
        return f"{self.transaction_type} - {self.amount} ({self.user})"



class Budget(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='budgets'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='budgets'
    )
    name = models.CharField(max_length=100)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    period = models.CharField(
        max_length=20,
        choices=BudgetPeriod.choices,
        default=BudgetPeriod.MONTHLY
    )
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'start_date', 'end_date'], name='idx_budget_user_dates'),
            models.Index(fields=['user', 'category'], name='idx_budget_user_category'),
            models.Index(fields=['user', 'period'], name='idx_budget_user_period'),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name='budget_amount_positive'
            ),
            models.CheckConstraint(
                condition=models.Q(end_date__gte=models.F('start_date')),
                name='budget_start_lte_end_date'
            )
        ]

    @property
    def is_overall(self):
        return self.category_id is None

    def get_budget_type(self):
        """
        Distinguishes between a category-specific budget and an overall budget.
        """
        return 'Overall' if self.is_overall else f"Category: {self.category.name}"

    def __str__(self):
        return f"{self.name} - {self.amount} ({self.user})"


class FinancialGoal(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='financial_goals'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='financial_goals'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default='')
    target_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    target_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['target_date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'target_date'], name='idx_goal_user_target_date'),
            models.Index(fields=['user', 'category'], name='idx_goal_user_category'),
            models.Index(fields=['user', 'is_active'], name='idx_goal_user_is_active'),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(target_amount__gt=0),
                name='goal_target_amount_positive'
            )
        ]

    def __str__(self):
        return f"{self.name} - {self.target_amount} ({self.user})"


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read'], name='idx_notif_user_is_read'),
            models.Index(fields=['user', 'notification_type'], name='idx_notif_user_type'),
            models.Index(fields=['user', 'created_at'], name='idx_notif_user_created'),
        ]

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    def mark_as_unread(self):
        if self.is_read:
            self.is_read = False
            self.read_at = None
            self.save(update_fields=['is_read', 'read_at'])

    def __str__(self):
        return f"{self.notification_type} - {self.title} ({self.user})"



