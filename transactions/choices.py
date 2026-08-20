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


class GoalStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', _('Active')
    COMPLETED = 'COMPLETED', _('Completed')
    OVERDUE = 'OVERDUE', _('Overdue')
    PAUSED = 'PAUSED', _('Paused')


class NotificationType(models.TextChoices):
    BUDGET_EXCEEDED = 'BUDGET_EXCEEDED', _('Budget Exceeded')
    BUDGET_WARNING = 'BUDGET_WARNING', _('Budget Warning')
    GOAL_COMPLETED = 'GOAL_COMPLETED', _('Goal Completed')
    GOAL_WARNING = 'GOAL_WARNING', _('Goal Warning')
    RECURRING_DUE = 'RECURRING_DUE', _('Recurring Transaction Due')
    RECURRING_GENERATED = 'RECURRING_GENERATED', _('Recurring Transaction Generated')
    RECURRING_EXPIRED = 'RECURRING_EXPIRED', _('Recurring Schedule Expired')

    @classmethod
    def is_valid_type(cls, value):
        return value in cls.values if value else False


