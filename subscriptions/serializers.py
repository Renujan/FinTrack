from rest_framework import serializers
from .models import SubscriptionPlan, UserSubscription


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id',
            'name',
            'code',
            'description',
            'price',
            'billing_period',
            'max_transactions',
            'max_budgets',
            'max_goals',
            'max_categories',
            'max_recurring_transactions',
            'max_import_size',
            'features',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)
    effective_status = serializers.CharField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = UserSubscription
        fields = [
            'id',
            'plan',
            'status',
            'effective_status',
            'is_expired',
            'start_date',
            'end_date',
            'auto_renew',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


class SubscriptionUpgradeSerializer(serializers.Serializer):
    plan_code = serializers.CharField(max_length=50, required=True)

    def validate_plan_code(self, value):
        if value is None or not str(value).strip():
            raise serializers.ValidationError("Plan code is required and cannot be empty.")
        code_clean = str(value).strip().lower()
        if not SubscriptionPlan.objects.filter(code=code_clean, is_active=True).exists():
            raise serializers.ValidationError(f"Invalid or inactive plan code: '{value}'.")
        return code_clean
