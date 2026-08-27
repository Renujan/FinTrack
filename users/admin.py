from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from users.models import User, UserProfile, UserPreference


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


class UserPreferenceInline(admin.StackedInline):
    model = UserPreference
    can_delete = False
    verbose_name_plural = 'Preferences'
    fk_name = 'user'


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    inlines = (UserProfileInline, UserPreferenceInline)
    list_display = ['username', 'email', 'currency', 'is_staff', 'is_active', 'created_at']
    list_filter = ['is_staff', 'is_active', 'currency', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    fieldsets = UserAdmin.fieldsets + (
        ('Finance Info', {'fields': ('currency',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Finance Info', {'fields': ('currency',)}),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'display_name', 'phone_number', 'updated_at']
    search_fields = ['user__username', 'user__email', 'display_name', 'phone_number']
    raw_id_fields = ['user']


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'currency', 'date_format', 'timezone', 'budget_alerts', 'goal_alerts', 'updated_at']
    list_filter = ['currency', 'date_format', 'budget_alerts', 'goal_alerts', 'recurring_transaction_alerts']
    search_fields = ['user__username', 'user__email', 'currency', 'timezone']
    raw_id_fields = ['user']
