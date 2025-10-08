from django.db import models
from django.utils import timezone
from authapp.models import User

class ExchangeRate(models.Model):
    last_update = models.DateTimeField(default=timezone.now)
    p2p_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sale_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.p2p_rate is not None:
            self.sale_rate = self.p2p_rate * 1.04
        super().save(*args, **kwargs)


class Wallet(models.Model):
    BANK_CHOICES = [
        ('tinkoff', 'Тинькофф'),
        ('sber', 'Сбербанк'),
        ('mts', 'МТС Банк'),
        ('gazprombank', 'Газпромбанк'),
        ('vtb', 'ВТБ'),
        ('akbars', 'Ак Барс'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wallets")
    bank = models.CharField(max_length=20, choices=BANK_CHOICES, default='tinkoff')
    card_number = models.CharField(max_length=16, unique=True)
    owner_name = models.CharField(max_length=255)
    is_enabled = models.BooleanField(default=True)
    limit_per_day = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wallets"


class DepWallet(models.Model):
    wallet_address = models.CharField(max_length=255, unique=True)
    is_enabled = models.BooleanField(default=True)

    def __str__(self):
        return self.wallet_address


class DepositRequest(models.Model):
    STATUS_CHOICES = [
        ('active', 'Активная'),
        ('completed', 'Завершенная'),
        ('canceled', 'Отмененная'),
        ('expired', 'Просроченная'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    wallet_address = models.ForeignKey(DepWallet, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    expiration_date = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.id:
            self.expiration_date = timezone.now() + timezone.timedelta(minutes=15)
        super().save(*args, **kwargs)

    class Meta:
        db_table = "deposit_requests"


class Bid(models.Model):
    STATUS_CHOICES = [
        ('active', 'Активная'),
        ('pending', 'В ожидании'),
        ('completed', 'Завершена'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    amount_rub = models.DecimalField(max_digits=10, decimal_places=2)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "bids"
