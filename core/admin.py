from django.contrib import admin
from .models import Profile, Category, Budget, Transaction, Savings


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'monthly_income', 'money_on_hand', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'category_type', 'color', 'created_at']
    list_filter = ['category_type', 'created_at']
    search_fields = ['name', 'user__username']
    list_editable = ['color']

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'amount', 'budget_type', 'category', 'is_active', 'start_date']
    list_filter = ['budget_type', 'is_active', 'start_date']
    search_fields = ['name', 'user__username']
    list_editable = ['is_active']

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'amount', 'transaction_type', 'category', 'date', 'created_at']
    list_filter = ['transaction_type', 'date', 'created_at', 'category']
    search_fields = ['title', 'description', 'user__username']
    list_editable = ['transaction_type']
    date_hierarchy = 'date'

@admin.register(Savings)
class SavingsAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'description', 'date', 'created_at']
    list_filter = ['date', 'created_at']
    search_fields = ['description', 'user__username']
    date_hierarchy = 'date'

