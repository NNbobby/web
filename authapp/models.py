from django.db import models
import uuid
from django.utils.timezone import now
from django.utils import timezone
from django.db import models
import uuid

class User(models.Model):
    id = models.AutoField(primary_key=True)
    added_by = models.BigIntegerField(null=False, default=0)  # Telegram ID администратора
    tele_id = models.BigIntegerField(unique=True)  # Уникальный Telegram ID
    username = models.CharField(max_length=255, blank=True)  # Имя пользователя
    role = models.CharField(max_length=255, blank=True)  # Роль (например, клиент или трейдер)
    date_reg = models.DateTimeField(auto_now_add=True)  # Дата регистрации
    token = models.UUIDField(default=uuid.uuid4, null=False, unique=True)  # UUID токен для авторизации
    
    # Новые поля
    balance = models.DecimalField(null=True, max_digits=10, decimal_places=2, default=0.00, verbose_name="Баланс")  # Баланс пользователя
    escrow = models.DecimalField(null=True, max_digits=10, decimal_places=2, default=0.00, verbose_name="Эскроу")  # Замороженные средства
    deals_count = models.PositiveIntegerField(null=True, default=0, verbose_name="Количество сделок")  # Сделки
    turnover = models.DecimalField(null=True, max_digits=15, decimal_places=2, default=0.00, verbose_name="Оборот")  # Общий оборот

    class Meta:
        managed = True
        db_table = 'users'

    def __str__(self):
        return f"User: {self.username or self.tele_id} -- Баланс: {self.balance} ₽ -- Сделок: {self.deals_count}"

    # Метод для увеличения баланса
    def add_balance(self, amount):
        self.balance += amount
        self.save()

    # Метод для уменьшения баланса (с проверкой)
    def subtract_balance(self, amount):
        if self.balance >= amount:
            self.balance -= amount
            self.save()
        else:
            raise ValueError("Недостаточно средств!")


    
class AuthorizationStatus(models.Model):
    token = models.CharField(max_length=255, unique=True)  # Уникальный токен авторизации
    status = models.CharField(max_length=50, default="waiting")  # waiting, confirmed, blocked
    created_at = models.DateTimeField(default=now)  # Время создания записи

    def __str__(self):
        return f"{self.token}: {self.status}"

class UserSession(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE)  # Теперь ссылается на id
    ip_address = models.GenericIPAddressField()  # IP-адрес пользователя
    session_key = models.CharField(max_length=255)  # Ключ сессии
    login_time = models.DateTimeField(default=now)  # Время начала сессии
    logout_time = models.DateTimeField(null=True, blank=True)  # Время завершения сессии (может быть NULL)
    is_active = models.BooleanField(default=True)  # Флаг активности сессии

    def __str__(self):
        return f"Session ({self.session_key}) for {self.user} from IP {self.ip_address}"

    class Meta:
        db_table = 'user_sessions'  # Имя таблицы в базе

class Bid(models.Model):
    STATUS_CHOICES = [
        ('active', 'Активная'),
        ('pending', 'В ожидании'),
        ('completed', 'Завершена'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)  # Владелец заявки (может быть NULL)
    bank = models.CharField(max_length=100)  # Название банка
    amount_rub = models.DecimalField(max_digits=10, decimal_places=2)  # Сумма в рублях
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4)  # Курс обмена RUB -> USDT
    created_at = models.DateTimeField(auto_now_add=True)  # Дата и время создания заявки
    accepted_at = models.DateTimeField(null=True, blank=True)  # Дата принятия заявки, NoneНу 
    account_details = models.CharField(max_length=255)  # Реквизиты
    extra_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Пример
    extra_fee_usdt = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Надбавка в USDT")  # Надбавка в USDT

    class Meta:
        db_table = 'bids'  # Имя таблицы в базе данных

    def __str__(self):
        return f"Заявка {self.id} | {self.amount_rub} RUB -> {self.calculate_usdt()} USDT"

    def calculate_usdt(self):
        """
        Рассчитывает сумму в USDT на основе курса и добавляет надбавку в рублях, если указана `extra_fee_usdt`.
        """
        usdt = self.amount_rub / self.exchange_rate

        # Рассчитываем рублевую эквивалентность надбавки
        if self.extra_fee_usdt > 0:
            rub_fee = self.extra_fee_usdt * self.exchange_rate  # Конвертируем надбавку из USDT в рубли
            usdt += rub_fee / self.exchange_rate  # Добавляем к USDT

        return round(usdt, 2)


