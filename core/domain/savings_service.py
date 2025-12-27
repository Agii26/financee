# core/domain/savings_service.py
from core.models import Savings, Category
from core.domain.transactions_service import TransactionService
from django.db import transaction as db_tx


class SavingsService:
    @staticmethod
    @db_tx.atomic
    def create_savings(user, amount, description, date):
        # Create savings record
        Savings.objects.create(user=user, amount=amount, description=description, date=date)
        # Ensure category
        savings_cat, _ = Category.objects.get_or_create(user=user, category_type='savings', defaults={'name': 'Savings'})
        # Create corresponding transaction that will be applied to profile via TransactionService
        tx = TransactionService.create_transaction(user=user, amount=amount, tx_type='savings', category=savings_cat, title=description or "Savings", description=description, date=date)
        return tx
