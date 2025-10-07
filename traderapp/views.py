from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import now, timedelta
from functools import wraps
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from authapp.models import User, UserSession, Bid, ExchangeRate, DepositRequest, DepWallet
from django.contrib import messages  # Для системы сообщений
from uuid import UUID
from authapp.utils import get_client_ip  # Лучшая практика: перенос функции "получение IP" в отдельный файл utils.py (опционально)
import json
from django.http import JsonResponse
from authapp.models import ExchangeRate
from traderapp.utils import get_bybit_p2p_rate
from authapp.models import Wallet
from django.utils import timezone


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
    wallets = Wallet.objects.filter(user=user)  # По умолчанию отображаем все кошельки пользователя
    if request.method == 'POST':
        # Проверяем, был ли осуществлен сброс фильтров
        if 'reset' in request.POST:
            return redirect('wallets')  # Перенаправляем на другую страницу, сбрасывая параметры
    # Проверяем, есть ли полученные параметры фильтра в запросе
    bank_filter = request.POST.get('bank')
    card_number_filter = request.POST.get('card_number')
    phone_number_filter = request.POST.get('phone_number')

    # Применяем фильтры
    if bank_filter:
        wallets = wallets.filter(bank=bank_filter)
    if card_number_filter:
        wallets = wallets.filter(card_number__icontains=card_number_filter)
    if phone_number_filter:
        wallets = wallets.filter(phone_number__icontains=phone_number_filter)

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

            wallet_id = data.get('id')  # Получаем ID из входящих данных

            if wallet_id:  # Если ID существует, обновляем кошелек
                wallet = get_object_or_404(Wallet, id=wallet_id, user=user)
                # Обновление полей
                wallet.card_number = data.get('card_number')
                wallet.phone_number = data.get('phone_number')
                wallet.account_number = data.get('account_number')
                wallet.owner_name = data.get('owner_name')
                wallet.description = data.get('description')
                wallet.limit_transactions_per_day = data.get('limit_transactions_per_day', 0)
                wallet.limit_amount_per_day = data.get('limit_amount_per_day', 0)
                wallet.auto_disable_on_limit = data.get('auto_disable_on_limit', False)
                wallet.notify_on_disable = data.get('notify_on_disable', False)
                wallet.bank = data.get('bank')
                wallet.save()  # Сохраняем изменения
                message = 'Кошелек обновлен!'
            else:  # Если ID не существует, создаем новый кошелек
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
                    notify_on_disable=data.get('notify_on_disable', False),
                    bank=data.get('bank')
                )
                message = 'Кошелек создан!'

            # Преобразуем объект Wallet в словарь
            wallet_data = {
                'id': wallet.id,
                'card_number': wallet.card_number,
                'phone_number': wallet.phone_number,
                'account_number': wallet.account_number,
                'owner_name': wallet.owner_name,
                'description': wallet.description,
                'limit_transactions_per_day': wallet.limit_transactions_per_day,
                'limit_amount_per_day': wallet.limit_amount_per_day,
                'auto_disable_on_limit': wallet.auto_disable_on_limit,
                'notify_on_disable': wallet.notify_on_disable,
                'bank': wallet.bank,
                'is_enabled': wallet.is_enabled
            }

            return JsonResponse({'success': True, 'message': message, 'wallet': wallet_data})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Ошибка: {str(e)}'}, status=400)
    return JsonResponse({'success': False, 'message': 'Метод запроса не поддерживается'}, status=405)


