# core/models.py
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Sum


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    monthly_income = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    money_on_hand = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} Profile"

    @property
    def total_allocated(self):
        """Sum of all active budgets allocated for this user."""
        total = Budget.objects.filter(user=self.user, is_active=True).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        return total

    @property
    def available_to_allocate(self):
        """How much cash remains available to be allocated into budgets."""
        return (self.money_on_hand or Decimal('0.00')) - self.total_allocated


class Category(models.Model):
    CATEGORY_CHOICES = [
        ('bills', 'Bills'),
        ('wants', 'Wants'),
        ('needs', 'Needs'),
        ('grocery', 'Grocery'),
        ('school', 'School/Education'),
        ('allowance', 'Daily Allowance'),
        ('load', 'Mobile Load'),
        ('transportation', 'Transportation'),
        ('food', 'Food & Dining'),
        ('entertainment', 'Entertainment'),
        ('health', 'Health & Medical'),
        ('clothing', 'Clothing'),
        ('savings', 'Savings'),
        ('other', 'Other'),
        ('income', 'Income'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    category_type = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='other')
    color = models.CharField(max_length=7, default='#6f42c1')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'name')

    def __str__(self):
        return f"{self.user.username} - {self.name}"


class Budget(models.Model):
    BUDGET_TYPE_CHOICES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=150, default='Budget')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    budget_type = models.CharField(max_length=10, choices=BUDGET_TYPE_CHOICES, default='weekly')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.name} ({self.budget_type} ₱{self.amount})"


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('savings', 'Savings'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title or self.transaction_type} (₱{self.amount})"


class Savings(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.user.username} saved ₱{self.amount} on {self.date}"
