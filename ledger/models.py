from django.db import models
from django.utils.timezone import now
from authapp.models import User

class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="account")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    escrow = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    turnover = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username or self.user.tele_id}: {self.balance}₽"

    def deposit(self, amount):
        self.balance += amount
        self.turnover += amount
        self.save()

    def withdraw(self, amount):
        if self.balance >= amount:
            self.balance -= amount
            self.save()
        else:
            raise ValueError("Недостаточно средств")

    class Meta:
        db_table = "accounts"

class TransactionLog(models.Model):
    OPERATION_TYPES = [
        ("deposit", "Пополнение"),
        ("withdraw", "Вывод"),
        ("transfer", "Перевод"),
        ("freeze", "Заморозка"),
        ("unfreeze", "Разморозка"),
        ("escrow_release", "Разблокировка эскроу"),
    ]

    user = models.ForeignKey("authapp.User", on_delete=models.CASCADE)
    operation = models.CharField(max_length=20, choices=OPERATION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)
    related_user = models.ForeignKey(
        "authapp.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="related_transactions"
    )

    class Meta:
        db_table = "transaction_logs"

    def __str__(self):
        return f"[{self.operation}] {self.user} → {self.amount}"