@trader_required
def get_wallet(request, wallet_id):
    if request.method == 'GET':
        wallet = get_object_or_404(Wallet, id=wallet_id)
        wallet_data = {
            'id': wallet.id,
            'card_number': wallet.card_number,
            'phone_number': wallet.phone_number,
            'account_number': wallet.account_number,
            'owner_name': wallet.owner_name,
            'description': wallet.description,
            'limit_transactions_per_day': wallet.limit_transactions_per_day,
            'limit_amount_per_day': wallet.limit_amount_per_day,
            'auto_disable_on_limit': wallet.auto_disable_on_limit,
            'notify_on_disable': wallet.notify_on_disable,
            'bank': wallet.bank,
            'is_enabled': wallet.is_enabled
        }
        return JsonResponse({'success': True, 'wallet': wallet_data})
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
    """Обработчик страницы депозита"""
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('auth')

    user = User.objects.filter(tele_id=user_id).first()

    # Текущее серверное время
    server_time = now()

    # Обновляем статус всех истекших заявок
    DepositRequest.objects.filter(status='active', expiration_date__lt=server_time).update(status='expired')

    # Получаем заявки пользователя с нужными данными
    deposit_requests = DepositRequest.objects.filter(user=user)

    # Вычисляем оставшееся время для каждой заявки
    for deposit in deposit_requests:
        expiration_date = deposit.expiration_date
        remaining_time_sec = max(0, (expiration_date - server_time).total_seconds())  # Оставшееся время в секундах
        deposit.remaining_time = timedelta(seconds=remaining_time_sec)  # Преобразуем обратно в timedelta

    # Передаем данные в шаблон
    return render(request, 'traderapp/deposit.html', {
        'user': user,
        'server_time': server_time.isoformat(),  # Передаем серверное время отдельно
        'deposit_requests': deposit_requests
    })






@trader_required
def news_view(request):
    return render(request, 'traderapp/news.html')

@trader_required
def update_wallet_status(request, wallet_id):
    if request.method == 'POST':
        wallet = get_object_or_404(Wallet, id=wallet_id)
        wallet.toggle_enabled()
        return JsonResponse({'success': True, 'message': 'Состояние кошелька обновлено!', 'is_enabled': wallet.is_enabled})

@trader_required
def delete_wallet(request, wallet_id):
    if request.method == 'POST':
        wallet = get_object_or_404(Wallet, id=wallet_id)
        wallet.delete()
        return JsonResponse({'success': True, 'message': 'Кошелек удалён!'})



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
                
                # Добавляем сумму к балансу при завершении заявки
                if bid.extra_fee_usdt != 0:
                    user.add_balance(bid.amount_rub)  
                    user.add_balance(bid.extra_fee_usdt)  
                else:
                    user.add_balance(bid.amount_rub)  
                
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


@trader_required
def create_deposit_request(request):
    """API для создания новой заявки на пополнение"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            amount = data.get('amount')

            user = User.objects.get(tele_id=request.session.get('user_id'))
            
            server_time = now()  # Получаем текущее серверное время
            expiration_time = server_time + timedelta(minutes=2)  # Устанавливаем время истечения

            print("create_deposit_request - server_time:", server_time)
            print("create_deposit_request - expiration_time:", expiration_time)

            # Проверка доступных кошельков
            wallets = DepWallet.objects.filter(is_enabled=True)
            if not wallets.exists():
                return JsonResponse({'success': False, 'message': 'Нет доступных адресов для депозита.'}, status=400)

            wallet = wallets.first()

            # Создание новой заявки
            deposit_request = DepositRequest.objects.create(
                user=user,
                amount=amount,
                wallet_address=wallet,
                status='active',
                expiration_date=expiration_time
            )

            print("create_deposit_request - saved expiration_date:", deposit_request.expiration_date)

            # Возвращаем данные о заявке
            return JsonResponse({
                'success': True,
                'message': 'Заявка создана!',
                'request_id': deposit_request.id,
                'wallet_address': wallet.wallet_address,
                'server_time': server_time.isoformat(),  # Передача времени сервера в ISO-формате UTC
                'expiration_date': expiration_time.isoformat(),  # Время истечения заявки в ISO-формате UTC
            })

        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Ошибка: {str(e)}'}, status=400)

    return JsonResponse({'success': False, 'message': 'Метод запроса не поддерживается'}, status=405)





@trader_required
def cancel_deposit_request(request, request_id):
    """API для отмены заявки на пополнение"""
    if request.method == 'POST':
        try:
            user_id = request.session.get('user_id')
            user = get_object_or_404(User, tele_id=user_id)

            deposit_request = get_object_or_404(DepositRequest, id=request_id, user=user)
            deposit_request.status = 'canceled'
            deposit_request.save()

            return JsonResponse({'success': True, 'message': 'Заявка успешно отменена.'})

        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Ошибка: {str(e)}'}, status=400)

    return JsonResponse({'success': False, 'message': 'Неверный метод запроса.'}, status=405)