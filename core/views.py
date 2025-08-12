
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
    TransactionForm, SavingsForm, QuickTransactionForm,
    WeekFilterForm, MonthFilterForm, AddCashOnHandForm
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
                ('Wants', 'wants', '#8b5cf6'),
                ('Needs', 'needs', '#6f42c1'),
                ('Grocery', 'grocery', '#28a745'),
                ('School/Education', 'school', '#007bff'),
                ('Daily Allowance', 'allowance', '#ffc107'),
                ('Mobile Load', 'load', '#17a2b8'),
                ('Transportation', 'transportation', '#6c757d'),
                ('Food & Dining', 'food', '#fd7e14'),
                ('Entertainment', 'entertainment', '#e83e8c'),
                ('Health & Medical', 'health', '#20c997'),
                ('Savings', 'savings', '#6f42c1'),
                ('Other', 'other', '#6c757d'),
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
    add_cash_form = AddCashOnHandForm()
    
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
        'add_cash_form': add_cash_form,
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


@login_required
def weekly_report(request):
    """Weekly report page with allowance, savings, and expenses breakdown."""
    today = timezone.now().date()
    form = WeekFilterForm(request.GET or None)
    if form.is_valid() and form.cleaned_data.get('week_start'):
        week_start = form.cleaned_data['week_start']
    else:
        week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    # Data
    weekly_transactions = Transaction.objects.filter(user=request.user, date__range=[week_start, week_end])
    weekly_allowance = weekly_transactions.filter(category__category_type='allowance').aggregate(total=Sum('amount'))['total'] or 0
    weekly_savings = Savings.objects.filter(user=request.user, date__range=[week_start, week_end]).aggregate(total=Sum('amount'))['total'] or 0
    weekly_expenses_by_category = (
        weekly_transactions.filter(transaction_type='expense')
        .values('category__name', 'category__color')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )

    # Weekly budget (Cash on Hand for the week)
    weekly_budget = Budget.objects.filter(user=request.user, budget_type='weekly', start_date=week_start).first()
    weekly_expense_total = weekly_transactions.filter(transaction_type='expense').aggregate(total=Sum('amount'))['total'] or 0
    weekly_budget_spent = weekly_budget.spent_amount() if weekly_budget else weekly_expense_total
    weekly_budget_amount = weekly_budget.amount if weekly_budget else Decimal('0')
    weekly_budget_remaining = (weekly_budget_amount - weekly_budget_spent) if weekly_budget else Decimal('0')
    weekly_budget_percentage = float((weekly_budget_spent / weekly_budget_amount * 100) if weekly_budget_amount > 0 else 0)
    if weekly_budget_percentage > 100:
        weekly_budget_percentage = 100

    add_cash_form = AddCashOnHandForm()

    context = {
        'form': form,
        'week_start': week_start,
        'week_end': week_end,
        'weekly_allowance': weekly_allowance,
        'weekly_savings': weekly_savings,
        'weekly_expenses_by_category': weekly_expenses_by_category,
        'weekly_budget': weekly_budget,
        'weekly_budget_amount': weekly_budget_amount,
        'weekly_budget_spent': weekly_budget_spent,
        'weekly_budget_remaining': weekly_budget_remaining,
        'add_cash_form': add_cash_form,
        'weekly_budget_percentage': weekly_budget_percentage,
    }
    return render(request, 'core/weekly_report.html', context)


