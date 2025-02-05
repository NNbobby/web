from authapp.models import User  # Импорт твоей модели

def user_data(request):
    if 'user_id' in request.session:  # Проверяем, есть ли в сессии ID пользователя
        try:
            user = User.objects.get(tele_id=request.session['user_id'])  # Загружаем пользователя по `tele_id`
            return {
                'user_balance': user.balance,
                'user_escrow': user.escrow,
                'user_deals_count': user.deals_count,
                'user_turnover': user.turnover,
            }
        except User.DoesNotExist:
            return {}  # Если пользователя не нашли, возвращаем пустой контекст
    return {}

from authapp.models import ExchangeRate

def exchange_rate_context(request):
    try:
        exchange_rate = ExchangeRate.objects.first()
        return {
            'exchange_rate': exchange_rate
        }
    except ExchangeRate.DoesNotExist:
        return {'exchange_rate': None}