class ExchangeRate(models.Model):
    last_update = models.DateTimeField(default=now)  # Дата обновления
    p2p_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Курс BB p2p
    sale_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Курс Sale (+4%)

    def save(self, *args, **kwargs):
        # Автоматический пересчёт "sale_rate" только если "p2p_rate" задан
        if self.p2p_rate is not None:
            self.sale_rate = self.p2p_rate * 1.04
        super().save(*args, **kwargs)


class Wallet(models.Model):
    BANK_CHOICES = [
        ('tinkoff', 'Тинькофф'),
        ('sber', 'Сбербанк'),
        ('mts', 'МТС Банк'),
        ('gazprombank', 'Газпромбанк'),  # Новый банк
        ('vtb', 'ВТБ'),                   # Новый банк
        ('akbars', 'Ак Барс'),            # Новый банк
    ]
    user = models.ForeignKey('authapp.User', on_delete=models.CASCADE, verbose_name="Пользователь", related_name="wallets")
    card_number = models.CharField(max_length=16, unique=True, verbose_name="Номер карты")
    phone_number = models.CharField(max_length=15, null=True, blank=True, verbose_name="Номер телефона")
    account_number = models.CharField(max_length=25, null=True, blank=True, verbose_name="Номер счета")
    owner_name = models.CharField(max_length=255, verbose_name="ФИО владельца")
    description = models.TextField(null=True, blank=True, verbose_name="Описание")
    limit_transactions_per_day = models.PositiveIntegerField(default=0, verbose_name="Лимит количества заявок в сутки")
    limit_amount_per_day = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Лимит суммы пополнений в сутки")
    current_transactions = models.PositiveIntegerField(default=0, verbose_name="Количество использованных заявок")
    current_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Сумма использованного лимита")
    total_turnover = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name="Общий оборот")
    is_enabled = models.BooleanField(default=True, verbose_name="Активен")
    auto_disable_on_limit = models.BooleanField(default=False, verbose_name="Автоотключение при превышении лимита")
    notify_on_disable = models.BooleanField(default=False, verbose_name="Уведомление об отключении")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")
    bank = models.CharField(max_length=20, choices=BANK_CHOICES, default='tinkoff')

    class Meta:
        verbose_name = "Кошелек"
        verbose_name_plural = "Кошельки"
    def toggle_enabled(self):
        self.is_enabled = not self.is_enabled
        self.save()
    def __str__(self):
        return f"{self.card_number} ({self.user.username or self.user.tele_id})"

    def formatted_transaction_limit(self):
        return f"{self.current_transactions}/{self.limit_transactions_per_day}"

    def formatted_amount_limit(self):
        return f"{self.current_amount}/{self.limit_amount_per_day}"

class DepositRequest(models.Model):
    STATUS_CHOICES = [
        ('active', 'Активная'),
        ('completed', 'Завершенная'),
        ('canceled', 'Отмененная'),
        ('expired', 'Просроченная'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # сумма в RUB
    wallet_address = models.ForeignKey('DepWallet', on_delete=models.CASCADE)  # Ссылаемся на DepWallet для адреса
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)  # дата создания заявки
    updated_at = models.DateTimeField(auto_now=True)
    expiration_date = models.DateTimeField(null=True, blank=True)  # Новый столбец

    class Meta:
        db_table = 'deposit_requests'

    def save(self, *args, **kwargs):
        # Устанавливаем expiration_date на 15 минут позже, если это новая запись
        if not self.id:
            self.expiration_date = timezone.now() + timezone.timedelta(minutes=3)
        super().save(*args, **kwargs)


    def __str__(self):
        return f"Заявка {self.id} на сумму {self.amount} RUB"

class DepWallet(models.Model):
    id = models.AutoField(primary_key=True)
    wallet_address = models.CharField(max_length=255, unique=True)  # Исправлено имя поля
    is_enabled = models.BooleanField(default=True)

    def __str__(self):
        return self.wallet_address  # Подправьте на правильное название поля