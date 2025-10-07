from django.shortcuts import render, get_object_or_404, redirect
from authapp.models import User, Bid, DepWallet  # Импортируем модели из authapp
from django.contrib import messages
from django.utils.timezone import now
from functools import wraps
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Логируем user_id из сессии
        user_id = request.session.get('user_id')
        print(f"admin_required: user_id = {user_id}")
        
        if not user_id:
            messages.error(request, 'Вы не авторизованы.')
            return HttpResponseRedirect('/auth/')
        
        # Логируем пользователя
        user = User.objects.filter(tele_id=user_id).first()
        print(f"admin_required: найден пользователь: {user}")
        
        if not user:
            messages.error(request, 'Вы не авторизованы.')
            request.session.flush()
            return HttpResponseRedirect('/auth/')
        
        if user.role != 'admin':
            messages.error(request, 'У вас нет доступа к этой странице.')
            print(f"admin_required: пользователь с ролью {user.role} пытается получить доступ.")
            return HttpResponseRedirect('/auth/')
        
        print("admin_required: пользователь авторизован как администратор.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@admin_required
def delete_bid(request, bid_id):
    bid = get_object_or_404(Bid, id=bid_id)
    bid.delete()
    messages.success(request, 'Заявка успешно удалена.')
    return redirect('databaseadm')  # Возвращаемся на страницу админ-панели

@admin_required
def databaseadm(request):
    # Получаем данные из нужных таблиц
    users = User.objects.all()
    bids = Bid.objects.all()
    wallets = DepWallet.objects.all()
    return render(request, 'adminapp/databaseadm.html', {
        'users': users,
        'bids': bids,
        'wallets': wallets,
        'user': request.user  # Передаем текущего авторизованного пользователя
    })
@admin_required
def newsadm(request):
    # Получаем данные из нужных таблиц
    users = User.objects.all()
    bids = Bid.objects.all()

    return render(request, 'adminapp/newsadm.html', {
        'users': users,
        'bids': bids,
        'user': request.user  # Передаем текущего авторизованного пользователя
    })
@admin_required
def statisticsadm(request):
    # Получаем данные из нужных таблиц
    users = User.objects.all()
    bids = Bid.objects.all()

    return render(request, 'adminapp/statisticsadm.html', {
        'users': users,
        'bids': bids,
        'user': request.user  # Передаем текущего авторизованного пользователя
    })
@admin_required
def settingsadm(request):
    # Получаем данные из нужных таблиц
    users = User.objects.all()
    bids = Bid.objects.all()

    return render(request, 'adminapp/settingsadm.html', {
        'users': users,
        'bids': bids,
        'user': request.user  # Передаем текущего авторизованного пользователя
    })

@admin_required
def add_user(request):
    if request.method == 'POST':
        username = request.POST.get('username').strip()
        role = request.POST.get('role').strip()
        added_by = request.POST.get('added_by').strip()

        if User.objects.filter(username=username).exists():
            messages.error(request, f'Пользователь с именем {username} уже существует.')
            return redirect('databaseadm')

        user = User.objects.create(username=username, role=role, added_by=added_by)
        messages.success(request, f'Пользователь {user.username} успешно добавлен.')
        return redirect('databaseadm')


@admin_required
def add_bid(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')  # Получаем ID пользователя из формы
        bank = request.POST.get('bank')       # Текстовые поля для заявки
        amount_rub = request.POST.get('amount_rub')
        exchange_rate = request.POST.get('exchange_rate')
        account_details = request.POST.get('account_details')
        extra_fee = request.POST.get('extra_fee') == 'on'  # Проверяем флажок
        extra_fee_usdt = request.POST.get('extra_fee_amount')  # Извлекаем значение надбавки
        # Проверяем, выбран ли пользователь
        user = None
        if user_id:
            user = get_object_or_404(User, id=user_id)
        if extra_fee and not extra_fee_usdt:
            extra_fee_usdt = 0  # Вы можете использовать None, если это соответствует вашей логике
        # Устанавливаем статус в зависимости от пользователя
        if user:
            status = 'pending'  # Если пользователь указан
        else:
            status = 'active'  # Если пользователь НЕ указан

        # Создаём заявку
        Bid.objects.create(
            user=user,
            bank=bank,
            amount_rub=amount_rub,
            exchange_rate=exchange_rate,
            account_details=account_details,
            extra_fee=extra_fee,
            status=status,  # Устанавливаем статус
            extra_fee_usdt=extra_fee_usdt or 0,
        )

        # Редиректим на нужную страницу
        return redirect('databaseadm')  # Укажите URL редиректа

@admin_required
def add_wallet(request):
    if request.method == 'POST':
        wallet_address = request.POST.get('wallet_address')  # Получаем адрес кошелька

        # Проверяем, что wallet_address не None
        if wallet_address is None:
            messages.error(request, 'Адрес кошелька не должен быть пустым.')
            return redirect('databaseadm')

        wallet_address = wallet_address.strip()  # Убираем пробелы
        is_enabled = request.POST.get('is_enabled') == 'on'  # Проверяем, включен ли кошелек

        # Создаем новый кошелек
        DepWallet.objects.create(
            wallet_address=wallet_address,
            is_enabled=is_enabled,
            # Добавьте остальные поля, если они существуют
        )
        messages.success(request, 'Кошелек успешно добавлен.')
        return redirect('databaseadm')  # Возвращаемся к странице управления кошельками
