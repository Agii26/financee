# core/domain/budgets_service.py
from core.models import Budget
from core.domain.money_engine import MoneyEngine
from django.db import transaction as db_tx
from datetime import timedelta, date


class BudgetService:
    @staticmethod
    @db_tx.atomic
    def create_weekly_budget(user, amount, start_date):
        """
        Creates a weekly Budget and deducts the allocation via MoneyEngine.
        """
        # allocate first (this will raise if insufficient)
        profile = user.profile
        MoneyEngine.allocate_budget(profile, amount)

        b = Budget.objects.create(
            user=user,
            name='Weekly Budget',
            amount=amount,
            budget_type='weekly',
            start_date=start_date
        )
        # set sensible end_date
        b.end_date = start_date + timedelta(days=6)
        b.save(update_fields=['end_date'])
        return b

    @staticmethod
    @db_tx.atomic
    def create_monthly_budget(user, amount, month_start):
        profile = user.profile
        MoneyEngine.allocate_budget(profile, amount)
        b = Budget.objects.create(
            user=user,
            name='Monthly Budget',
            amount=amount,
            budget_type='monthly',
            start_date=month_start
        )
        # compute end_date as last day of month
        next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
        b.end_date = next_month - timedelta(days=1)
        b.save(update_fields=['end_date'])
        return b

    @staticmethod
    @db_tx.atomic
    def update_budget(budget, new_amount):
        profile = budget.user.profile
        MoneyEngine.adjust_allocation(profile, budget.amount, new_amount)
        budget.amount = new_amount
        budget.save()
        return budget

    @staticmethod
    @db_tx.atomic
    def close_budget(budget):
        """
        Deactivate budget and return unspent funds to profile.money_on_hand.
        Unspent = budget.amount - sum(transactions that used this budget's period)
        We keep budgets simple; closing should be done by the calling code with correct spent calculation.
        """
        budget.is_active = False
        budget.save(update_fields=['is_active'])
