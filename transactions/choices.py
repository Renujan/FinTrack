from django.db import models
from django.utils.translation import gettext_lazy as _


class TransactionType(models.TextChoices):
    INCOME = 'INCOME', _('Income')
    EXPENSE = 'EXPENSE', _('Expense')


class BudgetPeriod(models.TextChoices):
    WEEKLY = 'WEEKLY', _('Weekly')
    MONTHLY = 'MONTHLY', _('Monthly')
    CUSTOM = 'CUSTOM', _('Custom')

