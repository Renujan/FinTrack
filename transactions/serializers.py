from decimal import Decimal
from rest_framework import serializers
from .choices import TransactionType, BudgetPeriod, RecurrenceFrequency, GoalStatus, NotificationType
from .models import Category, Transaction, Budget, RecurringTransaction, FinancialGoal, Notification, AuditLog
from .services import BudgetCalculationService, GoalCalculationService, NotificationService


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
    category_name = serializers.ReadOnlyField(source='category.name', help_text='Name of the associated category')
    next_run_date = serializers.DateField(required=False, help_text='Next scheduled date for automated transaction execution (YYYY-MM-DD)')


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


class FinancialGoalSerializer(serializers.ModelSerializer):
    """
    Serializer for FinancialGoal model with calculation status metrics, category ownership validation,
    target amount validation, and dynamic goal status calculation.
    """
    category_name = serializers.SerializerMethodField()
    target_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    current_amount = serializers.SerializerMethodField()
    remaining_amount = serializers.SerializerMethodField()
    percentage_complete = serializers.SerializerMethodField()
    is_completed = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = FinancialGoal
        fields = [
            'id',
            'name',
            'description',
            'category',
            'category_name',
            'target_amount',
            'target_date',
            'is_active',
            'current_amount',
            'remaining_amount',
            'percentage_complete',
            'is_completed',
            'status',
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
            obj._cached_metrics = GoalCalculationService.calculate_goal_metrics(obj)
        return obj._cached_metrics

    def get_current_amount(self, obj):
        return self._get_metrics(obj)['current_amount']

    def get_remaining_amount(self, obj):
        return self._get_metrics(obj)['remaining_amount']

    def get_percentage_complete(self, obj):
        return self._get_metrics(obj)['percentage_complete']

    def get_is_completed(self, obj):
        return self._get_metrics(obj)['is_completed']

    def get_status(self, obj):
        return self._get_metrics(obj)['status']

    def validate_name(self, value):
        if value is None or not str(value).strip():
            raise serializers.ValidationError("Goal name is required and cannot be empty.")
        value = str(value).strip()
        if len(value) > 100:
            raise serializers.ValidationError("Goal name cannot exceed 100 characters.")
        return value

    def validate_target_amount(self, value):
        if value is None or value <= Decimal('0.00'):
            raise serializers.ValidationError("Target amount must be greater than zero.")
        return value

    def validate_category(self, value):
        if value is not None:
            request = self.context.get('request')
            if request and hasattr(request, 'user') and request.user.is_authenticated:
                if value.user != request.user:
                    raise serializers.ValidationError("Category does not belong to the authenticated user.")
        return value


class NotificationSerializer(serializers.ModelSerializer):
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'notification_type_display',
            'title',
            'message',
            'is_read',
            'created_at',
            'read_at',
            'metadata'
        ]
        read_only_fields = [
            'id',
            'notification_type',
            'notification_type_display',
            'title',
            'message',
            'created_at',
            'read_at',
            'metadata'
        ]


class NotificationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['is_read']

    def update(self, instance, validated_data):
        is_read = validated_data.get('is_read', instance.is_read)
        if is_read:
            return NotificationService.mark_as_read(instance)
        else:
            return NotificationService.mark_as_unread(instance)


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = [
            'id',
            'user',
            'action',
            'resource_type',
            'resource_id',
            'ip_address',
            'metadata',
            'timestamp'
        ]
        read_only_fields = ['id', 'user', 'action', 'resource_type', 'resource_id', 'ip_address', 'metadata', 'timestamp']




