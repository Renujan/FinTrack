import csv
import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import io
from django.db import transaction
from django.http import HttpResponse
from rest_framework import serializers

from transactions.choices import TransactionType, BudgetPeriod, GoalStatus, RecurrenceFrequency
from transactions.models import Transaction, Category, Budget, FinancialGoal, RecurringTransaction
from transactions.filters import TransactionFilter, validate_filter_params
from transactions.analytics.services import AnalyticsService
from transactions.services import BudgetCalculationService, GoalCalculationService


class DataExportService:
    """
    Service layer providing user-scoped CSV exports for Transactions, Categories,
    Budgets, Financial Goals, and Recurring Transactions.
    """

    @classmethod
    def export_transactions_csv(cls, user, params=None):
        """
        Exports user-scoped transactions as CSV supporting date ranges, category, type, min/max amount, and search.
        """
        params = params or {}
        validate_filter_params(params)

        qs = Transaction.objects.filter(user=user).select_related('category').order_by('-date', '-created_at')

        # Apply transaction filtering
        filterset = TransactionFilter(params, queryset=qs)
        if filterset.is_valid():
            qs = filterset.qs

        search_query = params.get('search') or params.get('q')
        if search_query:
            from django.db.models import Q
            qs = qs.filter(
                Q(description__icontains=search_query) |
                Q(category__name__icontains=search_query)
            )

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="transactions_export.csv"'

        writer = csv.writer(response)
        writer.writerow(['Date', 'Description', 'Amount', 'Transaction Type', 'Category', 'Created Date'])

        for txn in qs.iterator():
            writer.writerow([
                txn.date.strftime('%Y-%m-%d'),
                txn.description,
                f"{txn.amount:.2f}",
                txn.transaction_type,
                txn.category.name if txn.category else '',
                txn.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])

        return response

    @classmethod
    def export_categories_csv(cls, user):
        qs = Category.objects.filter(user=user).order_by('name')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="categories_export.csv"'

        writer = csv.writer(response)
        writer.writerow(['ID', 'Name', 'Created At', 'Updated At'])

        for cat in qs.iterator():
            writer.writerow([
                cat.id,
                cat.name,
                cat.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                cat.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            ])

        return response

    @classmethod
    def export_budgets_csv(cls, user):
        qs = Budget.objects.filter(user=user).select_related('category').order_by('-start_date')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="budgets_export.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Name', 'Category', 'Amount', 'Period',
            'Start Date', 'End Date', 'Spent Amount', 'Remaining Amount',
            'Percentage Used', 'Is Exceeded', 'Created At'
        ])

        for budget in qs.iterator():
            metrics = BudgetCalculationService.calculate_budget_metrics(budget)
            writer.writerow([
                budget.id,
                budget.name,
                budget.category.name if budget.category else 'Overall',
                f"{budget.amount:.2f}",
                budget.period,
                budget.start_date.strftime('%Y-%m-%d'),
                budget.end_date.strftime('%Y-%m-%d'),
                f"{metrics['spent_amount']:.2f}",
                f"{metrics['remaining_amount']:.2f}",
                f"{metrics['percentage_used']:.2f}",
                budget.is_overall if hasattr(budget, 'is_overall') else (budget.category_id is None),
                budget.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])

        return response

    @classmethod
    def export_goals_csv(cls, user):
        qs = FinancialGoal.objects.filter(user=user).select_related('category').order_by('target_date')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="goals_export.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Name', 'Description', 'Category', 'Target Amount',
            'Target Date', 'Current Amount', 'Remaining Amount',
            'Percentage Complete', 'Status', 'Is Active', 'Created At'
        ])

        for goal in qs.iterator():
            metrics = GoalCalculationService.calculate_goal_metrics(goal)
            writer.writerow([
                goal.id,
                goal.name,
                goal.description,
                goal.category.name if goal.category else 'All Categories',
                f"{goal.target_amount:.2f}",
                goal.target_date.strftime('%Y-%m-%d'),
                f"{metrics['current_amount']:.2f}",
                f"{metrics['remaining_amount']:.2f}",
                f"{metrics['percentage_complete']:.2f}",
                metrics['status'],
                goal.is_active,
                goal.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])

        return response

    @classmethod
    def export_recurring_csv(cls, user):
        qs = RecurringTransaction.objects.filter(user=user).select_related('category').order_by('next_run_date')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="recurring_transactions_export.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Name', 'Description', 'Amount', 'Transaction Type',
            'Category', 'Frequency', 'Start Date', 'End Date',
            'Next Run Date', 'Last Run Date', 'Is Active', 'Created At'
        ])

        for rec in qs.iterator():
            writer.writerow([
                rec.id,
                rec.name,
                rec.description,
                f"{rec.amount:.2f}",
                rec.transaction_type,
                rec.category.name if rec.category else '',
                rec.frequency,
                rec.start_date.strftime('%Y-%m-%d'),
                rec.end_date.strftime('%Y-%m-%d') if rec.end_date else '',
                rec.next_run_date.strftime('%Y-%m-%d'),
                rec.last_run_date.strftime('%Y-%m-%d') if rec.last_run_date else '',
                rec.is_active,
                rec.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])

        return response


