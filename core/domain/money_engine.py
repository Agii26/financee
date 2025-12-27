# core/domain/money_engine.py
from django.db import transaction as db_tx
from decimal import Decimal
from core.models import Profile


class MoneyEngine:
    """
    Centralized money operations. Always use these methods — never write to
    Profile.money_on_hand directly outside this module.
    """

    @staticmethod
    @db_tx.atomic
    def apply_transaction_to_profile(tx):
        """
        Apply a saved Transaction instance to Profile.money_on_hand.
        tx: Transaction instance (assumed saved)
        """
        profile = tx.user.profile  # Ensure profile exists (create on registration)
        if tx.transaction_type == 'income':
            profile.money_on_hand = (profile.money_on_hand or Decimal('0.00')) + tx.amount
        elif tx.transaction_type in ('expense', 'savings'):
            profile.money_on_hand = (profile.money_on_hand or Decimal('0.00')) - tx.amount
        else:
            # Unknown type: do nothing
            pass
        profile.save(update_fields=['money_on_hand'])

    @staticmethod
    @db_tx.atomic
    def allocate_budget(profile, amount):
        """
        Reserve `amount` from profile.money_on_hand for budgets.
        Raises ValueError if insufficient funds.
        """
        if amount is None:
            raise ValueError("Amount is required")
        available = profile.available_to_allocate
        if amount > available:
            raise ValueError("Insufficient available funds to allocate budget")
        profile.money_on_hand = (profile.money_on_hand or Decimal('0.00')) - Decimal(amount)
        profile.save(update_fields=['money_on_hand'])

    @staticmethod
    @db_tx.atomic
    def adjust_allocation(profile, old_amount, new_amount):
        """
        Adjust a budget allocation when updating its amount:
        - if new_amount > old_amount -> deduct delta from money_on_hand
        - if new_amount < old_amount -> add back (negative delta)
        """
        delta = Decimal(new_amount) - Decimal(old_amount)
        if delta == 0:
            return
        if delta > 0:
            # Need to deduct
            if delta > profile.available_to_allocate:
                raise ValueError("Insufficient available funds to increase budget allocation")
            profile.money_on_hand = (profile.money_on_hand or Decimal('0.00')) - delta
        else:
            # Add back the freed funds
            profile.money_on_hand = (profile.money_on_hand or Decimal('0.00')) - delta  # delta negative
        profile.save(update_fields=['money_on_hand'])
