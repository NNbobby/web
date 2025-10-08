from decimal import Decimal
from django.db import transaction
from ledger.models import Account, TransactionLog
from authapp.models import User

class LedgerService:
    @staticmethod
    @transaction.atomic
    def transfer(from_user: User, to_user: User, amount: Decimal, description: str = ""):
        """Перевод между пользователями"""
        sender = Account.objects.select_for_update().get(user=from_user)
        receiver = Account.objects.select_for_update().get(user=to_user)

        if sender.balance < amount:
            raise ValueError("Недостаточно средств для перевода")

        sender.balance -= amount
        receiver.balance += amount

        sender.turnover += amount
        receiver.turnover += amount

        sender.save()
        receiver.save()

        TransactionLog.objects.create(
            user=from_user, related_user=to_user, operation="transfer", amount=amount, description=description
        )

    @staticmethod
    @transaction.atomic
    def freeze(user: User, amount: Decimal, description: str = ""):
        """Замораживает средства (например, на время сделки)"""
        account = Account.objects.select_for_update().get(user=user)
        if account.balance < amount:
            raise ValueError("Недостаточно средств для заморозки")

        account.balance -= amount
        account.escrow += amount
        account.save()

        TransactionLog.objects.create(
            user=user, operation="freeze", amount=amount, description=description
        )

    @staticmethod
    @transaction.atomic
    def unfreeze(user: User, amount: Decimal, description: str = ""):
        """Размораживает средства, возвращая их на баланс"""
        account = Account.objects.select_for_update().get(user=user)
        if account.escrow < amount:
            raise ValueError("Недостаточно средств в эскроу")

        account.escrow -= amount
        account.balance += amount
        account.save()

        TransactionLog.objects.create(
            user=user, operation="unfreeze", amount=amount, description=description
        )

    @staticmethod
    @transaction.atomic
    def release_escrow(from_user: User, to_user: User, amount: Decimal, description: str = ""):
        """Перевод замороженных средств от одного пользователя к другому"""
        sender = Account.objects.select_for_update().get(user=from_user)
        receiver = Account.objects.select_for_update().get(user=to_user)

        if sender.escrow < amount:
            raise ValueError("Недостаточно средств в эскроу для перевода")

        sender.escrow -= amount
        receiver.balance += amount

        sender.turnover += amount
        receiver.turnover += amount

        sender.save()
        receiver.save()

        TransactionLog.objects.create(
            user=from_user, related_user=to_user, operation="escrow_release", amount=amount, description=description
        )
