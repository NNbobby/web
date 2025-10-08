from django.shortcuts import render, redirect, get_object_or_404
from .models import User, UserSession
from trades.models import Bid
from django.utils.timezone import now
from django.contrib import messages  # Для системы сообщений
from uuid import UUID
from .utils import get_client_ip  # Лучшая практика: перенос функции "получение IP" в отдельный файл utils.py (опционально)
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from functools import wraps
import json
from django.http import JsonResponse
from django.utils.timezone import now, timedelta  # Работа с временем


def auth_view(request):
    """
    Проверка активных сессий и авторизация пользователя с перенаправлением по роли.
    """
    # Получаем IP клиента
    ip_address = get_client_ip(request)

    # Проверяем, существует ли активная сессия
    user_id = request.session.get('user_id')
    if user_id:
        user = User.objects.filter(tele_id=user_id).first()
        if user:
            # Перенаправляем в зависимости от роли
            if user.role == 'admin':
                return redirect('databaseadm')  # Для админа
            elif user.role == 'trader':
                return redirect('news')  # Для трейдера
            elif user.role == 'client':
                return redirect('client_dashboard')  # Для клиента

    # Если активной сессии нет, продолжаем авторизацию пользователя
    if request.method == 'POST':
        auth_key = request.POST.get('auth_key', '').strip()

        if not auth_key:
            messages.error(request, 'Вы не ввели ключ авторизации!')
            return redirect('auth')  # Перенаправляем обратно на страницу авторизации

        try:
            # Проверяем, соответствует ли ключ формату UUID
            _ = UUID(auth_key, version=4)
        except ValueError:
            messages.error(request, 'Неверный формат ключа. Попробуйте еще раз!')
            return redirect('auth')

        # Пытаемся найти пользователя по ключу
        user = User.objects.filter(token=auth_key).first()
        if not user:
            messages.error(request, 'Такого ключа нет. Доступ отклонён!')
            return redirect('auth')

        # Проверяем наличие активной сессии для этого пользователя
        user_active_session = UserSession.objects.filter(user=user, is_active=True).first()

        if user_active_session:
            # Если сессия есть, обновляем её данные
            user_active_session.ip_address = ip_address
            user_active_session.login_time = now()
            user_active_session.save()
        else:
            # Генерируем ключ сессии Django, если он отсутствует
            if not request.session.session_key:
                request.session.create()

            # Создаём новую запись активной сессии
            UserSession.objects.create(
                user=user,
                ip_address=ip_address,
                session_key=request.session.session_key,
                login_time=now(),
                is_active=True
            )

        # Сохраняем данные в сессии Django
        request.session['user_id'] = user.tele_id
        request.session['ip'] = ip_address
        request.session.set_expiry(259200)  # Срок жизни сессии (3 дня)

        messages.success(request, 'Добро пожаловать! Авторизация прошла успешно.')

        # Перенаправляем в зависимости от роли
        if user.role == 'admin':
            return redirect('databaseadm')  # Админская панель
        elif user.role == 'trader':
            return redirect('news')  # Трейдерский функционал
        elif user.role == 'client':
            return redirect('client_dashboard')  # Клиентский функционал

    return render(request, 'authapp/auth.html')

def logout_view(request):
    """
    Логаут пользователя.
    """
    user_id = request.session.get('user_id')
    if user_id:
        user = User.objects.filter(tele_id=user_id).first()
        if user:
            # Завершаем все активные сессии пользователя
            UserSession.objects.filter(user=user, is_active=True).update(is_active=False, logout_time=now())

    # Завершаем сессию в Django
    request.session.flush()
    messages.info(request, 'Вы вышли из системы. Возвращайтесь снова!')
    return redirect('auth')


# Простые представления для других страниц


