import datetime
from decimal import Decimal, InvalidOperation
import django_filters
from rest_framework import serializers
from .choices import TransactionType
from .models import Transaction


class TransactionFilter(django_filters.FilterSet):
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


def validate_filter_params(params):
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