class FinancialReportService:
    """
    Service layer providing comprehensive user-scoped financial reports.
    Integrates Day 8 AnalyticsService with Goal Analytics and Budget Analytics.
    """

    @classmethod
    def get_financial_report(cls, user, start_date=None, end_date=None):
        summary = AnalyticsService.get_summary(user, start_date, end_date)
        all_category_analytics = AnalyticsService.get_category_analytics(user, start_date, end_date)
        top_spending_categories = AnalyticsService.get_category_analytics(user, start_date, end_date, limit=5)
        monthly_totals = AnalyticsService.get_monthly_summary(user, start_date, end_date)
        budget_summary = AnalyticsService.get_budget_analytics(user, start_date, end_date)

        # Financial Goal Analytics
        goals_qs = FinancialGoal.objects.filter(user=user).select_related('category')
        total_goals = goals_qs.count()
        active_goals_count = 0
        completed_goals_count = 0
        total_target_amount = Decimal('0.00')
        total_current_amount = Decimal('0.00')
        goals_summary_list = []

        for goal in goals_qs:
            metrics = GoalCalculationService.calculate_goal_metrics(goal)
            if goal.is_active:
                active_goals_count += 1
            if metrics['is_completed']:
                completed_goals_count += 1

            total_target_amount += goal.target_amount
            total_current_amount += metrics['current_amount']

            goals_summary_list.append({
                'id': goal.id,
                'name': goal.name,
                'category_name': goal.category.name if goal.category else None,
                'target_amount': f"{goal.target_amount:.2f}",
                'current_amount': f"{metrics['current_amount']:.2f}",
                'remaining_amount': f"{metrics['remaining_amount']:.2f}",
                'percentage_complete': metrics['percentage_complete'],
                'status': metrics['status'],
                'target_date': goal.target_date.strftime('%Y-%m-%d'),
            })

        if total_target_amount > Decimal('0.00'):
            overall_goal_progress = round(float((total_current_amount / total_target_amount) * 100), 2)
        else:
            overall_goal_progress = 0.0

        goal_summary = {
            'total_goals': total_goals,
            'active_goals_count': active_goals_count,
            'completed_goals_count': completed_goals_count,
            'total_target_amount': f"{total_target_amount:.2f}",
            'total_current_amount': f"{total_current_amount:.2f}",
            'overall_goal_progress': overall_goal_progress,
            'goals_summary': goals_summary_list,
        }

        return {
            'total_income': summary['total_income'],
            'total_expenses': summary['total_expenses'],
            'net_balance': summary['net_balance'],
            'transaction_count': summary['transaction_count'],
            'top_spending_categories': top_spending_categories,
            'category_spending_breakdown': all_category_analytics,
            'monthly_totals': monthly_totals,
            'budget_summary': budget_summary,
            'goal_summary': goal_summary,
        }