@login_required
def monthly_report(request):
    """Monthly report page with bills, expenses breakdown, and savings."""
    today = timezone.now().date()
    form = MonthFilterForm(request.GET or None)
    month = int(form.data.get('month') or today.month)
    year = int(form.data.get('year') or today.year)

    month_start = date(year, month, 1)
    if month == 12:
        next_month_start = date(year + 1, 1, 1)
    else:
        next_month_start = date(year, month + 1, 1)
    month_end = next_month_start - timedelta(days=1)

    monthly_transactions = Transaction.objects.filter(user=request.user, date__range=[month_start, month_end])
    monthly_expenses_by_category = (
        monthly_transactions.filter(transaction_type='expense')
        .values('category__name', 'category__color')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )
    monthly_savings_total = Savings.objects.filter(user=request.user, date__range=[month_start, month_end]).aggregate(total=Sum('amount'))['total'] or 0

    # Placeholder for bills: if you later add a Bill model, replace this
    monthly_bills = []

    # Monthly budget (Cash on Hand for the month)
    monthly_budget = Budget.objects.filter(user=request.user, budget_type='monthly', start_date=month_start).first()
    monthly_expense_total = monthly_transactions.filter(transaction_type='expense').aggregate(total=Sum('amount'))['total'] or 0
    monthly_budget_spent = monthly_budget.spent_amount() if monthly_budget else monthly_expense_total
    monthly_budget_amount = monthly_budget.amount if monthly_budget else Decimal('0')
    monthly_budget_remaining = (monthly_budget_amount - monthly_budget_spent) if monthly_budget else Decimal('0')
    monthly_budget_percentage = float((monthly_budget_spent / monthly_budget_amount * 100) if monthly_budget_amount > 0 else 0)
    if monthly_budget_percentage > 100:
        monthly_budget_percentage = 100

    add_cash_form = AddCashOnHandForm()

    context = {
        'form': form,
        'month': month,
        'year': year,
        'monthly_bills': monthly_bills,
        'monthly_expenses_by_category': monthly_expenses_by_category,
        'monthly_savings_total': monthly_savings_total,
        'monthly_budget': monthly_budget,
        'monthly_budget_amount': monthly_budget_amount,
        'monthly_budget_spent': monthly_budget_spent,
        'monthly_budget_remaining': monthly_budget_remaining,
        'month_start': month_start,
        'month_end': month_end,
        'add_cash_form': add_cash_form,
        'monthly_budget_percentage': monthly_budget_percentage,
    }
    return render(request, 'core/monthly_report.html', context)


@login_required
def add_cash_on_hand(request):
    if request.method == 'POST':
        form = AddCashOnHandForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            description = form.cleaned_data.get('description')
            profile, _ = Profile.objects.get_or_create(user=request.user)
            profile.money_on_hand += amount
            profile.save()
            # Optionally log as a transaction of type income with 'Other' category if available
            other_category = Category.objects.filter(user=request.user, category_type='other').first()
            if other_category:
                Transaction.objects.create(
                    user=request.user,
                    title=description or 'Cash top-up',
                    description=description or 'Added cash on hand',
                    amount=amount,
                    transaction_type='income',
                    category=other_category,
                    date=timezone.now().date(),
                )
            messages.success(request, 'Cash on hand updated successfully.')
            return redirect('core:dashboard')
    return redirect('core:dashboard')


@login_required
def add_weekly_budget(request):
    if request.method == 'POST':
        form = AddCashOnHandForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            # Expect hidden input week_start
            try:
                week_start_str = request.POST.get('week_start')
                week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
            except Exception:
                today = timezone.now().date()
                week_start = today - timedelta(days=today.weekday())
            budget, _ = Budget.objects.update_or_create(
                user=request.user,
                budget_type='weekly',
                start_date=week_start,
                defaults={'name': 'Weekly Budget', 'amount': amount, 'is_active': True}
            )
            messages.success(request, 'Weekly cash on hand (budget) set successfully.')
            return redirect('core:weekly_report')
    return redirect('core:weekly_report')


@login_required
def add_monthly_budget(request):
    if request.method == 'POST':
        form = AddCashOnHandForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            # Expect hidden month and year
            try:
                month = int(request.POST.get('month'))
                year = int(request.POST.get('year'))
            except Exception:
                today = timezone.now().date()
                month = today.month
                year = today.year
            month_start = date(year, month, 1)
            budget, _ = Budget.objects.update_or_create(
                user=request.user,
                budget_type='monthly',
                start_date=month_start,
                defaults={'name': 'Monthly Budget', 'amount': amount, 'is_active': True}
            )
            messages.success(request, 'Monthly cash on hand (budget) set successfully.')
            return redirect('core:monthly_report')
    return redirect('core:monthly_report')


def logout_view(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('core:home')

