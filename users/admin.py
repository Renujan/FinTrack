from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'email', 'currency', 'is_staff', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Finance Info', {'fields': ('currency',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Finance Info', {'fields': ('currency',)}),
    )
