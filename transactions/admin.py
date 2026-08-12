from django.contrib import admin
from .models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user', 'created_at', 'updated_at')
    list_filter = ('user',)
    search_fields = ('name', 'user__email', 'user__username')
