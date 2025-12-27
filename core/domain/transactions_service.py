# core/domain/transactions_service.py
from core.models import Transaction
from core.domain.money_engine import MoneyEngine
from django.db import transaction as db_tx


class TransactionService:
    @staticmethod
    @db_tx.atomic
    def create_transaction(user, amount, tx_type, category=None, title='', description='', date=None):
        """
        Creates a Transaction and applies its financial effect via MoneyEngine.
        Returns the created Transaction.
        """
        tx = Transaction.objects.create(
            user=user,
            title=title or tx_type.capitalize(),
            description=description or '',
            amount=amount,
            transaction_type=tx_type,
            category=category,
            date=date
        )
        # Apply balance change
        MoneyEngine.apply_transaction_to_profile(tx)
        return tx
