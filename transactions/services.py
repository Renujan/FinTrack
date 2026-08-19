from decimal import Decimal
from django.db.models import Sum, Q
from .choices import TransactionType, GoalStatus
from .models import Transaction


class BudgetCalculationService:
    """
    Service layer to calculate financial usage and status metrics for budgets.
    Calculates spent_amount, remaining_amount, percentage_used, and is_exceeded.
    Budget consumption is based ONLY on EXPENSE transactions belonging to the budget's user
    within the budget date range [start_date, end_date].
    """

    @staticmethod
    def get_budget_transactions(budget):
        """
        Returns the queryset of expense transactions contributing to a budget's spending.
        """
        filters = Q(
            user=budget.user,
            transaction_type=TransactionType.EXPENSE,
            date__gte=budget.start_date,
            date__lte=budget.end_date
        )
        if budget.category_id is not None:
            filters &= Q(category_id=budget.category_id)
        return Transaction.objects.filter(filters)

    @classmethod
    def calculate_spent_amount(cls, budget):
        """
        Calculates total expense spending for a specific budget instance.
        """
        result = cls.get_budget_transactions(budget).aggregate(total=Sum('amount'))
        total_spent = result['total'] if result['total'] is not None else Decimal('0.00')
        return total_spent


    @classmethod
    def calculate_budget_metrics(cls, budget):
        """
        Calculates all usage metrics for a budget.
        Returns a dictionary containing spent_amount, remaining_amount, percentage_used, is_exceeded.
        """
        spent_amount = cls.calculate_spent_amount(budget)
        budget_amount = budget.amount

        remaining_amount = budget_amount - spent_amount

        if budget_amount > Decimal('0.00'):
            percentage_used = round(float((spent_amount / budget_amount) * 100), 2)
        else:
            percentage_used = 0.0

        is_exceeded = spent_amount > budget_amount

        return {
            'budget_amount': budget_amount,
            'spent_amount': spent_amount,
            'remaining_amount': remaining_amount,
            'percentage_used': percentage_used,
            'is_exceeded': is_exceeded,
        }


class GoalCalculationService:
    """
    Service layer for calculating progress metrics and dynamic status for financial goals.
    Calculates current_amount, remaining_amount, percentage_complete, is_completed, and status.
    Goal progress is based on INCOME transactions belonging to the goal's user with date <= target_date.
    If the goal specifies a category, contributions are restricted to that category.
    """

    @staticmethod
    def get_goal_transactions(goal):
        """
        Returns the queryset of income transactions contributing to a financial goal.
        """
        filters = Q(
            user=goal.user,
            transaction_type=TransactionType.INCOME,
            date__lte=goal.target_date
        )
        if goal.category_id is not None:
            filters &= Q(category_id=goal.category_id)
        return Transaction.objects.filter(filters)

    @classmethod
    def calculate_current_amount(cls, goal):
        """
        Calculates total income saved towards a specific financial goal.
        """
        result = cls.get_goal_transactions(goal).aggregate(total=Sum('amount'))
        return result['total'] if result['total'] is not None else Decimal('0.00')

    @classmethod
    def calculate_goal_metrics(cls, goal):
        """
        Calculates all usage metrics and dynamic status for a goal instance.
        """
        target_amount = goal.target_amount
        current_amount = cls.calculate_current_amount(goal)
        remaining_amount = max(Decimal('0.00'), target_amount - current_amount)

        if target_amount > Decimal('0.00'):
            percentage_complete = round(float((current_amount / target_amount) * 100), 2)
        else:
            percentage_complete = 0.0

        is_completed = current_amount >= target_amount

        today = timezone.now().date()
        if is_completed:
            status_val = GoalStatus.COMPLETED
        elif not goal.is_active:
            status_val = GoalStatus.PAUSED
        elif goal.target_date < today:
            status_val = GoalStatus.OVERDUE
        else:
            status_val = GoalStatus.ACTIVE

        return {
            'target_amount': target_amount,
            'current_amount': current_amount,
            'remaining_amount': remaining_amount,
            'percentage_complete': percentage_complete,
            'is_completed': is_completed,
            'status': status_val,
        }


import calendar
import datetime
import logging
from django.db import transaction, IntegrityError
from django.utils import timezone
from .choices import RecurrenceFrequency
from .models import RecurringTransaction

logger = logging.getLogger(__name__)


