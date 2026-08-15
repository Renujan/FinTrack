from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from .choices import TransactionType


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
            )
        ]

    def __str__(self):
        return f"{self.transaction_type} - {self.amount} ({self.user})"
