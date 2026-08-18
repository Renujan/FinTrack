import datetime
from decimal import Decimal, InvalidOperation
import django_filters
from rest_framework import serializers
from .choices import TransactionType, BudgetPeriod, RecurrenceFrequency
from .models import Transaction, Budget, RecurringTransaction
from .services import BudgetCalculationService


class TransactionFilter(django_filters.FilterSet):
    """
    Advanced filter set supporting transaction type, category ID/name, date exact/range,
    and min/max amount parameters.
    """
    type = django_filters.CharFilter(method='filter_by_type')
    category = django_filters.CharFilter(method='filter_by_category')
    date = django_filters.DateFilter(field_name='date')
    start_date = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name='date', lookup_expr='lte')
    min_amount = django_filters.NumberFilter(field_name='amount', lookup_expr='gte')
    max_amount = django_filters.NumberFilter(field_name='amount', lookup_expr='lte')

    class Meta:
        model = Transaction
        fields = ['type', 'category', 'date', 'start_date', 'end_date', 'min_amount', 'max_amount']

    def filter_by_type(self, queryset, name, value):
        if not value:
            return queryset
        val_upper = value.upper()
        if val_upper not in TransactionType.values:
            raise serializers.ValidationError({
                'type': f"Invalid transaction type '{value}'. Allowed choices are: {', '.join(TransactionType.values)}."
            })
        return queryset.filter(transaction_type=val_upper)

    def filter_by_category(self, queryset, name, value):
        if not value:
            return queryset
        if value.isdigit():
            return queryset.filter(category_id=int(value))
        return queryset.filter(category__name__iexact=value)


class BudgetFilter(django_filters.FilterSet):
    """
    Advanced filter set for Budget queries supporting category (ID or name), budget period,
    start_date / end_date filters, overall budget indicator, and exceeded status filter.
    """
    category = django_filters.CharFilter(method='filter_by_category')
    period = django_filters.CharFilter(method='filter_by_period')
    start_date = django_filters.DateFilter(field_name='start_date', lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name='end_date', lookup_expr='lte')
    is_overall = django_filters.BooleanFilter(field_name='category', lookup_expr='isnull')
    is_exceeded = django_filters.BooleanFilter(method='filter_by_exceeded')

    class Meta:
        model = Budget
        fields = ['category', 'period', 'start_date', 'end_date', 'is_overall', 'is_exceeded']

    def filter_by_category(self, queryset, name, value):
        if not value:
            return queryset
        if value.isdigit():
            return queryset.filter(category_id=int(value))
        return queryset.filter(category__name__iexact=value)

    def filter_by_period(self, queryset, name, value):
        if not value:
            return queryset
        val_upper = value.upper()
        if val_upper not in BudgetPeriod.values:
            raise serializers.ValidationError({
                'period': f"Invalid budget period '{value}'. Allowed choices are: {', '.join(BudgetPeriod.values)}."
            })
        return queryset.filter(period=val_upper)

    def filter_by_exceeded(self, queryset, name, value):
        if value is None:
            return queryset
        matching_ids = []
        for budget in queryset:
            metrics = BudgetCalculationService.calculate_budget_metrics(budget)
            if metrics['is_exceeded'] == value:
                matching_ids.append(budget.id)
        return queryset.filter(id__in=matching_ids)


def validate_filter_params(params):
    """
    Validates query parameters for transaction filtering, including date formats,
    date ranges (start_date <= end_date), amount ranges (min_amount <= max_amount),
    transaction types, and ordering fields.
    """
    errors = {}

    parsed_start_date = None
    parsed_end_date = None

    for field in ['date', 'start_date', 'end_date']:
        val = params.get(field)
        if val:
            try:
                dt = datetime.datetime.strptime(val, '%Y-%m-%d').date()
                if field == 'start_date':
                    parsed_start_date = dt
                elif field == 'end_date':
                    parsed_end_date = dt
            except ValueError:
                errors[field] = [f"Invalid date format for {field}. Expected YYYY-MM-DD."]

    if parsed_start_date and parsed_end_date and parsed_start_date > parsed_end_date:
        errors['start_date'] = ["start_date cannot be greater than end_date."]

    parsed_min = None
    parsed_max = None

    for field in ['min_amount', 'max_amount']:
        val = params.get(field)
        if val is not None and val != '':
            try:
                amt = Decimal(val)
                if field == 'min_amount':
                    parsed_min = amt
                elif field == 'max_amount':
                    parsed_max = amt
            except (InvalidOperation, TypeError, ValueError):
                errors[field] = [f"Invalid numeric format for {field}."]

    if parsed_min is not None and parsed_max is not None and parsed_min > parsed_max:
        errors['min_amount'] = ["min_amount cannot be greater than max_amount."]

    type_val = params.get('type')
    if type_val and type_val.upper() not in TransactionType.values:
        errors['type'] = [f"Invalid transaction type '{type_val}'. Allowed choices: {', '.join(TransactionType.values)}."]

    ordering_val = params.get('ordering')
    if ordering_val:
        allowed_ordering = {
            'date', '-date',
            'transaction_date', '-transaction_date',
            'amount', '-amount',
            'created_at', '-created_at'
        }
        requested_fields = [f.strip() for f in ordering_val.split(',') if f.strip()]
        invalid_fields = [f for f in requested_fields if f not in allowed_ordering]
        if invalid_fields:
            errors['ordering'] = [f"Invalid ordering field(s): {', '.join(invalid_fields)}."]

    if errors:
        raise serializers.ValidationError(errors)


