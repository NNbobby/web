from django.urls import path
from . import views

urlpatterns = [
    path('client/', views.client_dashboard, name='client_dashboard'),  # Клиентская панель
]
