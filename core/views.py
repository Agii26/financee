
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta, date
from decimal import Decimal
import json

from .models import Profile, Category, Budget, Transaction, Savings
from .forms import (
    SignUpForm, ProfileForm, CategoryForm, BudgetForm, 
    TransactionForm, SavingsForm, QuickTransactionForm
)

def home(request):
    """Home page view"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    return render(request, 'core/home.html')

def login_view(request):
    """User login view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('core:dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'core/login.html')

def register(request):
    """User registration view"""

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()

            monthly_income = form.cleaned_data.get('monthly_income', 0)
            money_on_hand = form.cleaned_data.get('money_on_hand', 0)
            
            # Create user profile
            Profile.objects.create(
                user=user,
                monthly_income=monthly_income or 0,
                money_on_hand=money_on_hand or 0
            )
            
            # Create default categories
            default_categories = [
                ('Bills', 'bills', '#dc3545'),
                ('Grocery', 'grocery', '#28a745'),
                ('School/Education', 'school', '#007bff'),
                ('Daily Allowance', 'allowance', '#ffc107'),
                ('Mobile Load', 'load', '#17a2b8'),
                ('Transportation', 'transportation', '#6c757d'),
                ('Food & Dining', 'food', '#fd7e14'),
                ('Entertainment', 'entertainment', '#e83e8c'),
                ('Health & Medical', 'health', '#20c997'),
                ('Savings', 'savings', '#6f42c1'),
            ]
            
            for name, cat_type, color in default_categories:
                Category.objects.create(
                    user=user,
                    name=name,
                    category_type=cat_type,
                    color=color
                )
            
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            
            messages.success(request, f'Welcome to FinanceHub, {user.first_name}!')
            return redirect('core:dashboard')
    else:
        form = SignUpForm()
    
    return render(request, 'core/register.html', {'form': form})

@login_required
def dashboard(request):
    """Main dashboard view with comprehensive financial overview"""

    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)
    
    # Get current date info
    today = timezone.now().date()
    current_month = today.month
    current_year = today.year
    
    # Calculate date ranges
    month_start = date(current_year, current_month, 1)
    if current_month == 12:
        next_month_start = date(current_year + 1, 1, 1)
    else:
        next_month_start = date(current_year, current_month + 1, 1)
    month_end = next_month_start - timedelta(days=1)
    
    # Week calculation
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    # Get transactions for current month
    monthly_transactions = Transaction.objects.filter(
        user=request.user,
        date__range=[month_start, month_end]
    )
    
    # Calculate totals
    monthly_income = monthly_transactions.filter(transaction_type='income').aggregate(
        total=Sum('amount'))['total'] or 0
    monthly_expenses = monthly_transactions.filter(transaction_type='expense').aggregate(
        total=Sum('amount'))['total'] or 0
    monthly_savings = monthly_transactions.filter(transaction_type='savings').aggregate(
        total=Sum('amount'))['total'] or 0
    
    # Weekly expenses
    weekly_expenses = Transaction.objects.filter(
        user=request.user,
        date__range=[week_start, week_end],
        transaction_type='expense'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Daily savings for current month
    daily_savings = Savings.objects.filter(
        user=request.user,
        date__range=[month_start, month_end]
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Total savings all time
    total_savings = Savings.objects.filter(user=request.user).aggregate(
        total=Sum('amount'))['total'] or 0
    
    # Recent transactions (last 10)
    recent_transactions = Transaction.objects.filter(user=request.user)[:10]
    
    # Category wise expenses for pie chart
    category_expenses = monthly_transactions.filter(
        transaction_type='expense'
    ).values('category__name', 'category__color').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    # Budget overview
    active_budgets = Budget.objects.filter(user=request.user, is_active=True)
    budget_overview = []
    for budget in active_budgets:
        spent = budget.spent_amount()
        remaining = budget.remaining_amount()
        percentage = (spent / budget.amount * 100) if budget.amount > 0 else 0
        budget_overview.append({
            'budget': budget,
            'spent': spent,
            'remaining': remaining,
            'percentage': min(percentage, 100)
        })
    
    # Quick transaction form
    quick_form = QuickTransactionForm()
    
    # Prepare chart data
    chart_data = {
        'categories': [item['category__name'] for item in category_expenses],
        'amounts': [float(item['total']) for item in category_expenses],
        'colors': [item['category__color'] for item in category_expenses],
    }
    
    # Monthly expense trend (last 6 months)
    monthly_trend = []
    for i in range(6):
        month_date = today.replace(day=1) - timedelta(days=30*i)
        month_expenses = Transaction.objects.filter(
            user=request.user,
            date__year=month_date.year,
            date__month=month_date.month,
            transaction_type='expense'
        ).aggregate(total=Sum('amount'))['total'] or 0
        monthly_trend.append({
            'month': month_date.strftime('%b %Y'),
            'amount': float(month_expenses)
        })
    monthly_trend.reverse()
    
    context = {
        'profile': profile,
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'monthly_savings': monthly_savings,
        'weekly_expenses': weekly_expenses,
        'daily_savings': daily_savings,
        'total_savings': total_savings,
        'recent_transactions': recent_transactions,
        'category_expenses': category_expenses,
        'budget_overview': budget_overview,
        'quick_form': quick_form,
        'chart_data': json.dumps(chart_data),
        'monthly_trend': json.dumps(monthly_trend),
        'current_month': today.strftime('%B %Y'),
    }
    
    return render(request, 'core/dashboard.html', context)

@login_required
def quick_expense(request):
    """Quick expense addition via AJAX"""
    if request.method == 'POST':
        form = QuickTransactionForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            category_type = form.cleaned_data['category']
            description = form.cleaned_data['description']
            
            # Get or create category
            category, created = Category.objects.get_or_create(
                user=request.user,
                category_type=category_type,
                defaults={'name': dict(QuickTransactionForm.QUICK_CATEGORIES)[category_type]}
            )
            
            # Create transaction
            Transaction.objects.create(
                user=request.user,
                title=description or f"{category.name} Expense",
                description=description,
                amount=amount,
                transaction_type='expense',
                category=category,
                date=timezone.now().date()
            )
            
            # Update money on hand
            profile = request.user.profile
            profile.money_on_hand -= amount
            profile.save()
            
            return JsonResponse({'success': True, 'message': 'Expense added successfully!'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

def logout_view(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('core:home')

