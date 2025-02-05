from celery import shared_task
from authapp.models import ExchangeRate
from traderapp.utils import get_bybit_p2p_rate
from django.utils.timezone import now

@shared_task
def update_exchange_rate():
    """Обновление курса валют каждые 5 минут."""
    p2p_rate = get_bybit_p2p_rate()
    if p2p_rate:
        exchange_rate, created = ExchangeRate.objects.get_or_create(id=1)
        exchange_rate.p2p_rate = p2p_rate
        exchange_rate.last_update = now()
        exchange_rate.save()
    return f"Курс обновлен: {p2p_rate}"