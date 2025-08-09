from django.db import models
from django.contrib.auth.models import User

from django.utils import timezone
from decimal import Decimal

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    monthly_income = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    money_on_hand = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Category(models.Model):
    CATEGORY_CHOICES = [
        ('bills', 'Bills'),
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
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    category_type = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    color = models.CharField(max_length=7, default='#6f42c1')  # Violet default
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        unique_together = ['user', 'name']

    def __str__(self):
        return f"{self.user.username} - {self.name}"

class Budget(models.Model):
    BUDGET_TYPE_CHOICES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    budget_type = models.CharField(max_length=10, choices=BUDGET_TYPE_CHOICES, default='weekly')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    start_date = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.name} (₱{self.amount})"

    def spent_amount(self):
        """Calculate total spent for this budget period"""
        if self.budget_type == 'weekly':
            # Calculate spent in current week
            from datetime import timedelta
            week_start = self.start_date
            week_end = week_start + timedelta(days=7)
            transactions = Transaction.objects.filter(
                user=self.user,
                date__range=[week_start, week_end],
                transaction_type='expense'
            )
        else:
            # Calculate spent in current month
            from django.db.models import Q
            transactions = Transaction.objects.filter(
                user=self.user,
                date__year=self.start_date.year,
                date__month=self.start_date.month,
                transaction_type='expense'
            )
        
        if self.category:
            transactions = transactions.filter(category=self.category)
        
        return sum(t.amount for t in transactions)

    def remaining_amount(self):
        return self.amount - self.spent_amount()

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('savings', 'Savings'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title} (₱{self.amount})"

class Savings(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=200, blank=True)
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name_plural = "Savings"

    def __str__(self):
        return f"{self.user.username} - ₱{self.amount} on {self.date}"

