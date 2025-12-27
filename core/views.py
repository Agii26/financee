# core/views.py
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta, date, datetime
from django.http import JsonResponse
from django.db.models import Sum
import json
import math

from .models import Profile, Category, Budget, Transaction, Savings
from .forms import (
    QuickTransactionForm, AddCashOnHandForm, SavingsForm, 
    WeekFilterForm, MonthFilterForm, WeeklyAllowanceForm,
    UserRegistrationForm, LoginForm
)
from core.domain.transactions_service import TransactionService
from core.domain.budgets_service import BudgetService
from core.domain.savings_service import SavingsService

# --------- Home Page ----------
def home(request):
    """Landing page for the application"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    return render(request, 'core/home.html')


# --------- Authentication Views ----------
def login_view(request):
    """Handle user login"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                return redirect('core:dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    
    return render(request, 'core/login.html', {'form': form})


def register(request):
    """Handle user registration"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.save()
            
            # Create or update profile with additional info
            profile, created = Profile.objects.get_or_create(user=user)
            if form.cleaned_data.get('monthly_income'):
                profile.monthly_income = form.cleaned_data['monthly_income']
            if form.cleaned_data.get('money_on_hand'):
                profile.money_on_hand = form.cleaned_data['money_on_hand']
            profile.save()
            
            messages.success(request, 'Account created successfully! Please login.')
            return redirect('core:login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'core/register.html', {'form': form})


def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('core:home')


# --------- Dashboard (read-only, no mutations) ----------
@login_required
def dashboard(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    today = timezone.now().date()
    current_month = today.month
    current_year = today.year

    month_start = date(current_year, current_month, 1)
    if current_month == 12:
        next_month_start = date(current_year + 1, 1, 1)
    else:
        next_month_start = date(current_year, current_month + 1, 1)
    month_end = next_month_start - timedelta(days=1)

    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    monthly_transactions = Transaction.objects.filter(user=request.user, date__range=[month_start, month_end])

    monthly_income = monthly_transactions.filter(transaction_type='income').aggregate(total=Sum('amount'))['total'] or Decimal('0')
    monthly_expenses = monthly_transactions.filter(transaction_type='expense').aggregate(total=Sum('amount'))['total'] or Decimal('0')
    monthly_savings = monthly_transactions.filter(transaction_type='savings').aggregate(total=Sum('amount'))['total'] or Decimal('0')

    weekly_expenses = Transaction.objects.filter(user=request.user, date__range=[week_start, week_end], transaction_type='expense').aggregate(total=Sum('amount'))['total'] or Decimal('0')

    daily_savings = Savings.objects.filter(user=request.user, date__range=[month_start, month_end]).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    total_savings = Savings.objects.filter(user=request.user).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    recent_transactions = Transaction.objects.filter(user=request.user).order_by('-date')[:10]

    category_expenses = monthly_transactions.filter(transaction_type='expense').values('category__name', 'category__color').annotate(total=Sum('amount')).order_by('-total')

    active_budgets = Budget.objects.filter(user=request.user, is_active=True)
    budget_overview = []
    for budget in active_budgets:
        spent = Transaction.objects.filter(user=request.user, date__range=[budget.start_date, budget.end_date], transaction_type__in=['expense', 'savings']).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        remaining = Decimal(budget.amount) - Decimal(spent)
        percentage = float((Decimal(spent) / Decimal(budget.amount) * 100) if budget.amount > 0 else 0)
        budget_overview.append({'budget': budget, 'spent': spent, 'remaining': remaining, 'percentage': min(percentage, 100)})

    quick_form = QuickTransactionForm()
    add_cash_form = AddCashOnHandForm()
    add_savings_form = SavingsForm()

    chart_data = {
        'categories': [item['category__name'] for item in category_expenses],
        'amounts': [float(item['total']) for item in category_expenses],
        'colors': [item['category__color'] for item in category_expenses],
    }

    monthly_trend = []
    for i in range(6):
        month_date = today.replace(day=1) - timedelta(days=30*i)
        month_expenses = Transaction.objects.filter(user=request.user, date__year=month_date.year, date__month=month_date.month, transaction_type='expense').aggregate(total=Sum('amount'))['total'] or Decimal('0')
        monthly_trend.append({'month': month_date.strftime('%b %Y'), 'amount': float(month_expenses)})
    monthly_trend.reverse()

    context = {
        'profile': profile,
        'monthly_income': monthly_income,
        'total_cash_on_hand': profile.money_on_hand,
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
        'add_savings_form': add_savings_form,
        'chart_data': json.dumps(chart_data),
        'monthly_trend': json.dumps(monthly_trend),
        'current_month': today.strftime('%B %Y'),
    }
    return render(request, 'core/dashboard.html', context)


# ---------- Quick expense (AJAX) ----------
@login_required
def quick_expense(request):
    if request.method == 'POST':
        form = QuickTransactionForm(request.POST)
        if not form.is_valid():
            return JsonResponse({'success': False, 'errors': form.errors})
        amount = form.cleaned_data['amount']
        category_type = form.cleaned_data['category']
        description = form.cleaned_data.get('description', '')

        category, _ = Category.objects.get_or_create(user=request.user, category_type=category_type, defaults={'name': category_type.capitalize()})
        TransactionService.create_transaction(user=request.user, amount=amount, tx_type='expense', category=category, title=description or f"{category.name} Expense", description=description, date=timezone.now().date())
        return JsonResponse({'success': True, 'message': 'Expense added successfully.'})
    return JsonResponse({'success': False, 'message': 'Invalid request'})


# ---------- Add cash (TOP-UP) ----------
@login_required
def add_cash_on_hand(request):
    if request.method == 'POST':
        form = AddCashOnHandForm(request.POST)
        if not form.is_valid():
            messages.error(request, 'Invalid input.')
            return redirect('core:dashboard')
        amount = form.cleaned_data['amount']
        description = form.cleaned_data.get('description', 'Cash top-up')
        income_cat, _ = Category.objects.get_or_create(user=request.user, category_type='income', defaults={'name': 'Income'})
        TransactionService.create_transaction(user=request.user, amount=amount, tx_type='income', category=income_cat, title=description, description=description, date=timezone.now().date())
        messages.success(request, 'Cash topped up successfully.')
    return redirect('core:dashboard')


# ---------- Weekly budget ----------
@login_required
def add_weekly_budget(request):
    if request.method == 'POST':
        form = AddCashOnHandForm(request.POST)
        if not form.is_valid():
            messages.error(request, 'Invalid input.')
            return redirect('core:weekly_report')
        amount = Decimal(form.cleaned_data['amount'])
        week_start_str = request.POST.get('week_start')
        if week_start_str:
            try:
                week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
            except Exception:
                week_start = timezone.now().date() - timedelta(days=timezone.now().date().weekday())
        else:
            week_start = timezone.now().date() - timedelta(days=timezone.now().date().weekday())

        try:
            BudgetService.create_weekly_budget(user=request.user, amount=amount, start_date=week_start)
            messages.success(request, 'Weekly budget allocated successfully.')
        except Exception as e:
            messages.error(request, str(e))
    return redirect('core:weekly_report')


# ---------- Monthly budget ----------
@login_required
def add_monthly_budget(request):
    if request.method == 'POST':
        form = AddCashOnHandForm(request.POST)
        if not form.is_valid():
            messages.error(request, 'Invalid input.')
            return redirect('core:monthly_report')
        amount = Decimal(form.cleaned_data['amount'])
        try:
            month = int(request.POST.get('month'))
            year = int(request.POST.get('year'))
            month_start = date(year, month, 1)
        except Exception:
            today = timezone.now().date()
            month_start = date(today.year, today.month, 1)
        try:
            BudgetService.create_monthly_budget(user=request.user, amount=amount, month_start=month_start)
            messages.success(request, 'Monthly budget allocated successfully.')
        except Exception as e:
            messages.error(request, str(e))
    return redirect('core:monthly_report')


# ---------- Add savings ----------
@login_required
def add_savings(request):
    if request.method == 'POST':
        form = SavingsForm(request.POST)
        if not form.is_valid():
            messages.error(request, 'Invalid input.')
            return redirect('core:weekly_report')
        amount = form.cleaned_data['amount']
        description = form.cleaned_data.get('description', '')
        date_val = form.cleaned_data['date']
        try:
            SavingsService.create_savings(user=request.user, amount=amount, description=description, date=date_val)
            messages.success(request, 'Savings added.')
        except Exception as e:
            messages.error(request, str(e))
    return redirect('core:weekly_report')


# ---------- Weekly allowance (income) ----------
@login_required
def add_weekly_allowance(request):
    if request.method == 'POST':
        form = WeeklyAllowanceForm(request.POST)
        if not form.is_valid():
            messages.error(request, f"Allowance form error: {form.errors}")
            return redirect('core:weekly_report')
        amount = form.cleaned_data['amount']
        date_val = form.cleaned_data['date']
        allowance_cat, _ = Category.objects.get_or_create(user=request.user, category_type='allowance', defaults={'name': 'Allowance'})
        TransactionService.create_transaction(user=request.user, amount=amount, tx_type='income', category=allowance_cat, title='Weekly Allowance', description=f'Allowance for {date_val}', date=date_val)
        messages.success(request, 'Allowance added.')
    return redirect('core:weekly_report')


# ---------- Add weekly savings ----------
@login_required
def add_weekly_savings(request):
    if request.method == 'POST':
        form = SavingsForm(request.POST)
        if not form.is_valid():
            messages.error(request, 'Invalid input.')
            return redirect('core:weekly_report')
        amount = form.cleaned_data['amount']
        description = form.cleaned_data.get('description', 'Weekly savings')
        # Use current week start as default date
        week_start = timezone.now().date() - timedelta(days=timezone.now().date().weekday())
        try:
            SavingsService.create_savings(user=request.user, amount=amount, description=description, date=week_start)
            messages.success(request, 'Weekly savings added.')
        except Exception as e:
            messages.error(request, str(e))
    return redirect('core:weekly_report')


# ---------- Weekly Report ----------
@login_required
def weekly_report(request):
    form = WeekFilterForm(request.GET or None)
    
    # Get week start from form or default to current week
    if form.is_valid() and form.cleaned_data.get('week_start'):
        week_start = form.cleaned_data['week_start']
    else:
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
    
    week_end = week_start + timedelta(days=6)
    
    # Get weekly transactions
    weekly_transactions = Transaction.objects.filter(
        user=request.user,
        date__range=[week_start, week_end]
    )
    
    # Calculate weekly expenses by category
    weekly_expenses_by_category = weekly_transactions.filter(
        transaction_type='expense'
    ).values('category__name', 'category__color').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    # Get weekly budget
    weekly_budget = Budget.objects.filter(
        user=request.user,
        budget_type='weekly',
        start_date=week_start,
        is_active=True
    ).first()
    
    weekly_budget_amount = weekly_budget.amount if weekly_budget else Decimal('0')
    weekly_budget_spent = weekly_transactions.filter(
        transaction_type__in=['expense', 'savings']
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    weekly_budget_remaining = weekly_budget_amount - weekly_budget_spent
    weekly_budget_percentage = float((weekly_budget_spent / weekly_budget_amount * 100) if weekly_budget_amount > 0 else 0)
    
    # Get weekly allowance
    weekly_allowance = weekly_transactions.filter(
        transaction_type='income',
        category__category_type='allowance'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Get weekly savings
    weekly_savings = Savings.objects.filter(
        user=request.user,
        date__range=[week_start, week_end]
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    context = {
        'form': form,
        'week_start': week_start,
        'week_end': week_end,
        'weekly_expenses_by_category': weekly_expenses_by_category,
        'weekly_budget_amount': weekly_budget_amount,
        'weekly_budget_spent': weekly_budget_spent,
        'weekly_budget_remaining': weekly_budget_remaining,
        'weekly_budget_percentage': weekly_budget_percentage,
        'weekly_allowance': weekly_allowance,
        'weekly_savings': weekly_savings,
        'add_cash_form': AddCashOnHandForm(),
        'add_allowance_form': WeeklyAllowanceForm(),
        'add_savings_form': SavingsForm(),
    }
    
    return render(request, 'core/weekly_report.html', context)


# ---------- Monthly Report ----------
@login_required
def monthly_report(request):
    form = MonthFilterForm(request.GET or None)
    
    # Get month and year from form or default to current month
    if form.is_valid():
        month = form.cleaned_data.get('month') or timezone.now().date().month
        year = form.cleaned_data.get('year') or timezone.now().date().year
    else:
        today = timezone.now().date()
        month = today.month
        year = today.year
    
    month_start = date(year, month, 1)
    if month == 12:
        next_month_start = date(year + 1, 1, 1)
    else:
        next_month_start = date(year, month + 1, 1)
    month_end = next_month_start - timedelta(days=1)
    
    # Get monthly transactions
    monthly_transactions = Transaction.objects.filter(
        user=request.user,
        date__range=[month_start, month_end]
    )
    
    # Calculate monthly expenses by category
    monthly_expenses_by_category = monthly_transactions.filter(
        transaction_type='expense'
    ).values('category__name', 'category__color').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    # Get monthly budget
    monthly_budget = Budget.objects.filter(
        user=request.user,
        budget_type='monthly',
        start_date=month_start,
        is_active=True
    ).first()
    
    monthly_budget_amount = monthly_budget.amount if monthly_budget else Decimal('0')
    monthly_budget_spent = monthly_transactions.filter(
        transaction_type__in=['expense', 'savings']
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    monthly_budget_remaining = monthly_budget_amount - monthly_budget_spent
    monthly_budget_percentage = float((monthly_budget_spent / monthly_budget_amount * 100) if monthly_budget_amount > 0 else 0)
    
    # Get monthly savings
    monthly_savings_total = Savings.objects.filter(
        user=request.user,
        date__range=[month_start, month_end]
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    context = {
        'form': form,
        'month': month,
        'year': year,
        'month_start': month_start,
        'month_end': month_end,
        'monthly_expenses_by_category': monthly_expenses_by_category,
        'monthly_budget_amount': monthly_budget_amount,
        'monthly_budget_spent': monthly_budget_spent,
        'monthly_budget_remaining': monthly_budget_remaining,
        'monthly_budget_percentage': monthly_budget_percentage,
        'monthly_savings_total': monthly_savings_total,
        'add_cash_form': AddCashOnHandForm(),
    }
    
    return render(request, 'core/monthly_report.html', context)

def transaction_list(request):
    transactions = Transaction.objects.filter(user=request.user).order_by('-date')
    categories = Category.objects.filter(user=request.user)
    
    # Calculate totals
    total_income = transactions.filter(transaction_type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = transactions.filter(transaction_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    total_savings = transactions.filter(transaction_type='savings').aggregate(Sum('amount'))['amount__sum'] or 0
    net_balance = total_income - total_expenses
    
    # Category breakdown for chart - CONVERT DECIMAL TO FLOAT
    category_breakdown = []
    for cat in transactions.filter(transaction_type='expense').values('category__id', 'category__name', 'category__color').annotate(total=Sum('amount')).order_by('-total'):
        category_breakdown.append({
            'id': cat['category__id'],
            'name': cat['category__name'],
            'color': cat['category__color'],
            'total': float(cat['total']) if cat['total'] else 0  # Convert Decimal to float
        })
    
    # Serialize transactions for JavaScript - CONVERT DECIMAL TO STRING
    transactions_json = json.dumps([{
        'id': t.id,
        'title': t.title,
        'amount': str(t.amount),  # Convert Decimal to string
        'date': t.date.isoformat(),
        'transaction_type': t.transaction_type,
        'description': t.description or '',
        'category': {
            'id': t.category.id,
            'name': t.category.name,
            'color': t.category.color
        }
    } for t in transactions])
    
    categories_json = json.dumps([{
        'id': c.id,
        'name': c.name,
        'color': c.color
    } for c in categories])
    
    context = {
        'transactions': transactions,
        'transactions_json': transactions_json,
        'categories': categories,
        'categories_json': categories_json,
        'category_breakdown': json.dumps(category_breakdown),  # Now safe to serialize
        'total_income': total_income,
        'total_expenses': total_expenses,
        'total_savings': total_savings,
        'net_balance': net_balance,
        'total_pages': math.ceil(transactions.count() / 50) if transactions.count() > 0 else 1
    }
    
    return render(request, 'core/transaction_list.html', context)