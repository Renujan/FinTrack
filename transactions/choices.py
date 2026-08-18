from django.db import models
from django.utils.translation import gettext_lazy as _


class TransactionType(models.TextChoices):
    INCOME = 'INCOME', _('Income')
    EXPENSE = 'EXPENSE', _('Expense')


class BudgetPeriod(models.TextChoices):
    WEEKLY = 'WEEKLY', _('Weekly')
    MONTHLY = 'MONTHLY', _('Monthly')
    CUSTOM = 'CUSTOM', _('Custom')

    @classmethod
    def is_valid_period(cls, value):
        return value in cls.values if value else False


class RecurrenceFrequency(models.TextChoices):
    DAILY = 'DAILY', _('Daily')
    WEEKLY = 'WEEKLY', _('Weekly')
    MONTHLY = 'MONTHLY', _('Monthly')
    YEARLY = 'YEARLY', _('Yearly')

    @classmethod
    def is_valid_frequency(cls, value):
        return value in cls.values if value else False



