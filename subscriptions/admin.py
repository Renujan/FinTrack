from django.contrib import admin
from .models import SubscriptionPlan, UserSubscription


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'code',
        'price',
        'billing_period',
        'max_transactions',
        'max_budgets',
        'max_goals',
        'max_categories',
        'max_recurring_transactions',
        'max_import_size',
        'is_active',
        'created_at',
    )
    list_filter = ('billing_period', 'is_active', 'created_at')
    search_fields = ('name', 'code', 'description')
    ordering = ('price', 'name')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'description', 'is_active')
        }),
        ('Pricing & Billing', {
            'fields': ('price', 'billing_period')
        }),
        ('Resource Limits (-1 for unlimited)', {
            'fields': (
                'max_transactions',
                'max_budgets',
                'max_goals',
                'max_categories',
                'max_recurring_transactions',
                'max_import_size',
            )
        }),
        ('Feature Flags', {
            'fields': ('features',)
        }),
    )


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'plan',
        'status',
        'effective_status',
        'start_date',
        'end_date',
        'auto_renew',
        'created_at',
    )
    list_filter = ('status', 'auto_renew', 'plan', 'created_at')
    search_fields = ('user__username', 'user__email', 'plan__name', 'plan__code')
    raw_id_fields = ('user',)
    ordering = ('-created_at',)
    readonly_fields = ('effective_status', 'created_at', 'updated_at')

    def effective_status(self, obj):
        return obj.effective_status
    effective_status.short_description = 'Effective Status'
