from django.shortcuts import render, redirect
from core.models import Profile
from .forms import SignUpForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('/')  # or redirect to 'dashboard'
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})
def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            monthly_income = form.cleaned_data.get('monthly_income')
            Profile.objects.create(user=user, monthly_income=monthly_income)
            login(request, user)
            return redirect('dashboard')  # Redirect to dashboard
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

@login_required
def dashboard(request):
    return render(request, 'dashboard.html')
