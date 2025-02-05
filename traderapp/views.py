from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import now, timedelta
from functools import wraps
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from authapp.models import User, UserSession, Bid, ExchangeRate
from django.contrib import messages  # Для системы сообщений
from uuid import UUID
from authapp.utils import get_client_ip  # Лучшая практика: перенос функции "получение IP" в отдельный файл utils.py (опционально)
import json
from django.http import JsonResponse
from authapp.models import ExchangeRate
from traderapp.utils import get_bybit_p2p_rate
from authapp.models import Wallet

def fetch_and_sync_exchange_rate(request):
    if request.method == "GET":
        p2p_rate = get_bybit_p2p_rate()  # Получаем курс с Bybit
        if p2p_rate is None:
            return JsonResponse({"success": False, "message": "Не удалось получить курс с Bybit"}, status=500)
        
        # Обновляем или создаем объект ExchangeRate
        exchange_rate, created = ExchangeRate.objects.get_or_create(id=1)
        exchange_rate.p2p_rate = p2p_rate
        exchange_rate.last_update = now()
        exchange_rate.save()

        return JsonResponse({
            "success": True,
            "p2p_rate": exchange_rate.p2p_rate,
            "sale_rate": exchange_rate.sale_rate
        })
    # Если метод не соответствует (например, POST):
    return JsonResponse({"success": False, "message": "Метод запрещен"}, status=405)



def trader_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user_id = request.session.get('user_id')  # Проверяем наличие user_id в сессии
        if not user_id:
            messages.error(request, 'Вы не авторизованы.')
            return HttpResponseRedirect('/auth/')  # Редирект на страницу авторизации
        
        # Проверяем роль пользователя
        user = User.objects.filter(tele_id=user_id).first()
        if not user or user.role != 'trader':  # Если пользователь отсутствует или роль не "client"
            messages.error(request, 'У вас нет доступа к этой странице.')
            return HttpResponseRedirect('/auth/')  # Вернуть на авторизацию
        
        # Если всё окей, передаем управление представлению
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@trader_required
def wallets(request):
    user = User.objects.get(tele_id=request.session.get('user_id'))
    wallets = Wallet.objects.filter(user=user)  # Показываем кошельки только текущего пользователя
    return render(request, 'traderapp/banks.html', {'wallets': wallets})

@trader_required
def api_wallets(request):
    try:
        user = User.objects.get(tele_id=request.session.get('user_id'))
        wallets = Wallet.objects.filter(user=user).values(
            'id', 'card_number', 'phone_number', 'description', 'current_transactions',
            'limit_transactions_per_day', 'current_amount', 'limit_amount_per_day',
            'total_turnover', 'is_enabled', 'created_at'
        )
        return JsonResponse(list(wallets), safe=False)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Ошибка: {str(e)}'}, status=500)

# API для создания и обновления
@trader_required
def add_wallet(request):
    if request.method == "POST":
        try:
            user = User.objects.get(tele_id=request.session.get('user_id'))
            data = json.loads(request.body)
            wallet = Wallet.objects.create(
                user=user,
                card_number=data.get('card_number'),
                phone_number=data.get('phone_number'),
                account_number=data.get('account_number'),
                owner_name=data.get('owner_name'),
                description=data.get('description'),
                limit_transactions_per_day=data.get('limit_transactions_per_day', 0),
                limit_amount_per_day=data.get('limit_amount_per_day', 0),
                auto_disable_on_limit=data.get('auto_disable_on_limit', False),
                notify_on_disable=data.get('notify_on_disable', False)
            )
            return JsonResponse({'success': True, 'message': 'Кошелек создан!', 'wallet_id': wallet.id})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Ошибка при создании кошелька: {str(e)}'}, status=400)
    return JsonResponse({'success': False, 'message': 'Метод запроса не поддерживается'}, status=405)


