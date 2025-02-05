# web/urls.py
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('authapp.urls')),  # Подключение всех маршрутов приложения authapp
    path('trade/', include('traderapp.urls')),  # Подключение всех маршрутов приложения traderapp
    path('payments/', include('paymentapp.urls')), #
    path('admin-panel/', include('adminapp.urls')), 
    path('private-lk/', include('clientapp.urls')), 
]
