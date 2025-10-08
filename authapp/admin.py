# web/authapp/admin.py
from django.contrib import admin
from .models import User, AuthorizationStatus, UserSession, Invite

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'tele_id', 'role', 'is_verified', 'date_reg')
    list_filter = ('role', 'is_verified')
    search_fields = ('username', 'tele_id')

admin.site.register(AuthorizationStatus)
admin.site.register(UserSession)
admin.site.register(Invite)