def validate_budget_filter_params(params):
    """
    Validates query parameters for budget filtering and ordering.
    """
    errors = {}

    parsed_start_date = None
    parsed_end_date = None

    for field in ['start_date', 'end_date']:
        val = params.get(field)
        if val:
            try:
                dt = datetime.datetime.strptime(val, '%Y-%m-%d').date()
                if field == 'start_date':
                    parsed_start_date = dt
                elif field == 'end_date':
                    parsed_end_date = dt
            except ValueError:
                errors[field] = [f"Invalid date format for {field}. Expected YYYY-MM-DD."]

    if parsed_start_date and parsed_end_date and parsed_start_date > parsed_end_date:
        errors['start_date'] = ["start_date cannot be greater than end_date."]

    period_val = params.get('period')
    if period_val and period_val.upper() not in BudgetPeriod.values:
        errors['period'] = [f"Invalid budget period '{period_val}'. Allowed choices: {', '.join(BudgetPeriod.values)}."]

    ordering_val = params.get('ordering')
    if ordering_val:
        allowed_ordering = {
            'start_date', '-start_date',
            'end_date', '-end_date',
            'amount', '-amount',
            'created_at', '-created_at',
            'percentage_used', '-percentage_used',
            'name', '-name'
        }
        requested_fields = [f.strip() for f in ordering_val.split(',') if f.strip()]
        invalid_fields = [f for f in requested_fields if f not in allowed_ordering]
        if invalid_fields:
            errors['ordering'] = [f"Invalid ordering field(s): {', '.join(invalid_fields)}."]

    if errors:
        raise serializers.ValidationError(errors)


class RecurringTransactionFilter(django_filters.FilterSet):
    """
    FilterSet for RecurringTransaction list querysets.
    Supports type, category, frequency, is_active, start_date, end_date, next_run_date range filters.
    """
    type = django_filters.CharFilter(method='filter_by_type')
    category = django_filters.CharFilter(method='filter_by_category')
    frequency = django_filters.CharFilter(method='filter_by_frequency')
    is_active = django_filters.BooleanFilter(field_name='is_active')
    start_date = django_filters.DateFilter(field_name='start_date', lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name='end_date', lookup_expr='lte')
    next_run_date = django_filters.DateFilter(field_name='next_run_date')

    class Meta:
        model = RecurringTransaction
        fields = ['type', 'category', 'frequency', 'is_active', 'start_date', 'end_date', 'next_run_date']

    def filter_by_type(self, queryset, name, value):
        if not value:
            return queryset
        val_upper = value.upper()
        if val_upper not in TransactionType.values:
            raise serializers.ValidationError({
                'type': f"Invalid transaction type '{value}'. Allowed choices are: {', '.join(TransactionType.values)}."
            })
        return queryset.filter(transaction_type=val_upper)

    def filter_by_category(self, queryset, name, value):
        if not value:
            return queryset
        if value.isdigit():
            return queryset.filter(category_id=int(value))
        return queryset.filter(category__name__iexact=value)

    def filter_by_frequency(self, queryset, name, value):
        if not value:
            return queryset
        val_upper = value.upper()
        if val_upper not in RecurrenceFrequency.values:
            raise serializers.ValidationError({
                'frequency': f"Invalid recurrence frequency '{value}'. Allowed choices are: {', '.join(RecurrenceFrequency.values)}."
            })
        return queryset.filter(frequency=val_upper)


def validate_recurring_filter_params(params):
    """
    Validates query parameters for recurring transaction filtering and ordering.
    """
    errors = {}

    parsed_start_date = None
    parsed_end_date = None

    for field in ['start_date', 'end_date', 'next_run_date']:
        val = params.get(field)
        if val:
            try:
                dt = datetime.datetime.strptime(val, '%Y-%m-%d').date()
                if field == 'start_date':
                    parsed_start_date = dt
                elif field == 'end_date':
                    parsed_end_date = dt
            except ValueError:
                errors[field] = [f"Invalid date format for {field}. Expected YYYY-MM-DD."]

    if parsed_start_date and parsed_end_date and parsed_start_date > parsed_end_date:
        errors['start_date'] = ["start_date cannot be greater than end_date."]

    type_val = params.get('type')
    if type_val and type_val.upper() not in TransactionType.values:
        errors['type'] = [f"Invalid transaction type '{type_val}'. Allowed choices: {', '.join(TransactionType.values)}."]

    freq_val = params.get('frequency')
    if freq_val and freq_val.upper() not in RecurrenceFrequency.values:
        errors['frequency'] = [f"Invalid recurrence frequency '{freq_val}'. Allowed choices: {', '.join(RecurrenceFrequency.values)}."]

    ordering_val = params.get('ordering')
    if ordering_val:
        allowed_ordering = {
            'amount', '-amount',
            'start_date', '-start_date',
            'next_run_date', '-next_run_date',
            'created_at', '-created_at',
            'frequency', '-frequency',
            'name', '-name'
        }
        requested_fields = [f.strip() for f in ordering_val.split(',') if f.strip()]
        invalid_fields = [f for f in requested_fields if f not in allowed_ordering]
        if invalid_fields:
            errors['ordering'] = [f"Invalid ordering field(s): {', '.join(invalid_fields)}."]

    if errors:
        raise serializers.ValidationError(errors)


