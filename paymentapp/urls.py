from django.urls import path
from . import views

urlpatterns = [
    path('payment_form/', views.payment_form, name='payment_form'),
    
]
