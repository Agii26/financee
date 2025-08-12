from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('quick-expense/', views.quick_expense, name='quick_expense'),
    path('reports/weekly/', views.weekly_report, name='weekly_report'),
    path('reports/monthly/', views.monthly_report, name='monthly_report'),
    path('profile/add-cash/', views.add_cash_on_hand, name='add_cash_on_hand'),
    path('budget/add-weekly/', views.add_weekly_budget, name='add_weekly_budget'),
    path('budget/add-monthly/', views.add_monthly_budget, name='add_monthly_budget'),
]

