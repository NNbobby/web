# web/authapp/management/commands/create_invite.py
from django.core.management.base import BaseCommand
from authapp.models import Invite

class Command(BaseCommand):
    help = "Create invite token"

    def add_arguments(self, parser):
        parser.add_argument('--role', default='trader', help='Role for invite (trader/merchant/teamlead/admin)')
        parser.add_argument('--days', type=int, default=7, help='Expiry in days (optional)')

    def handle(self, *args, **options):
        role = options['role']
        days = options['days']
        invite = Invite.objects.create(role=role)
        if days:
            from django.utils import timezone
            invite.expires_at = timezone.now() + timezone.timedelta(days=days)
            invite.save()
        self.stdout.write(f"Invite token: {invite.token} (role={role})")
