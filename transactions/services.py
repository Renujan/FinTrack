from decimal import Decimal
import datetime
from django.db.models import Sum, Q
from django.utils import timezone
from .choices import TransactionType, GoalStatus, NotificationType
from .models import Transaction, Budget, FinancialGoal, Notification, RecurringTransaction


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
    def calculate_budget_metrics(cls, budget) -> dict:
        """
        Calculates all usage metrics for a budget.
        Returns a dictionary containing budget_amount, spent_amount, remaining_amount, percentage_used, is_exceeded.
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
        Integrates goal tracking with authenticated user transaction records.
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
    def get_contributing_transactions(cls, goal):
        """
        Retrieves user transaction records contributing to progress for this goal.
        """
        return cls.get_goal_transactions(goal).select_related('category')

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
from .choices import RecurrenceFrequency, ExecutionStatus, AuditAction, NotificationType
from .models import RecurringTransaction, RecurringTransactionExecution, Transaction
from .audit_services import AuditLogService

logger = logging.getLogger(__name__)


class RecurringTransactionService:
    """
    Service layer for recurring transaction processing, next occurrence calculation,
    pause/resume operations, manual execution, execution history tracking, and
    transaction generation with duplicate protection.
    """

    @classmethod
    def calculate_next_run_date(cls, current_date, frequency, interval=1):
        """
        Calculates the next run date based on frequency and interval multiplier while
        handling month-end dates, leap years, custom intervals, and boundary edge cases safely.
        """
        if isinstance(current_date, datetime.datetime):
            current_date = current_date.date()

        if not interval or interval < 1:
            interval = 1

        if frequency == RecurrenceFrequency.DAILY:
            return current_date + datetime.timedelta(days=1 * interval)
        elif frequency == RecurrenceFrequency.WEEKLY:
            return current_date + datetime.timedelta(days=7 * interval)
        elif frequency == RecurrenceFrequency.MONTHLY:
            total_months = current_date.year * 12 + (current_date.month - 1) + interval
            year = total_months // 12
            month = (total_months % 12) + 1
            max_days = calendar.monthrange(year, month)[1]
            day = min(current_date.day, max_days)
            return datetime.date(year, month, day)
        elif frequency == RecurrenceFrequency.YEARLY:
            year = current_date.year + interval
            month = current_date.month
            day = current_date.day
            if month == 2 and day == 29 and not calendar.isleap(year):
                day = 28
            return datetime.date(year, month, day)
        elif frequency == RecurrenceFrequency.CUSTOM:
            return current_date + datetime.timedelta(days=interval)
        else:
            raise ValueError(f"Unsupported recurrence frequency: {frequency}")

    @classmethod
    def calculate_next_run(cls, current_date, frequency, interval=1):
        """
        Alias for calculate_next_run_date.
        """
        return cls.calculate_next_run_date(current_date, frequency, interval)

    @classmethod
    def validate_schedule(cls, schedule_data):
        """
        Validates recurring schedule fields and date boundary consistency.
        """
        amount = schedule_data.get('amount')
        if amount is not None and amount <= Decimal('0.00'):
            raise ValueError("Amount must be positive.")
        interval = schedule_data.get('interval', 1)
        if interval < 1:
            raise ValueError("Interval must be at least 1.")
        start_date = schedule_data.get('start_date')
        end_date = schedule_data.get('end_date')
        if start_date and end_date and end_date < start_date:
            raise ValueError("End date cannot be before start date.")
        return True

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
    def check_duplicate_occurrence(cls, schedule, schedule_date):
        """
        Checks if a transaction has already been generated for a specific recurring schedule and occurrence date.
        """
        return Transaction.objects.filter(
            recurring_transaction=schedule,
            recurring_schedule_date=schedule_date
        ).exists()

    @classmethod
    def create_transaction(cls, schedule, schedule_date=None):
        """
        Generates a standard Transaction from a RecurringTransaction schedule for schedule_date.
        Records execution history and prevents duplicate transactions.
        """
        if schedule_date is None:
            schedule_date = schedule.next_run_date

        if cls.check_duplicate_occurrence(schedule, schedule_date):
            existing_txn = Transaction.objects.filter(
                recurring_transaction=schedule,
                recurring_schedule_date=schedule_date
            ).first()
            return existing_txn

        description = schedule.description if schedule.description else schedule.name
        with transaction.atomic():
            new_txn = Transaction.objects.create(
                user=schedule.user,
                category=schedule.category,
                recurring_transaction=schedule,
                recurring_schedule_date=schedule_date,
                transaction_type=schedule.transaction_type,
                amount=schedule.amount,
                description=description,
                date=schedule_date
            )
            RecurringTransactionExecution.objects.create(
                recurring_transaction=schedule,
                transaction=new_txn,
                scheduled_for=schedule_date,
                status=ExecutionStatus.SUCCESS,
                error_message=''
            )
            NotificationService.create_recurring_alert(
                schedule,
                NotificationType.RECURRING_GENERATED,
                transaction=new_txn,
                schedule_date=schedule_date
            )
            return new_txn

    @classmethod
    def execute_now(cls, schedule, request=None):
        """
        Manually triggers execution of a recurring transaction on demand.
        Creates transaction, updates execution metadata, calculates next run date,
        and logs audit event.
        """
        if not schedule.is_active:
            raise ValueError("Cannot execute a paused or inactive recurring transaction schedule.")

        schedule_date = schedule.next_run_date or timezone.now().date()
        try:
            txn = cls.create_transaction(schedule, schedule_date=schedule_date)
            schedule.last_run_date = schedule_date
            next_date = cls.calculate_next_run_date(schedule_date, schedule.frequency, schedule.interval)
            schedule.next_run_date = next_date

            if schedule.end_date and schedule.next_run_date > schedule.end_date:
                schedule.is_active = False
                NotificationService.create_recurring_alert(
                    schedule,
                    NotificationType.RECURRING_EXPIRED
                )

            schedule.save(update_fields=['last_run_date', 'next_run_date', 'is_active', 'updated_at'])

            AuditLogService.log_action(
                user=schedule.user,
                action=AuditAction.RECURRING_TRANSACTION_EXECUTED,
                resource_type='RecurringTransaction',
                resource_id=schedule.id,
                metadata={'name': schedule.name, 'amount': str(schedule.amount), 'execution_date': str(schedule_date)},
                request=request
            )
            return txn, schedule
        except Exception as e:
            err_msg = str(e)[:255]
            RecurringTransactionExecution.objects.create(
                recurring_transaction=schedule,
                transaction=None,
                scheduled_for=schedule_date,
                status=ExecutionStatus.FAILED,
                error_message=err_msg
            )
            logger.error(f"Manual execution failed for schedule {schedule.id}: {e}", exc_info=True)
            raise

    @classmethod
    def pause_schedule(cls, schedule, request=None):
        """
        Pauses an active recurring transaction schedule.
        """
        if schedule.is_active:
            schedule.is_active = False
            schedule.save(update_fields=['is_active', 'updated_at'])
            AuditLogService.log_action(
                user=schedule.user,
                action=AuditAction.RECURRING_TRANSACTION_PAUSED,
                resource_type='RecurringTransaction',
                resource_id=schedule.id,
                metadata={'name': schedule.name},
                request=request
            )
            NotificationService.create_notification(
                user=schedule.user,
                notification_type=NotificationType.RECURRING_TRANSACTION_PAUSED,
                title=f"Schedule Paused: {schedule.name}",
                message=f"Your recurring schedule '{schedule.name}' has been paused.",
                metadata={'recurring_transaction_id': schedule.id}
            )
        return schedule

    @classmethod
    def resume_schedule(cls, schedule, request=None):
        """
        Resumes a paused recurring transaction schedule and validates next_run_date.
        """
        if not schedule.is_active:
            schedule.is_active = True
            today = timezone.now().date()
            if schedule.next_run_date < today:
                if schedule.end_date and today > schedule.end_date:
                    schedule.next_run_date = schedule.end_date
                else:
                    schedule.next_run_date = today

            schedule.save(update_fields=['is_active', 'next_run_date', 'updated_at'])
            AuditLogService.log_action(
                user=schedule.user,
                action=AuditAction.RECURRING_TRANSACTION_RESUMED,
                resource_type='RecurringTransaction',
                resource_id=schedule.id,
                metadata={'name': schedule.name, 'next_run_date': str(schedule.next_run_date)},
                request=request
            )
            NotificationService.create_notification(
                user=schedule.user,
                notification_type=NotificationType.RECURRING_TRANSACTION_RESUMED,
                title=f"Schedule Resumed: {schedule.name}",
                message=f"Your recurring schedule '{schedule.name}' has been resumed.",
                metadata={'recurring_transaction_id': schedule.id}
            )
        return schedule

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
                NotificationService.create_recurring_alert(
                    schedule,
                    NotificationType.RECURRING_EXPIRED
                )
                break

            current_run_date = schedule.next_run_date

            try:
                with transaction.atomic():
                    existing_txn = Transaction.objects.filter(
                        recurring_transaction=schedule,
                        recurring_schedule_date=current_run_date
                    ).first()

                    if not existing_txn:
                        description = schedule.description if schedule.description else schedule.name
                        new_txn = Transaction.objects.create(
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
                        RecurringTransactionExecution.objects.create(
                            recurring_transaction=schedule,
                            transaction=new_txn,
                            scheduled_for=current_run_date,
                            status=ExecutionStatus.SUCCESS,
                            error_message=''
                        )
                        NotificationService.create_recurring_alert(
                            schedule,
                            NotificationType.RECURRING_GENERATED,
                            transaction=new_txn,
                            schedule_date=current_run_date
                        )

                    next_date = cls.calculate_next_run_date(current_run_date, schedule.frequency, schedule.interval)
                    schedule.last_run_date = current_run_date
                    schedule.next_run_date = next_date

                    if schedule.end_date and schedule.next_run_date > schedule.end_date:
                        schedule.is_active = False
                        is_expired = True
                        NotificationService.create_recurring_alert(
                            schedule,
                            NotificationType.RECURRING_EXPIRED
                        )

                    schedule.save(update_fields=['last_run_date', 'next_run_date', 'is_active', 'updated_at'])

            except IntegrityError:
                logger.warning(
                    f"Duplicate transaction attempt for recurring schedule {schedule.id} on date {current_run_date}"
                )
            except Exception as e:
                err_msg = str(e)[:255]
                RecurringTransactionExecution.objects.create(
                    recurring_transaction=schedule,
                    transaction=None,
                    scheduled_for=current_run_date,
                    status=ExecutionStatus.FAILED,
                    error_message=err_msg
                )
                logger.error(f"Error processing recurring schedule {schedule.id} for date {current_run_date}: {e}", exc_info=True)
                break

        return generated_count, is_expired

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
    def process_due_transactions(cls, target_date=None):
        """
        Alias for process_due_recurring_transactions.
        """
        return cls.process_due_recurring_transactions(target_date=target_date)

    @classmethod
    def process_recurring_transaction(cls, schedule, target_date=None):
        """
        Processes a single recurring schedule up to target_date.
        """
        if target_date is None:
            target_date = timezone.now().date()
        elif isinstance(target_date, datetime.datetime):
            target_date = target_date.date()
        return cls._process_single_schedule(schedule, target_date)


class NotificationService:
    """
    Service layer for notification creation, management, financial alert checking,
    and duplicate notification prevention.
    """

    @classmethod
    def create_notification(cls, user, notification_type, title, message, metadata=None):
        """
        Creates and persists a Notification record for a user if user preferences permit.
        """
        from users.services import UserPreferenceService
        if not UserPreferenceService.should_receive_notification(user, notification_type):
            return None

        if metadata is None:
            metadata = {}
        return Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            metadata=metadata
        )

    @classmethod
    def create_budget_alert(cls, budget, warning_threshold=Decimal('80.0')):
        """
        Generates budget notifications (BUDGET_EXCEEDED or BUDGET_WARNING)
        based on BudgetCalculationService metrics.
        Prevents duplicate alerts for the same budget period.
        Configured with configurable warning threshold (default 80%).
        """

        metrics = BudgetCalculationService.calculate_budget_metrics(budget)
        spent = metrics['spent_amount']
        budget_amt = budget.amount
        pct = metrics['percentage_used']

        if metrics['is_exceeded']:
            exists = Notification.objects.filter(
                user=budget.user,
                notification_type=NotificationType.BUDGET_EXCEEDED,
                metadata__budget_id=budget.id,
                metadata__start_date=str(budget.start_date)
            ).exists()
            if not exists:
                title = f"Budget Exceeded: {budget.name}"
                message = f"You have exceeded your budget '{budget.name}'. Spent ${spent} of ${budget_amt} ({pct}%)."
                metadata = {
                    'budget_id': budget.id,
                    'budget_name': budget.name,
                    'start_date': str(budget.start_date),
                    'end_date': str(budget.end_date),
                    'spent_amount': str(spent),
                    'budget_amount': str(budget_amt),
                    'percentage_used': pct,
                }
                return cls.create_notification(
                    user=budget.user,
                    notification_type=NotificationType.BUDGET_EXCEEDED,
                    title=title,
                    message=message,
                    metadata=metadata
                )
        elif pct >= float(warning_threshold):
            exists = Notification.objects.filter(
                user=budget.user,
                notification_type=NotificationType.BUDGET_WARNING,
                metadata__budget_id=budget.id,
                metadata__start_date=str(budget.start_date)
            ).exists()
            if not exists:
                title = f"Budget Warning: {budget.name}"
                message = f"Your budget '{budget.name}' has reached {pct}% of limit. Spent ${spent} of ${budget_amt}."
                metadata = {
                    'budget_id': budget.id,
                    'budget_name': budget.name,
                    'start_date': str(budget.start_date),
                    'end_date': str(budget.end_date),
                    'spent_amount': str(spent),
                    'budget_amount': str(budget_amt),
                    'percentage_used': pct,
                }
                return cls.create_notification(
                    user=budget.user,
                    notification_type=NotificationType.BUDGET_WARNING,
                    title=title,
                    message=message,
                    metadata=metadata
                )
        return None

    @classmethod
    def create_goal_alert(cls, goal, warning_threshold=Decimal('80.0')):
        """
        Generates financial goal notifications (GOAL_COMPLETED or GOAL_WARNING)
        based on GoalCalculationService metrics.
        Prevents duplicate alerts per goal milestone.
        Monitors progress threshold against goal target amount.
        """

        metrics = GoalCalculationService.calculate_goal_metrics(goal)
        current = metrics['current_amount']
        target = goal.target_amount
        pct = metrics['percentage_complete']

        if metrics['is_completed']:
            exists = Notification.objects.filter(
                user=goal.user,
                notification_type=NotificationType.GOAL_COMPLETED,
                metadata__goal_id=goal.id
            ).exists()
            if not exists:
                title = f"Financial Goal Completed: {goal.name}"
                message = f"Congratulations! You reached your target amount of ${target} for '{goal.name}'."
                metadata = {
                    'goal_id': goal.id,
                    'goal_name': goal.name,
                    'target_amount': str(target),
                    'current_amount': str(current),
                    'percentage_complete': pct,
                }
                return cls.create_notification(
                    user=goal.user,
                    notification_type=NotificationType.GOAL_COMPLETED,
                    title=title,
                    message=message,
                    metadata=metadata
                )
        elif pct >= float(warning_threshold):
            exists = Notification.objects.filter(
                user=goal.user,
                notification_type=NotificationType.GOAL_WARNING,
                metadata__goal_id=goal.id
            ).exists()
            if not exists:
                title = f"Goal Approaching Target: {goal.name}"
                message = f"Your goal '{goal.name}' has reached {pct}% of target (${current} of ${target})."
                metadata = {
                    'goal_id': goal.id,
                    'goal_name': goal.name,
                    'target_amount': str(target),
                    'current_amount': str(current),
                    'percentage_complete': pct,
                }
                return cls.create_notification(
                    user=goal.user,
                    notification_type=NotificationType.GOAL_WARNING,
                    title=title,
                    message=message,
                    metadata=metadata
                )
        return None

    @classmethod
    def create_recurring_alert(cls, schedule, alert_type, transaction=None, schedule_date=None):
        """
        Generates recurring transaction notifications:
        - RECURRING_DUE (upcoming due date)
        - RECURRING_GENERATED (auto-generated transaction)
        - RECURRING_EXPIRED (schedule completed/expired)
        Enforces duplicate protection and skips due alerts for paused schedules.
        """

        if not schedule.is_active and alert_type == NotificationType.RECURRING_DUE:
            return None

        if alert_type == NotificationType.RECURRING_DUE:
            run_date_str = str(schedule.next_run_date)
            exists = Notification.objects.filter(
                user=schedule.user,
                notification_type=NotificationType.RECURRING_DUE,
                metadata__recurring_transaction_id=schedule.id,
                metadata__next_run_date=run_date_str
            ).exists()
            if not exists:
                title = f"Recurring Transaction Due Soon: {schedule.name}"
                message = f"Your recurring transaction '{schedule.name}' of ${schedule.amount} is due on {schedule.next_run_date}."
                metadata = {
                    'recurring_transaction_id': schedule.id,
                    'schedule_name': schedule.name,
                    'amount': str(schedule.amount),
                    'next_run_date': run_date_str,
                }
                return cls.create_notification(
                    user=schedule.user,
                    notification_type=NotificationType.RECURRING_DUE,
                    title=title,
                    message=message,
                    metadata=metadata
                )
        elif alert_type == NotificationType.RECURRING_GENERATED:
            s_date = schedule_date or (transaction.date if transaction else schedule.next_run_date)
            s_date_str = str(s_date)
            exists = Notification.objects.filter(
                user=schedule.user,
                notification_type=NotificationType.RECURRING_GENERATED,
                metadata__recurring_transaction_id=schedule.id,
                metadata__schedule_date=s_date_str
            ).exists()
            if not exists:
                title = f"Recurring Transaction Generated: {schedule.name}"
                message = f"Recurring transaction '{schedule.name}' of ${schedule.amount} was generated for {s_date_str}."
                metadata = {
                    'recurring_transaction_id': schedule.id,
                    'schedule_name': schedule.name,
                    'amount': str(schedule.amount),
                    'schedule_date': s_date_str,
                    'transaction_id': transaction.id if transaction else None
                }
                return cls.create_notification(
                    user=schedule.user,
                    notification_type=NotificationType.RECURRING_GENERATED,
                    title=title,
                    message=message,
                    metadata=metadata
                )
        elif alert_type == NotificationType.RECURRING_EXPIRED:
            exists = Notification.objects.filter(
                user=schedule.user,
                notification_type=NotificationType.RECURRING_EXPIRED,
                metadata__recurring_transaction_id=schedule.id
            ).exists()
            if not exists:
                title = f"Recurring Schedule Expired: {schedule.name}"
                message = f"Recurring transaction schedule '{schedule.name}' has reached its end date and expired."
                metadata = {
                    'recurring_transaction_id': schedule.id,
                    'schedule_name': schedule.name,
                    'end_date': str(schedule.end_date) if schedule.end_date else None
                }
                return cls.create_notification(
                    user=schedule.user,
                    notification_type=NotificationType.RECURRING_EXPIRED,
                    title=title,
                    message=message,
                    metadata=metadata
                )
        return None

    @classmethod
    def mark_as_read(cls, notification):
        """
        Marks a notification as read and sets read_at timestamp.
        """
        notification.mark_as_read()
        return notification

    @classmethod
    def mark_as_unread(cls, notification):
        """
        Marks a notification as unread and resets read_at timestamp.
        """
        notification.mark_as_unread()
        return notification

    @classmethod
    def mark_all_as_read(cls, user):
        """
        Bulk updates all unread notifications for a user to read status.
        """
        now = timezone.now()
        updated_count = Notification.objects.filter(user=user, is_read=False).update(
            is_read=True,
            read_at=now
        )
        return updated_count

    @classmethod
    def process_all_financial_alerts(cls, user=None, target_date=None, budget_threshold=80.0, goal_threshold=80.0):
        """
        Scans budgets, goals, and recurring transactions to generate alerts.
        Can process globally or for a specific user.
        """
        if target_date is None:
            target_date = timezone.now().date()
        elif isinstance(target_date, datetime.datetime):
            target_date = target_date.date()

        alerts_created = 0

        # 1. Process Budgets
        budgets_qs = Budget.objects.all()
        if user:
            budgets_qs = budgets_qs.filter(user=user)

        budgets_processed = 0
        for budget in budgets_qs.select_related('category', 'user'):
            budgets_processed += 1
            notif = cls.create_budget_alert(budget, warning_threshold=budget_threshold)
            if notif:
                alerts_created += 1

        # 2. Process Financial Goals
        goals_qs = FinancialGoal.objects.filter(is_active=True)
        if user:
            goals_qs = goals_qs.filter(user=user)

        goals_processed = 0
        for goal in goals_qs.select_related('category', 'user'):
            goals_processed += 1
            notif = cls.create_goal_alert(goal, warning_threshold=goal_threshold)
            if notif:
                alerts_created += 1

        # 3. Process Due Recurring Transactions
        due_window = target_date + datetime.timedelta(days=3)
        recurring_qs = RecurringTransaction.objects.filter(
            is_active=True,
            next_run_date__lte=due_window
        )
        if user:
            recurring_qs = recurring_qs.filter(user=user)

        recurring_processed = 0
        for schedule in recurring_qs.select_related('category', 'user'):
            recurring_processed += 1
            notif = cls.create_recurring_alert(schedule, NotificationType.RECURRING_DUE)
            if notif:
                alerts_created += 1

        return {
            'alerts_created_count': alerts_created,
            'budgets_processed_count': budgets_processed,
            'goals_processed_count': goals_processed,
            'recurring_processed_count': recurring_processed,
            'target_date': target_date
        }