@trader_required
def purchases(request):
    user_id = request.session.get('user_id')  # ID текущего пользователя
    current_user = User.objects.filter(tele_id=user_id).first()

    filter_type = request.GET.get('filter_type', 'all')

    if filter_type == 'active':  
        bids = Bid.objects.filter(status='active').order_by('-created_at')  # Активные
    elif filter_type == 'mine':  
        bids = Bid.objects.filter(user=current_user, status='pending').order_by('-created_at')  # Мои
    elif filter_type == 'completed':  
        bids = Bid.objects.filter(user=current_user, status='completed').order_by('-created_at')  # Завершенные
    else:
        bids = Bid.objects.none()  # Ничего не возвращаем
    exchange_rate = ExchangeRate.objects.first()  # Берём текущий курс
    # Таймеры для моих заявок
    for bid in bids:
        if bid.status == 'pending' and bid.accepted_at:
            # Рассчитываем оставшееся время (40 минут на оплату)
            bid.remaining_time = (bid.accepted_at + timedelta(minutes=40)) - now()

            # Если время истекло, устанавливаем 0
            if bid.remaining_time.total_seconds() < 0:
                bid.remaining_time = timedelta(seconds=0)

    return render(request, 'traderapp/purchases.html', {
        'bids': bids,
        'filter_type': filter_type,  # текущий фильтр
        "exchange_rate": exchange_rate,
    })



@trader_required
def cancel_bid(request, bid_id):
    if request.method == 'POST':
        try:
            bid = Bid.objects.get(id=bid_id)

            # Проверяем: заявка должна быть в статусе "pending" и время должно истечь
            if bid.status == 'pending' and bid.accepted_at + timedelta(minutes=40) <= now():
                bid.status = 'active'
                bid.user = None
                bid.accepted_at = None
                bid.save()
                return JsonResponse({'success': True, 'message': 'Заявка успешно отменена.'})

            return JsonResponse({'success': False, 'message': 'Неверное состояние заявки.'})
        except Bid.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Заявка не найдена.'}, status=404)
    return JsonResponse({'success': False, 'message': 'Метод запроса не поддерживается.'}, status=405)