class TransactionImportService:
    """
    Service layer providing CSV import parsing, row-by-row validation, category ownership enforcement,
    and structured error reporting for failed rows.
    """

    REQUIRED_HEADERS = {'date', 'description', 'amount', 'transaction_type', 'category'}

    @classmethod
    def import_transactions_csv(cls, user, file_obj):
        try:
            content = file_obj.read().decode('utf-8-sig')
        except UnicodeDecodeError:
            return {
                'success': False,
                'imported': 0,
                'failed': 1,
                'errors': [{
                    'row': 0,
                    'field': 'file',
                    'message': 'File encoding must be UTF-8.'
                }]
            }

        reader = csv.reader(io.StringIO(content))

        rows = list(reader)
        if not rows:
            return {
                'success': False,
                'imported': 0,
                'failed': 1,
                'errors': [{
                    'row': 0,
                    'field': 'file',
                    'message': 'Uploaded CSV file is empty.'
                }]
            }

        if len(rows) - 1 > 1000:
            return {
                'success': False,
                'imported': 0,
                'failed': 1,
                'errors': [{
                    'row': 0,
                    'field': 'file',
                    'message': 'CSV file contains more than 1000 rows limit.'
                }]
            }

        header_row = [col.strip().lower().replace(' ', '_') for col in rows[0]]
        header_map = {}

        # Normalize column header aliases
        for idx, col in enumerate(header_row):
            if col in ('date', 'txn_date', 'transaction_date'):
                header_map['date'] = idx
            elif col in ('description', 'desc', 'details', 'memo'):
                header_map['description'] = idx
            elif col in ('amount', 'value', 'sum'):
                header_map['amount'] = idx
            elif col in ('transaction_type', 'type', 'type_name'):
                header_map['transaction_type'] = idx
            elif col in ('category', 'category_name', 'cat'):
                header_map['category'] = idx

        missing_fields = cls.REQUIRED_HEADERS - set(header_map.keys())
        if missing_fields:
            return {
                'success': False,
                'imported': 0,
                'failed': 1,
                'errors': [{
                    'row': 1,
                    'field': 'header',
                    'message': f"Missing required column headers: {', '.join(sorted(missing_fields))}."
                }]
            }

        # Cache existing user categories by iexact name and id for efficient lookup
        user_categories = {cat.name.lower(): cat for cat in Category.objects.filter(user=user)}
        user_categories_by_id = {str(cat.id): cat for cat in Category.objects.filter(user=user)}

        errors = []
        to_create = []
        batch_hashes = set()
        failed_count = 0

        # Process data rows starting at line 2 (row_idx=2 in 1-based indexing)
        for row_num, row in enumerate(rows[1:], start=2):
            if not row or not any(field.strip() for field in row):
                # Skip completely blank lines
                continue

            row_errors = []

            # 1. Extract values
            date_raw = row[header_map['date']].strip() if header_map['date'] < len(row) else ''
            desc_raw = row[header_map['description']].strip() if header_map['description'] < len(row) else ''
            amount_raw = row[header_map['amount']].strip() if header_map['amount'] < len(row) else ''
            type_raw = row[header_map['transaction_type']].strip() if header_map['transaction_type'] < len(row) else ''
            category_raw = row[header_map['category']].strip() if header_map['category'] < len(row) else ''

            # 2. Validate required presence
            if not date_raw:
                row_errors.append({'row': row_num, 'field': 'date', 'message': 'Date field is required.'})
            if not amount_raw:
                row_errors.append({'row': row_num, 'field': 'amount', 'message': 'Amount field is required.'})
            if not type_raw:
                row_errors.append({'row': row_num, 'field': 'transaction_type', 'message': 'Transaction type field is required.'})
            if not category_raw:
                row_errors.append({'row': row_num, 'field': 'category', 'message': 'Category field is required.'})

            if row_errors:
                errors.extend(row_errors)
                failed_count += 1
                continue

            # 3. Validate Date format
            parsed_date = None
            try:
                parsed_date = datetime.datetime.strptime(date_raw, '%Y-%m-%d').date()
            except ValueError:
                errors.append({'row': row_num, 'field': 'date', 'message': f"Invalid date format '{date_raw}'. Expected YYYY-MM-DD."})

            # 4. Validate Amount format and value
            parsed_amount = None
            try:
                parsed_amount = Decimal(amount_raw)
                if parsed_amount <= Decimal('0.00'):
                    errors.append({'row': row_num, 'field': 'amount', 'message': 'Amount must be greater than zero.'})
                    parsed_amount = None
            except (InvalidOperation, TypeError, ValueError):
                errors.append({'row': row_num, 'field': 'amount', 'message': f"Invalid numeric format for amount '{amount_raw}'."})

            # 5. Validate Transaction Type
            parsed_type = type_raw.upper()
            if parsed_type not in TransactionType.values:
                errors.append({
                    'row': row_num,
                    'field': 'transaction_type',
                    'message': f"Invalid transaction type '{type_raw}'. Allowed choices: {', '.join(TransactionType.values)}."
                })
                parsed_type = None

            # 6. Validate Category existence and ownership
            category_obj = None
            if category_raw.isdigit() and category_raw in user_categories_by_id:
                category_obj = user_categories_by_id[category_raw]
            elif category_raw.lower() in user_categories:
                category_obj = user_categories[category_raw.lower()]
            else:
                errors.append({
                    'row': row_num,
                    'field': 'category',
                    'message': f"Category '{category_raw}' does not exist for this user."
                })

            if not (parsed_date and parsed_amount and parsed_type and category_obj):
                failed_count += 1
                continue

            # 7. Duplicate import protection via SHA-256 fingerprint and database checks
            row_hash = hashlib.sha256(
                f"{user.id}:{parsed_date}:{parsed_amount}:{parsed_type}:{category_obj.id}:{desc_raw}".encode('utf-8')
            ).hexdigest()

            if row_hash in batch_hashes:
                errors.append({'row': row_num, 'field': 'duplicate', 'message': 'Duplicate transaction row found within CSV file.'})
                failed_count += 1
                continue

            # Check database for pre-existing duplicate transaction
            db_duplicate = Transaction.objects.filter(
                user=user,
                date=parsed_date,
                amount=parsed_amount,
                transaction_type=parsed_type,
                category=category_obj,
                description=desc_raw
            ).exists()

            if db_duplicate:
                errors.append({'row': row_num, 'field': 'duplicate', 'message': 'Duplicate transaction already exists in database.'})
                failed_count += 1
                continue

            batch_hashes.add(row_hash)
            to_create.append(Transaction(
                user=user,
                date=parsed_date,
                amount=parsed_amount,
                transaction_type=parsed_type,
                category=category_obj,
                description=desc_raw
            ))

        # Perform atomic bulk insertion for all valid rows
        imported_count = 0
        if to_create:
            with transaction.atomic():
                created = Transaction.objects.bulk_create(to_create)
                imported_count = len(created)

        return {
            'success': failed_count == 0,
            'imported': imported_count,
            'failed': failed_count,
            'errors': errors
        }
