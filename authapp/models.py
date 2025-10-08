import uuid
from django.db import models
from django.utils.timezone import now
from django.utils import timezone
from decimal import Decimal

class User(models.Model):
    id = models.AutoField(primary_key=True)
    added_by = models.BigIntegerField(null=False, default=0)
    tele_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=255, blank=True)
    role = models.CharField(max_length=255, blank=True)  # trader/merchant/teamlead/admin
    date_reg = models.DateTimeField(auto_now_add=True)
    token = models.UUIDField(default=uuid.uuid4, null=False, unique=True)

    # removed monetary fields from User — kept minimal; balances moved to ledger.Account
    is_verified = models.BooleanField(default=False)  # админ активирует аккаунт после проверки

    class Meta:
        managed = True
        db_table = 'users'

    def __str__(self):
        return f"{self.username or self.tele_id}"


class AuthorizationStatus(models.Model):
    token = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=50, default="waiting")
    created_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.token}: {self.status}"


class UserSession(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    session_key = models.CharField(max_length=255)
    login_time = models.DateTimeField(default=now)
    logout_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'user_sessions'

    def __str__(self):
        return f"Session ({self.session_key}) for {self.user} from IP {self.ip_address}"
    
class Invite(models.Model):
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_invites')
    role = models.CharField(max_length=50, default='trader')  # роль, которую приглашает админ
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)   # срок действия (если нужен)
    used = models.BooleanField(default=False)
    used_by = models.ForeignKey('User', related_name='used_invites', null=True, blank=True, on_delete=models.SET_NULL)

    def is_valid(self):
        if self.used:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True

    def __str__(self):
        return str(self.token)