@trader_required
def sales(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('auth')  # Если пользователь не авторизован, перенаправляем на авторизацию

    user = User.objects.filter(tele_id=user_id).first()
    session = UserSession.objects.filter(user=user, is_active=True).last()

    return render(request, 'traderapp/sell.html', {
        'user': user,
        'ip': session.ip_address if session else "IP неизвестен",
        'login_time': session.login_time if session else "Неизвестно",
    })


@trader_required
def wallets(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('auth')  # Если пользователь не авторизован, перенаправляем на авторизацию

    user = User.objects.filter(tele_id=user_id).first()
    session = UserSession.objects.filter(user=user, is_active=True).last()

    return render(request, 'traderapp/banks.html', {
        'user': user,
        'ip': session.ip_address if session else "IP неизвестен",
        'login_time': session.login_time if session else "Неизвестно",
    })

@trader_required
def update_status(request):
    if request.method == 'POST':
        try:
            # Разбираем JSON-запрос
            data = json.loads(request.body)
            bid_id = data.get('bid_id')
            new_status = data.get('status')

            # Проверяем, существует ли заявка
            bid = Bid.objects.get(id=bid_id)

            # Логика обновления: пользователь может изменять только свои заявки
            if bid.user == request.user:
                bid.status = new_status

                # Дополнительно: Если заявка завершена, оставляем её за пользователем
                if new_status == "completed":
                    bid.user = request.user
                elif new_status == "active":
                    bid.user = None  # Убираем связь пользователя

                bid.save()

                return JsonResponse({"success": True, "message": "Статус обновлён!"})

            # Если не принадлежит текущему пользователю
            return JsonResponse({"success": False, "message": "Нет прав на изменение этой заявки."}, status=403)
        
        except Bid.DoesNotExist:
            return JsonResponse({"success": False, "message": "Заявка не найдена."}, status=404)

        except Exception as e:
            return JsonResponse({"success": False, "message": "Произошла ошибка: " + str(e)}, status=500)

    return JsonResponse({"success": False, "message": "Неверный метод запроса."}, status=405)

@trader_required
def referrals(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('auth')  # Если пользователь не авторизован, перенаправляем на авторизацию

    user = User.objects.filter(tele_id=user_id).first()
    session = UserSession.objects.filter(user=user, is_active=True).last()

    return render(request, 'traderapp/referals.html', {
        'user': user,
        'ip': session.ip_address if session else "IP неизвестен",
        'login_time': session.login_time if session else "Неизвестно",
    })

@trader_required
def statistics(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('auth')  # Если пользователь не авторизован, перенаправляем на авторизацию

    user = User.objects.filter(tele_id=user_id).first()
    session = UserSession.objects.filter(user=user, is_active=True).last()

    return render(request, 'traderapp/stat.html', {
        'user': user,
        'ip': session.ip_address if session else "IP неизвестен",
        'login_time': session.login_time if session else "Неизвестно",
    })

@trader_required
def api(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('auth')  # Если пользователь не авторизован, перенаправляем на авторизацию

    user = User.objects.filter(tele_id=user_id).first()
    session = UserSession.objects.filter(user=user, is_active=True).last()

    return render(request, 'traderapp/API.html', {
        'user': user,
        'ip': session.ip_address if session else "IP неизвестен",
        'login_time': session.login_time if session else "Неизвестно",
    })

@trader_required
def settings(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('auth')  # Если пользователь не авторизован, перенаправляем на авторизацию

    user = User.objects.filter(tele_id=user_id).first()
    session = UserSession.objects.filter(user=user, is_active=True).last()

    return render(request, 'traderapp/settings.html', {
        'user': user,
        'ip': session.ip_address if session else "IP неизвестен",
        'login_time': session.login_time if session else "Неизвестно",
    })

@trader_required
def faq(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('auth')  # Если пользователь не авторизован, перенаправляем на авторизацию

    user = User.objects.filter(tele_id=user_id).first()
    session = UserSession.objects.filter(user=user, is_active=True).last()

    return render(request, 'traderapp/FAQ.html', {
        'user': user,
        'ip': session.ip_address if session else "IP неизвестен",
        'login_time': session.login_time if session else "Неизвестно",
    })

@trader_required
def deposit(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('auth')  # Если пользователь не авторизован, перенаправляем на авторизацию

    user = User.objects.filter(tele_id=user_id).first()
    session = UserSession.objects.filter(user=user, is_active=True).last()

    return render(request, 'traderapp/deposit.html', {
        'user': user,
        'ip': session.ip_address if session else "IP неизвестен",
        'login_time': session.login_time if session else "Неизвестно",
    })

@trader_required
def news_view(request):
    return render(request, 'traderapp/news.html')

 



@trader_required
def accept_bid(request, bid_id):
    if request.method == 'POST':
        # Получаем заявку
        bid = get_object_or_404(Bid, id=bid_id)
        user_id = request.session.get('user_id')
        user = User.objects.filter(tele_id=user_id).first()

        if not user:
            return JsonResponse({'success': False, 'message': 'Пользователь не найден.'}, status=403)

        action = request.POST.get('action', '')

        # Принятие активной заявки
        if bid.status == 'active' and not action:
            bid.status = 'pending'         # Меняем статус на "принята"
            bid.user = user                # Привязываем заявку к пользователю
            bid.accepted_at = now()        # Фиксируем время принятия заявки
            bid.save()

            return JsonResponse({'success': True, 'message': 'Заявка успешно принята!'})

        # Действия с заявкой в статусе "pending"
        elif bid.status == 'pending':  
            if action == 'complete':       # Завершение заявки
                bid.status = 'completed'
            elif action == 'cancel':       # Отмена заявки
                bid.status = 'active'
                bid.user = None
                bid.accepted_at = None  # Сбрасываем дату принятия, так как заявка снова активна
            else:
                return JsonResponse({'success': False, 'message': 'Недействительное действие.'}, status=400)

            bid.save()
            return JsonResponse({'success': True, 'message': 'Действие успешно выполнено!'})

        return JsonResponse({'success': False, 'message': 'Недопустимое состояние заявки.'}, status=400)

    return JsonResponse({'success': False, 'message': 'Неверный метод запроса.'}, status=405)


