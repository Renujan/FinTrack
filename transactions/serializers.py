from decimal import Decimal
from rest_framework import serializers
from .choices import TransactionType, BudgetPeriod, RecurrenceFrequency, GoalStatus, GoalType, GoalPriority, NotificationType, ExecutionStatus
from .models import Category, Transaction, Budget, RecurringTransaction, RecurringTransactionExecution, FinancialGoal, GoalContribution, Notification, AuditLog
from .services import BudgetCalculationService, GoalCalculationService, FinancialGoalService, NotificationService


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
    transaction_type, recurrence frequency, interval, user-owned category validation,
    and schedule date-range boundaries. Supports 'title' as alias for 'name'.
    """
    title = serializers.CharField(source='name', required=False, help_text='Title of the recurring transaction (alias for name)')
    category_name = serializers.ReadOnlyField(source='category.name', help_text='Name of the associated category')
    next_run_date = serializers.DateField(required=False, help_text='Next scheduled date for automated transaction execution (YYYY-MM-DD)')
    interval = serializers.IntegerField(default=1, required=False, help_text='Recurrence interval multiplier (must be >= 1)')

    class Meta:
        model = RecurringTransaction
        fields = [
            'id',
            'category',
            'category_name',
            'name',
            'title',
            'description',
            'amount',
            'transaction_type',
            'frequency',
            'interval',
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

    def validate_interval(self, value):
        if value is None or value < 1:
            raise serializers.ValidationError("Interval must be a positive integer greater than or equal to 1.")
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
        # Handle title/name alias fallback
        if 'name' not in attrs and 'title' in self.initial_data:
            attrs['name'] = self.initial_data['title']

        start_date = attrs.get('start_date') or (self.instance.start_date if self.instance else None)
        end_date = attrs.get('end_date') if 'end_date' in attrs else (self.instance.end_date if self.instance else None)
        next_run_date = attrs.get('next_run_date')
        interval = attrs.get('interval') or (self.instance.interval if self.instance else 1)

        if interval < 1:
            raise serializers.ValidationError({"interval": "Interval must be greater than or equal to 1."})

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


class RecurringTransactionExecutionSerializer(serializers.ModelSerializer):
    """
    Serializer for RecurringTransactionExecution history records.
    """
    recurring_transaction_id = serializers.ReadOnlyField(source='recurring_transaction.id')
    recurring_transaction_name = serializers.ReadOnlyField(source='recurring_transaction.name')
    transaction_id = serializers.ReadOnlyField(source='transaction.id')

    class Meta:
        model = RecurringTransactionExecution
        fields = [
            'id',
            'recurring_transaction_id',
            'recurring_transaction_name',
            'transaction_id',
            'executed_at',
            'scheduled_for',
            'status',
            'error_message'
        ]
        read_only_fields = fields


class GoalContributionSerializer(serializers.ModelSerializer):
    """
    Serializer for GoalContribution model with contribution validation and ownership scoping.
    """
    goal_name = serializers.ReadOnlyField(source='goal.name')

    class Meta:
        model = GoalContribution
        fields = ['id', 'goal', 'goal_name', 'amount', 'note', 'contribution_date', 'created_at']
        read_only_fields = ['id', 'goal', 'created_at']

    def validate_amount(self, value):
        if value is None or value <= Decimal('0.00'):
            raise serializers.ValidationError("Contribution amount must be greater than zero.")
        return value


class FinancialGoalSerializer(serializers.ModelSerializer):
    """
    Serializer for FinancialGoal model with calculation status metrics, category ownership validation,
    target amount validation, and goal status / forecast calculations.
    """
    category_name = serializers.SerializerMethodField()
    target_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    current_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    remaining_amount = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()
    required_monthly_saving = serializers.SerializerMethodField()
    is_completed = serializers.SerializerMethodField()

    class Meta:
        model = FinancialGoal
        fields = [
            'id',
            'name',
            'description',
            'category',
            'category_name',
            'target_amount',
            'current_amount',
            'remaining_amount',
            'progress_percentage',
            'required_monthly_saving',
            'target_date',
            'goal_type',
            'status',
            'priority',
            'is_active',
            'is_completed',
            'completed_at',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id', 'completed_at', 'created_at', 'updated_at',
            'remaining_amount', 'progress_percentage', 'required_monthly_saving', 'is_completed'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            self.fields['category'].queryset = Category.objects.filter(user=request.user)

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None

    def get_remaining_amount(self, obj):
        return FinancialGoalService.calculate_remaining_amount(obj)

    def get_progress_percentage(self, obj):
        return FinancialGoalService.calculate_percentage(obj)

    def get_required_monthly_saving(self, obj):
        return FinancialGoalService.calculate_required_monthly_saving(obj)

    def get_is_completed(self, obj):
        return obj.status == GoalStatus.COMPLETED or obj.current_amount >= obj.target_amount

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

    def validate_current_amount(self, value):
        if value is not None and value < Decimal('0.00'):
            raise serializers.ValidationError("Current amount cannot be negative.")
        return value

    def validate_category(self, value):
        if value is not None:
            request = self.context.get('request')
            if request and hasattr(request, 'user') and request.user.is_authenticated:
                if value.user != request.user:
                    raise serializers.ValidationError("Category does not belong to the authenticated user.")
        return value


class GoalProgressForecastSerializer(serializers.Serializer):
    goal_id = serializers.IntegerField()
    goal_name = serializers.CharField()
    target_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    current_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    remaining_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    progress_percentage = serializers.FloatField()
    days_remaining = serializers.IntegerField()
    required_monthly_saving = serializers.DecimalField(max_digits=12, decimal_places=2)
    required_weekly_saving = serializers.DecimalField(max_digits=12, decimal_places=2)
    required_daily_saving = serializers.DecimalField(max_digits=12, decimal_places=2)
    projected_completion_date = serializers.DateField(allow_null=True)
    status = serializers.CharField()
    priority = serializers.CharField()
    goal_type = serializers.CharField()


class FinancialGoalSummarySerializer(serializers.Serializer):
    total_goals = serializers.IntegerField()
    active_goals = serializers.IntegerField()
    completed_goals = serializers.IntegerField()
    paused_goals = serializers.IntegerField()
    cancelled_goals = serializers.IntegerField()
    total_target_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_saved_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_remaining_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    overall_progress_percentage = serializers.FloatField()



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




