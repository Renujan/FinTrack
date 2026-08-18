from decimal import Decimal
from rest_framework import serializers
from .choices import TransactionType, BudgetPeriod, RecurrenceFrequency
from .models import Category, Transaction, Budget, RecurringTransaction
from .services import BudgetCalculationService


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_name(self, value):
        if value is None or not str(value).strip():
            raise serializers.ValidationError("Category name is required and cannot be empty.")
        value = str(value).strip()
        if len(value) > 100:
            raise serializers.ValidationError("Category name cannot exceed 100 characters.")

        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            user = request.user
            qs = Category.objects.filter(user=user, name__iexact=value)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError("A category with this name already exists.")
        return value


class TransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for Transaction model with strict validation on amount, transaction_type,
    user-owned category validation, and required transaction date formatting.
    """
    category_name = serializers.ReadOnlyField(source='category.name')

    class Meta:
        model = Transaction
        fields = [
            'id',
            'category',
            'category_name',
            'transaction_type',
            'amount',
            'description',
            'date',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            self.fields['category'].queryset = Category.objects.filter(user=request.user)

    def validate_amount(self, value):
        if value is None or value <= Decimal('0.00'):
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def validate_transaction_type(self, value):
        if value not in TransactionType.values:
            raise serializers.ValidationError(
                f"Invalid transaction type. Choices are: {', '.join(TransactionType.values)}"
            )
        return value

    def validate_category(self, value):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            if value.user != request.user:
                raise serializers.ValidationError("Category does not belong to the authenticated user.")
        return value

    def validate_date(self, value):
        if value is None:
            raise serializers.ValidationError("Transaction date is required.")
        return value


class BudgetSerializer(serializers.ModelSerializer):
    """
    Serializer for Budget model with calculation status metrics, category ownership validation,
    date-range validation, and budget period validation.
    """
    category_name = serializers.SerializerMethodField()
    is_overall = serializers.ReadOnlyField()
    budget_amount = serializers.DecimalField(source='amount', max_digits=12, decimal_places=2, read_only=True)
    spent_amount = serializers.SerializerMethodField()
    remaining_amount = serializers.SerializerMethodField()
    percentage_used = serializers.SerializerMethodField()
    is_exceeded = serializers.SerializerMethodField()

    class Meta:
        model = Budget
        fields = [
            'id',
            'name',
            'category',
            'category_name',
            'is_overall',
            'amount',
            'budget_amount',
            'period',
            'start_date',
            'end_date',
            'spent_amount',
            'remaining_amount',
            'percentage_used',
            'is_exceeded',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            self.fields['category'].queryset = Category.objects.filter(user=request.user)

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None

    def _get_metrics(self, obj):
        if not hasattr(obj, '_cached_metrics'):
            obj._cached_metrics = BudgetCalculationService.calculate_budget_metrics(obj)
        return obj._cached_metrics

    def get_spent_amount(self, obj):
        return self._get_metrics(obj)['spent_amount']

    def get_remaining_amount(self, obj):
        return self._get_metrics(obj)['remaining_amount']

    def get_percentage_used(self, obj):
        return self._get_metrics(obj)['percentage_used']

    def get_is_exceeded(self, obj):
        return self._get_metrics(obj)['is_exceeded']

    def validate_name(self, value):
        if value is None or not str(value).strip():
            raise serializers.ValidationError("Budget name is required and cannot be empty.")
        value = str(value).strip()
        if len(value) > 100:
            raise serializers.ValidationError("Budget name cannot exceed 100 characters.")
        return value

    def validate_amount(self, value):
        if value is None or value <= Decimal('0.00'):
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def validate_period(self, value):
        if value not in BudgetPeriod.values:
            raise serializers.ValidationError(
                f"Invalid budget period. Choices are: {', '.join(BudgetPeriod.values)}"
            )
        return value

    def validate_category(self, value):
        if value is not None:
            request = self.context.get('request')
            if request and hasattr(request, 'user') and request.user.is_authenticated:
                if value.user != request.user:
                    raise serializers.ValidationError("Category does not belong to the authenticated user.")
        return value

    def validate(self, attrs):
        start_date = attrs.get('start_date') or (self.instance.start_date if self.instance else None)
        end_date = attrs.get('end_date') or (self.instance.end_date if self.instance else None)

        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({"end_date": "End date cannot be before start date."})

        return attrs


class RecurringTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for RecurringTransaction model with strict validation on amount,
    transaction_type, recurrence frequency, user-owned category validation,
    and schedule date-range boundaries.
    """
    category_name = serializers.ReadOnlyField(source='category.name')
    next_run_date = serializers.DateField(required=False)

    class Meta:
        model = RecurringTransaction
        fields = [
            'id',
            'category',
            'category_name',
            'name',
            'description',
            'amount',
            'transaction_type',
            'frequency',
            'start_date',
            'end_date',
            'next_run_date',
            'last_run_date',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'last_run_date', 'created_at', 'updated_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            self.fields['category'].queryset = Category.objects.filter(user=request.user)

    def validate_name(self, value):
        if value is None or not str(value).strip():
            raise serializers.ValidationError("Name is required and cannot be empty.")
        value = str(value).strip()
        if len(value) > 100:
            raise serializers.ValidationError("Name cannot exceed 100 characters.")
        return value

    def validate_amount(self, value):
        if value is None or value <= Decimal('0.00'):
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def validate_transaction_type(self, value):
        if value not in TransactionType.values:
            raise serializers.ValidationError(
                f"Invalid transaction type. Choices are: {', '.join(TransactionType.values)}"
            )
        return value

    def validate_frequency(self, value):
        if value not in RecurrenceFrequency.values:
            raise serializers.ValidationError(
                f"Invalid recurrence frequency. Choices are: {', '.join(RecurrenceFrequency.values)}"
            )
        return value

    def validate_category(self, value):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            if value.user != request.user:
                raise serializers.ValidationError("Category does not belong to the authenticated user.")
        return value

    def validate(self, attrs):
        start_date = attrs.get('start_date') or (self.instance.start_date if self.instance else None)
        end_date = attrs.get('end_date') if 'end_date' in attrs else (self.instance.end_date if self.instance else None)
        next_run_date = attrs.get('next_run_date')

        if not self.instance and not next_run_date and start_date:
            attrs['next_run_date'] = start_date
            next_run_date = start_date

        effective_next_run = next_run_date or (self.instance.next_run_date if self.instance else None)

        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({"end_date": "End date cannot be before start date."})

        if effective_next_run and start_date and effective_next_run < start_date:
            raise serializers.ValidationError({"next_run_date": "Next run date cannot be before start date."})

        if effective_next_run and end_date and effective_next_run > end_date:
            raise serializers.ValidationError({"next_run_date": "Next run date cannot be after end date."})

        return attrs


