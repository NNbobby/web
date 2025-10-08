from django.db import models
import uuid
from django.utils.timezone import now

class User(models.Model):
    id = models.AutoField(primary_key=True)
    added_by = models.BigIntegerField(null=False, default=0)
    tele_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=255, blank=True)
    role = models.CharField(max_length=255, blank=True)
    date_reg = models.DateTimeField(auto_now_add=True)
    token = models.UUIDField(default=uuid.uuid4, unique=True)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.username or str(self.tele_id)


class AuthorizationStatus(models.Model):
    token = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=50, default="waiting")
    created_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.token}: {self.status}"


class UserSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    session_key = models.CharField(max_length=255)
    login_time = models.DateTimeField(default=now)
    logout_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'user_sessions'

    def __str__(self):
        return f"{self.user} — {self.ip_address}"