class RecurringTransactionService:
    """
    Service layer for recurring transaction processing, next occurrence calculation,
    pause/resume operations, and transaction generation with duplicate protection.
    """

    @staticmethod
    def calculate_next_run_date(current_date, frequency):
        """
        Calculates the next run date based on frequency while handling month-end dates,
        leap years, and boundary edge cases safely.
        """
        if frequency == RecurrenceFrequency.DAILY:
            return current_date + datetime.timedelta(days=1)
        elif frequency == RecurrenceFrequency.WEEKLY:
            return current_date + datetime.timedelta(days=7)
        elif frequency == RecurrenceFrequency.MONTHLY:
            year = current_date.year + (1 if current_date.month == 12 else 0)
            month = 1 if current_date.month == 12 else current_date.month + 1
            max_days = calendar.monthrange(year, month)[1]
            day = min(current_date.day, max_days)
            return datetime.date(year, month, day)
        elif frequency == RecurrenceFrequency.YEARLY:
            year = current_date.year + 1
            month = current_date.month
            day = current_date.day
            if month == 2 and day == 29 and not calendar.isleap(year):
                day = 28
            return datetime.date(year, month, day)
        else:
            raise ValueError(f"Unsupported recurrence frequency: {frequency}")

    @classmethod
    def get_due_schedules(cls, target_date=None):
        """
        Queries all active recurring schedules due on or before target_date.
        """
        if target_date is None:
            target_date = timezone.now().date()
        elif isinstance(target_date, datetime.datetime):
            target_date = target_date.date()

        return RecurringTransaction.objects.filter(
            is_active=True,
            next_run_date__lte=target_date
        ).select_related('category', 'user')

    @classmethod
    def process_due_recurring_transactions(cls, target_date=None):
        """
        Scans for all active recurring transactions due on or before target_date (defaults to today).
        Generates corresponding Transaction records, updates last_run_date and next_run_date,
        prevents duplicate generation via database transactions and constraints, and deactivates expired schedules.
        """
        if target_date is None:
            target_date = timezone.now().date()
        elif isinstance(target_date, datetime.datetime):
            target_date = target_date.date()

        due_schedules = RecurringTransaction.objects.filter(
            is_active=True,
            next_run_date__lte=target_date
        ).select_related('category', 'user')

        generated_count = 0
        expired_count = 0
        processed_schedule_ids = set()

        for schedule in due_schedules:
            processed_schedule_ids.add(schedule.id)
            gen_count, is_expired = cls._process_single_schedule(schedule, target_date)
            generated_count += gen_count
            if is_expired:
                expired_count += 1

        return {
            'processed_schedules_count': len(processed_schedule_ids),
            'generated_transactions_count': generated_count,
            'expired_schedules_count': expired_count,
            'target_date': target_date
        }

    @classmethod
    def check_duplicate_occurrence(cls, schedule, schedule_date):
        """
        Checks if a transaction has already been generated for a specific recurring schedule and occurrence date.
        """
        return Transaction.objects.filter(
            recurring_transaction=schedule,
            recurring_schedule_date=schedule_date
        ).exists()

    @classmethod
    def _process_single_schedule(cls, schedule, target_date):
        """
        Processes a single recurring schedule up to target_date.
        Iteratively generates transactions while next_run_date <= target_date,
        updating last_run_date and advancing next_run_date until it goes past target_date or end_date.
        """
        generated_count = 0
        is_expired = False

        while schedule.is_active and schedule.next_run_date <= target_date:
            if schedule.end_date and schedule.next_run_date > schedule.end_date:
                schedule.is_active = False
                schedule.save(update_fields=['is_active', 'updated_at'])
                is_expired = True
                break

            current_run_date = schedule.next_run_date

            with transaction.atomic():
                existing_txn = Transaction.objects.filter(
                    recurring_transaction=schedule,
                    recurring_schedule_date=current_run_date
                ).first()

                if not existing_txn:
                    description = schedule.description if schedule.description else schedule.name
                    try:
                        Transaction.objects.create(
                            user=schedule.user,
                            category=schedule.category,
                            recurring_transaction=schedule,
                            recurring_schedule_date=current_run_date,
                            transaction_type=schedule.transaction_type,
                            amount=schedule.amount,
                            description=description,
                            date=current_run_date
                        )
                        generated_count += 1
                    except IntegrityError:
                        logger.warning(
                            f"Duplicate transaction attempt for recurring schedule {schedule.id} on date {current_run_date}"
                        )

                next_date = cls.calculate_next_run_date(current_run_date, schedule.frequency)
                schedule.last_run_date = current_run_date
                schedule.next_run_date = next_date

                if schedule.end_date and schedule.next_run_date > schedule.end_date:
                    schedule.is_active = False
                    is_expired = True

                schedule.save(update_fields=['last_run_date', 'next_run_date', 'is_active', 'updated_at'])

        return generated_count, is_expired

    @classmethod
    def pause_schedule(cls, schedule):
        """
        Pauses an active recurring transaction schedule.
        """
        if schedule.is_active:
            schedule.is_active = False
            schedule.save(update_fields=['is_active', 'updated_at'])
        return schedule

    @classmethod
    def resume_schedule(cls, schedule):
        """
        Resumes a paused recurring transaction schedule.
        """
        if not schedule.is_active:
            schedule.is_active = True
            schedule.save(update_fields=['is_active', 'updated_at'])
        return schedule

