from django.shortcuts import render
from authapp.models import User
from functools import wraps
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.contrib import messages

def client_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user_id = request.session.get('user_id')  # Проверяем наличие user_id в сессии
        if not user_id:
            messages.error(request, 'Вы не авторизованы.')
            return HttpResponseRedirect('/auth/')  # Редирект на страницу авторизации
        
        # Проверяем роль пользователя
        user = User.objects.filter(tele_id=user_id).first()
        if not user or user.role != 'client':  # Если пользователь отсутствует или роль не "client"
            messages.error(request, 'У вас нет доступа к этой странице.')
            return HttpResponseRedirect('/auth/')  # Вернуть на авторизацию
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


@client_required
def client_dashboard(request):
    user_id = request.session.get('user_id')
    user = User.objects.filter(tele_id=user_id).first()

    return render(request, 'clientapp/client_dashboard.html', {'user': user})

