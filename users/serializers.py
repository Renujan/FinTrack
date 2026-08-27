from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from users.models import (
    UserProfile,
    UserPreference,
    DateFormatChoice,
    DefaultTransactionTypeChoice,
    SUPPORTED_CURRENCIES,
    CURRENCY_SYMBOLS,
)
from users.services import UserPreferenceService

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', required=False)
    email = serializers.EmailField(source='user.email', required=False)
    first_name = serializers.CharField(source='user.first_name', required=False, allow_blank=True)
    last_name = serializers.CharField(source='user.last_name', required=False, allow_blank=True)
    currency = serializers.CharField(source='user.currency', required=False)
    full_name = serializers.ReadOnlyField()
    profile_updated_at = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = UserProfile
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'display_name',
            'bio',
            'phone_number',
            'currency',
            'profile_updated_at',
            'created_at',
        )
        read_only_fields = ('created_at', 'profile_updated_at')

    def validate_email(self, value):
        request = self.context.get('request')
        user = request.user if request else None
        if value and User.objects.filter(email__iexact=value).exclude(pk=user.pk if user else None).exists():
            raise serializers.ValidationError("A user with this email address already exists.")
        return value

    def validate_username(self, value):
        request = self.context.get('request')
        user = request.user if request else None
        if value and User.objects.filter(username__iexact=value).exclude(pk=user.pk if user else None).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate_currency(self, value):
        valid_codes = [code for code, _ in SUPPORTED_CURRENCIES]
        if value and value.upper() not in valid_codes:
            raise serializers.ValidationError(f"Unsupported currency code. Supported: {', '.join(valid_codes)}")
        return value.upper() if value else value

    def update(self, instance, validated_data):
        user = instance.user
        user_data = validated_data.pop('user', {})

        # Update User fields if provided
        if 'username' in user_data:
            user.username = user_data['username']
        if 'email' in user_data:
            user.email = user_data['email']
        if 'first_name' in user_data:
            user.first_name = user_data['first_name']
        if 'last_name' in user_data:
            user.last_name = user_data['last_name']
        if 'currency' in user_data:
            new_curr = user_data['currency'].upper()
            user.currency = new_curr
            # Sync user preferences currency as well
            UserPreferenceService.update_preferences(user, {'currency': new_curr})

        user.save()

        # Update Profile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance


class UserPreferenceSerializer(serializers.ModelSerializer):
    currency_symbol = serializers.ReadOnlyField()

    class Meta:
        model = UserPreference
        fields = (
            'currency',
            'currency_symbol',
            'default_currency',
            'date_format',
            'timezone',
            'language',
            'financial_year_start_month',
            'default_transaction_type',
            'budget_alerts',
            'goal_alerts',
            'recurring_transaction_alerts',
            'system_notifications',
            'updated_at',
        )
        read_only_fields = ('currency_symbol', 'default_currency', 'updated_at')

    def validate_currency(self, value):
        valid_codes = [code for code, _ in SUPPORTED_CURRENCIES]
        if value and value.upper() not in valid_codes:
            raise serializers.ValidationError(f"Unsupported currency. Allowed options: {', '.join(valid_codes)}")
        return value.upper() if value else value

    def validate_financial_year_start_month(self, value):
        if value < 1 or value > 12:
            raise serializers.ValidationError("Financial year start month must be an integer between 1 and 12.")
        return value

    def update(self, instance, validated_data):
        user = instance.user
        updated_pref = UserPreferenceService.update_preferences(user, validated_data)
        return updated_pref


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate(self, attrs):
        if attrs.get('new_password') != attrs.get('confirm_password'):
            raise serializers.ValidationError({"confirm_password": "New passwords do not match."})
        if attrs.get('current_password') == attrs.get('new_password'):
            raise serializers.ValidationError({"new_password": "New password cannot be identical to current password."})
        return attrs


class AccountOverviewSerializer(serializers.Serializer):
    user_info = serializers.DictField()
    profile = serializers.DictField()
    preferences = serializers.DictField()
    subscription = serializers.DictField()
    statistics = serializers.DictField()
    recent_activity = serializers.ListField()
